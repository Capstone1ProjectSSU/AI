import argparse
import os
import sys
import tempfile
import subprocess
from dataclasses import dataclass
from typing import Literal
import numpy as np
from pathlib import Path

sys.path.append('MVSEP-MDX23-Colab_v2')
sys.path.append('YourMT3')
sys.path.append('YourMT3/amt/src')

# from inference import demix_wrapper, get_models  # Not needed with direct Demucs usage
import mido

def main():
    print("Hello from hiscore!")

TranscriptMode = Literal["vocal", "guitar", "bass", "piano"]
TranscriberEngine = Literal["yourmt3", "basic-pitch"]

@dataclass
class Arguments:
    input_audio: str
    mode: TranscriptMode
    transcriber: TranscriberEngine
    format: Literal["html", "pdf"]
    output_folder: str
    keep_temp: bool = False

def parse_args()->Arguments:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", "-m", type=str, default="piano", choices=TranscriptMode.__args__)
    parser.add_argument("--transcriber", "-t", type=str, default="yourmt3", choices=TranscriberEngine.__args__, help="Transcription engine to use")
    parser.add_argument("--input_audio" ,"-i", type=str, required=True)
    parser.add_argument("--format", "-f", type=str, default="html", choices=["html", "pdf"])
    parser.add_argument("--output_folder", "-o", type=str, default="output")
    parser.add_argument("--keep_temp", "-k", action="store_true", help="Keep temporary files for debugging")
    args = parser.parse_args()  
    return Arguments(
        input_audio=args.input_audio,
        mode=args.mode,
        transcriber=args.transcriber,
        format=args.format,
        output_folder=args.output_folder,
        keep_temp=args.keep_temp
    )

def audio_separation(args: Arguments, target: TranscriptMode, temp_folder: str):
    # Use Demucs for simpler and more reliable audio separation
    from demucs import pretrained
    from demucs.apply import apply_model
    import torch
    import torchaudio
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Load pre-trained Demucs model  
    model = pretrained.get_model('htdemucs')
    model.to(device)
    
    # Load and process audio
    waveform, sample_rate = torchaudio.load(args.input_audio)
    if waveform.shape[0] == 1:  # Convert mono to stereo
        waveform = waveform.repeat(2, 1)
    
    waveform = waveform.to(device)
    
    # Apply separation
    with torch.no_grad():
        sources = apply_model(model, waveform.unsqueeze(0))
    
    # Extract bass (index 1 in htdemucs: drums, bass, other, vocals)
    bass_audio = sources[0, 1]  # Get bass channel
    
    # Save separated bass track
    bass_path = os.path.join(temp_folder, f'{target}_separated.wav')
    torchaudio.save(bass_path, bass_audio.cpu(), sample_rate)
    
    return bass_path

def bass_note_simplification(midi_path: str, temp_folder: str):
    # For now, just return the original midi path without modification
    # In the future, this could implement bass note simplification logic
    return midi_path

def render_tablature(midi_path: str, temp_folder: str, format: Literal["html", "pdf"]):
    output_file = os.path.join(temp_folder, f'tablature.{format}')
    
    # Use MuseScore AppImage to convert MIDI to tablature
    musescore_path = './bin/msscore.AppImage'
    
    try:
        if format == "html":
            cmd = [musescore_path, midi_path, '-o', output_file]
        else:  # pdf
            cmd = [musescore_path, midi_path, '-o', output_file]
        env = os.environ.copy()
        env.setdefault('QT_QPA_PLATFORM', 'offscreen')
        subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error running MuseScore: {e}")
        print(f"stderr: {e.stderr}")
        raise


