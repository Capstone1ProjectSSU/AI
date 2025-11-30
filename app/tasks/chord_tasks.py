import os
import sys
import json
from pathlib import Path
from celery import Task
from app.celery_app import celery_app

# Add halmoni to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../halmoni'))
# Add noten to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../noten/src'))


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
def chord_recognition_task(self, midi_file_path: str, format: str = "json"):
    """
    Recognize chords from MIDI file

    Args:
        midi_file_path: Path to the MIDI file
        format: Output format ('json' or 'txt')

    Returns:
        dict with chord progression file path
    """
    job_id = self.request.id
    from halmoni import MIDIAnalyzer, ChordDetector, KeyDetector, ChordProgression

    self.update_progress(0, 100, "Loading MIDI file")

    try:
        # Analyze MIDI file
        analyzer = MIDIAnalyzer()
        midi_data = analyzer.load_midi_file(midi_file_path)

        self.update_progress(30, 100, "Detecting chords")

        # Detect chords
        detector = ChordDetector()
        # get_time_windows expects a flat list of notes
        all_notes = midi_data['notes']  # Already a flat list
        time_windows = analyzer.get_time_windows(all_notes, window_size=1.0)

        chords = []
        for window_start, window_notes in time_windows:
            notes = analyzer.group_simultaneous_notes(window_notes)
            if notes:
                chord = detector.detect_chord_from_midi_notes(notes[0])
                if chord:
                    chords.append(chord)

        self.update_progress(60, 100, "Detecting key")

        # Detect key
        key_detector = KeyDetector()
        key, confidence = key_detector.detect_key_from_midi_notes(all_notes)

        self.update_progress(80, 100, "Creating chord progression")

        # Create progression
        progression = ChordProgression(chords=chords, key=key)

        output_dir = Path(f"./outputs/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare chord data
        chord_data = [{'symbol': str(chord), 'duration': 1.0} for chord in chords]

        if format == "json":
            output_path = output_dir / "chord_progression.json"
            progression_data = {
                'key': str(key) if key else None,
                'chords': chord_data
            }
            with open(output_path, 'w') as f:
                json.dump(progression_data, f, indent=2)
        else:  # txt
            output_path = output_dir / "chord_progression.txt"
            with open(output_path, 'w') as f:
                if key:
                    f.write(f"Key: {key}\n\n")
                f.write(' - '.join(str(chord) for chord in chords))

        # Create unified format
        from app.chord_format_utils import create_unified_progression
        try:
            unified_progression = create_unified_progression(
                chords=chord_data,
                key=str(key) if key else None,
                time_signature='4/4'
            )
            # Save unified format
            unified_path = output_dir / "unified_progression.json"
            with open(unified_path, 'w') as f:
                json.dump(unified_progression, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to create unified format: {e}")
            unified_progression = None

        self.update_progress(100, 100, "Chord recognition completed")

        return {
            'jobId': job_id,
            'chordProgressionUrl': f'/outputs/{job_id}/chord_progression.{format}',
            'format': format,
            'unifiedProgression': unified_progression
        }

    except Exception as e:
        raise Exception(f"Chord recognition failed: {str(e)}")


@celery_app.task(bind=True, base=ProgressTask)
def easier_chord_recommendation_task(
    self, chord_file_path: str, target_instrument: str, format: str = "json"
):
    """
    Recommend easier chord alternatives for an instrument

    Args:
        chord_file_path: Path to the chord progression file
        target_instrument: Target instrument name
        format: Output format ('json' or 'txt')

    Returns:
        dict with easier chord progression file path
    """
    job_id = self.request.id
    from halmoni import ChordProgression, Key, Chord, ChordSuggestionEngine
    from halmoni.instruments import GuitarDifficulty, PianoDifficulty, BassDifficulty

    self.update_progress(0, 100, "Loading chord progression")

    def parse_key_string(key_str):
        """Parse key string like 'G# Major' into Key object"""
        from halmoni import Note
        if not key_str:
            return Key(Note('C', 4), 'major')
        parts = key_str.strip().split()
        if len(parts) == 2:
            tonic_str, mode_str = parts
            tonic = Note(tonic_str, 4)  # Use octave 4 as default
            mode = mode_str.lower()
            return Key(tonic, mode)
        return Key(Note('C', 4), 'major')

    try:
        # Load chord progression
        with open(chord_file_path, 'r') as f:
            if format == "json":
                data = json.load(f)
                key_str = data.get('key')
                key = parse_key_string(key_str)
                chord_symbols = [c['symbol'] for c in data['chords']]
            else:
                content = f.read()
                lines = content.split('\n')
                key = Key(Note('C', 4), 'major')
                for line in lines:
                    if line.startswith('Key:'):
                        key_str = line.replace('Key:', '').strip()
                        key = parse_key_string(key_str)
                        break
                chord_line = [l for l in lines if '-' in l][0] if any('-' in l for l in lines) else ''
                chord_symbols = [c.strip() for c in chord_line.split('-')]

        chords = [Chord.from_symbol(sym) for sym in chord_symbols]
        progression = ChordProgression(chords=chords, key=key)

        self.update_progress(30, 100, "Analyzing chord difficulty")

        # Select difficulty analyzer based on instrument
        if target_instrument.lower() == 'guitar':
            difficulty_analyzer = GuitarDifficulty()
        elif target_instrument.lower() == 'piano':
            difficulty_analyzer = PianoDifficulty()
        elif target_instrument.lower() == 'bass':
            difficulty_analyzer = BassDifficulty()
        else:
            difficulty_analyzer = None

        self.update_progress(50, 100, "Finding easier alternatives")

        # Find easier alternatives
        easier_chords = []
        for chord in chords:
            if difficulty_analyzer:
                difficulty_info = difficulty_analyzer.analyze_chord_difficulty(chord)
                difficulty = difficulty_info.get('difficulty_score', 0.0) / 10.0  # Normalize to 0-1
                if difficulty > 0.7:  # If difficult, try to simplify
                    # Suggest simpler voicing or alternative
                    engine = ChordSuggestionEngine()
                    suggestions = engine.get_suggestions_for_position(progression, len(easier_chords), key)
                    if suggestions:
                        easier_chords.append(suggestions[0].chord)
                    else:
                        easier_chords.append(chord)
                else:
                    easier_chords.append(chord)
            else:
                easier_chords.append(chord)

        self.update_progress(80, 100, "Saving easier chord progression")

        output_dir = Path(f"./outputs/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare chord data
        chord_data = [{'symbol': str(chord), 'duration': 1.0} for chord in easier_chords]

        if format == "json":
            output_path = output_dir / "easier_chord_progression.json"
            progression_data = {
                'key': str(key),
                'instrument': target_instrument,
                'chords': chord_data
            }
            with open(output_path, 'w') as f:
                json.dump(progression_data, f, indent=2)
        else:  # txt
            output_path = output_dir / "easier_chord_progression.txt"
            with open(output_path, 'w') as f:
                f.write(f"Key: {key}\n")
                f.write(f"Instrument: {target_instrument}\n\n")
                f.write(' - '.join(str(chord) for chord in easier_chords))

        # Create unified format
        from app.chord_format_utils import create_unified_progression
        try:
            unified_progression = create_unified_progression(
                chords=chord_data,
                key=str(key),
                time_signature='4/4'
            )
            # Save unified format
            unified_path = output_dir / "unified_progression.json"
            with open(unified_path, 'w') as f:
                json.dump(unified_progression, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to create unified format: {e}")
            unified_progression = None

        self.update_progress(100, 100, "Easier chord recommendation completed")

        return {
            'jobId': job_id,
            'easierChordProgressionUrl': f'/outputs/{job_id}/easier_chord_progression.{format}',
            'format': format,
            'unifiedProgression': unified_progression
        }

    except Exception as e:
        raise Exception(f"Easier chord recommendation failed: {str(e)}")


@celery_app.task(bind=True, base=ProgressTask)
def e2e_base_ready_task(self, audio_file_path: str, instrument: str):
    """
    End-to-end pipeline: separation + transcription + chord recognition

    Args:
        audio_file_path: Path to the input audio file
        instrument: Target instrument name

    Returns:
        dict with all output file paths
    """
    job_id = self.request.id
    from demucs import pretrained
    from demucs.apply import apply_model
    import torch
    import torchaudio
    from halmoni import MIDIAnalyzer, ChordDetector, KeyDetector, ChordProgression
    import json

    self.update_progress(0, 100, "Starting E2E pipeline")

    try:
        output_dir = Path(f"./outputs/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Audio separation
        self.update_progress(10, 100, "Separating audio")

        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = pretrained.get_model('htdemucs')
        model.to(device)

        waveform, sample_rate = torchaudio.load(audio_file_path)
        if waveform.shape[0] == 1:
            waveform = waveform.repeat(2, 1)
        waveform = waveform.to(device)

        with torch.no_grad():
            sources = apply_model(model, waveform.unsqueeze(0))

        # Get instrument index (bass=1, drums=0, other=2, vocals=3)
        instrument_map = {'drums': 0, 'bass': 1, 'other': 2, 'vocals': 3, 'piano': 2, 'guitar': 2}
        instrument_idx = instrument_map.get(instrument.lower(), 2)
        separated_audio = sources[0, instrument_idx]

        separated_audio_path = output_dir / f"{instrument}_separated.wav"
        torchaudio.save(str(separated_audio_path), separated_audio.cpu(), sample_rate)
        separated_audio_url = f'/outputs/{job_id}/{instrument}_separated.wav'

        # Step 2: Transcription
        self.update_progress(40, 100, "Transcribing audio")

        from hiscore.basic_pitch_onnx import predict_basic_pitch
        model_path = os.path.join("hiscore", "basic-pitch", "basic_pitch", "saved_models", "icassp_2022", "nmp.onnx")

        _, midi_data, _ = predict_basic_pitch(str(separated_audio_path), model_path)

        midi_path = output_dir / f"{instrument}_transcription.mid"
        midi_data.write(str(midi_path))

        # Apply BPM detection (temporarily disabled)
        # from hiscore.main import detect_bpm, apply_bpm_to_midi_file
        # bpm = detect_bpm(str(separated_audio_path))
        # apply_bpm_to_midi_file(str(midi_path), bpm)

        transcription_url = f'/outputs/{job_id}/{instrument}_transcription.mid'

        # Step 3: Chord recognition
        self.update_progress(70, 100, "Recognizing chords")

        analyzer = MIDIAnalyzer()
        midi_data_analysis = analyzer.load_midi_file(str(midi_path))

        detector = ChordDetector()
        # get_time_windows expects a flat list of notes
        all_notes_flat = midi_data_analysis['notes']  # Already a flat list
        time_windows = analyzer.get_time_windows(all_notes_flat, window_size=1.0)

        chords = []
        for window_start, window_notes in time_windows:
            notes = analyzer.group_simultaneous_notes(window_notes)
            if notes:
                chord = detector.detect_chord_from_midi_notes(notes[0])
                if chord:
                    chords.append(chord)

        key_detector = KeyDetector()
        all_notes = all_notes_flat
        key, confidence = key_detector.detect_key_from_midi_notes(all_notes)

        progression = ChordProgression(chords=chords, key=key)

        chord_output_path = output_dir / "chord_progression.json"
        progression_data = {
            'key': str(key) if key else None,
            'chords': [{'symbol': str(chord), 'duration': 1.0} for chord in chords]
        }
        with open(chord_output_path, 'w') as f:
            json.dump(progression_data, f, indent=2)

        chord_progression_url = f'/outputs/{job_id}/chord_progression.json'

        self.update_progress(100, 100, "E2E pipeline completed")

        return {
            'jobId': job_id,
            'transcriptionUrl': transcription_url,
            'separatedAudioUrl': separated_audio_url,
            'chordProgressionUrl': chord_progression_url,
            'format': 'json'
        }

    except Exception as e:
        raise Exception(f"E2E pipeline failed: {str(e)}")


@celery_app.task(bind=True, base=ProgressTask)
def chord_complexification_task(
    self, chord_file_path: str, target_style: str, format: str = "noten"
):
    """
    Complexify chord progression using LLM

    Args:
        chord_file_path: Path to the chord progression file
        target_style: Target style for complexification (e.g., 'jazz', 'gospel')
        format: Output format ('noten', 'json', or 'txt')

    Returns:
        dict with complexified chord progression file path and unified format
    """
    job_id = self.request.id

    self.update_progress(0, 100, "Loading chord progression")

    try:
        # Import necessary modules
        from app.chord_format_utils import create_unified_progression, create_noten_from_chords
        import anthropic

        # Check for API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        # Load chord progression
        with open(chord_file_path, 'r') as f:
            if chord_file_path.endswith('.json'):
                data = json.load(f)
                key_str = data.get('key')
                time_sig = data.get('timeSignature', '4/4')
                chords = data.get('chords', [])

                # Convert to noten format for LLM input
                input_noten = create_noten_from_chords(chords, key_str, time_sig)
            else:
                # Assume it's already in noten or txt format
                input_noten = f.read()
                key_str = None
                time_sig = '4/4'

        self.update_progress(20, 100, "Preparing LLM prompt")

        # Create LLM prompt for chord complexification
        prompt = f"""You are a music theory expert. Please complexify the following chord progression in {target_style} style.

Add more sophisticated chords, extensions (7ths, 9ths, 11ths, 13ths), alterations, and substitute chords while maintaining the harmonic function and musical coherence.

Original progression in noten format:
{input_noten}

Please output the complexified progression in the same noten format. Keep the same structure (measures, timing) but use more complex chords.

Output ONLY the noten format chart, without any explanations."""

        self.update_progress(40, 100, "Calling LLM for complexification")

        # Call Anthropic API
        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract noten output from LLM response
        llm_output = message.content[0].text.strip()

        # Clean up output if it contains markdown code blocks
        if '```' in llm_output:
            # Extract content between code blocks
            lines = llm_output.split('\n')
            in_code_block = False
            clean_lines = []
            for line in lines:
                if line.strip().startswith('```'):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (not line.strip().startswith('```')):
                    clean_lines.append(line)
            llm_output = '\n'.join(clean_lines).strip()

        self.update_progress(70, 100, "Processing LLM output")

        # Parse the LLM output to create unified format
        try:
            from noten import parse, calculate_durations

            unified_progression = create_unified_progression(
                noten_string=llm_output,
                key=key_str,
                time_signature=time_sig
            )
        except Exception as e:
            print(f"Warning: Failed to parse noten output: {e}")
            # Fallback: save as-is without unified format
            unified_progression = None

        self.update_progress(85, 100, "Saving complexified progression")

        # Save output
        output_dir = Path(f"./outputs/{job_id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        if format == "noten":
            output_path = output_dir / "complexified_chord_progression.noten"
            with open(output_path, 'w') as f:
                f.write(llm_output)
        elif format == "json":
            output_path = output_dir / "complexified_chord_progression.json"
            # Save unified format as JSON
            with open(output_path, 'w') as f:
                json.dump(unified_progression if unified_progression else {'noten': llm_output}, f, indent=2)
        else:  # txt
            output_path = output_dir / "complexified_chord_progression.txt"
            with open(output_path, 'w') as f:
                f.write(llm_output)

        # Also save unified format separately
        if unified_progression:
            unified_path = output_dir / "unified_progression.json"
            with open(unified_path, 'w') as f:
                json.dump(unified_progression, f, indent=2)

        self.update_progress(100, 100, "Chord complexification completed")

        return {
            'jobId': job_id,
            'complexifiedChordProgressionUrl': f'/outputs/{job_id}/complexified_chord_progression.{format}',
            'format': format,
            'unifiedProgression': unified_progression
        }

    except Exception as e:
        raise Exception(f"Chord complexification failed: {str(e)}")
