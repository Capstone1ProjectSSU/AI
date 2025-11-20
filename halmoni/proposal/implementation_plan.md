# Implementation Plan: Halmoni Library Evolution

**Status:** Draft for Review
**Target Version:** v1.0.0
**Estimated Timeline:** 6-8 weeks

---

## Executive Summary

This document provides a concrete implementation plan for evolving the `halmoni` library based on the clarified proposal. It selects the features to implement, fills critical specification gaps, and provides step-by-step implementation guidance.

### Scope Selection

**IN SCOPE (Phases 1-3):**
- ✅ Core `Score` object with `from_midi()` constructor
- ✅ Enhanced `ChordAnalysis` with functional analysis
- ✅ Updated `ChordSuggestion` with structured metadata
- ✅ `Reharmonizer` engine with beam search
- ✅ Three default style profiles (Jazz, Classical, Pop)
- ✅ Complete migration guide and examples

**OUT OF SCOPE (Future v1.1+):**
- ❌ Interactive/incremental reharmonization
- ❌ Custom user-defined style profiles (will use presets only)
- ❌ Multiple alternative outputs (`reharmonize_multiple()`)
- ❌ Rock and Folk style profiles (defer to v1.1)
- ❌ Advanced voicing-aware suggestions

---

## Part 1: Resolved Specifications

This section fills the critical gaps identified in the technical review.

### 1.1. Complete Data Model Specifications

#### `PitchClass` Implementation

**Decision:** Use a proper class with validation, NOT `NewType`.

```python
# halmoni/core/pitch_class.py

from typing import ClassVar, Set

class PitchClass:
    """
    Represents a pitch without octave information (C, C#, Db, etc.).

    Used in contexts where octave is irrelevant, such as:
    - Key signatures (Key.from_string("C Major"))
    - Scale degrees
    - Chord root specification without register
    """

    # All valid pitch class names (enharmonic equivalents included)
    VALID_NAMES: ClassVar[Set[str]] = {
        'C', 'C#', 'Db', 'D', 'D#', 'Eb', 'E', 'Fb', 'E#',
        'F', 'F#', 'Gb', 'G', 'G#', 'Ab', 'A', 'A#', 'Bb', 'B', 'Cb', 'B#'
    }

    # Canonical (simplified) names
    CANONICAL_NAMES: ClassVar[Set[str]] = {
        'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'
    }

    def __init__(self, name: str):
        """
        Create a pitch class from a name.

        Args:
            name: Pitch class name (e.g., 'C', 'F#', 'Bb')

        Raises:
            ValueError: If name is not a valid pitch class
        """
        if name not in self.VALID_NAMES:
            raise ValueError(
                f"Invalid pitch class: {name}. "
                f"Must be one of: {sorted(self.VALID_NAMES)}"
            )
        self._name = name

    @property
    def name(self) -> str:
        """Get the pitch class name."""
        return self._name

    def to_canonical(self) -> 'PitchClass':
        """Convert to canonical sharp-based representation."""
        # Enharmonic mapping
        enharmonic_map = {
            'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
            'Fb': 'E', 'E#': 'F', 'Cb': 'B', 'B#': 'C'
        }
        canonical_name = enharmonic_map.get(self._name, self._name)
        return PitchClass(canonical_name)

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"PitchClass('{self._name}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PitchClass):
            return NotImplemented
        # Compare canonical forms for enharmonic equivalence
        return self.to_canonical().name == other.to_canonical().name

    def __hash__(self) -> int:
        return hash(self.to_canonical().name)
```

#### `Note` Constructor API

**Decision:** Support both patterns, with string form as primary.

```python
# halmoni/core/note.py (updated)

class Note:
    """Represents a musical note with pitch and octave."""

    def __init__(self, pitch: Union[str, PitchClass], octave: Optional[int] = None):
        """
        Create a note from pitch and octave.

        Args:
            pitch: Either "C4" string notation, or PitchClass/"C" without octave
            octave: Octave number (required if pitch is PitchClass/string without octave)

        Examples:
            >>> Note("C4")              # String notation (preferred)
            >>> Note("C", 4)            # Separate pitch and octave
            >>> Note(PitchClass("C"), 4)  # Explicit PitchClass

        Raises:
            ValueError: If octave is missing when required
        """
        # Case 1: "C4" string notation
        if isinstance(pitch, str) and any(char.isdigit() for char in pitch):
            self._parse_from_string(pitch)
            if octave is not None:
                raise ValueError(
                    f"Octave specified twice: in string '{pitch}' and as argument {octave}"
                )

        # Case 2: PitchClass or pitch name without octave
        else:
            if octave is None:
                raise ValueError(
                    f"Octave required when pitch is PitchClass or pitch name. "
                    f"Use Note('{pitch}', octave) or Note('{pitch}4') notation."
                )

            if isinstance(pitch, str):
                pitch = PitchClass(pitch)

            self._pitch_class = pitch
            self._octave = octave

    def _parse_from_string(self, note_str: str) -> None:
        """Parse 'C4', 'F#5', 'Bb3' notation."""
        # Implementation: extract pitch class and octave
        # ... (existing logic)
        pass

    @classmethod
    def from_pitch_class(cls, pitch_class: Union[str, PitchClass], octave: int = 4) -> 'Note':
        """
        Create a note from pitch class with default octave.

        Args:
            pitch_class: PitchClass or string like "C"
            octave: Octave number (default: 4, middle octave)

        Returns:
            Note instance
        """
        if isinstance(pitch_class, str):
            pitch_class = PitchClass(pitch_class)
        return cls(pitch_class, octave)
```

#### `Score` Object Complete Specification

**Decision:** Separate tracks from melodies, add convenience properties.

