"""Tests for analysis module (MIDI, chord detection, key detection)."""

import pytest
from halmoni import (
    Note, Chord, Key, MIDIAnalyzer, ChordDetector, KeyDetector
)


class TestChordDetector:
    """Tests for the ChordDetector class."""

    def test_detector_creation(self) -> None:
        """Test creating a chord detector."""
        detector = ChordDetector()
        assert detector.min_notes == 2

    def test_detect_major_chord(self) -> None:
        """Test detecting a major chord."""
        detector = ChordDetector()
        notes = [Note('C', 4), Note('E', 4), Note('G', 4)]
        chord = detector.detect_chord_from_notes(notes)

        assert chord is not None
        assert chord.root.pitch_class == 'C'
        assert chord.quality == 'major'

    def test_detect_minor_chord(self) -> None:
        """Test detecting a minor chord."""
        detector = ChordDetector()
        notes = [Note('A', 4), Note('C', 4), Note('E', 4)]
        chord = detector.detect_chord_from_notes(notes)

        assert chord is not None
        assert chord.root.pitch_class == 'A'
        assert chord.quality == 'minor'

    def test_detect_seventh_chord(self) -> None:
        """Test detecting a seventh chord."""
        detector = ChordDetector()
        notes = [Note('G', 4), Note('B', 4), Note('D', 4), Note('F', 4)]
        chord = detector.detect_chord_from_notes(notes)

        assert chord is not None
        assert chord.root.pitch_class == 'G'
        assert chord.quality == 'dominant7'

    def test_detect_too_few_notes(self) -> None:
        """Test that too few notes returns None."""
        detector = ChordDetector()
        notes = [Note('C', 4)]
        chord = detector.detect_chord_from_notes(notes)
        assert chord is None

    def test_detect_from_midi_notes(self) -> None:
        """Test detecting chord from MIDI note dictionaries."""
        detector = ChordDetector()
        midi_notes = [
            {'midi_note': 60, 'duration': 1.0, 'velocity': 100},  # C
            {'midi_note': 64, 'duration': 1.0, 'velocity': 100},  # E
            {'midi_note': 67, 'duration': 1.0, 'velocity': 100},  # G
        ]
        chord = detector.detect_chord_from_midi_notes(midi_notes)

        assert chord is not None
        assert chord.root.pitch_class == 'C'

    def test_analyze_chord_complexity(self) -> None:
        """Test analyzing chord complexity."""
        detector = ChordDetector()
        simple_chord = Chord.from_symbol('C')
        complex_chord = Chord.from_symbol('C')  # Would be complex if extended

        analysis = detector.analyze_chord_complexity(simple_chord)
        assert 'complexity_score' in analysis
        assert analysis['chord'] == simple_chord

    def test_voice_leading_analysis(self) -> None:
        """Test analyzing voice leading between chords."""
        detector = ChordDetector()
        c_major = Chord.from_symbol('C')
        f_major = Chord.from_symbol('F')

        analysis = detector.analyze_voice_leading_motion(c_major, f_major)
        assert 'root_motion' in analysis
        assert 'common_tones' in analysis
        assert 'motion_type' in analysis


