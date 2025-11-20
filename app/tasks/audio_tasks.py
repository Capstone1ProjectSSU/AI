import os
import sys
import tempfile
from pathlib import Path
from celery import Task
from app.celery_app import celery_app

# Add hiscore to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../hiscore'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../hiscore/MVSEP-MDX23-Colab_v2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../hiscore/YourMT3'))


class ProgressTask(Task):
    """Base task with progress tracking"""
    def update_progress(self, current: int, total: int, message: str = ""):
        self.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'percent': int((current / total) * 100) if total > 0 else 0,
                'message': message
            }
        )


@celery_app.task(bind=True, base=ProgressTask)
def audio_separation_task(self, file_path: str, instruments: list[str]):
    """
    Separate audio into different instrument stems

    Args:
        file_path: Path to the input audio file
        instruments: List of instruments to separate

    Returns:
        dict with separated audio file paths
    """
    job_id = self.request.id
    from demucs import pretrained
    from demucs.apply import apply_model
    import torch
    import torchaudio

    self.update_progress(0, 100, "Loading audio separation model")

    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = pretrained.get_model('htdemucs')
        model.to(device)

        self.update_progress(20, 100, "Loading audio file")

        waveform, sample_rate = torchaudio.load(file_path)
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        waveform = waveform.to(device)

        self.update_progress(40, 100, "Separating audio")

        with torch.no_grad():
            sources = apply_model(model, waveform.unsqueeze(0))

        # htdemucs outputs: drums (0), bass (1), other (2), vocals (3)
        instrument_map = {
            'drums': 0,
            'bass': 1,
            'other': 2,
            'vocals': 3,
            'piano': 2,  # Map piano to 'other' for now
            'guitar': 2  # Map guitar to 'other' for now
        }

        output_dir = Path(f"./outputs/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        progress_per_instrument = 60 / len(instruments)

        for idx, instrument in enumerate(instruments):
            instrument_idx = instrument_map.get(instrument.lower(), 2)
            separated_audio = sources[0, instrument_idx]

            output_path = output_dir / f"{instrument}.opus"

            # Convert to opus format (using .wav for now, would need opus encoder)
            output_path_wav = output_dir / f"{instrument}.wav"
            torchaudio.save(str(output_path_wav), separated_audio.cpu(), sample_rate)

            # For now, use .wav instead of .opus
            results.append({
                'instrument': instrument,
                'url': f'/outputs/{job_id}/{instrument}.wav',
                'format': 'wav'
            })

            self.update_progress(
                40 + int((idx + 1) * progress_per_instrument),
                100,
                f"Separated {instrument}"
            )

        self.update_progress(100, 100, "Audio separation completed")

        return {
            'jobId': job_id,
            'outputs': results
        }

    except Exception as e:
        raise Exception(f"Audio separation failed: {str(e)}")


@celery_app.task(bind=True, base=ProgressTask)
def audio_transcription_task(self, file_path: str, instrument: str, engine: str = "basic-pitch"):
    """
    Transcribe audio to MIDI

    Args:
        file_path: Path to the input audio file
        instrument: Target instrument name
        engine: Transcription engine ("basic-pitch" or "yourmt3")

    Returns:
        dict with transcription file path
    """
    job_id = self.request.id
    self.update_progress(0, 100, "Starting transcription")

    try:
        output_dir = Path(f"./outputs/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        temp_folder = str(output_dir)

        if engine == "basic-pitch":
            from basic_pitch_onnx import predict_basic_pitch
            import mido

            self.update_progress(20, 100, "Loading Basic Pitch model")

            model_path = os.path.join("hiscore", "basic-pitch", "basic_pitch", "saved_models", "icassp_2022", "nmp.onnx")

            self.update_progress(40, 100, "Transcribing audio")

            _, midi_data, _ = predict_basic_pitch(file_path, model_path)

            midi_path = output_dir / f"{instrument}_transcription.mid"
            midi_data.write(str(midi_path))

            # Apply BPM detection
            from hiscore.main import detect_bpm, apply_bpm_to_midi_file
            bpm = detect_bpm(file_path)
            apply_bpm_to_midi_file(str(midi_path), bpm)

        elif engine == "yourmt3":
            self.update_progress(20, 100, "Loading YourMT3 model")

            from hiscore.main import yourmt3_transcript
            midi_path = yourmt3_transcript(file_path, track_name=f'{instrument}_transcription')

            # Move to output directory
            import shutil
            final_path = output_dir / f"{instrument}_transcription.mid"
            shutil.move(midi_path, str(final_path))
            midi_path = final_path
        else:
            raise ValueError(f"Unknown transcription engine: {engine}")

        self.update_progress(100, 100, "Transcription completed")

        return {
            'jobId': job_id,
            'transcriptionUrl': f'/outputs/{job_id}/{instrument}_transcription.mid',
            'format': 'mid'
        }

    except Exception as e:
        raise Exception(f"Audio transcription failed: {str(e)}")