```python
# halmoni/core/score.py

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class AnalysisMetadata:
    """Metadata about the analysis process."""
    key_detection_confidence: float
    key_detection_method: str  # "krumhansl_schmuckler" or "manual"
    chord_detection_method: str  # "halmoni" or "adam_stark"
    quantization_grid: float  # in beats
    primary_melody_track: int
    harmony_tracks: List[int]

@dataclass
class Metadata:
    """Song metadata extracted from MIDI file."""
    title: Optional[str] = None
    composer: Optional[str] = None
    copyright: Optional[str] = None
    track_names: List[str] = None
    initial_tempo: float = 120.0
    initial_time_signature: Tuple[int, int] = (4, 4)

    def __post_init__(self):
        if self.track_names is None:
            self.track_names = []

@dataclass
class NoteEvent:
    """A single note event with timing information."""
    pitch: Note
    start_time: float  # in beats from start of piece
    duration: float    # in beats
    velocity: int      # MIDI velocity (0-127)
    track_id: int

@dataclass
class Track:
    """A single MIDI track with separated melody and harmony."""
    track_id: int
    name: str
    notes: List[NoteEvent]
    is_percussion: bool

    def get_melody_notes(self) -> List[NoteEvent]:
        """
        Extract melody notes (highest voice) from this track.
        Uses heuristic: notes that are the highest pitch at each time window.
        """
        # Implementation in Phase 1
        pass

    def get_harmony_notes(self) -> List[NoteEvent]:
        """Extract harmony notes (non-melody) from this track."""
        # Implementation in Phase 1
        pass

class Score:
    """
    Unified container for all musical information about a piece.

    The primary entry point for users. Created from MIDI files with
    automatic analysis of chords, melody, and key.
    """

    def __init__(
        self,
        progression: ChordProgression,
        tracks: Dict[int, Track],
        key: Key,
        metadata: Metadata,
        analysis_metadata: AnalysisMetadata,
        warnings: Optional[List[str]] = None
    ):
        self.progression = progression
        self.tracks = tracks
        self.key = key
        self.metadata = metadata
        self.analysis_metadata = analysis_metadata
        self.warnings = warnings or []

    @property
    def primary_melody(self) -> List[NoteEvent]:
        """Get the primary melody line (convenience property)."""
        primary_track_id = self.analysis_metadata.primary_melody_track
        return self.tracks[primary_track_id].get_melody_notes()

    @property
    def all_melody_notes(self) -> List[NoteEvent]:
        """Get all melody notes from all tracks, sorted by start_time."""
        all_notes = []
        for track in self.tracks.values():
            if not track.is_percussion:
                all_notes.extend(track.get_melody_notes())
        return sorted(all_notes, key=lambda n: n.start_time)

    @classmethod
    def from_midi(
        cls,
        filepath: str,
        manual_key: Optional[Union[str, Key]] = None,
        melody_track_id: Optional[int] = None,
        harmony_track_ids: Optional[List[int]] = None,
        quantization_grid: float = 0.25,
        key_confidence_threshold: float = 0.6
    ) -> 'Score':
        """
        Create a Score from a MIDI file with automatic analysis.

        Args:
            filepath: Path to MIDI file
            manual_key: Override automatic key detection (e.g., "C Major" or Key object)
            melody_track_id: Manually specify primary melody track (0-indexed)
            harmony_track_ids: Manually specify harmony tracks
            quantization_grid: Note timing quantization in beats (default 0.25 = 16th notes)
            key_confidence_threshold: Minimum confidence for auto key detection (default 0.6)

        Returns:
            Score object with analyzed progression, melody, and key

        Raises:
            FileNotFoundError: If MIDI file doesn't exist
            ValueError: If MIDI has no tracks or cannot detect key
        """
        # Implementation in Phase 1
        pass

    def __repr__(self) -> str:
        return (
            f"Score(key={self.key}, "
            f"progression_length={len(self.progression.chords)}, "
            f"tracks={len(self.tracks)})"
        )
```

#### `ChordAnalysis` Complete Specification

**Decision:** Use two-tier scale degree (diatonic + chromatic).

```python
# halmoni/core/analysis.py

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class HarmonicFunction(Enum):
    """Enumeration of harmonic functions."""
    TONIC = "Tonic"
    SUBDOMINANT = "Subdominant"
    DOMINANT = "Dominant"
    SECONDARY_DOMINANT = "SecondaryDominant"
    SECONDARY_LEADING_TONE = "SecondaryLeadingTone"
    MODAL = "Modal"  # For non-functional progressions
    BORROWED = "Borrowed"  # When function unclear due to borrowing

@dataclass
class Tension:
    """Represents a chord extension/tension."""
    interval: int  # 9, 11, 13
    alteration: Optional[str] = None  # "flat", "sharp", or None

    def __str__(self) -> str:
        if self.alteration == "flat":
            return f"♭{self.interval}"
        elif self.alteration == "sharp":
            return f"#{self.interval}"
        else:
            return str(self.interval)

@dataclass
class ChordAnalysis:
    """
    Rich harmonic analysis of a chord within a key context.

    This object provides complete music-theoretical information about
    how a chord functions within a specific key.
    """

    # Roman numeral representation (e.g., "V7", "V7/IV", "♭II", "iv")
    roman_numeral: str

    # Harmonic function (Tonic, Dominant, etc.)
    function: HarmonicFunction

    # Whether the chord is diatonic to the key
    is_diatonic: bool

    # Whether the chord is borrowed from parallel mode
    is_borrowed: bool

    # Scale degree of the root
    # - For diatonic chords: 1-7 (e.g., V = 5)
    # - For chromatic chords: chromatic degree (e.g., ♭II = 1, V7/V = 5)
    # - For secondary dominants: degree of temporary tonic (e.g., V7/ii has scale_degree=2)
    scale_degree: int

    # Chord quality (from existing Chord.quality)
    quality: str

    # Extensions/tensions (9, 11, 13, with alterations)
    tensions: List[Tension]

    # If borrowed, which mode it's from (e.g., "parallel_minor", "mixolydian")
    borrowed_from_mode: Optional[str]

    # Functional strength: 0.0 (weak) to 1.0 (strong)
    # Examples:
    #   V7 -> I: 1.0 (strongest resolution)
    #   IV -> I: 0.7 (plagal cadence)
    #   iii -> IV: 0.3 (weak progression)
    functional_strength: float

    def __str__(self) -> str:
        return f"{self.roman_numeral} ({self.function.value})"
```

