"""
Demonstrates an expert-level approach to making a chord progression "jazzier".

This example loads a MIDI file, analyzes its progression, and then uses a
sophisticated beam search algorithm to find a harmonically rich and musically
coherent "jazzy" chord progression.

This approach incorporates music theory concepts like:
- Manual key specification to ensure correct harmonic analysis.
- Melody-aware scoring to avoid clashes between harmony and melody.
- Functional harmony analysis to reward strong, logical progressions (e.g., ii-V-I).
- A variety-promoting mechanism to avoid monotonous substitutions.
"""

import os
import heapq
from typing import List, Tuple, Optional, Dict

from halmoni.analysis.midi_analyzer import MIDIAnalyzer
from halmoni.analysis.chord_detector import ChordDetector
from halmoni.core import ChordProgression, Key, Note, Chord, Interval
from halmoni.suggestions import ChordSuggestionEngine, ChordSuggestion


def _calculate_voice_leading_quality(chord1: Chord, chord2: Chord) -> float:
    """Calculates voice leading quality based on common tones and root movement."""
    pc1 = set(note.pitch_class for note in chord1.notes)
    pc2 = set(note.pitch_class for note in chord2.notes)
    common_tones = len(pc1.intersection(pc2))
    max_possible_common = min(len(pc1), len(pc2))
    common_tone_ratio = common_tones / max_possible_common if max_possible_common > 0 else 0.5

    root_interval = Interval.from_notes(chord1.root, chord2.root)
    root_motion_semitones = abs(root_interval.simple_semitones)
    effective_semitones = min(root_motion_semitones, 12 - root_motion_semitones)
    root_motion_quality = 1.0 - (effective_semitones / 6.0)  # Penalize large leaps more

    return (common_tone_ratio * 0.6 + root_motion_quality * 0.4)


def get_harmonic_function(chord: Chord, key: Key) -> str:
    """Determines the harmonic function (Tonic, Subdominant, Dominant) of a chord."""
    analysis = key.analyze_chord(chord)
    return analysis.get('function', 'unknown')


def score_functional_transition(func1: str, func2: str) -> float:
    """Scores the transition between two harmonic functions."""
    # Strong progressions are rewarded
    if func1 == 'subdominant' and func2 == 'dominant': return 1.0  # S -> D
    if func1 == 'dominant' and func2 == 'tonic': return 1.0     # D -> T (Cadence)
    # Common progressions
    if func1 == 'tonic' and func2 in ['subdominant', 'dominant']: return 0.7
    # Weaker progressions (retrogressions) are penalized
    if func1 == 'dominant' and func2 == 'subdominant': return 0.1
    if func1 == 'tonic' and func2 == 'tonic': return 0.5 # Allowable, but not driving motion
    return 0.3  # Default for other transitions


def get_melody_notes_for_chord(
    chord_start_time: float, chord_duration: float, melody: List[Dict]
) -> List[Note]:
    """Finds melody notes that occur during a chord's duration."""
    melody_notes = []
    chord_end_time = chord_start_time + chord_duration
    for note_event in melody:
        if note_event['start_time'] < chord_end_time and note_event['end_time'] > chord_start_time:
            melody_notes.append(Note(note_event['midi_note']))
    return melody_notes


def calculate_melodic_clash_penalty(chord: Chord, melody_notes: List[Note]) -> float:
    """Calculates a penalty if a chord clashes with the melody."""
    penalty = 0.0
    chord_pitch_classes = set(n.pitch_class for n in chord.notes)
    for m_note in melody_notes:
        for c_note_pc in chord_pitch_classes:
            # Check for minor 2nd clashes (a common source of harsh dissonance)
            if abs(m_note.midi_number - Note(c_note_pc, m_note.octave).midi_number) % 12 == 1:
                penalty += 5.0  # Heavy penalty for a clash
    return penalty


