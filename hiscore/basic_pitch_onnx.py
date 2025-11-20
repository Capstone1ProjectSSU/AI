#!/usr/bin/env python
# Simplified ONNX-based Basic Pitch implementation
# Extracted from basic-pitch library to avoid TensorFlow dependencies

import os
import pathlib
from typing import Dict, Tuple, List, Optional
import numpy as np
import numpy.typing as npt
import librosa
import pretty_midi
import onnxruntime as ort

# Constants from basic_pitch.constants
AUDIO_SAMPLE_RATE = 22050
AUDIO_N_SAMPLES = 43844  # Expected by the ONNX model
ANNOTATIONS_FPS = 86  # AUDIO_SAMPLE_RATE // FFT_HOP 
FFT_HOP = 256
ANNOTATIONS_N_SEMITONES = 88
ANNOTATIONS_BASE_FREQUENCY = 27.5
CONTOURS_BINS_PER_SEMITONE = 3
DEFAULT_OVERLAPPING_FRAMES = 30

# Model output processing constants
MIDI_OFFSET = 21
DEFAULT_MIN_NOTE_LEN = 11
DEFAULT_ONSET_THRESHOLD = 0.5
DEFAULT_FRAME_THRESHOLD = 0.3
DEFAULT_MINIMUM_MIDI_TEMPO = 120


class BasicPitchONNX:
    def __init__(self, model_path: str):
        """Initialize ONNX model for Basic Pitch inference."""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        # Set up ONNX runtime with CPU provider (avoiding CUDA issues)
        providers = ["CPUExecutionProvider"]
        self.model = ort.InferenceSession(model_path, providers=providers)
    
    def predict(self, audio_input: npt.NDArray[np.float32]) -> Dict[str, npt.NDArray[np.float32]]:
        """Run inference on audio input."""
        result = self.model.run(
            [
                "StatefulPartitionedCall:1",  # note
                "StatefulPartitionedCall:2",  # onset  
                "StatefulPartitionedCall:0",  # contour
            ],
            {"serving_default_input_2:0": audio_input},
        )
        
        return {
            "note": result[0],
            "onset": result[1], 
            "contour": result[2],
        }


def window_audio_file(audio_original: npt.NDArray[np.float32], hop_size: int):
    """Window audio file into fixed-size chunks."""
    for i in range(0, audio_original.shape[0], hop_size):
        window = audio_original[i : i + AUDIO_N_SAMPLES]
        if len(window) < AUDIO_N_SAMPLES:
            window = np.pad(
                window,
                pad_width=[[0, AUDIO_N_SAMPLES - len(window)]],
            )
        t_start = float(i) / AUDIO_SAMPLE_RATE
        window_time = {
            "start": t_start,
            "end": t_start + (AUDIO_N_SAMPLES / AUDIO_SAMPLE_RATE),
        }
        yield np.expand_dims(window, axis=-1), window_time


def get_audio_input(audio_path: str, overlap_len: int, hop_size: int):
    """Load and window audio file."""
    assert overlap_len % 2 == 0, f"overlap_length must be even, got {overlap_len}"
    
    audio_original, _ = librosa.load(audio_path, sr=AUDIO_SAMPLE_RATE, mono=True)
    original_length = audio_original.shape[0]
    audio_original = np.concatenate([
        np.zeros((int(overlap_len / 2),), dtype=np.float32), 
        audio_original
    ])
    
    for window, window_time in window_audio_file(audio_original, hop_size):
        yield np.expand_dims(window, axis=0), window_time, original_length


def unwrap_output(
    output: npt.NDArray[np.float32],
    audio_original_length: int,
    n_overlapping_frames: int,
) -> np.array:
    """Unwrap batched model predictions to a single matrix."""
    if len(output.shape) != 3:
        return None

    n_olap = int(0.5 * n_overlapping_frames)
    if n_olap > 0:
        # remove half of the overlapping frames from beginning and end
        output = output[:, n_olap:-n_olap, :]

    output_shape = output.shape
    n_output_frames_original = int(np.floor(
        audio_original_length * (ANNOTATIONS_FPS / AUDIO_SAMPLE_RATE)
    ))
    unwrapped_output = output.reshape(
        output_shape[0] * output_shape[1], 
        output_shape[2]
    )
    return unwrapped_output[:n_output_frames_original, :]