#### `SubstitutionType` Complete Enumeration

```python
# halmoni/suggestions/types.py

from enum import Enum

class SubstitutionType(Enum):
    """Types of chord substitutions/suggestions."""

    # Functional harmony (TSDMovementStrategy)
    FUNCTIONAL_REPLACEMENT = "functional_replacement"  # Replace iii with I
    FUNCTIONAL_INSERTION = "functional_insertion"      # Insert S between T and D

    # Modal borrowing (BorrowedChordStrategy)
    MODAL_BORROWING = "modal_borrowing"               # Borrow from parallel mode

    # Chromatic alterations
    TRITONE_SUBSTITUTION = "tritone_substitution"     # SubV7Strategy
    NEAPOLITAN_SIXTH = "neapolitan_sixth"             # NeapolitanStrategy

    # Voice leading / passing
    CHROMATIC_APPROACH = "chromatic_approach"         # ChromaticApproachStrategy
    DIATONIC_PASSING = "diatonic_passing"             # Future: diatonic passing chords

    # Color/texture
    SUSPENSION = "suspension"                          # SuspendStrategy
    ADDED_TENSION = "added_tension"                   # Future: add 9th, 11th, etc.

    # Secondary function
    SECONDARY_DOMINANT = "secondary_dominant"         # Future: V7/X suggestions
    SECONDARY_LEADING_TONE = "secondary_leading_tone" # Future: vii°7/X

    # Diatonic
    DIATONIC_SUBSTITUTION = "diatonic_substitution"   # Future: vi for I, etc.
```

#### Updated `ChordSuggestion`

```python
# halmoni/suggestions/base.py (updated)

from dataclasses import dataclass
from typing import Optional

@dataclass
class ChordSuggestion:
    """
    A suggested chord modification with rich metadata.

    This object represents a single suggestion from a strategy,
    including all information needed for scoring and reasoning.
    """

    # The suggested chord
    suggested_chord: Chord

    # Confidence score (0.0 to 1.0) before style weighting
    confidence: float

    # Human-readable explanation
    reasoning: str

    # Position in progression (0-indexed)
    # For insertions: position to insert BEFORE
    position: int

    # Voice leading quality (0.0 to 1.0)
    voice_leading_quality: float

    # NEW: Strategy that generated this suggestion
    strategy_source: str

    # NEW: Type of substitution (for variety tracking)
    substitution_type: SubstitutionType

    # NEW: The chord this replaces (None if insertion)
    target_chord: Optional[Chord]

    # NEW: True if this inserts a chord, False if it replaces
    is_insertion: bool

    # NEW: Melodic implications (for debugging/explanation)
    melodic_implications: Optional[str] = None

    def __post_init__(self):
        """Validate suggestion data."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")
        if not 0.0 <= self.voice_leading_quality <= 1.0:
            raise ValueError(f"Voice leading quality must be 0.0-1.0, got {self.voice_leading_quality}")
        if self.is_insertion and self.target_chord is not None:
            raise ValueError("Insertion should not have target_chord")
        if not self.is_insertion and self.target_chord is None:
            raise ValueError("Replacement must have target_chord")
```

### 1.2. Melody Clash Detection Table

**Decision:** Define specific interval clash penalties.

```python
# halmoni/analysis/melody_analysis.py

from typing import Dict, Tuple
from halmoni.core import Note, Chord

# Interval clash penalties (0.0 = consonant, 1.0 = complete dissonance)
INTERVAL_CLASH_PENALTIES: Dict[int, float] = {
    # Perfect consonances
    0: 0.0,   # Unison
    7: 0.0,   # Perfect 5th
    12: 0.0,  # Octave

    # Imperfect consonances
    3: 0.0,   # Minor 3rd
    4: 0.0,   # Major 3rd
    8: 0.0,   # Minor 6th
    9: 0.0,   # Major 6th

    # Mild dissonances (acceptable in many contexts)
    2: 0.2,   # Major 2nd
    10: 0.2,  # Minor 7th
    5: 0.3,   # Perfect 4th (contextual)

    # Strong dissonances
    1: 0.8,   # Minor 2nd
    11: 0.8,  # Major 7th
    6: 0.6,   # Tritone (if not in chord)

    # Compound intervals (treat as simple + small penalty)
    13: 0.2,  # Minor 9th (compound minor 2nd - very harsh)
    14: 0.3,  # Major 9th (compound major 2nd)
    15: 0.2,  # Minor 10th (compound minor 3rd)
    # ... etc
}

def calculate_melodic_clash_penalty(
    melody_note: Note,
    chord: Chord,
    penalty_multiplier: float = 1.0
) -> float:
    """
    Calculate penalty for melody-chord clash.

    Args:
        melody_note: The melody note to check
        chord: The chord being played
        penalty_multiplier: Multiply final penalty (from StyleProfile)

    Returns:
        Clash penalty (0.0 = no clash, higher = more dissonant)
    """
    # Get chord tones
    chord_pitches = chord.get_pitches()  # Method to implement

    min_penalty = 1.0  # Start with worst case

    for chord_pitch in chord_pitches:
        # Calculate interval (in semitones)
        interval = abs(melody_note.midi_number - chord_pitch.midi_number) % 12

        # Get penalty for this interval
        penalty = INTERVAL_CLASH_PENALTIES.get(interval, 0.5)  # Unknown intervals: moderate

        # Track minimum (best case for this melody note)
        min_penalty = min(min_penalty, penalty)

    return min_penalty * penalty_multiplier

def analyze_melody_chord_compatibility(
    melody_notes: List[NoteEvent],
    progression: ChordProgression
) -> List[Tuple[int, float]]:
    """
    Analyze compatibility between melody and chord progression.

    Returns:
        List of (chord_index, average_clash_penalty) tuples
    """
    # Implementation in Phase 2
    pass
```