def piano_transcript(args: Arguments):
    # Create temp folder
    if args.keep_temp:
        temp_folder = tempfile.mkdtemp(prefix='hiscore_debug_')
        print(f"Debug: Using temp folder (will be kept): {temp_folder}")
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory()
        temp_folder = temp_context.__enter__()
    
    try:
        # For piano we don't separate stems by default; operate on full mix
        audio_path = args.input_audio

        # Choose transcription engine
        if args.transcriber == "basic-pitch":
            midi_path = basic_pitch_transcript(audio_path, temp_folder, track_name='piano')
        elif args.transcriber == "yourmt3":
            midi_path = yourmt3_transcript(audio_path, track_name='piano_transcription')
        else:
            raise ValueError(f"Unknown transcriber: {args.transcriber}")

        # Render sheet (not tablature) using MuseScore export
        output_file = os.path.join(temp_folder, f'piano_sheet.{args.format}')
        musescore_path = './bin/msscore.AppImage'
        render_ok = True
        try:
            cmd = [musescore_path, midi_path, '-o', output_file]
            env = os.environ.copy()
            env.setdefault('QT_QPA_PLATFORM', 'offscreen')
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
        except subprocess.CalledProcessError as e:
            print(f"Error running MuseScore: {e}")
            print(f"stderr: {e.stderr}")
            render_ok = False

        # Copy result to output folder
        os.makedirs(args.output_folder, exist_ok=True)
        if render_ok and os.path.exists(output_file):
            final_output = os.path.join(args.output_folder, f'piano_sheet.{args.format}')
            import shutil
            shutil.copy2(output_file, final_output)
            if args.keep_temp:
                print(f"Debug: Temp files kept in: {temp_folder}")
                print(f"Debug: MIDI file: {midi_path}")
                print(f"Debug: Sheet: {output_file}")
            return final_output
        else:
            # Fallback: provide MIDI file if rendering failed
            final_output = os.path.join(args.output_folder, 'piano_transcription.mid')
            import shutil
            shutil.copy2(midi_path, final_output)
            if args.keep_temp:
                print(f"Debug: Temp files kept in: {temp_folder}")
                print(f"Debug: MIDI file: {midi_path}")
                print(f"Debug: Sheet render failed, provided MIDI instead")
            return final_output
    finally:
        if temp_context:
            temp_context.__exit__(None, None, None)


def detect_bpm_with_madmom(audio_path: str) -> float:
    try:
        from madmom.features.tempo import CNNTempoProcessor, DBNTempoEstimationProcessor
    except ImportError as e:
        raise ImportError(
            "madmom is required for BPM detection. Install it with: pip install madmom"
        ) from e

    activation = CNNTempoProcessor()(audio_path)
    tempo_estimates = DBNTempoEstimationProcessor(fps=100)(activation)

    # tempo_estimates is typically an array like [[bpm1, weight1], [bpm2, weight2]]
    primary = tempo_estimates[0]
    bpm = float(primary[0]) if isinstance(primary, (list, tuple, np.ndarray)) else float(primary)
    return bpm


def detect_bpm_with_librosa(audio_path: str) -> float:
    try:
        import librosa
    except ImportError as e:
        raise ImportError(
            "librosa is required for BPM fallback. Install it with: pip install librosa"
        ) from e

    y, sr = librosa.load(audio_path, sr=None, mono=True)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo_value = np.asarray(tempo).reshape(-1)[0]
    return float(tempo_value)


def detect_bpm(audio_path: str) -> float:
    try:
        return detect_bpm_with_madmom(audio_path)
    except Exception:
        try:
            return detect_bpm_with_librosa(audio_path)
        except Exception:
            return 120.0


def apply_bpm_to_midi(midi_file: mido.MidiFile, bpm: float) -> None:
    tempo_us_per_beat = mido.bpm2tempo(bpm)
    if not midi_file.tracks:
        from mido import MidiTrack
        midi_file.tracks.append(MidiTrack())
    track = midi_file.tracks[0]

    set_tempo_msg = mido.MetaMessage('set_tempo', tempo=tempo_us_per_beat, time=0)

    # Replace existing set_tempo if present, else insert at start
    for idx, msg in enumerate(track):
        if msg.type == 'set_tempo':
            track[idx] = set_tempo_msg
            break
    else:
        track.insert(0, set_tempo_msg)


def apply_bpm_to_midi_file(midi_path: str, bpm: float) -> None:
    mid = mido.MidiFile(midi_path)
    tempo_us_per_beat = mido.bpm2tempo(bpm)
    if not mid.tracks:
        from mido import MidiTrack
        track = MidiTrack()
        mid.tracks.append(track)
    else:
        track = mid.tracks[0]

    # Replace existing set_tempo if present, else insert at start
    for idx, msg in enumerate(track):
        if msg.type == 'set_tempo':
            track[idx] = mido.MetaMessage('set_tempo', tempo=tempo_us_per_beat, time=msg.time)
            break
    else:
        track.insert(0, mido.MetaMessage('set_tempo', tempo=tempo_us_per_beat, time=0))

    mid.save(midi_path)


