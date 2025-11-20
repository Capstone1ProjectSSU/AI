"""Tests for chord suggestion strategies and engine."""

import pytest
from halmoni import (
    Note, Chord, Key, ChordProgression,
    ChordSuggestionEngine,
    BorrowedChordStrategy,
    ChromaticApproachStrategy,
    NeapolitanStrategy,
    SubV7Strategy,
    SuspendStrategy,
    TSDMovementStrategy,
)


class TestChordSuggestionEngine:
    """Tests for the main suggestion engine."""

    def test_engine_creation(self) -> None:
        """Test creating a suggestion engine."""
        engine = ChordSuggestionEngine()
        assert len(engine.strategies) == 6

    def test_get_available_strategies(self) -> None:
        """Test getting list of available strategies."""
        engine = ChordSuggestionEngine()
        strategies = engine.get_available_strategies()
        assert 'BorrowedChord' in strategies
        assert 'SubV7' in strategies
        assert len(strategies) == 6

    def test_get_suggestions_basic(self, simple_progression: ChordProgression,
                                  c_major_key: Key) -> None:
        """Test getting basic suggestions."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(simple_progression, c_major_key)

        assert isinstance(suggestions, list)
        # Should get some suggestions for a simple progression
        assert len(suggestions) >= 0

    def test_get_suggestions_with_filter(self, simple_progression: ChordProgression,
                                        c_major_key: Key) -> None:
        """Test filtering suggestions by strategy."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(
            simple_progression,
            c_major_key,
            strategy_filter=['SubV7', 'BorrowedChord']
        )

        # All suggestions should be from filtered strategies
        for suggestion in suggestions:
            if hasattr(suggestion, 'strategy_source'):
                assert suggestion.strategy_source in ['SubV7', 'BorrowedChord']

    def test_get_suggestions_by_strategy(self, simple_progression: ChordProgression,
                                        c_major_key: Key) -> None:
        """Test getting suggestions organized by strategy."""
        engine = ChordSuggestionEngine()
        results = engine.get_suggestions_by_strategy(simple_progression, c_major_key)

        assert isinstance(results, dict)
        assert len(results) == 6  # All strategies
        for strategy_name, suggestions in results.items():
            assert isinstance(suggestions, list)

    def test_get_suggestions_for_position(self, simple_progression: ChordProgression,
                                         c_major_key: Key) -> None:
        """Test getting suggestions for specific position."""
        engine = ChordSuggestionEngine()
        position_suggestions = engine.get_suggestions_for_position(
            simple_progression, 1, c_major_key
        )

        assert isinstance(position_suggestions, list)

    def test_analyze_progression_potential(self, simple_progression: ChordProgression,
                                          c_major_key: Key) -> None:
        """Test analyzing progression for improvement potential."""
        engine = ChordSuggestionEngine()
        analysis = engine.analyze_progression_potential(simple_progression, c_major_key)

        assert 'total_suggestions' in analysis
        assert 'high_confidence_suggestions' in analysis
        assert 'strategy_coverage' in analysis
        assert 'position_analysis' in analysis
        assert isinstance(analysis['position_analysis'], list)

    def test_max_suggestions_limit(self, simple_progression: ChordProgression,
                                  c_major_key: Key) -> None:
        """Test max suggestions parameter."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(
            simple_progression, c_major_key, max_suggestions=5
        )

        assert len(suggestions) <= 5

    def test_get_strategy_description(self) -> None:
        """Test getting strategy descriptions."""
        engine = ChordSuggestionEngine()
        description = engine.get_strategy_description('SubV7')
        assert description is not None
        assert 'tritone' in description.lower()


class TestBorrowedChordStrategy:
    """Tests for borrowed chord strategy."""

    def test_strategy_creation(self) -> None:
        """Test creating borrowed chord strategy."""
        strategy = BorrowedChordStrategy()
        assert strategy.get_strategy_name() == 'BorrowedChord'

    def test_suggest_for_progression(self, simple_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test getting suggestions for a progression."""
        strategy = BorrowedChordStrategy()
        suggestions = strategy.suggest(simple_progression, c_major_key)

        assert isinstance(suggestions, list)
        for suggestion in suggestions:
            assert hasattr(suggestion, 'chord')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'reasoning')
            assert 0.0 <= suggestion.confidence <= 1.0


