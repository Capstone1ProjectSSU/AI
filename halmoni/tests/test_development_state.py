"""Tests to check the development state and module completeness."""

import pytest
from halmoni import (
    Note, Interval, Chord, Scale, Key, ChordProgression, ChordVoicing,
    MIDIAnalyzer, ChordDetector, KeyDetector, AdamStarkChordDetector,
    GuitarDifficulty, PianoDifficulty, BassDifficulty,
    ChordSuggestionEngine,
    BorrowedChordStrategy, ChromaticApproachStrategy,
    NeapolitanStrategy, SubV7Strategy, SuspendStrategy, TSDMovementStrategy,
)


class TestModuleImports:
    """Test that all advertised modules can be imported."""

    def test_core_module_imports(self) -> None:
        """Test core module classes are importable."""
        assert Note is not None
        assert Interval is not None
        assert Chord is not None
        assert Scale is not None
        assert Key is not None
        assert ChordProgression is not None
        assert ChordVoicing is not None

    def test_analysis_module_imports(self) -> None:
        """Test analysis module classes are importable."""
        assert MIDIAnalyzer is not None
        assert ChordDetector is not None
        assert KeyDetector is not None
        assert AdamStarkChordDetector is not None

    def test_instruments_module_imports(self) -> None:
        """Test instruments module classes are importable."""
        assert GuitarDifficulty is not None
        assert PianoDifficulty is not None
        assert BassDifficulty is not None

    def test_suggestions_module_imports(self) -> None:
        """Test suggestions module classes are importable."""
        assert ChordSuggestionEngine is not None
        assert BorrowedChordStrategy is not None
        assert ChromaticApproachStrategy is not None
        assert NeapolitanStrategy is not None
        assert SubV7Strategy is not None
        assert SuspendStrategy is not None
        assert TSDMovementStrategy is not None


class TestModuleInstantiation:
    """Test that all classes can be instantiated."""

    def test_core_classes_instantiation(self) -> None:
        """Test core classes can be instantiated."""
        note = Note('C', 4)
        assert note is not None

        interval = Interval(7)
        assert interval is not None

        chord = Chord.from_symbol('C')
        assert chord is not None

        scale = Scale.major(Note('C', 4))
        assert scale is not None

        key = Key(Note('C', 4), 'major')
        assert key is not None

        progression = ChordProgression.from_symbols(['C', 'Am', 'F', 'G'])
        assert progression is not None

    def test_analysis_classes_instantiation(self) -> None:
        """Test analysis classes can be instantiated."""
        midi_analyzer = MIDIAnalyzer()
        assert midi_analyzer is not None

        chord_detector = ChordDetector()
        assert chord_detector is not None

        key_detector = KeyDetector()
        assert key_detector is not None

        # AdamStarkChordDetector may or may not be fully implemented
        try:
            adam_stark = AdamStarkChordDetector()
            assert adam_stark is not None
        except (NotImplementedError, AttributeError):
            pytest.skip("AdamStarkChordDetector not yet implemented")

    def test_instruments_classes_instantiation(self) -> None:
        """Test instruments classes can be instantiated."""
        guitar = GuitarDifficulty()
        assert guitar is not None

        piano = PianoDifficulty()
        assert piano is not None

        bass = BassDifficulty()
        assert bass is not None

    def test_suggestions_classes_instantiation(self) -> None:
        """Test suggestion classes can be instantiated."""
        engine = ChordSuggestionEngine()
        assert engine is not None

        borrowed = BorrowedChordStrategy()
        assert borrowed is not None

        chromatic = ChromaticApproachStrategy()
        assert chromatic is not None

        neapolitan = NeapolitanStrategy()
        assert neapolitan is not None

        subv7 = SubV7Strategy()
        assert subv7 is not None

        suspend = SuspendStrategy()
        assert suspend is not None

        tsd = TSDMovementStrategy()
        assert tsd is not None