### 1.3. Reharmonizer Complete Specification

#### Complete Method Signature

```python
# halmoni/reharmonization/reharmonizer.py

from typing import Optional, Union
from halmoni.core import Score
from halmoni.reharmonization.style_profile import StyleProfile

class Reharmonizer:
    """
    Engine for intelligent reharmonization of musical progressions.

    Uses beam search with music-theoretical scoring to generate
    stylistically appropriate chord substitutions and insertions.
    """

    def __init__(self):
        """
        Create a reharmonizer instance.

        Note: Reharmonizer is stateless and can be reused for multiple scores.
        """
        pass

    def reharmonize(
        self,
        score: Score,
        style: Union[str, StyleProfile],
        complexity: float,
        seed: Optional[int] = None,
        beam_width: int = 10,
        max_suggestions: int = 50,
        max_time_seconds: float = 30.0,
        preserve_melody_harmonization: bool = True
    ) -> Score:
        """
        Reharmonize a score with specified style and complexity.

        Args:
            score: Original score to reharmonize
            style: Style profile name ("jazz", "classical", "pop") or custom StyleProfile
            complexity: 0.0 (minimal diatonic changes) to 1.0 (maximum chromaticism)
            seed: Random seed for reproducibility (None = non-deterministic)
            beam_width: Number of candidates to keep at each step (higher = slower but better)
            max_suggestions: Maximum number of suggestions to apply (prevents over-reharmonization)
            max_time_seconds: Timeout for beam search
            preserve_melody_harmonization: If True, heavily penalize melody-chord clashes

        Returns:
            New Score with reharmonized progression (original score unchanged)

        Raises:
            ValueError: If style is unknown or complexity not in [0.0, 1.0]
            TimeoutError: If beam search exceeds max_time_seconds
        """
        # Implementation in Phase 3
        pass

    def explain_reharmonization(
        self,
        original_score: Score,
        reharmonized_score: Score
    ) -> str:
        """
        Generate human-readable explanation of what changed.

        Args:
            original_score: Original score
            reharmonized_score: Reharmonized score

        Returns:
            Multi-line string explaining each change
        """
        # Implementation in Phase 3 or 4
        pass
```

#### Style Profiles with Complete Weights

```python
# halmoni/reharmonization/style_profile.py

from dataclasses import dataclass

@dataclass
class StyleProfile:
    """
    Configuration for reharmonization style.

    Controls which strategies are active and how scoring works.
    """

    # --- Strategy Activation Weights (0.0 = disabled, 1.0 = full confidence) ---
    tsd_movement_weight: float = 1.0
    neapolitan_weight: float = 0.0
    borrowed_chord_weight: float = 0.5
    subv7_weight: float = 0.0
    suspend_weight: float = 0.5
    chromatic_approach_weight: float = 0.2

    # --- Scoring Function Weights ---

    # Weight for voice leading quality in total score
    voice_leading_weight: float = 0.3

    # Weight for functional progression strength
    functional_progression_weight: float = 0.4

    # Weight for melodic consonance
    melodic_consonance_weight: float = 0.2

    # Weight for variety (penalizes repetitive strategy use)
    variety_weight: float = 0.1

    # --- Penalty Multipliers ---

    # Penalty for melody-chord clashes (higher = stricter)
    melodic_clash_penalty: float = 5.0

    # Penalty for consecutive same-strategy suggestions
    repetition_penalty: float = 0.3

    # --- Style-Specific Rules ---

    # Allow D→S progressions (retrogression)
    allow_dominant_to_subdominant: bool = False

    # Allow consecutive suspensions
    allow_consecutive_suspensions: bool = False

# Default style profiles
STYLE_PROFILES = {
    "jazz": StyleProfile(
        tsd_movement_weight=0.6,
        neapolitan_weight=0.1,
        borrowed_chord_weight=0.9,
        subv7_weight=1.0,
        suspend_weight=0.8,
        chromatic_approach_weight=1.0,
        voice_leading_weight=0.4,
        functional_progression_weight=0.2,
        melodic_consonance_weight=0.2,
        variety_weight=0.2,
        melodic_clash_penalty=3.0,  # Jazz tolerates more tension
        repetition_penalty=0.4,
        allow_dominant_to_subdominant=True,
        allow_consecutive_suspensions=True
    ),

    "classical": StyleProfile(
        tsd_movement_weight=1.0,
        neapolitan_weight=0.8,
        borrowed_chord_weight=0.6,
        subv7_weight=0.0,  # No tritone subs in classical
        suspend_weight=0.3,
        chromatic_approach_weight=0.5,
        voice_leading_weight=0.5,
        functional_progression_weight=0.8,  # Very strict functional harmony
        melodic_consonance_weight=0.4,
        variety_weight=0.05,
        melodic_clash_penalty=8.0,  # Classical is strict about dissonance
        repetition_penalty=0.2,
        allow_dominant_to_subdominant=False,
        allow_consecutive_suspensions=False
    ),

    "pop": StyleProfile(
        tsd_movement_weight=0.8,
        neapolitan_weight=0.0,  # Too dramatic for pop
        borrowed_chord_weight=1.0,  # Very common in pop
        subv7_weight=0.2,  # Rare but possible
        suspend_weight=1.0,  # Very common in pop
        chromatic_approach_weight=0.4,
        voice_leading_weight=0.2,
        functional_progression_weight=0.5,
        melodic_consonance_weight=0.3,
        variety_weight=0.1,
        melodic_clash_penalty=6.0,
        repetition_penalty=0.2,
        allow_dominant_to_subdominant=True,  # V-IV-I is common in pop
        allow_consecutive_suspensions=True
    )
}

def get_style_profile(name: str) -> StyleProfile:
    """Get a default style profile by name."""
    if name not in STYLE_PROFILES:
        raise ValueError(
            f"Unknown style: {name}. Available: {list(STYLE_PROFILES.keys())}"
        )
    return STYLE_PROFILES[name]
```