class TestKeyDetector:
    """Tests for the KeyDetector class."""

    def test_detector_creation(self) -> None:
        """Test creating a key detector."""
        detector = KeyDetector()
        assert detector.profile_type == 'standard'

    def test_detector_with_profile_type(self) -> None:
        """Test creating detector with different profile types."""
        classical = KeyDetector('classical')
        assert classical.profile_type == 'classical'

        folk = KeyDetector('folk')
        assert folk.profile_type == 'folk'

    def test_detect_c_major(self) -> None:
        """Test detecting C major key."""
        detector = KeyDetector()
        c_major_scale = [Note('C', 4), Note('D', 4), Note('E', 4),
                        Note('F', 4), Note('G', 4), Note('A', 4), Note('B', 4)]

        key, confidence = detector.detect_key_from_notes(c_major_scale)
        assert key.tonic.pitch_class == 'C'
        assert key.mode == 'major'
        assert confidence > 0.5

    def test_detect_a_minor(self) -> None:
        """Test detecting A minor key."""
        detector = KeyDetector()
        a_minor_scale = [Note('A', 4), Note('B', 4), Note('C', 4),
                        Note('D', 4), Note('E', 4), Note('F', 4), Note('G', 4)]

        key, confidence = detector.detect_key_from_notes(a_minor_scale)
        assert key.tonic.pitch_class == 'A'
        assert key.mode == 'minor'

    def test_detect_from_chords(self) -> None:
        """Test detecting key from chord progression."""
        detector = KeyDetector()
        chords = [
            Chord.from_symbol('C'),
            Chord.from_symbol('Am'),
            Chord.from_symbol('F'),
            Chord.from_symbol('G')
        ]

        key, confidence = detector.detect_key_from_chords(chords)
        assert key.tonic.pitch_class == 'C'
        assert key.mode == 'major'

    def test_detect_empty_notes(self) -> None:
        """Test detecting key from empty notes list."""
        detector = KeyDetector()
        key, confidence = detector.detect_key_from_notes([])
        assert key.tonic.pitch_class == 'C'  # Default
        assert confidence == 0.0

    def test_detect_from_midi_notes(self) -> None:
        """Test detecting key from MIDI notes."""
        detector = KeyDetector()
        midi_notes = [
            {'midi_note': 60, 'duration': 2.0, 'velocity': 100},  # C
            {'midi_note': 62, 'duration': 1.0, 'velocity': 80},   # D
            {'midi_note': 64, 'duration': 1.0, 'velocity': 80},   # E
        ]

        key, confidence = detector.detect_key_from_midi_notes(midi_notes)
        assert key is not None
        assert 0.0 <= confidence <= 1.0

    def test_compare_keys(self) -> None:
        """Test comparing two keys."""
        detector = KeyDetector()
        c_major = Key(Note('C', 4), 'major')
        a_minor = Key(Note('A', 4), 'minor')

        analysis = detector.compare_keys(c_major, a_minor)
        assert analysis['relationship'] == 'relative'
        assert analysis['common_notes'] == 7

    def test_compare_parallel_keys(self) -> None:
        """Test comparing parallel keys."""
        detector = KeyDetector()
        c_major = Key(Note('C', 4), 'major')
        c_minor = Key(Note('C', 4), 'minor')

        analysis = detector.compare_keys(c_major, c_minor)
        assert analysis['relationship'] == 'parallel'

    def test_detect_tonicization(self) -> None:
        """Test detecting tonicization in progression."""
        detector = KeyDetector()
        c_major = Key(Note('C', 4), 'major')
        chords = [
            Chord.from_symbol('C'),
            Chord.from_symbol('D7'),  # Secondary dominant
            Chord.from_symbol('G'),   # Tonicized chord
        ]

        tonicizations = detector.detect_tonicization(chords, c_major)
        assert len(tonicizations) == 3