def simple_note_extraction(
    frames: np.array,
    onsets: np.array,
    onset_thresh: float = DEFAULT_ONSET_THRESHOLD,
    frame_thresh: float = DEFAULT_FRAME_THRESHOLD,
    min_note_len: int = DEFAULT_MIN_NOTE_LEN,
    midi_tempo: float = DEFAULT_MINIMUM_MIDI_TEMPO,
) -> Tuple[pretty_midi.PrettyMIDI, List[Tuple[float, float, int, float]]]:
    """Simple note extraction from model outputs."""
    
    # Create MIDI object
    midi = pretty_midi.PrettyMIDI(initial_tempo=midi_tempo)
    instrument = pretty_midi.Instrument(program=0)  # Piano
    
    note_events = []
    
    # Simple peak detection approach
    time_step = 1.0 / ANNOTATIONS_FPS
    
    for freq_idx in range(frames.shape[1]):
        # Find onsets above threshold
        onset_frames = np.where(onsets[:, freq_idx] > onset_thresh)[0]
        
        for onset_frame in onset_frames:
            # Look for end of note (where frame activation drops below threshold)
            end_frame = onset_frame + 1
            while (end_frame < frames.shape[0] and 
                   frames[end_frame, freq_idx] > frame_thresh):
                end_frame += 1
            
            # Check minimum note length
            if end_frame - onset_frame >= min_note_len:
                start_time = onset_frame * time_step
                end_time = end_frame * time_step
                midi_note = freq_idx + MIDI_OFFSET
                
                # Get average amplitude for velocity
                amplitude = np.mean(frames[onset_frame:end_frame, freq_idx])
                velocity = int(min(127, max(1, amplitude * 127)))
                
                # Create MIDI note
                note = pretty_midi.Note(
                    velocity=velocity,
                    pitch=midi_note,
                    start=start_time,
                    end=end_time,
                )
                instrument.notes.append(note)
                
                # Add to note events list
                note_events.append((start_time, end_time, midi_note, amplitude))
    
    midi.instruments.append(instrument)
    return midi, note_events


def run_inference(audio_path: str, model_path: str) -> Dict[str, np.array]:
    """Run Basic Pitch inference on audio file."""
    model = BasicPitchONNX(model_path)
    
    # Setup windowing parameters
    n_overlapping_frames = DEFAULT_OVERLAPPING_FRAMES
    overlap_len = n_overlapping_frames * FFT_HOP
    hop_size = AUDIO_N_SAMPLES - overlap_len
    
    output = {"note": [], "onset": [], "contour": []}
    
    for audio_windowed, _, audio_original_length in get_audio_input(
        audio_path, overlap_len, hop_size
    ):
        predictions = model.predict(audio_windowed)
        for k, v in predictions.items():
            output[k].append(v)
    
    # Unwrap outputs
    unwrapped_output = {
        k: unwrap_output(
            np.concatenate(output[k]), 
            audio_original_length, 
            n_overlapping_frames
        ) 
        for k in output
    }
    
    return unwrapped_output


def predict_basic_pitch(
    audio_path: str,
    model_path: str,
    onset_threshold: float = DEFAULT_ONSET_THRESHOLD,
    frame_threshold: float = DEFAULT_FRAME_THRESHOLD,
    minimum_note_length_ms: float = 127.7,
    midi_tempo: float = DEFAULT_MINIMUM_MIDI_TEMPO,
) -> Tuple[Dict[str, np.array], pretty_midi.PrettyMIDI, List[Tuple[float, float, int, float]]]:
    """Predict MIDI from audio using Basic Pitch ONNX model."""
    
    print(f"Running Basic Pitch inference on {audio_path}...")
    
    # Run model inference
    model_output = run_inference(audio_path, model_path)
    
    # Convert minimum note length from ms to frames
    min_note_len = int(np.round(
        minimum_note_length_ms / 1000 * (AUDIO_SAMPLE_RATE / FFT_HOP)
    ))
    
    # Extract notes from model output
    midi_data, note_events = simple_note_extraction(
        model_output["note"],
        model_output["onset"],
        onset_thresh=onset_threshold,
        frame_thresh=frame_threshold,
        min_note_len=min_note_len,
        midi_tempo=midi_tempo,
    )
    
    return model_output, midi_data, note_events