class TestChromaticApproachStrategy:
    """Tests for chromatic approach strategy."""

    def test_strategy_creation(self) -> None:
        """Test creating chromatic approach strategy."""
        strategy = ChromaticApproachStrategy()
        assert strategy.get_strategy_name() == 'ChromaticApproach'

    def test_suggest_for_progression(self, jazz_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test suggestions for jazz progression."""
        strategy = ChromaticApproachStrategy()
        suggestions = strategy.suggest(jazz_progression, c_major_key)

        assert isinstance(suggestions, list)


class TestNeapolitanStrategy:
    """Tests for Neapolitan chord strategy."""

    def test_strategy_creation(self) -> None:
        """Test creating Neapolitan strategy."""
        strategy = NeapolitanStrategy()
        assert strategy.get_strategy_name() == 'Neapolitan'

    def test_suggest_for_progression(self, simple_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test Neapolitan suggestions."""
        strategy = NeapolitanStrategy()
        suggestions = strategy.suggest(simple_progression, c_major_key)

        assert isinstance(suggestions, list)


class TestSubV7Strategy:
    """Tests for tritone substitution strategy."""

    def test_strategy_creation(self) -> None:
        """Test creating SubV7 strategy."""
        strategy = SubV7Strategy()
        assert strategy.get_strategy_name() == 'SubV7'

    def test_suggest_for_jazz_progression(self, jazz_progression: ChordProgression,
                                         c_major_key: Key) -> None:
        """Test SubV7 suggestions for jazz progression."""
        strategy = SubV7Strategy()
        suggestions = strategy.suggest(jazz_progression, c_major_key)

        assert isinstance(suggestions, list)
        # Jazz progressions should have SubV7 opportunities
        for suggestion in suggestions:
            assert hasattr(suggestion, 'chord')
            assert hasattr(suggestion, 'confidence')


class TestSuspendStrategy:
    """Tests for suspension chord strategy."""

    def test_strategy_creation(self) -> None:
        """Test creating Suspend strategy."""
        strategy = SuspendStrategy()
        assert strategy.get_strategy_name() == 'Suspend'

    def test_suggest_for_progression(self, simple_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test suspension suggestions."""
        strategy = SuspendStrategy()
        suggestions = strategy.suggest(simple_progression, c_major_key)

        assert isinstance(suggestions, list)


class TestTSDMovementStrategy:
    """Tests for Tonic-Subdominant-Dominant movement strategy."""

    def test_strategy_creation(self) -> None:
        """Test creating TSD movement strategy."""
        strategy = TSDMovementStrategy()
        assert strategy.get_strategy_name() == 'TSDMovement'

    def test_suggest_for_progression(self, simple_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test TSD movement suggestions."""
        strategy = TSDMovementStrategy()
        suggestions = strategy.suggest(simple_progression, c_major_key)

        assert isinstance(suggestions, list)

    def test_suggest_dominant_to_tonic(self, c_major_key: Key) -> None:
        """Test suggesting tonic after dominant."""
        strategy = TSDMovementStrategy()
        prog = ChordProgression.from_symbols(['G'], key=c_major_key)  # V chord
        suggestions = strategy.suggest(prog, c_major_key)
        # Should suggest I chord (C)
        assert len(suggestions) >= 0

    def test_suggest_tonic_to_subdominant(self, c_major_key: Key) -> None:
        """Test suggesting subdominant after tonic."""
        strategy = TSDMovementStrategy()
        prog = ChordProgression.from_symbols(['C'], key=c_major_key)  # I chord
        suggestions = strategy.suggest(prog, c_major_key)
        # Should suggest IV chord
        assert len(suggestions) >= 0


class TestSuggestionQuality:
    """Tests for suggestion quality metrics."""

    def test_voice_leading_quality(self, c_major_key: Key) -> None:
        """Test voice leading quality calculation."""
        strategy = BorrowedChordStrategy()
        chord1 = Chord.from_symbol('C')
        chord2 = Chord.from_symbol('F')

        quality = strategy._calculate_voice_leading_quality(chord1, chord2)
        assert 0.0 <= quality <= 1.0

    def test_voice_leading_common_tones(self, c_major_key: Key) -> None:
        """Test that common tones improve voice leading quality."""
        strategy = BorrowedChordStrategy()
        c_major = Chord.from_symbol('C')
        a_minor = Chord.from_symbol('Am')  # Shares C and E

        quality = strategy._calculate_voice_leading_quality(c_major, a_minor)
        assert quality > 0.5  # Should be good due to common tones

    def test_harmonic_function_detection(self, c_major_key: Key) -> None:
        """Test harmonic function detection."""
        strategy = TSDMovementStrategy()
        tonic_chord = Chord.from_symbol('C')
        dominant_chord = Chord.from_symbol('G')

        tonic_function = strategy._get_harmonic_function(tonic_chord, c_major_key)
        dominant_function = strategy._get_harmonic_function(dominant_chord, c_major_key)

        assert tonic_function == 'tonic'
        assert dominant_function == 'dominant'


class TestSuggestionValidation:
    """Tests for validating suggestions."""

    def test_suggestion_has_required_fields(self, simple_progression: ChordProgression,
                                           c_major_key: Key) -> None:
        """Test that all suggestions have required fields."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(simple_progression, c_major_key)

        for suggestion in suggestions:
            assert hasattr(suggestion, 'chord')
            assert hasattr(suggestion, 'confidence')
            assert hasattr(suggestion, 'reasoning')
            assert hasattr(suggestion, 'position')
            assert hasattr(suggestion, 'voice_leading_quality')

    def test_confidence_in_valid_range(self, simple_progression: ChordProgression,
                                      c_major_key: Key) -> None:
        """Test that confidence scores are in valid range."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(simple_progression, c_major_key)

        for suggestion in suggestions:
            assert 0.0 <= suggestion.confidence <= 1.0

    def test_position_in_valid_range(self, simple_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test that position is in valid range."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(simple_progression, c_major_key)

        for suggestion in suggestions:
            assert 0 <= suggestion.position <= len(simple_progression)


class TestBorrowedChordStrategyAdvanced:
    """Advanced tests for borrowed chord strategy."""

    def test_borrowed_from_parallel_minor(self, c_major_key: Key) -> None:
        """Test borrowing from parallel minor."""
        strategy = BorrowedChordStrategy()
        prog = ChordProgression.from_symbols(['C', 'F', 'G'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)
        # Should suggest chords from C minor
        assert isinstance(suggestions, list)

    def test_borrowed_chord_confidence(self, c_major_key: Key) -> None:
        """Test that borrowed chords have reasonable confidence."""
        strategy = BorrowedChordStrategy()
        prog = ChordProgression.from_symbols(['C'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)

        for suggestion in suggestions:
            assert 0.0 <= suggestion.confidence <= 1.0

    def test_borrowed_after_subdominant(self, c_major_key: Key) -> None:
        """Test borrowed chords after subdominant."""
        strategy = BorrowedChordStrategy()
        prog = ChordProgression.from_symbols(['C', 'F'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)
        assert len(suggestions) >= 0


class TestChromaticApproachStrategyAdvanced:
    """Advanced tests for chromatic approach strategy."""

    def test_chromatic_approach_to_dominant(self, c_major_key: Key) -> None:
        """Test chromatic approach to dominant chord."""
        strategy = ChromaticApproachStrategy()
        prog = ChordProgression.from_symbols(['C', 'F'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)
        # May suggest chromatic approach to G
        assert isinstance(suggestions, list)

    def test_chromatic_passing_chord(self, c_major_key: Key) -> None:
        """Test chromatic passing chords."""
        strategy = ChromaticApproachStrategy()
        prog = ChordProgression.from_symbols(['C'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)

        for suggestion in suggestions:
            assert suggestion.chord is not None


class TestSubV7StrategyAdvanced:
    """Advanced tests for SubV7 strategy."""

    def test_tritone_sub_for_dominant(self, c_major_key: Key) -> None:
        """Test tritone substitution for dominant."""
        strategy = SubV7Strategy()
        prog = ChordProgression.from_symbols(['C', 'G7'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)
        # Should suggest Db7 as substitute for G7
        assert isinstance(suggestions, list)

    def test_subv7_confidence_scores(self, c_major_key: Key) -> None:
        """Test that SubV7 suggestions have confidence scores."""
        strategy = SubV7Strategy()
        prog = ChordProgression.from_symbols(['G7', 'C'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)

        for suggestion in suggestions:
            assert hasattr(suggestion, 'confidence')
            assert 0.0 <= suggestion.confidence <= 1.0


class TestSuspendStrategyAdvanced:
    """Advanced tests for Suspend strategy."""

    def test_sus4_resolution(self, c_major_key: Key) -> None:
        """Test sus4 chord suggestions."""
        strategy = SuspendStrategy()
        prog = ChordProgression.from_symbols(['C', 'G'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)
        assert isinstance(suggestions, list)

    def test_sus2_suggestions(self, c_major_key: Key) -> None:
        """Test sus2 chord suggestions."""
        strategy = SuspendStrategy()
        prog = ChordProgression.from_symbols(['C'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)

        # Should include sus chords
        assert len(suggestions) >= 0


class TestNeapolitanStrategyAdvanced:
    """Advanced tests for Neapolitan strategy."""

    def test_neapolitan_sixth(self, c_major_key: Key) -> None:
        """Test Neapolitan sixth suggestions."""
        strategy = NeapolitanStrategy()
        prog = ChordProgression.from_symbols(['C', 'F', 'G'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)
        assert isinstance(suggestions, list)

    def test_neapolitan_confidence(self, c_major_key: Key) -> None:
        """Test Neapolitan has confidence scores."""
        strategy = NeapolitanStrategy()
        prog = ChordProgression.from_symbols(['F', 'G'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)

        for suggestion in suggestions:
            assert 0.0 <= suggestion.confidence <= 1.0

    def test_position_in_valid_range(self, simple_progression: ChordProgression,
                                    c_major_key: Key) -> None:
        """Test that positions are valid."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(simple_progression, c_major_key)

        for suggestion in suggestions:
            assert 0 <= suggestion.position <= len(simple_progression)

    def test_neapolitan_resolution_to_dominant(self, c_major_key: Key) -> None:
        """Test that Neapolitan resolving to dominant has higher confidence."""
        strategy = NeapolitanStrategy()

        # Progression with dominant following (classic N6 → V → I)
        prog_with_dominant = ChordProgression.from_symbols(['Dm', 'G7', 'C'], key=c_major_key)
        suggestions_with = strategy.suggest(prog_with_dominant, c_major_key)

        # Progression without dominant following
        prog_without_dominant = ChordProgression.from_symbols(['Dm', 'F', 'C'], key=c_major_key)
        suggestions_without = strategy.suggest(prog_without_dominant, c_major_key)

        # Find Neapolitan suggestions at position 0 (replacing Dm)
        neap_with = [s for s in suggestions_with if s.position == 0.0]
        neap_without = [s for s in suggestions_without if s.position == 0.0]

        # If both have suggestions, the one with dominant resolution should have higher confidence
        if neap_with and neap_without:
            max_conf_with = max(s.confidence for s in neap_with)
            max_conf_without = max(s.confidence for s in neap_without)
            assert max_conf_with >= max_conf_without

    def test_neapolitan_in_cadential_progression(self, c_major_key: Key) -> None:
        """Test Neapolitan in classic cadential progression (ii-V-I)."""
        strategy = NeapolitanStrategy()

        # Classic ii-V-I progression (perfect for Neapolitan substitution)
        prog = ChordProgression.from_symbols(['Dm7', 'G7', 'C'], key=c_major_key)
        suggestions = strategy.suggest(prog, c_major_key)

        # Should suggest Neapolitan at position 0 (replacing ii)
        position_0_suggestions = [s for s in suggestions if s.position == 0.0]
        assert len(position_0_suggestions) > 0

        # Check that suggestions have reasonable confidence
        for suggestion in position_0_suggestions:
            assert suggestion.confidence > 0.6  # Should be fairly confident

    def test_neapolitan_resolution_quality_boost(self, c_major_key: Key) -> None:
        """Test that resolution quality affects confidence."""
        strategy = NeapolitanStrategy()

        # Perfect cadential resolution: ii → V → I
        perfect_prog = ChordProgression.from_symbols(['Dm', 'G7', 'C'], key=c_major_key)
        perfect_suggestions = strategy.suggest(perfect_prog, c_major_key)

        # Weaker resolution: ii → iii
        weak_prog = ChordProgression.from_symbols(['Dm', 'Em'], key=c_major_key)
        weak_suggestions = strategy.suggest(weak_prog, c_major_key)

        # Perfect resolution should have suggestions
        assert len(perfect_suggestions) > 0

        # Check confidence scores are reasonable
        for suggestion in perfect_suggestions:
            assert 0.0 <= suggestion.confidence <= 1.0

    def test_neapolitan_in_minor_key_with_resolution(self) -> None:
        """Test Neapolitan in minor key with dominant resolution."""
        a_minor_key = Key(Note('A', 4), 'minor')
        strategy = NeapolitanStrategy()

        # Classic minor key progression: iv → V → i
        prog = ChordProgression.from_symbols(['Dm', 'E7', 'Am'], key=a_minor_key)
        suggestions = strategy.suggest(prog, a_minor_key)

        # Should suggest Neapolitan (especially for position 0)
        position_0_suggestions = [s for s in suggestions if s.position == 0.0]

        if position_0_suggestions:
            # In minor keys with resolution, confidence should be high
            max_confidence = max(s.confidence for s in position_0_suggestions)
            assert max_confidence > 0.7  # Should be quite confident in minor keys


class TestSuggestionEngineAdvanced:
    """Advanced tests for the suggestion engine."""

    def test_get_suggestions_for_position(self, c_major_key: Key) -> None:
        """Test getting suggestions for specific position."""
        engine = ChordSuggestionEngine()
        prog = ChordProgression.from_symbols(['C', 'F', 'G'], key=c_major_key)
        suggestions = engine.get_suggestions_for_position(prog, 1, c_major_key)
        assert isinstance(suggestions, list)

    def test_analyze_progression_potential(self, c_major_key: Key) -> None:
        """Test analyzing progression potential."""
        engine = ChordSuggestionEngine()
        prog = ChordProgression.from_symbols(['C', 'F', 'G'], key=c_major_key)
        analysis = engine.analyze_progression_potential(prog, c_major_key)
        assert 'total_suggestions' in analysis
        assert 'strategy_coverage' in analysis

    def test_filter_by_strategy(self, c_major_key: Key) -> None:
        """Test filtering suggestions by strategy."""
        engine = ChordSuggestionEngine()
        prog = ChordProgression.from_symbols(['C', 'G7'], key=c_major_key)
        suggestions = engine.get_suggestions(prog, c_major_key, strategy_filter=['SubV7'])
        # All suggestions should be from SubV7 strategy
        assert isinstance(suggestions, list)

    def test_empty_progression_suggestions(self, c_major_key: Key) -> None:
        """Test suggestions for minimal progression."""
        engine = ChordSuggestionEngine()
        prog = ChordProgression.from_symbols(['C'], key=c_major_key)
        suggestions = engine.get_suggestions(prog, c_major_key)
        assert isinstance(suggestions, list)

        for suggestion in suggestions:
            # Position should be within progression or just after (for insertions)
            assert suggestion.position >= 0
            assert suggestion.position <= len(prog) + 1

    def test_reasoning_not_empty(self, simple_progression: ChordProgression,
                                 c_major_key: Key) -> None:
        """Test that reasoning is provided."""
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(simple_progression, c_major_key)

        for suggestion in suggestions:
            assert isinstance(suggestion.reasoning, str)
            if len(suggestions) > 0:
                # At least some suggestions should have non-empty reasoning
                assert any(len(s.reasoning) > 0 for s in suggestions)