def find_best_progression_sequence(
    progression: ChordProgression,
    engine,
    key: Key,
    melody: List[Dict],
    strategy_filter: List[str],
    beam_width: int = 5
) -> ChordProgression:
    """Finds the best sequence of chords using a music-theory-aware beam search."""
    # Beam stores: (score, chord_sequence, last_strategy_used)
    beam: List[Tuple[float, List[Chord], Optional[str]]] = [(0.0, [], None)]

    for i, original_chord in enumerate(progression.chords):
        all_candidates = []
        
        suggestions = engine.get_suggestions_for_position(progression, i, key, strategy_filter)
        
        # The original chord is always a candidate
        candidates = [ChordSuggestion(original_chord, 1.0, "Original Chord", float(i), 1.0, "Original")] + suggestions

        # Get melody context for this chord's time slice
        chord_start_time = sum(progression.durations[:i])
        chord_duration = progression.durations[i]
        melody_notes = get_melody_notes_for_chord(chord_start_time, chord_duration, melody)

        for score, sequence, last_strategy in beam:
            for suggestion in candidates:
                new_chord = suggestion.chord
                
                # --- SCORING ---
                # 1. Base confidence from the suggestion engine
                confidence_score = suggestion.confidence

                # 2. Voice leading from previous chord
                voice_leading_score = 0.5
                if sequence:
                    voice_leading_score = _calculate_voice_leading_quality(sequence[-1], new_chord)

                # 3. Functional harmony score
                functional_score = 0.5
                if sequence:
                    prev_func = get_harmonic_function(sequence[-1], key)
                    new_func = get_harmonic_function(new_chord, key)
                    functional_score = score_functional_transition(prev_func, new_func)

                # 4. Penalty for melody clashes
                clash_penalty = calculate_melodic_clash_penalty(new_chord, melody_notes)

                # 5. Penalty for repeating the same substitution strategy
                repetition_penalty = 0.0
                if last_strategy and last_strategy == suggestion.strategy_source and suggestion.strategy_source != "Original":
                    repetition_penalty = 0.2 # Discourage using the same trick twice in a row

                # Combine scores with weights
                new_score = score + \
                            (confidence_score * 0.2) + \
                            (voice_leading_score * 0.3) + \
                            (functional_score * 0.5) - \
                            clash_penalty - \
                            repetition_penalty

                new_sequence = sequence + [new_chord]
                all_candidates.append((new_score, new_sequence, suggestion.strategy_source))
        
        beam = heapq.nlargest(beam_width, all_candidates, key=lambda x: x[0])

    if not beam:
        return progression
    
    best_score, best_sequence, _ = max(beam, key=lambda x: x[0])
    return ChordProgression(best_sequence, key=key, durations=progression.durations)


def jazz_up_progression(input_file: str, manual_key: Optional[Key] = None):
    """Analyzes a MIDI file and suggests a jazzier chord progression."""
    print(f"Analyzing MIDI file: {input_file}...")
    analyzer = MIDIAnalyzer()
    midi_data = analyzer.load_midi_file(input_file)
    notes = midi_data['notes']

    # --- Extract Melody and Chords ---
    melody_line = analyzer.extract_melody_line(notes)
    grouped_notes = analyzer.group_simultaneous_notes(notes, tolerance=0.1)
    
    # Get chord timings and objects
    chord_events = []
    for group in grouped_notes:
        start_time = group[0]['start_time']
        chord = ChordDetector().detect_chord_from_notes(analyzer.convert_to_note_objects(group))
        if chord:
            chord_events.append({'chord': chord, 'start_time': start_time})
    
    if not chord_events:
        print("No chords detected.")
        return

    # Create ChordProgression with durations
    detected_chords = [event['chord'] for event in chord_events]
    durations = [
        chord_events[i+1]['start_time'] - chord_events[i]['start_time'] 
        for i in range(len(chord_events) - 1)
    ]
    durations.append(1.0) # Assume last chord has duration of 1 beat
    progression = ChordProgression(detected_chords, durations=durations)
    
    print(f"\nOriginal Chord Progression:\n{progression}")

    # --- Determine the Key ---
    if manual_key:
        key = manual_key
        print(f"\nUsing manually specified key: {key}")
    else:
        print("\nAttempting to detect key automatically...")
        tonic, mode = analyzer.detect_key_signature(notes)
        key = Key(Note(tonic, 4), mode)
        print(f"Detected Key: {key} (Warning: Automatic detection may be inaccurate)")

    # --- Find the Best Jazzy Progression ---
    print("\nFinding a jazzier progression with music theory constraints...")
    from halmoni.suggestions import ChordSuggestionEngine
    engine = ChordSuggestionEngine()
    jazzy_strategies = ["SubV7", "BorrowedChord", "ChromaticApproach", "Suspend"]

    jazzy_progression = find_best_progression_sequence(
        progression, engine, key, melody_line, jazzy_strategies, beam_width=5
    )

    # --- Display the Results ---
    print("\n--- Results ---")
    print(f"Original Progression: {progression}")
    print(f"Jazzier Progression:  {jazzy_progression}")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    input_midi_file = os.path.join(script_dir, "ode-to-joy-easy-variation.mid")

    if not os.path.exists(input_midi_file):
        print(f"Error: MIDI file not found at {input_midi_file}")
    else:
        # Manually specify the key for Ode to Joy, which is in G Major.
        # This corrects the biggest flaw in the previous approach.
        ode_to_joy_key = Key(Note("G", 4), "major")
        jazz_up_progression(input_midi_file, manual_key=ode_to_joy_key)