class TestMIDIAnalyzer:
    """Tests for the MIDIAnalyzer class."""

    def test_analyzer_creation(self) -> None:
        """Test creating a MIDI analyzer."""
        analyzer = MIDIAnalyzer()
        assert analyzer.quantization == 0.25
        assert analyzer.min_velocity == 20

    def test_custom_quantization(self) -> None:
        """Test creating analyzer with custom quantization."""
        analyzer = MIDIAnalyzer(quantization=0.5)
        assert analyzer.quantization == 0.5

    def test_quantize_timing(self) -> None:
        """Test quantizing note timings."""
        analyzer = MIDIAnalyzer(quantization=0.25)
        notes = [
            {'start_time': 0.12, 'duration': 0.88, 'end_time': 1.0}
        ]

        quantized = analyzer.quantize_timing(notes)
        assert quantized[0]['start_time'] == 0.0  # Quantized to 0
        assert quantized[0]['duration'] >= 0.25  # Minimum duration

    def test_group_simultaneous_notes(self) -> None:
        """Test grouping simultaneous notes."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'start_time': 0.0, 'midi_note': 60},
            {'start_time': 0.05, 'midi_note': 64},  # Within tolerance
            {'start_time': 1.0, 'midi_note': 67},
        ]

        groups = analyzer.group_simultaneous_notes(notes, tolerance=0.1)
        assert len(groups) == 2
        assert len(groups[0]) == 2  # First two notes grouped

    def test_extract_melody_line(self) -> None:
        """Test extracting melody (highest notes)."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'start_time': 0.0, 'midi_note': 60},
            {'start_time': 0.0, 'midi_note': 67},  # Highest
            {'start_time': 1.0, 'midi_note': 72},  # Highest in second group
        ]

        melody = analyzer.extract_melody_line(notes)
        assert len(melody) == 2
        assert melody[0]['midi_note'] == 67
        assert melody[1]['midi_note'] == 72

    def test_extract_bass_line(self) -> None:
        """Test extracting bass line (lowest notes)."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'start_time': 0.0, 'midi_note': 48},  # Lowest
            {'start_time': 0.0, 'midi_note': 60},
            {'start_time': 1.0, 'midi_note': 43},  # Lowest in second group
        ]

        bass = analyzer.extract_bass_line(notes)
        assert len(bass) == 2
        assert bass[0]['midi_note'] == 48
        assert bass[1]['midi_note'] == 43

    def test_convert_to_note_objects(self) -> None:
        """Test converting MIDI notes to Note objects."""
        analyzer = MIDIAnalyzer()
        midi_notes = [
            {'midi_note': 60},
            {'midi_note': 64},
            {'midi_note': 67},
        ]

        notes = analyzer.convert_to_note_objects(midi_notes)
        assert len(notes) == 3
        assert notes[0].midi_number == 60

    def test_pitch_class_histogram(self) -> None:
        """Test creating pitch class histogram."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'midi_note': 60},  # C
            {'midi_note': 60},  # C
            {'midi_note': 64},  # E
        ]

        histogram = analyzer.get_pitch_class_histogram(notes)
        assert histogram['C'] == 2
        assert histogram['E'] == 1

    def test_get_active_notes_at_time(self) -> None:
        """Test getting active notes at specific time."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'start_time': 0.0, 'end_time': 2.0, 'midi_note': 60},
            {'start_time': 1.0, 'end_time': 3.0, 'midi_note': 64},
            {'start_time': 3.0, 'end_time': 4.0, 'midi_note': 67},
        ]

        # At time 1.5, first two notes should be active
        active = analyzer.get_active_notes_at_time(notes, 1.5)
        assert len(active) == 2
        assert active[0]['midi_note'] == 60
        assert active[1]['midi_note'] == 64

    def test_get_active_notes_boundary(self) -> None:
        """Test active notes at boundary times."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'start_time': 0.0, 'end_time': 2.0, 'midi_note': 60},
        ]

        # At exact start time
        active = analyzer.get_active_notes_at_time(notes, 0.0)
        assert len(active) == 1

        # At exact end time (should not be active)
        active = analyzer.get_active_notes_at_time(notes, 2.0)
        assert len(active) == 0

    def test_get_time_windows(self) -> None:
        """Test dividing notes into time windows."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'start_time': 0.0, 'end_time': 1.0, 'midi_note': 60},
            {'start_time': 2.0, 'end_time': 3.0, 'midi_note': 64},
            {'start_time': 4.0, 'end_time': 5.0, 'midi_note': 67},
        ]

        windows = analyzer.get_time_windows(notes, window_size=2.0)
        assert len(windows) >= 2
        assert all(isinstance(w[0], float) for w in windows)
        assert all(isinstance(w[1], list) for w in windows)

    def test_get_time_windows_empty(self) -> None:
        """Test time windows with empty notes list."""
        analyzer = MIDIAnalyzer()
        windows = analyzer.get_time_windows([], window_size=1.0)
        assert windows == []

    def test_detect_key_signature(self) -> None:
        """Test simple key detection from notes."""
        analyzer = MIDIAnalyzer()
        # C major scale notes
        notes = [
            {'midi_note': 60},  # C
            {'midi_note': 62},  # D
            {'midi_note': 64},  # E
            {'midi_note': 65},  # F
            {'midi_note': 67},  # G
            {'midi_note': 69},  # A
            {'midi_note': 71},  # B
        ]

        tonic, mode = analyzer.detect_key_signature(notes)
        assert tonic in ['C', 'A']  # Could be C major or A minor
        assert mode in ['major', 'minor']

    def test_detect_key_signature_empty(self) -> None:
        """Test key detection with empty notes."""
        analyzer = MIDIAnalyzer()
        tonic, mode = analyzer.detect_key_signature([])
        assert tonic == 'C'
        assert mode == 'major'

    def test_quantize_with_custom_value(self) -> None:
        """Test quantization with custom quantization value."""
        analyzer = MIDIAnalyzer(quantization=0.25)
        notes = [
            {'start_time': 0.37, 'duration': 0.89, 'end_time': 1.26}
        ]

        quantized = analyzer.quantize_timing(notes, quantization=0.5)
        # Should quantize to nearest 0.5
        assert quantized[0]['start_time'] in [0.0, 0.5]
        assert quantized[0]['duration'] % 0.5 == 0.0

    def test_group_simultaneous_notes_empty(self) -> None:
        """Test grouping with empty notes list."""
        analyzer = MIDIAnalyzer()
        groups = analyzer.group_simultaneous_notes([])
        assert groups == []

    def test_convert_to_note_objects_with_invalid(self) -> None:
        """Test converting MIDI notes with some invalid entries."""
        analyzer = MIDIAnalyzer()
        midi_notes = [
            {'midi_note': 60},
            {'midi_note': 200},  # Invalid - out of range
            {'midi_note': 64},
        ]

        notes = analyzer.convert_to_note_objects(midi_notes)
        # Should skip invalid note
        assert len(notes) == 2

    def test_histogram_with_invalid_notes(self) -> None:
        """Test histogram creation with invalid MIDI notes."""
        analyzer = MIDIAnalyzer()
        notes = [
            {'midi_note': 60},
            {'midi_note': 200},  # Invalid
            {'midi_note': 64},
        ]

        histogram = analyzer.get_pitch_class_histogram(notes)
        # Should skip invalid note
        assert 'C' in histogram
        assert 'E' in histogram


class TestChordDetectorAdvanced:
    """Advanced tests for ChordDetector."""

    def test_detect_chord_with_bass_weight(self) -> None:
        """Test chord detection with bass weighting."""
        detector = ChordDetector(bass_weight=2.0)
        notes = [Note('C', 4), Note('E', 4), Note('G', 4)]
        chord = detector.detect_chord_from_notes(notes)
        assert chord is not None

    def test_detect_chord_with_specified_bass(self) -> None:
        """Test chord detection with specific bass note."""
        detector = ChordDetector()
        notes = [Note('E', 4), Note('G', 4), Note('C', 5)]
        bass = Note('C', 3)
        chord = detector.detect_chord_from_notes(notes, bass)
        assert chord is not None

    def test_detect_from_midi_with_timing(self) -> None:
        """Test MIDI note detection with timing consideration."""
        detector = ChordDetector()
        midi_notes = [
            {'midi_note': 60, 'duration': 2.0, 'velocity': 100},
            {'midi_note': 64, 'duration': 1.0, 'velocity': 80},
            {'midi_note': 67, 'duration': 1.0, 'velocity': 80},
        ]
        chord = detector.detect_chord_from_midi_notes(midi_notes, consider_timing=True)
        assert chord is not None

    def test_detect_from_midi_without_timing(self) -> None:
        """Test MIDI note detection without timing."""
        detector = ChordDetector()
        midi_notes = [
            {'midi_note': 60, 'duration': 1.0, 'velocity': 100},
            {'midi_note': 64, 'duration': 1.0, 'velocity': 100},
        ]
        chord = detector.detect_chord_from_midi_notes(midi_notes, consider_timing=False)
        # Should handle 2-note chord
        assert chord is not None or len(midi_notes) < detector.min_notes

    def test_analyze_voice_leading_different_roots(self) -> None:
        """Test voice leading analysis with different root motion."""
        detector = ChordDetector()
        c_major = Chord.from_symbol('C')
        g_major = Chord.from_symbol('G')

        analysis = detector.analyze_voice_leading_motion(c_major, g_major)
        assert analysis['root_motion'].semitones == 7  # Perfect 5th

    def test_analyze_chord_with_extensions(self) -> None:
        """Test complexity analysis with extended chords."""
        detector = ChordDetector()
        simple = Chord.from_symbol('C')
        extended = Chord.from_symbol('Cmaj9')

        simple_analysis = detector.analyze_chord_complexity(simple)
        extended_analysis = detector.analyze_chord_complexity(extended)

        assert extended_analysis['complexity_score'] >= simple_analysis['complexity_score']

    def test_detect_augmented_chord(self) -> None:
        """Test detecting augmented chords."""
        detector = ChordDetector()
        notes = [Note('C', 4), Note('E', 4), Note('G#', 4)]
        chord = detector.detect_chord_from_notes(notes)
        assert chord is not None
        # May detect as augmented or as major with altered 5th

    def test_detect_diminished_seventh(self) -> None:
        """Test detecting diminished seventh chord."""
        detector = ChordDetector()
        notes = [Note('B', 3), Note('D', 4), Note('F', 4), Note('Ab', 4)]
        chord = detector.detect_chord_from_notes(notes)
        assert chord is not None

    def test_voice_leading_common_tones_analysis(self) -> None:
        """Test that voice leading detects common tones."""
        detector = ChordDetector()
        c_major = Chord.from_symbol('C')
        a_minor = Chord.from_symbol('Am')  # Shares C and E

        analysis = detector.analyze_voice_leading_motion(c_major, a_minor)
        assert len(analysis['common_tones']) >= 2