#### Scoring Function Formula

```python
# halmoni/reharmonization/scoring.py

from typing import List, Optional
from halmoni.core import ChordProgression, Key
from halmoni.suggestions import ChordSuggestion
from halmoni.reharmonization.style_profile import StyleProfile
from halmoni.analysis.melody_analysis import calculate_melodic_clash_penalty

def calculate_suggestion_score(
    suggestion: ChordSuggestion,
    progression: ChordProgression,
    key: Key,
    melody_notes: List[NoteEvent],
    previous_suggestion: Optional[ChordSuggestion],
    style: StyleProfile,
    complexity: float
) -> float:
    """
    Calculate total score for a suggestion using multi-component formula.

    Score Formula:
        total_score = (
            w1 * adjusted_confidence +
            w2 * voice_leading_quality +
            w3 * functional_progression_score +
            w4 * melodic_consonance_score +
            w5 * variety_score
        ) - penalties

    Args:
        suggestion: The suggestion to score
        progression: Current progression
        key: Key of the piece
        melody_notes: Melody notes at this position
        previous_suggestion: Previously applied suggestion (for variety)
        style: Style profile with weights
        complexity: Complexity parameter (0.0-1.0)

    Returns:
        Total score (higher is better)
    """

    # Component 1: Adjusted Confidence
    # Base confidence from strategy, weighted by style and complexity
    strategy_weight = _get_strategy_weight(suggestion.strategy_source, style)
    complexity_multiplier = _calculate_complexity_multiplier(
        suggestion, complexity
    )
    adjusted_confidence = (
        suggestion.confidence *
        strategy_weight *
        complexity_multiplier
    )

    # Component 2: Voice Leading Quality
    # Already calculated in suggestion
    voice_leading_quality = suggestion.voice_leading_quality

    # Component 3: Functional Progression Score
    functional_score = _calculate_functional_score(
        suggestion, progression, key, style
    )

    # Component 4: Melodic Consonance Score
    melodic_score = _calculate_melodic_score(
        suggestion, melody_notes, style
    )

    # Component 5: Variety Score
    variety_score = _calculate_variety_score(
        suggestion, previous_suggestion, style
    )

    # Weighted sum
    total_score = (
        style.voice_leading_weight * voice_leading_quality +
        style.functional_progression_weight * functional_score +
        style.melodic_consonance_weight * melodic_score +
        style.variety_weight * variety_score
    )

    # Note: adjusted_confidence is implicitly weighted as it's the base
    # that gets modified by other factors

    return total_score * adjusted_confidence


def _get_strategy_weight(strategy_name: str, style: StyleProfile) -> float:
    """Map strategy name to style profile weight."""
    strategy_weight_map = {
        "TSDMovementStrategy": style.tsd_movement_weight,
        "NeapolitanStrategy": style.neapolitan_weight,
        "BorrowedChordStrategy": style.borrowed_chord_weight,
        "SubV7Strategy": style.subv7_weight,
        "SuspendStrategy": style.suspend_weight,
        "ChromaticApproachStrategy": style.chromatic_approach_weight,
    }
    return strategy_weight_map.get(strategy_name, 0.5)  # Default 0.5 for unknown


def _calculate_complexity_multiplier(
    suggestion: ChordSuggestion,
    complexity: float
) -> float:
    """
    Calculate multiplier based on complexity parameter.

    - complexity=0.0: Only diatonic suggestions get full weight
    - complexity=1.0: All suggestions get full weight
    - complexity=0.5: Chromatic suggestions get 50% weight
    """
    # Check if suggestion is chromatic
    is_chromatic = not suggestion.suggested_chord.is_diatonic  # To implement

    if not is_chromatic:
        return 1.0  # Diatonic always full weight
    else:
        # Chromatic suggestions scale with complexity
        return complexity


def _calculate_functional_score(
    suggestion: ChordSuggestion,
    progression: ChordProgression,
    key: Key,
    style: StyleProfile
) -> float:
    """
    Score based on functional harmony strength.

    Rewards strong progressions like S→D→T.
    """
    # Implementation: Check function of suggestion and following chord
    # Award points for:
    # - T→S: +0.3
    # - S→D: +0.5
    # - D→T: +1.0 (strongest)
    # - D→S: -0.5 if not allowed in style
    pass


def _calculate_melodic_score(
    suggestion: ChordSuggestion,
    melody_notes: List[NoteEvent],
    style: StyleProfile
) -> float:
    """
    Score based on melody-chord consonance.

    Returns value from 0.0 (harsh clashes) to 1.0 (perfect consonance).
    """
    if not melody_notes:
        return 1.0  # No melody = no clashes

    total_penalty = 0.0
    for note_event in melody_notes:
        penalty = calculate_melodic_clash_penalty(
            note_event.pitch,
            suggestion.suggested_chord,
            style.melodic_clash_penalty
        )
        total_penalty += penalty

    avg_penalty = total_penalty / len(melody_notes)

    # Convert penalty to score (invert)
    return max(0.0, 1.0 - avg_penalty)


def _calculate_variety_score(
    suggestion: ChordSuggestion,
    previous_suggestion: Optional[ChordSuggestion],
    style: StyleProfile
) -> float:
    """
    Score based on variety (penalize repetitive strategies).

    Returns 1.0 if different from previous, lower if same.
    """
    if previous_suggestion is None:
        return 1.0  # First suggestion, no penalty

    if suggestion.substitution_type == previous_suggestion.substitution_type:
        return 1.0 - style.repetition_penalty
    else:
        return 1.0
```

### 1.4. Strategy Base Confidence Values

**Decision:** Define base confidence for each strategy pattern.

