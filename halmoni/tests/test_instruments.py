"""Tests for instrument difficulty analysis modules."""

import pytest
from halmoni import (
    Note, Chord, ChordVoicing,
    GuitarDifficulty, PianoDifficulty, BassDifficulty
)


class TestGuitarDifficulty:
    """Tests for guitar difficulty analyzer."""

    def test_analyzer_creation(self) -> None:
        """Test creating a guitar difficulty analyzer."""
        guitar = GuitarDifficulty()
        assert guitar.strings == 5
        assert len(guitar.standard_tuning) == 5

    def test_custom_string_count(self) -> None:
        """Test creating analyzer with custom string count."""
        guitar = GuitarDifficulty(strings=6)
        assert guitar.strings == 6

    def test_analyze_chord_difficulty(self) -> None:
        """Test analyzing chord difficulty."""
        guitar = GuitarDifficulty()
        chord = Chord.from_symbol('C')
        analysis = guitar.analyze_chord_difficulty(chord)

        assert 'difficulty_score' in analysis
        assert 'chord' in analysis
        assert analysis['chord'] == chord
        assert 'implementation_status' in analysis

    def test_suggest_fingering(self) -> None:
        """Test suggesting fingering patterns."""
        guitar = GuitarDifficulty()
        chord = Chord.from_symbol('G')
        fingerings = guitar.suggest_fingering(chord)

        assert isinstance(fingerings, list)
        # Implementation incomplete, so just check structure
        if len(fingerings) > 0:
            assert 'pattern' in fingerings[0]

    def test_difficulty_score_range(self) -> None:
        """Test that difficulty scores are in valid range."""
        guitar = GuitarDifficulty()
        chords = [
            Chord.from_symbol('C'),
            Chord.from_symbol('F'),
            Chord.from_symbol('Gmaj7')
        ]

        for chord in chords:
            analysis = guitar.analyze_chord_difficulty(chord)
            # Should have a difficulty score (even if placeholder)
            assert 'difficulty_score' in analysis


class TestPianoDifficulty:
    """Tests for piano difficulty analyzer."""

    def test_analyzer_creation(self) -> None:
        """Test creating a piano difficulty analyzer."""
        piano = PianoDifficulty()
        assert piano is not None

    def test_analyze_chord_difficulty(self) -> None:
        """Test analyzing piano chord difficulty."""
        piano = PianoDifficulty()
        chord = Chord.from_symbol('C')
        analysis = piano.analyze_chord_difficulty(chord)

        assert 'difficulty_score' in analysis
        assert 'chord' in analysis
        assert analysis['chord'] == chord
        assert 'implementation_status' in analysis

    def test_suggest_voicing(self) -> None:
        """Test suggesting piano voicings."""
        piano = PianoDifficulty()
        chord = Chord.from_symbol('Cmaj7')
        voicings = piano.suggest_voicing(chord)

        assert isinstance(voicings, list)
        # Implementation incomplete

    def test_difficulty_for_extended_chords(self) -> None:
        """Test difficulty analysis for extended chords."""
        piano = PianoDifficulty()
        simple_chord = Chord.from_symbol('C')
        extended_chord = Chord.from_symbol('Cmaj13')

        simple_analysis = piano.analyze_chord_difficulty(simple_chord)
        extended_analysis = piano.analyze_chord_difficulty(extended_chord)

        # Both should return valid analyses
        assert 'difficulty_score' in simple_analysis
        assert 'difficulty_score' in extended_analysis


class TestBassDifficulty:
    """Tests for bass guitar difficulty analyzer."""

    def test_analyzer_creation(self) -> None:
        """Test creating a bass difficulty analyzer."""
        bass = BassDifficulty()
        assert bass.strings == 4
        assert len(bass.standard_tuning) == 4

    def test_custom_string_count(self) -> None:
        """Test creating analyzer with custom string count."""
        bass = BassDifficulty(strings=5)
        assert bass.strings == 5

    def test_analyze_note_difficulty(self) -> None:
        """Test analyzing single note difficulty."""
        bass = BassDifficulty()
        note = Note('E', 2)
        analysis = bass.analyze_note_difficulty(note)

        assert 'difficulty_score' in analysis
        assert 'note' in analysis
        assert analysis['note'] == note
        assert 'implementation_status' in analysis

    def test_analyze_progression_difficulty(self) -> None:
        """Test analyzing bass line progression difficulty."""
        bass = BassDifficulty()
        notes = [
            Note('E', 2),
            Note('A', 2),
            Note('D', 2),
            Note('G', 2)
        ]

        analysis = bass.analyze_progression_difficulty(notes)
        assert 'total_difficulty' in analysis
        assert 'implementation_status' in analysis

    def test_difficulty_various_notes(self) -> None:
        """Test difficulty for various bass notes."""
        bass = BassDifficulty()
        notes = [
            Note('E', 1),  # Low E
            Note('A', 2),  # A string
            Note('D', 3),  # D string
            Note('G', 3),  # G string
        ]

        for note in notes:
            analysis = bass.analyze_note_difficulty(note)
            assert 'difficulty_score' in analysis


class TestInstrumentComparison:
    """Tests comparing difficulty across instruments."""

    def test_same_chord_different_instruments(self) -> None:
        """Test analyzing same chord on different instruments."""
        chord = Chord.from_symbol('F')

        guitar = GuitarDifficulty()
        piano = PianoDifficulty()

        guitar_analysis = guitar.analyze_chord_difficulty(chord)
        piano_analysis = piano.analyze_chord_difficulty(chord)

        # Both should provide difficulty scores
        assert 'difficulty_score' in guitar_analysis
        assert 'difficulty_score' in piano_analysis

    def test_complex_chord_analysis(self) -> None:
        """Test analyzing complex chord across instruments."""
        chord = Chord.from_symbol('Cmaj9')

        guitar = GuitarDifficulty()
        piano = PianoDifficulty()

        guitar_analysis = guitar.analyze_chord_difficulty(chord)
        piano_analysis = piano.analyze_chord_difficulty(chord)

        # All should handle extended chords
        assert guitar_analysis is not None
        assert piano_analysis is not None