def basic_pitch_transcript(audio_path: str, temp_folder: str, track_name: str = 'bass') -> str:
    print("Loading Basic Pitch ONNX model...")
    try:
        from basic_pitch_onnx import predict_basic_pitch
    except ImportError as e:
        raise ImportError(f"Failed to import basic_pitch_onnx module: {e}")
    
    # Path to the ONNX model
    model_path = os.path.join("basic-pitch", "basic_pitch", "saved_models", "icassp_2022", "nmp.onnx")
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Basic Pitch ONNX model not found at: {model_path}\n"
            "Please ensure the basic-pitch directory is present with the ONNX model."
        )
    
    print("Transcribing audio to MIDI with Basic Pitch...")
    
    # Use our simplified ONNX implementation
    _, midi_data, _ = predict_basic_pitch(audio_path, model_path)

    # Save the MIDI file first
    midi_path = os.path.join(temp_folder, f'{track_name}_transcription_basic_pitch.mid')
    midi_data.write(midi_path)

    # Detect tempo and apply to the saved MIDI file
    bpm = detect_bpm(audio_path)
    apply_bpm_to_midi_file(midi_path, bpm)
    
    return midi_path

def yourmt3_transcript(audio_path: str, track_name: str = 'transcription') -> str:
    print("Loading YourMT3 model...")
    # Lazy import to avoid preloading cost
    from model_helper import load_model_checkpoint, transcribe
    model_name = 'YPTF.MoE+Multi (noPS)'
    precision = '16'
    project = '2024'
    
    if model_name == "YPTF.MoE+Multi (noPS)":
        checkpoint = "mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops@last.ckpt"
        model_args = [checkpoint, '-p', project, '-tk', 'mc13_full_plus_256', '-dec', 'multi-t5',
                '-nl', '26', '-enc', 'perceiver-tf', '-sqr', '1', '-ff', 'moe',
                '-wf', '4', '-nmoe', '8', '-kmoe', '2', '-act', 'silu', '-epe', 'rope',
                '-rp', '1', '-ac', 'spec', '-hop', '300', '-atc', '1', '-pr', precision]
    
    device = "cpu"
    
    old_cwd = os.getcwd()
    os.chdir('YourMT3')
    try:
        model = load_model_checkpoint(args=model_args, device=device)
    finally:
        os.chdir(old_cwd)
    
    print("Transcribing audio to MIDI with YourMT3...")
    audio_info = {
        'filepath': audio_path,
        'track_name': track_name
    }
    
    midi_path = transcribe(model, audio_info)
    return midi_path


def bass_transcript(args: Arguments):
    # Create temp folder
    if args.keep_temp:
        temp_folder = tempfile.mkdtemp(prefix='hiscore_debug_')
        print(f"Debug: Using temp folder (will be kept): {temp_folder}")
        temp_context = None
    else:
        temp_context = tempfile.TemporaryDirectory()
        temp_folder = temp_context.__enter__()
    
    try:
        # Separate audio to extract bass
        bass_audio_path = audio_separation(args, "bass", temp_folder)
        
        # Choose transcription engine
        if args.transcriber == "basic-pitch":
            midi_path = basic_pitch_transcript(bass_audio_path, temp_folder, track_name='bass')
        elif args.transcriber == "yourmt3":
            midi_path = yourmt3_transcript(bass_audio_path, track_name='bass_transcription')
        else:
            raise ValueError(f"Unknown transcriber: {args.transcriber}")
        
        # Simplify bass notes
        simplified_midi_path = bass_note_simplification(midi_path, temp_folder)
        
        # Render tablature
        tablature_path = render_tablature(simplified_midi_path, temp_folder, args.format)
        
        # Copy result to output folder
        os.makedirs(args.output_folder, exist_ok=True)
        final_output = os.path.join(args.output_folder, f'bass_tablature.{args.format}')
        
        if os.path.exists(tablature_path):
            import shutil
            shutil.copy2(tablature_path, final_output)
            if args.keep_temp:
                print(f"Debug: Temp files kept in: {temp_folder}")
                print(f"Debug: Bass audio: {bass_audio_path}")
                print(f"Debug: MIDI file: {midi_path}")
                print(f"Debug: Tablature: {tablature_path}")
            return final_output
        else:
            raise FileNotFoundError(f"Tablature file not found: {tablature_path}")
    finally:
        if temp_context:
            temp_context.__exit__(None, None, None)


def main_impl(args: Arguments):
    match args.mode:
        case "vocal":
            raise NotImplementedError("Vocal mode is not implemented yet")
        case "guitar":
            raise NotImplementedError("Guitar mode is not implemented yet")
        case "bass":
            result = bass_transcript(args)
            print(f"Bass tablature generated: {result}")
            return result
        case "piano":
            result = piano_transcript(args)
            print(f"Piano sheet generated: {result}")
            return result

if __name__ == "__main__":
    args = parse_args()
    main_impl(args)