```python
# Base confidence values to use in strategy implementations

# BorrowedChordStrategy
BORROWED_CHORD_CONFIDENCE = {
    "same_function": 0.75,      # Borrowing iv to replace IV (same function)
    "different_function": 0.50,  # Borrowing ♭VII (different function)
    "tonic_borrowing": 0.30,    # Edge case: borrowing i in major key
}

# NeapolitanStrategy
NEAPOLITAN_CONFIDENCE = {
    "before_dominant": 0.65,    # N6 → V (proper resolution)
    "before_tonic": 0.40,       # N6 → I (less common)
    "other": 0.25,              # Other contexts (rare)
    "major_key": 0.85,          # Multiplier if in major key (reduce)
    "melody_clash": 0.05,       # If ♭2 clashes with natural 2 in melody
}

# SubV7Strategy
SUBV7_CONFIDENCE = {
    "descending_chromatic_bass": 0.80,  # Creates smooth bassline
    "normal": 0.65,                      # Standard tritone sub
    "melody_compatible": 1.0,            # Multiplier if no melody clash
    "melody_clash_m9": 0.1,              # Severe penalty for ♭9 clash
}

# SuspendStrategy
SUSPEND_CONFIDENCE = {
    "with_resolution": 0.70,     # sus4 → major/minor (resolves)
    "without_resolution": 0.45,  # sus chord doesn't resolve
    "consecutive": 0.30,         # Multiple sus chords in a row
}

# ChromaticApproachStrategy
CHROMATIC_APPROACH_CONFIDENCE = {
    "dim7_passing": 0.75,        # Diminished 7th passing chord
    "dom7_passing": 0.70,        # Dominant 7th passing chord
    "semitone_approach": 0.80,   # Approaching from semitone
    "whole_tone": 0.60,          # Approaching from whole tone
}

# TSDMovementStrategy
TSD_CONFIDENCE = {
    "strong_replacement": 0.80,  # Replace iii with I (strong tonic)
    "weak_replacement": 0.60,    # Replace vi with I (both tonic function)
    "insertion": 0.70,           # Insert S between T and D
}
```

---

## Part 2: Implementation Phases

### Phase 1: Core Data Model (Week 1-2)

**Goal:** Implement foundational data structures and MIDI loading.

#### Tasks:

1. **Create new modules:**
   ```
   halmoni/core/pitch_class.py
   halmoni/core/score.py
   halmoni/core/analysis.py
   ```

2. **Implement `PitchClass` class:**
   - [ ] Basic class with validation
   - [ ] Enharmonic equivalence (`__eq__`, `__hash__`)
   - [ ] `to_canonical()` method
   - [ ] Unit tests (20+ test cases)

3. **Update `Note` class:**
   - [ ] Support string notation `Note("C4")`
   - [ ] Add `from_pitch_class()` factory method
   - [ ] Backward compatibility tests
   - [ ] Update docstrings

4. **Implement data classes:**
   - [ ] `Metadata`
   - [ ] `AnalysisMetadata`
   - [ ] `NoteEvent`
   - [ ] `Track`
   - [ ] `Tension`
   - [ ] `ChordAnalysis` (basic, enhance in Phase 2)

5. **Implement `Score` class:**
   - [ ] Basic `__init__`
   - [ ] `primary_melody` property
   - [ ] `all_melody_notes` property
   - [ ] `__repr__`

6. **Implement `Score.from_midi()`:**
   - [ ] Load MIDI with `MIDIAnalyzer`
   - [ ] Auto-detect melody vs. harmony tracks
   - [ ] Handle manual overrides (`melody_track_id`, etc.)
   - [ ] Populate `Metadata` from MIDI
   - [ ] Run key detection
   - [ ] Generate warnings for low confidence
   - [ ] Create `Track` objects with note separation
   - [ ] Unit tests with sample MIDI files

7. **Integration tests:**
   - [ ] Load simple single-track MIDI
   - [ ] Load complex multi-track MIDI
   - [ ] Manual key override
   - [ ] Edge cases (no melody, percussion only)

**Deliverable:** Users can create `Score` objects from MIDI and access progression, melody, and key.

---

### Phase 2: Enhanced Analysis (Week 3)

**Goal:** Upgrade analysis capabilities and suggestion metadata.

#### Tasks:

1. **Implement `HarmonicFunction` enum:**
   - [ ] All function types defined
   - [ ] String representations

2. **Enhance `Key.analyze_chord()`:**
   - [ ] Return `ChordAnalysis` object (not string)
   - [ ] Calculate roman numerals (including secondary dominants)
   - [ ] Determine harmonic function
   - [ ] Detect borrowed chords
   - [ ] Calculate functional strength
   - [ ] Extract tensions from chord
   - [ ] Handle edge cases (modal, chromatic)
   - [ ] Unit tests (50+ test cases covering all functions)

3. **Implement `SubstitutionType` enum:**
   - [ ] All types defined
   - [ ] Documentation for each

4. **Update `ChordSuggestion` dataclass:**
   - [ ] Add new fields
   - [ ] Validation in `__post_init__`
   - [ ] Update `__repr__`

5. **Refactor ALL suggestion strategies:**
   - [ ] Update `ChordSuggestionStrategy` base class
   - [ ] Refactor `BorrowedChordStrategy`
     - Add `substitution_type`
     - Add `target_chord`
     - Set `is_insertion`
     - Use base confidence values
   - [ ] Refactor `ChromaticApproachStrategy`
   - [ ] Refactor `NeapolitanStrategy`
   - [ ] Refactor `SubV7Strategy`
   - [ ] Refactor `SuspendStrategy`
   - [ ] Refactor `TSDMovementStrategy`

6. **Implement melody analysis:**
   - [ ] Create `halmoni/analysis/melody_analysis.py`
   - [ ] `INTERVAL_CLASH_PENALTIES` constant
   - [ ] `calculate_melodic_clash_penalty()` function
   - [ ] `analyze_melody_chord_compatibility()` function
   - [ ] Unit tests