class TestImplementationStatus:
    """Test implementation status of various modules."""

    def test_core_module_complete(self) -> None:
        """Test that core module is functional."""
        # Create a chord progression and analyze it
        progression = ChordProgression.from_symbols(['C', 'Am', 'F', 'G'])
        key = Key(Note('C', 4), 'major')

        # These should work without errors
        assert len(progression) == 4
        assert progression[0].symbol == 'C'
        assert key.analyze_chord(progression[0]) is not None

    def test_analysis_module_complete(self) -> None:
        """Test that analysis module is functional."""
        # Test chord detection
        detector = ChordDetector()
        notes = [Note('C', 4), Note('E', 4), Note('G', 4)]
        chord = detector.detect_chord_from_notes(notes)
        assert chord is not None

        # Test key detection
        key_detector = KeyDetector()
        key, confidence = key_detector.detect_key_from_notes(notes)
        assert key is not None

    def test_suggestions_module_complete(self) -> None:
        """Test that suggestions module is functional."""
        engine = ChordSuggestionEngine()
        progression = ChordProgression.from_symbols(['C', 'Am', 'F', 'G'])
        key = Key(Note('C', 4), 'major')

        # Should be able to get suggestions
        suggestions = engine.get_suggestions(progression, key)
        assert isinstance(suggestions, list)

        # Should have all strategies
        strategies = engine.get_available_strategies()
        assert len(strategies) == 6

    def test_instruments_module_status(self) -> None:
        """Test instruments module status (may be incomplete)."""
        guitar = GuitarDifficulty()
        piano = PianoDifficulty()
        bass = BassDifficulty()

        chord = Chord.from_symbol('C')

        # These should return results even if implementation is incomplete
        guitar_analysis = guitar.analyze_chord_difficulty(chord)
        piano_analysis = piano.analyze_chord_difficulty(chord)

        assert 'implementation_status' in guitar_analysis
        assert 'implementation_status' in piano_analysis

        # Bass analyzes notes, not chords
        note = Note('E', 2)
        bass_analysis = bass.analyze_note_difficulty(note)
        assert 'implementation_status' in bass_analysis


class TestEndToEndWorkflow:
    """Test end-to-end workflows to verify integration."""

    def test_progression_analysis_workflow(self) -> None:
        """Test complete progression analysis workflow."""
        # 1. Create a progression
        progression = ChordProgression.from_symbols(['Dm7', 'G7', 'Cmaj7'])
        key = Key(Note('C', 4), 'major')

        # 2. Analyze it
        roman_numerals = progression.get_roman_numerals(key)
        assert len(roman_numerals) == 3

        # 3. Get suggestions
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(progression, key)
        assert isinstance(suggestions, list)

        # 4. Analyze progression potential
        analysis = engine.analyze_progression_potential(progression, key)
        assert 'total_suggestions' in analysis
        assert 'position_analysis' in analysis

    def test_midi_to_suggestions_workflow(self) -> None:
        """Test MIDI analysis to suggestions workflow."""
        # 1. Simulate MIDI notes
        midi_notes = [
            {'midi_note': 60, 'duration': 1.0, 'velocity': 100, 'start_time': 0.0, 'end_time': 1.0},
            {'midi_note': 64, 'duration': 1.0, 'velocity': 100, 'start_time': 0.0, 'end_time': 1.0},
            {'midi_note': 67, 'duration': 1.0, 'velocity': 100, 'start_time': 0.0, 'end_time': 1.0},
        ]

        # 2. Detect chord
        detector = ChordDetector()
        chord = detector.detect_chord_from_midi_notes(midi_notes)
        assert chord is not None

        # 3. Detect key
        key_detector = KeyDetector()
        key, confidence = key_detector.detect_key_from_midi_notes(midi_notes)
        assert key is not None

    def test_key_detection_to_analysis_workflow(self) -> None:
        """Test key detection and harmonic analysis workflow."""
        # 1. Create notes in a key
        c_major_notes = [
            Note('C', 4), Note('D', 4), Note('E', 4),
            Note('F', 4), Note('G', 4), Note('A', 4), Note('B', 4)
        ]

        # 2. Detect key
        key_detector = KeyDetector()
        key, confidence = key_detector.detect_key_from_notes(c_major_notes)

        # 3. Analyze chords in that key
        chord = Chord.from_symbol('C')
        analysis = key.analyze_chord(chord)

        assert analysis['is_diatonic'] is True
        assert analysis['function'] == 'tonic'


class TestPackageVersion:
    """Test package metadata."""

    def test_package_has_version(self) -> None:
        """Test that package has version info."""
        import halmoni
        assert hasattr(halmoni, '__version__')
        assert halmoni.__version__ == "0.1.0"

    def test_package_has_all_exports(self) -> None:
        """Test that package __all__ includes expected exports."""
        import halmoni
        assert hasattr(halmoni, '__all__')
        assert 'Note' in halmoni.__all__
        assert 'ChordSuggestionEngine' in halmoni.__all__