7. **Update all tests:**
   - [ ] Fix tests broken by `ChordSuggestion` changes
   - [ ] Add tests for new `ChordAnalysis`
   - [ ] Add tests for melody clash detection

**Deliverable:** Rich analysis objects and updated suggestion strategies with full metadata.

---

### Phase 3: Reharmonizer Engine (Week 4-5)

**Goal:** Implement beam search reharmonization engine.

#### Tasks:

1. **Create new modules:**
   ```
   halmoni/reharmonization/__init__.py
   halmoni/reharmonization/style_profile.py
   halmoni/reharmonization/reharmonizer.py
   halmoni/reharmonization/scoring.py
   halmoni/reharmonization/beam_search.py
   ```

2. **Implement `StyleProfile`:**
   - [ ] Complete dataclass with all fields
   - [ ] Validation (weights in valid ranges)
   - [ ] `__repr__`

3. **Implement default profiles:**
   - [ ] Jazz profile
   - [ ] Classical profile
   - [ ] Pop profile
   - [ ] `get_style_profile()` function
   - [ ] Unit tests for each profile

4. **Implement scoring functions:**
   - [ ] `calculate_suggestion_score()` (main function)
   - [ ] `_get_strategy_weight()`
   - [ ] `_calculate_complexity_multiplier()`
   - [ ] `_calculate_functional_score()`
   - [ ] `_calculate_melodic_score()`
   - [ ] `_calculate_variety_score()`
   - [ ] Unit tests (30+ test cases)

5. **Implement beam search:**
   - [ ] `BeamSearchState` class (represents search state)
   - [ ] `beam_search()` function
   - [ ] Beam width management
   - [ ] Max depth limiting
   - [ ] Timeout handling
   - [ ] Random seed support
   - [ ] Unit tests

6. **Implement `Reharmonizer` class:**
   - [ ] `__init__` (stateless)
   - [ ] `reharmonize()` method
     - Parse style parameter
     - Validate complexity
     - Set up beam search
     - Apply top-scoring sequence
     - Create new Score
   - [ ] Error handling
   - [ ] Integration tests

7. **Test with examples:**
   - [ ] Reharmonize "Ode to Joy" in jazz style
   - [ ] Reharmonize simple progression in classical style
   - [ ] Verify complexity parameter works
   - [ ] Verify seed produces reproducible results

**Deliverable:** Working reharmonization engine with three style profiles.

---

### Phase 4: Documentation & Migration (Week 6)

**Goal:** Complete documentation, examples, and migration guide.

#### Tasks:

1. **Create examples:**
   - [ ] `examples/score_basic_usage.py` - Load MIDI, inspect Score
   - [ ] `examples/reharmonization_simple.py` - Basic reharmonization
   - [ ] `examples/reharmonization_comparison.py` - Compare styles
   - [ ] `examples/melody_analysis.py` - Analyze melody-chord fit
   - [ ] Update existing examples to use new API

2. **Write migration guide:**
   - [ ] Create `MIGRATION.md`
   - [ ] Document API changes
   - [ ] Provide before/after code examples
   - [ ] Explain deprecation timeline

3. **API documentation:**
   - [ ] Docstrings for all public classes
   - [ ] Docstrings for all public methods
   - [ ] Type annotations complete
   - [ ] Run mypy strict mode

4. **Update README:**
   - [ ] Quick start with new API
   - [ ] Reharmonization example
   - [ ] Link to examples

5. **Add deprecation warnings:**
   - [ ] Mark old API methods with `@deprecated`
   - [ ] Print warnings when old API used
   - [ ] Point to migration guide

**Deliverable:** Complete documentation and smooth migration path.

---

### Phase 5: Strategy Improvements (Week 7-8)

**Goal:** Enhance individual strategies based on proposal feedback.

#### Tasks:

1. **Enhance `TSDMovementStrategy`:**
   - [ ] Use `allow_dominant_to_subdominant` from style
   - [ ] Improve chromatic chord function detection
   - [ ] Add tests for style-dependent behavior

2. **Enhance `NeapolitanStrategy`:**
   - [ ] Implement melody clash detection
   - [ ] Lower base confidence
   - [ ] Add `melodic_implications` field
   - [ ] Add tests with melody

3. **Enhance `BorrowedChordStrategy`:**
   - [ ] Function-driven logic (higher confidence for same function)
   - [ ] Expand modal palette (Dorian, Lydian borrowing)
   - [ ] Add tests for new modes

4. **Enhance `SubV7Strategy`:**
   - [ ] Melody-awareness (check for clashes)
   - [ ] Only activate in jazz context (style check)
   - [ ] Add tests with melody

5. **Enhance `SuspendStrategy`:**
   - [ ] Prioritize resolution (insertion + resolution)
   - [ ] Implement `allow_consecutive_suspensions` check
   - [ ] Add tests for resolution patterns

6. **Enhance `ChromaticApproachStrategy`:**
   - [ ] Sequential passing (two-chord sequences)
   - [ ] Add tests for longer passing sequences

7. **Integration tests:**
   - [ ] Full reharmonization with all enhanced strategies
   - [ ] Verify improvements work together
   - [ ] Performance benchmarks

**Deliverable:** Production-ready strategy implementations with all enhancements.

---

## Part 3: Testing Strategy

### Unit Test Coverage Goals

- **Core classes:** 95%+ coverage
  - `PitchClass`, `Note`, `Score`, `Track`, `ChordAnalysis`
- **Analysis:** 90%+ coverage
  - `Key.analyze_chord()`, melody clash detection
- **Strategies:** 85%+ coverage
  - Each strategy with comprehensive test cases
- **Reharmonizer:** 80%+ coverage
  - Beam search, scoring, integration

### Integration Test Scenarios

1. **Simple MIDI files:**
   - Single track, clear melody
   - Verify correct progression detection

2. **Complex MIDI files:**
   - Multi-track with percussion
   - Verify track role detection

3. **Reharmonization quality:**
   - Known progressions (ii-V-I, I-IV-V-I)
   - Verify style-appropriate suggestions

4. **Edge cases:**
   - Empty tracks
   - Very short progressions (< 4 chords)
   - Very long progressions (> 64 chords)
   - Atonal/chromatic input

### Performance Tests

- `Score.from_midi()` should complete in < 2 seconds for typical song
- `reharmonize()` should complete in < 10 seconds for 32-bar progression
- Memory usage should be reasonable (< 100MB for typical usage)

---

## Part 4: Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Beam search too slow | Medium | High | Add timeout, optimize scoring, reduce beam width |
| MIDI parsing errors | High | Medium | Extensive error handling, clear warnings |
| Melody detection inaccurate | Medium | Medium | Manual override parameters, validate on examples |
| Breaking changes affect users | Low | High | Clear deprecation warnings, migration guide |
| Music theory edge cases | High | Low | Comprehensive test suite, graceful degradation |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Phase overruns | Medium | Medium | Prioritize core features, defer enhancements |
| Scope creep | Medium | High | Strict adherence to this plan, defer to v1.1 |
| Integration issues | Low | High | Continuous integration, test early and often |

---

## Part 5: Success Criteria

### Functional Requirements

- ✅ User can load MIDI and get `Score` with < 5 lines of code
- ✅ User can reharmonize with single method call
- ✅ Reharmonization produces musically valid results
- ✅ Three style profiles work distinctly
- ✅ Complexity parameter has clear effect
- ✅ All existing tests pass with deprecation warnings

### Quality Requirements

- ✅ Type checking passes (mypy --strict)
- ✅ Test coverage > 85% overall
- ✅ All public APIs documented
- ✅ Examples work without errors
- ✅ No regressions in existing functionality

### User Experience Requirements

- ✅ Clear error messages
- ✅ Helpful warnings for low-confidence analysis
- ✅ Migration guide is comprehensive
- ✅ Examples demonstrate common use cases

---

## Part 6: Post-Launch (v1.1+)

### Deferred Features

Features explicitly out of scope for v1.0, planned for future:

1. **Custom style profiles** (v1.1)
   - User-defined `StyleProfile` objects
   - Save/load profiles from files

2. **Additional styles** (v1.1)
   - Rock profile
   - Folk profile
   - Blues profile

3. **Multiple outputs** (v1.2)
   - `reharmonize_multiple()` returning top N results
   - Interactive refinement

4. **Advanced strategies** (v1.2)
   - Secondary dominant suggestions
   - Diatonic substitutions
   - Added tension suggestions

5. **Voicing awareness** (v2.0)
   - Specific chord voicings for better voice leading
   - Instrument-aware voicings

---

## Appendix A: File Structure

```
halmoni/
├── core/
│   ├── __init__.py
│   ├── note.py (updated)
│   ├── pitch_class.py (new)
│   ├── chord.py
│   ├── scale.py
│   ├── key.py (updated)
│   ├── progression.py
│   ├── score.py (new)
│   └── analysis.py (new)
├── analysis/
│   ├── __init__.py
│   ├── midi_analyzer.py
│   ├── chord_detector.py
│   ├── key_detector.py
│   └── melody_analysis.py (new)
├── suggestions/
│   ├── __init__.py
│   ├── base_strategy.py (updated)
│   ├── types.py (new)
│   ├── borrowed_chord.py (updated)
│   ├── chromatic_approach.py (updated)
│   ├── neapolitan.py (updated)
│   ├── sub_v7.py (updated)
│   ├── suspend.py (updated)
│   └── tsd_movement.py (updated)
├── reharmonization/ (new)
│   ├── __init__.py
│   ├── reharmonizer.py
│   ├── style_profile.py
│   ├── scoring.py
│   └── beam_search.py
└── instruments/
    ├── __init__.py
    ├── guitar.py
    ├── piano.py
    └── bass.py

tests/
├── core/
│   ├── test_pitch_class.py (new)
│   ├── test_note.py (updated)
│   ├── test_score.py (new)
│   └── test_analysis.py (new)
├── analysis/
│   └── test_melody_analysis.py (new)
├── suggestions/
│   └── test_*.py (all updated)
└── reharmonization/ (new)
    ├── test_style_profile.py
    ├── test_scoring.py
    ├── test_beam_search.py
    └── test_reharmonizer.py

examples/
├── score_basic_usage.py (new)
├── reharmonization_simple.py (new)
├── reharmonization_comparison.py (new)
└── melody_analysis.py (new)

MIGRATION.md (new)
```

---

## Appendix B: Example Usage (Target API)

```python
from halmoni import Score, Reharmonizer

# Load a MIDI file (automatic analysis)
score = Score.from_midi(
    "examples/ode-to-joy.mid",
    manual_key="G Major"  # Optional override
)

print(f"Key: {score.key}")
print(f"Progression: {score.progression}")
print(f"Primary melody: {len(score.primary_melody)} notes")

# Reharmonize in jazz style
reharmonizer = Reharmonizer()
jazzy_score = reharmonizer.reharmonize(
    score,
    style="jazz",
    complexity=0.7
)

print(f"\nOriginal: {score.progression}")
print(f"Jazzified: {jazzy_score.progression}")

# Compare different styles
classical_score = reharmonizer.reharmonize(score, style="classical", complexity=0.4)
pop_score = reharmonizer.reharmonize(score, style="pop", complexity=0.6)

print(f"\nClassical: {classical_score.progression}")
print(f"Pop: {pop_score.progression}")
```

---

## Sign-off

This implementation plan is ready for review and approval. Once approved, development can begin immediately with Phase 1.

**Estimated Total Effort:** 6-8 weeks (1 developer)
**Target Release:** v1.0.0
**Breaking Changes:** Yes (with deprecation period)
