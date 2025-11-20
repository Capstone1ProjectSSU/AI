# Phase 4: Advanced Reharmonization Features

**Version:** v1.1.0 - v1.2.0
**Prerequisites:** Core implementation (Phases 1-3) complete
**Estimated Timeline:** 6-8 weeks
**Status:** Design Specification

---

## Overview

This document specifies advanced reharmonization features that build upon the core engine:

1. **Interactive/Incremental Reharmonization** - User-driven iterative refinement
2. **Voicing Awareness** - Intelligent chord voicing for optimal voice leading

These features represent the next evolution of the `halmoni` library, enabling professional-level composition workflows.

---

## Part 1: Interactive/Incremental Reharmonization

### 1.1 Motivation & Use Cases

**Problem:** The core `reharmonize()` method is "all-or-nothing" - it processes the entire score and returns a result. Users cannot:
- Guide the process toward specific harmonic goals
- Accept/reject individual suggestions
- Iteratively refine specific sections
- Experiment with alternatives at decision points

**Target Workflow:**

```python
# Composer's workflow
score = Score.from_midi("my-song.mid")

# Start interactive session
session = InteractiveReharmonizer(score, style="jazz")

# Preview suggestions for first 4 bars
suggestions = session.get_suggestions_for_range(0, 4)
session.preview_suggestion(suggestions[0])  # Hear/see the change

# Accept suggestion
session.accept_suggestion(suggestions[0])

# Reject and try alternative
session.reject_suggestion(suggestions[1])
alternatives = session.get_alternatives(position=2, n=5)
session.accept_suggestion(alternatives[3])

# Lock a section (preserve it from further changes)
session.lock_range(0, 4)

# Continue with next section
suggestions = session.get_suggestions_for_range(4, 8)
# ... iterate

# Finalize
final_score = session.finalize()
```

### 1.2 Architecture Design

#### Core Components

```python
# halmoni/reharmonization/interactive.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from halmoni.core import Score, Chord, ChordProgression
from halmoni.suggestions import ChordSuggestion
from halmoni.reharmonization import StyleProfile

@dataclass
class ReharmonizationState:
    """
    Represents the current state of an interactive reharmonization session.

    This is an immutable snapshot that can be saved/restored.
    """
    # Current progression (reflects all accepted changes)
    current_progression: ChordProgression

    # History of accepted suggestions (for undo)
    accepted_suggestions: List[ChordSuggestion] = field(default_factory=list)

    # History of rejected suggestions (avoid re-suggesting)
    rejected_suggestions: Set[str] = field(default_factory=set)  # Hash of suggestions

    # Locked positions (cannot be modified)
    locked_positions: Set[int] = field(default_factory=set)

    # Section markers (user-defined structural boundaries)
    sections: Dict[str, Tuple[int, int]] = field(default_factory=dict)  # name -> (start, end)

    # Metadata
    change_count: int = 0
    last_modified_position: Optional[int] = None

    def to_dict(self) -> dict:
        """Serialize state for saving."""
        pass

    @classmethod
    def from_dict(cls, data: dict) -> 'ReharmonizationState':
        """Restore state from saved data."""
        pass


class InteractiveReharmonizer:
    """
    Interactive reharmonization engine with incremental refinement.

    Allows users to:
    - Get suggestions for specific ranges
    - Accept/reject individual suggestions
    - Undo/redo changes
    - Lock sections from modification
    - Save/load session state
    """

    def __init__(
        self,
        score: Score,
        style: Union[str, StyleProfile],
        complexity: float = 0.7,
        seed: Optional[int] = None
    ):
        """
        Create an interactive reharmonization session.

        Args:
            score: Original score to reharmonize
            style: Reharmonization style profile
            complexity: Base complexity level (can be overridden per-range)
            seed: Random seed for reproducibility
        """
        self._original_score = score
        self._style = self._resolve_style(style)
        self._complexity = complexity
        self._seed = seed

        # Initialize state with original progression
        self._state = ReharmonizationState(
            current_progression=score.progression.copy()
        )

        # Undo/redo stacks
        self._undo_stack: List[ReharmonizationState] = []
        self._redo_stack: List[ReharmonizationState] = []

        # Cache for suggestions (avoid recomputation)
        self._suggestion_cache: Dict[Tuple[int, int], List[ChordSuggestion]] = {}

    @property
    def current_score(self) -> Score:
        """Get current score with all accepted changes."""
        return Score(
            progression=self._state.current_progression,
            tracks=self._original_score.tracks,  # Tracks unchanged
            key=self._original_score.key,
            metadata=self._original_score.metadata,
            analysis_metadata=self._original_score.analysis_metadata,
            warnings=self._original_score.warnings
        )

    def get_suggestions_for_range(
        self,
        start: int,
        end: int,
        n_suggestions: int = 10,
        complexity_override: Optional[float] = None,
        filter_strategies: Optional[List[str]] = None
    ) -> List[ChordSuggestion]:
        """
        Get top suggestions for a specific range of the progression.

        Args:
            start: Start position (inclusive)
            end: End position (exclusive)
            n_suggestions: Maximum number of suggestions to return
            complexity_override: Override session complexity for this range
            filter_strategies: Only use specific strategies

        Returns:
            List of suggestions sorted by score
        """
        # Check cache
        cache_key = (start, end)
        if cache_key in self._suggestion_cache:
            return self._suggestion_cache[cache_key][:n_suggestions]

        # Get all suggestions in range, respecting locked positions
        suggestions = []
        for pos in range(start, end):
            if pos in self._state.locked_positions:
                continue

            pos_suggestions = self._get_suggestions_at_position(
                pos,
                complexity_override or self._complexity,
                filter_strategies
            )
            suggestions.extend(pos_suggestions)

        # Score and sort
        scored = self._score_suggestions(suggestions)

        # Filter out rejected suggestions
        filtered = [
            s for s in scored
            if self._suggestion_hash(s) not in self._state.rejected_suggestions
        ]

        # Cache and return
        self._suggestion_cache[cache_key] = filtered
        return filtered[:n_suggestions]

    def get_alternatives(
        self,
        position: int,
        n: int = 5,
        different_from: Optional[ChordSuggestion] = None
    ) -> List[ChordSuggestion]:
        """
        Get alternative suggestions for a specific position.

        Useful when user rejects a suggestion and wants to see other options.

        Args:
            position: Position in progression
            n: Number of alternatives
            different_from: Exclude suggestions similar to this one

        Returns:
            List of alternative suggestions
        """
        all_suggestions = self._get_suggestions_at_position(position, self._complexity)

        # Filter by difference
        if different_from:
            all_suggestions = [
                s for s in all_suggestions
                if s.substitution_type != different_from.substitution_type
                or s.suggested_chord != different_from.suggested_chord
            ]

        return self._score_suggestions(all_suggestions)[:n]

    def accept_suggestion(self, suggestion: ChordSuggestion) -> None:
        """
        Accept a suggestion and apply it to the current progression.

        Args:
            suggestion: Suggestion to accept
        """
        # Save current state for undo
        self._undo_stack.append(self._state)
        self._redo_stack.clear()  # Accepting breaks redo chain

        # Apply suggestion
        new_progression = self._apply_suggestion(
            self._state.current_progression,
            suggestion
        )

        # Update state
        self._state = ReharmonizationState(
            current_progression=new_progression,
            accepted_suggestions=self._state.accepted_suggestions + [suggestion],
            rejected_suggestions=self._state.rejected_suggestions.copy(),
            locked_positions=self._state.locked_positions.copy(),
            sections=self._state.sections.copy(),
            change_count=self._state.change_count + 1,
            last_modified_position=suggestion.position
        )

        # Invalidate cache
        self._invalidate_cache_for_position(suggestion.position)

    def reject_suggestion(self, suggestion: ChordSuggestion) -> None:
        """
        Reject a suggestion (won't be suggested again this session).

        Args:
            suggestion: Suggestion to reject
        """
        suggestion_hash = self._suggestion_hash(suggestion)
        self._state.rejected_suggestions.add(suggestion_hash)

        # Invalidate cache
        self._invalidate_cache_for_position(suggestion.position)

    def undo(self) -> bool:
        """
        Undo last accepted suggestion.

        Returns:
            True if undo succeeded, False if nothing to undo
        """
        if not self._undo_stack:
            return False

        # Move current state to redo stack
        self._redo_stack.append(self._state)

        # Restore previous state
        self._state = self._undo_stack.pop()

        # Invalidate cache
        self._suggestion_cache.clear()

        return True

    def redo(self) -> bool:
        """
        Redo previously undone suggestion.

        Returns:
            True if redo succeeded, False if nothing to redo
        """
        if not self._redo_stack:
            return False

        # Move current state to undo stack
        self._undo_stack.append(self._state)

        # Restore next state
        self._state = self._redo_stack.pop()

        # Invalidate cache
        self._suggestion_cache.clear()

        return True

    def lock_position(self, position: int) -> None:
        """Lock a single position from modification."""
        self._state.locked_positions.add(position)
        self._invalidate_cache_for_position(position)

    def unlock_position(self, position: int) -> None:
        """Unlock a position."""
        self._state.locked_positions.discard(position)
        self._invalidate_cache_for_position(position)

    def lock_range(self, start: int, end: int) -> None:
        """Lock a range of positions."""
        for pos in range(start, end):
            self.lock_position(pos)

    def unlock_range(self, start: int, end: int) -> None:
        """Unlock a range of positions."""
        for pos in range(start, end):
            self.unlock_position(pos)

    def define_section(self, name: str, start: int, end: int) -> None:
        """
        Define a named section (e.g., "verse", "chorus").

        Useful for organizing and targeting specific parts.
        """
        self._state.sections[name] = (start, end)

    def get_section(self, name: str) -> Tuple[int, int]:
        """Get section boundaries by name."""
        if name not in self._state.sections:
            raise ValueError(f"Unknown section: {name}")
        return self._state.sections[name]

    def reharmonize_section(
        self,
        section_name: str,
        auto_accept_top_n: int = 0
    ) -> List[ChordSuggestion]:
        """
        Get suggestions for an entire named section.

        Args:
            section_name: Name of section to reharmonize
            auto_accept_top_n: If > 0, automatically accept top N suggestions

        Returns:
            List of suggestions (or accepted suggestions if auto_accept > 0)
        """
        start, end = self.get_section(section_name)
        suggestions = self.get_suggestions_for_range(start, end)

        if auto_accept_top_n > 0:
            accepted = []
            for suggestion in suggestions[:auto_accept_top_n]:
                self.accept_suggestion(suggestion)
                accepted.append(suggestion)
            return accepted

        return suggestions

    def preview_suggestion(self, suggestion: ChordSuggestion) -> Score:
        """
        Preview what the score would look like with this suggestion applied.

        Does NOT modify session state.

        Args:
            suggestion: Suggestion to preview

        Returns:
            Score with suggestion applied (temporary)
        """
        preview_progression = self._apply_suggestion(
            self._state.current_progression,
            suggestion
        )

        return Score(
            progression=preview_progression,
            tracks=self._original_score.tracks,
            key=self._original_score.key,
            metadata=self._original_score.metadata,
            analysis_metadata=self._original_score.analysis_metadata,
            warnings=self._original_score.warnings + ["PREVIEW ONLY"]
        )

    def compare_with_original(self) -> List[Tuple[int, Chord, Chord, str]]:
        """
        Compare current progression with original.

        Returns:
            List of (position, original_chord, new_chord, reason) tuples
        """
        changes = []
        original_chords = self._original_score.progression.chords
        current_chords = self._state.current_progression.chords

        # Handle length differences (insertions)
        max_len = max(len(original_chords), len(current_chords))

        for i in range(max_len):
            orig = original_chords[i] if i < len(original_chords) else None
            curr = current_chords[i] if i < len(current_chords) else None

            if orig != curr:
                # Find which suggestion caused this change
                reason = self._find_change_reason(i)
                changes.append((i, orig, curr, reason))

        return changes

    def save_state(self, filepath: str) -> None:
        """
        Save current session state to file.

        Args:
            filepath: Path to save state JSON
        """
        import json
        state_dict = {
            "state": self._state.to_dict(),
            "style": self._style_to_dict(),
            "complexity": self._complexity,
            "original_score": self._score_to_dict(self._original_score)
        }

        with open(filepath, 'w') as f:
            json.dump(state_dict, f, indent=2)

    @classmethod
    def load_state(cls, filepath: str) -> 'InteractiveReharmonizer':
        """
        Load a saved session state.

        Args:
            filepath: Path to saved state JSON

        Returns:
            InteractiveReharmonizer with restored state
        """
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Reconstruct session
        original_score = cls._score_from_dict(data["original_score"])
        session = cls(
            original_score,
            style=cls._style_from_dict(data["style"]),
            complexity=data["complexity"]
        )
        session._state = ReharmonizationState.from_dict(data["state"])

        return session

    def finalize(self) -> Score:
        """
        Finalize the session and return the completed score.

        Returns:
            Final reharmonized score
        """
        return self.current_score

    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the reharmonization session.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_changes": self._state.change_count,
            "suggestions_accepted": len(self._state.accepted_suggestions),
            "suggestions_rejected": len(self._state.rejected_suggestions),
            "locked_positions": len(self._state.locked_positions),
            "sections_defined": len(self._state.sections),
            "can_undo": len(self._undo_stack) > 0,
            "can_redo": len(self._redo_stack) > 0,
            "change_percentage": (
                self._state.change_count / len(self._original_score.progression.chords)
            ) * 100 if len(self._original_score.progression.chords) > 0 else 0
        }

    # Private helper methods

    def _resolve_style(self, style: Union[str, StyleProfile]) -> StyleProfile:
        """Convert style string to StyleProfile."""
        pass

    def _get_suggestions_at_position(
        self,
        position: int,
        complexity: float,
        filter_strategies: Optional[List[str]] = None
    ) -> List[ChordSuggestion]:
        """Get all suggestions for a single position."""
        pass

    def _score_suggestions(
        self,
        suggestions: List[ChordSuggestion]
    ) -> List[ChordSuggestion]:
        """Score and sort suggestions."""
        pass

    def _apply_suggestion(
        self,
        progression: ChordProgression,
        suggestion: ChordSuggestion
    ) -> ChordProgression:
        """Apply a suggestion to a progression (immutably)."""
        pass

    def _suggestion_hash(self, suggestion: ChordSuggestion) -> str:
        """Generate unique hash for a suggestion."""
        pass

    def _invalidate_cache_for_position(self, position: int) -> None:
        """Invalidate cached suggestions affected by position change."""
        pass

    def _find_change_reason(self, position: int) -> str:
        """Find which suggestion caused a change at position."""
        pass

    def _style_to_dict(self) -> dict:
        """Serialize StyleProfile."""
        pass

    def _style_from_dict(self, data: dict) -> StyleProfile:
        """Deserialize StyleProfile."""
        pass

    def _score_to_dict(self, score: Score) -> dict:
        """Serialize Score."""
        pass

    def _score_from_dict(self, data: dict) -> Score:
        """Deserialize Score."""
        pass
```

### 1.3 Usage Examples

#### Example 1: Iterative Refinement

```python
from halmoni import Score
from halmoni.reharmonization import InteractiveReharmonizer

# Load score
score = Score.from_midi("my-song.mid")

# Start interactive session
session = InteractiveReharmonizer(score, style="jazz", complexity=0.7)

# Define song structure
session.define_section("intro", 0, 4)
session.define_section("verse", 4, 12)
session.define_section("chorus", 12, 20)

# Reharmonize intro conservatively
session.complexity = 0.4  # Lower complexity for intro
intro_suggestions = session.reharmonize_section("intro")

# Accept top 2 suggestions
session.accept_suggestion(intro_suggestions[0])
session.accept_suggestion(intro_suggestions[1])

# Lock intro (preserve it)
session.lock_range(0, 4)

# Reharmonize verse with higher complexity
session.complexity = 0.8
verse_suggestions = session.reharmonize_section("verse")

# Preview before accepting
preview = session.preview_suggestion(verse_suggestions[0])
print(f"Preview: {preview.progression}")

# Accept or reject
session.accept_suggestion(verse_suggestions[0])
session.reject_suggestion(verse_suggestions[1])  # Not quite right

# Get alternatives
alternatives = session.get_alternatives(position=5, n=3)
session.accept_suggestion(alternatives[1])

# Oops, undo that
session.undo()

# Try different alternative
session.accept_suggestion(alternatives[2])

# Compare with original
changes = session.compare_with_original()
for pos, orig, new, reason in changes:
    print(f"Position {pos}: {orig} → {new} ({reason})")

# Save session for later
session.save_state("reharmonization_session.json")

# Finalize
final_score = session.finalize()
```

#### Example 2: Collaborative Workflow

```python
# Composer starts session
session = InteractiveReharmonizer(score, style="jazz")
session.define_section("verse", 0, 8)
session.reharmonize_section("verse", auto_accept_top_n=3)
session.save_state("verse_draft.json")

# ... later, or different user ...

# Load and continue
session = InteractiveReharmonizer.load_state("verse_draft.json")

# Review what was done
stats = session.get_statistics()
print(f"Changes made: {stats['total_changes']}")
print(f"Can undo: {stats['can_undo']}")

# Continue with chorus
session.define_section("chorus", 8, 16)
chorus_suggestions = session.reharmonize_section("chorus")

# Accept selectively
for suggestion in chorus_suggestions[:5]:
    preview = session.preview_suggestion(suggestion)
    # (User listens/reviews preview)
    if user_approves(preview):  # Hypothetical approval function
        session.accept_suggestion(suggestion)
    else:
        session.reject_suggestion(suggestion)

# Finalize
final_score = session.finalize()
```

### 1.4 Implementation Tasks

**Week 1: Core Infrastructure**
- [ ] Implement `ReharmonizationState` dataclass
- [ ] Implement state serialization/deserialization
- [ ] Implement `InteractiveReharmonizer` skeleton
- [ ] Implement undo/redo stacks
- [ ] Unit tests for state management

**Week 2: Suggestion Management**
- [ ] Implement `get_suggestions_for_range()`
- [ ] Implement suggestion caching
- [ ] Implement `get_alternatives()`
- [ ] Implement `accept_suggestion()`
- [ ] Implement `reject_suggestion()`
- [ ] Unit tests for suggestion workflow

**Week 3: Section Management & Features**
- [ ] Implement lock/unlock functionality
- [ ] Implement section definition
- [ ] Implement `reharmonize_section()`
- [ ] Implement `preview_suggestion()`
- [ ] Implement `compare_with_original()`
- [ ] Unit tests

**Week 4: Persistence & Polish**
- [ ] Implement save/load state
- [ ] Implement statistics
- [ ] Error handling and edge cases
- [ ] Integration tests
- [ ] Documentation and examples

---

## Part 2: Voicing Awareness

### 2.1 Motivation & Use Cases

**Problem:** Current suggestions consider only chord symbols, not specific voicings. This limits:
- Voice leading quality (smooth connection between chord tones)
- Instrument-specific playability
- Stylistic authenticity (jazz voicings vs. classical voicings)
- Register-appropriate suggestions (bass vs. piano vs. guitar)

**Musical Context:**

The same chord (e.g., Cmaj7) has many voicings:
- **Close position:** C-E-G-B (tight, all within octave)
- **Open position:** C-G-E-B (spread out)
- **Drop-2:** G-C-E-B (second voice dropped octave)
- **Rootless:** E-G-B (no root, common in jazz piano)
- **Quartal:** C-F-B-E (stacked fourths)

Good voice leading moves smoothly between these voicings.

### 2.2 Architecture Design

#### Core Data Structures

```python
# halmoni/core/voicing.py

from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum

class VoicingType(Enum):
    """Standard voicing types."""
    CLOSE_POSITION = "close_position"
    OPEN_POSITION = "open_position"
    DROP_2 = "drop_2"
    DROP_3 = "drop_3"
    DROP_2_4 = "drop_2_4"
    ROOTLESS = "rootless"
    SHELL = "shell"  # Root, 3rd, 7th only
    QUARTAL = "quartal"  # Stacked 4ths
    SPREAD = "spread"  # Wide spacing
    CLUSTER = "cluster"  # Tight dissonant voicing

@dataclass
class VoicedNote:
    """A single note within a voicing."""
    pitch: Note
    voice_number: int  # 0 = bass, 1 = tenor, 2 = alto, 3 = soprano
    chord_degree: str  # "root", "3rd", "5th", "7th", "9th", etc.

    def __lt__(self, other: 'VoicedNote') -> bool:
        """Sort by pitch (low to high)."""
        return self.pitch.midi_number < other.pitch.midi_number

@dataclass
class ChordVoicing:
    """
    A specific voicing of a chord.

    Represents the exact notes and their arrangement,
    not just the chord symbol.
    """
    # Underlying chord
    chord: Chord

    # Specific notes in this voicing (sorted low to high)
    notes: List[VoicedNote]

    # Voicing type/category
    voicing_type: VoicingType

    # Register (average MIDI note number)
    register: float

    # Span in semitones (lowest to highest note)
    span: int

    # Whether root is in bass
    root_in_bass: bool

    # Inversion (0 = root position, 1 = first inversion, etc.)
    inversion: int

    def get_bass_note(self) -> VoicedNote:
        """Get lowest note (bass)."""
        return min(self.notes)

    def get_soprano_note(self) -> VoicedNote:
        """Get highest note (soprano)."""
        return max(self.notes)

    def get_voice_intervals(self) -> List[int]:
        """Get intervals between adjacent voices (in semitones)."""
        sorted_notes = sorted(self.notes)
        intervals = []
        for i in range(len(sorted_notes) - 1):
            interval = (
                sorted_notes[i + 1].pitch.midi_number -
                sorted_notes[i].pitch.midi_number
            )
            intervals.append(interval)
        return intervals

    def transpose(self, semitones: int) -> 'ChordVoicing':
        """Transpose entire voicing up/down."""
        pass

    def get_common_tones(self, other: 'ChordVoicing') -> List[Note]:
        """Find notes shared with another voicing."""
        pass

    def __repr__(self) -> str:
        notes_str = ", ".join(str(n.pitch) for n in sorted(self.notes))
        return f"ChordVoicing({self.chord.symbol}, [{notes_str}], {self.voicing_type.value})"


class VoicingGenerator:
    """
    Generates appropriate voicings for chords.

    Can generate voicings based on:
    - Style (jazz, classical, pop)
    - Instrument (piano, guitar, SATB choir)
    - Register constraints
    - Voice leading from previous voicing
    """

    def __init__(
        self,
        style: str = "jazz",
        instrument: str = "piano",
        min_note: Note = Note("E", 2),
        max_note: Note = Note("C", 6)
    ):
        self.style = style
        self.instrument = instrument
        self.min_note = min_note
        self.max_note = max_note

    def generate_voicings(
        self,
        chord: Chord,
        n_voicings: int = 10,
        previous_voicing: Optional[ChordVoicing] = None
    ) -> List[ChordVoicing]:
        """
        Generate possible voicings for a chord.

        Args:
            chord: Chord to voice
            n_voicings: Number of voicings to generate
            previous_voicing: Previous voicing (for voice leading)

        Returns:
            List of voicings, sorted by appropriateness
        """
        voicings = []

        # Generate different voicing types
        if self.style == "jazz":
            voicings.extend(self._generate_jazz_voicings(chord))
        elif self.style == "classical":
            voicings.extend(self._generate_classical_voicings(chord))
        elif self.style == "pop":
            voicings.extend(self._generate_pop_voicings(chord))

        # Filter by instrument constraints
        voicings = self._filter_by_instrument(voicings)

        # Filter by register
        voicings = [v for v in voicings if self._is_in_register(v)]

        # Score by voice leading if previous voicing provided
        if previous_voicing:
            voicings = self._sort_by_voice_leading(voicings, previous_voicing)
        else:
            voicings = self._sort_by_default_quality(voicings)

        return voicings[:n_voicings]

    def _generate_jazz_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate jazz-style voicings (drop-2, rootless, etc.)."""
        voicings = []

        # Drop-2 voicings (common in jazz)
        voicings.extend(self._generate_drop_2_voicings(chord))

        # Rootless voicings (3rd and 7th guide tones)
        if chord.quality in ["major7", "minor7", "dominant7"]:
            voicings.extend(self._generate_rootless_voicings(chord))

        # Quartal voicings (modern jazz)
        if chord.quality in ["major7", "minor7"]:
            voicings.extend(self._generate_quartal_voicings(chord))

        return voicings

    def _generate_classical_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate classical SATB-style voicings."""
        voicings = []

        # Close position (all voices within octave)
        voicings.extend(self._generate_close_position_voicings(chord))

        # Open position (spacing between voices)
        voicings.extend(self._generate_open_position_voicings(chord))

        return voicings

    def _generate_pop_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate pop/rock-style voicings (guitar-friendly)."""
        voicings = []

        # Root position with doubled root
        voicings.extend(self._generate_pop_root_position(chord))

        # Spread voicings (wide spacing)
        voicings.extend(self._generate_spread_voicings(chord))

        return voicings

    def _generate_drop_2_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """
        Generate drop-2 voicings.

        Drop-2: Take close position, drop 2nd-highest note down an octave.
        """
        # Implementation
        pass

    def _generate_rootless_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """
        Generate rootless voicings (3rd, 7th, extensions).

        Common in jazz piano comping.
        """
        # Implementation
        pass

    def _generate_quartal_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate voicings built from stacked perfect 4ths."""
        # Implementation
        pass

    def _generate_close_position_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate close position (all notes within octave)."""
        # Implementation
        pass

    def _generate_open_position_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate open position (spacing between voices)."""
        # Implementation
        pass

    def _generate_pop_root_position(self, chord: Chord) -> List[ChordVoicing]:
        """Generate pop-style root position voicings."""
        # Implementation
        pass

    def _generate_spread_voicings(self, chord: Chord) -> List[ChordVoicing]:
        """Generate wide-spaced voicings."""
        # Implementation
        pass

    def _filter_by_instrument(self, voicings: List[ChordVoicing]) -> List[ChordVoicing]:
        """Filter voicings by instrument playability."""
        if self.instrument == "piano":
            # Piano can play anything within 10th span per hand
            return [v for v in voicings if self._is_piano_playable(v)]
        elif self.instrument == "guitar":
            # Guitar has specific fret span limitations
            return [v for v in voicings if self._is_guitar_playable(v)]
        else:
            return voicings

    def _is_in_register(self, voicing: ChordVoicing) -> bool:
        """Check if voicing is within min/max note range."""
        bass = voicing.get_bass_note().pitch
        soprano = voicing.get_soprano_note().pitch

        return (
            bass.midi_number >= self.min_note.midi_number and
            soprano.midi_number <= self.max_note.midi_number
        )

    def _sort_by_voice_leading(
        self,
        voicings: List[ChordVoicing],
        previous_voicing: ChordVoicing
    ) -> List[ChordVoicing]:
        """Sort voicings by voice leading quality from previous."""
        def voice_leading_quality(v: ChordVoicing) -> float:
            return calculate_voice_leading_quality(previous_voicing, v)

        return sorted(voicings, key=voice_leading_quality, reverse=True)

    def _sort_by_default_quality(self, voicings: List[ChordVoicing]) -> List[ChordVoicing]:
        """Sort voicings by general quality (no previous voicing)."""
        # Prefer voicings with good spacing, root in bass, etc.
        pass

    def _is_piano_playable(self, voicing: ChordVoicing) -> bool:
        """Check if voicing is playable on piano (two hands)."""
        # Implementation: check hand span, etc.
        pass

    def _is_guitar_playable(self, voicing: ChordVoicing) -> bool:
        """Check if voicing is playable on guitar."""
        # Implementation: check fret span, string layout
        pass


def calculate_voice_leading_quality(
    voicing1: ChordVoicing,
    voicing2: ChordVoicing
) -> float:
    """
    Calculate voice leading quality between two voicings.

    High quality voice leading:
    - Minimizes total motion (sum of intervals moved)
    - Prefers stepwise motion in individual voices
    - Prefers contrary motion (voices moving in opposite directions)
    - Avoids parallel perfect 5ths and octaves (classical rule)

    Args:
        voicing1: First voicing
        voicing2: Second voicing

    Returns:
        Quality score (0.0 = poor, 1.0 = excellent)
    """
    # Get optimal voice mapping (Hungarian algorithm or greedy)
    voice_mapping = _find_optimal_voice_mapping(voicing1, voicing2)

    total_motion = 0
    stepwise_count = 0
    oblique_count = 0  # One voice stays, another moves
    contrary_count = 0  # Voices move in opposite directions
    parallel_5ths = 0
    parallel_octaves = 0

    for v1_note, v2_note in voice_mapping:
        interval = abs(v2_note.pitch.midi_number - v1_note.pitch.midi_number)

        # Track total motion
        total_motion += interval

        # Track stepwise motion (0-2 semitones)
        if interval <= 2:
            stepwise_count += 1

        # Check for oblique motion (interval = 0)
        if interval == 0:
            oblique_count += 1

    # Check for contrary motion
    # (need to track direction of each voice)

    # Check for parallel 5ths and octaves (classical prohibition)
    # ... implementation

    # Calculate quality score
    num_voices = len(voice_mapping)

    # Prefer minimal motion
    avg_motion = total_motion / num_voices if num_voices > 0 else 0
    motion_score = max(0.0, 1.0 - (avg_motion / 12.0))  # 0 semitones = 1.0, 12+ = 0.0

    # Prefer stepwise motion
    stepwise_score = stepwise_count / num_voices if num_voices > 0 else 0

    # Prefer common tones (oblique motion)
    common_tone_score = oblique_count / num_voices if num_voices > 0 else 0

    # Penalize parallel 5ths/octaves
    parallel_penalty = (parallel_5ths + parallel_octaves) * 0.2

    # Weighted combination
    quality = (
        0.5 * motion_score +
        0.3 * stepwise_score +
        0.2 * common_tone_score -
        parallel_penalty
    )

    return max(0.0, min(1.0, quality))


def _find_optimal_voice_mapping(
    voicing1: ChordVoicing,
    voicing2: ChordVoicing
) -> List[Tuple[VoicedNote, VoicedNote]]:
    """
    Find optimal mapping between voices to minimize motion.

    Uses greedy algorithm (or Hungarian for optimal solution).
    """
    # Sort both voicings by pitch
    notes1 = sorted(voicing1.notes)
    notes2 = sorted(voicing2.notes)

    # Simple greedy: match closest notes
    # (For production, use Hungarian algorithm for optimal matching)
    mapping = []

    # Handle different numbers of voices
    min_voices = min(len(notes1), len(notes2))

    for i in range(min_voices):
        mapping.append((notes1[i], notes2[i]))

    return mapping
```

#### Integration with Reharmonizer

```python
# halmoni/reharmonization/voicing_aware_reharmonizer.py

from halmoni.core.voicing import VoicingGenerator, ChordVoicing, calculate_voice_leading_quality
from halmoni.reharmonization import Reharmonizer

class VoicingAwareReharmonizer(Reharmonizer):
    """
    Reharmonizer that considers specific voicings for optimal voice leading.

    Extends base Reharmonizer with voicing awareness.
    """

    def __init__(
        self,
        voicing_style: str = "jazz",
        instrument: str = "piano",
        min_note: Note = Note("E", 2),
        max_note: Note = Note("C", 6)
    ):
        super().__init__()
        self.voicing_generator = VoicingGenerator(
            style=voicing_style,
            instrument=instrument,
            min_note=min_note,
            max_note=max_note
        )

    def reharmonize(
        self,
        score: Score,
        style: Union[str, StyleProfile],
        complexity: float,
        **kwargs
    ) -> Tuple[Score, List[ChordVoicing]]:
        """
        Reharmonize with voicing awareness.

        Returns:
            Tuple of (reharmonized_score, voicing_sequence)
        """
        # Get base reharmonization
        new_score = super().reharmonize(score, style, complexity, **kwargs)

        # Generate optimal voicing sequence
        voicing_sequence = self._generate_voicing_sequence(new_score.progression)

        return new_score, voicing_sequence

    def _generate_voicing_sequence(
        self,
        progression: ChordProgression
    ) -> List[ChordVoicing]:
        """
        Generate optimal voicing sequence for a progression.

        Uses dynamic programming to find voicing sequence with
        best overall voice leading.
        """
        chords = progression.chords
        n = len(chords)

        # Generate candidate voicings for each chord
        candidate_voicings = []
        for chord in chords:
            voicings = self.voicing_generator.generate_voicings(chord, n_voicings=10)
            candidate_voicings.append(voicings)

        # Dynamic programming: find best path through voicing graph
        # dp[i][j] = best score for path ending at voicing j of chord i
        dp = [[0.0] * len(candidate_voicings[i]) for i in range(n)]
        parent = [[None] * len(candidate_voicings[i]) for i in range(n)]

        # Base case: first chord (all voicings equally good)
        for j in range(len(candidate_voicings[0])):
            dp[0][j] = 1.0  # Default quality

        # Fill DP table
        for i in range(1, n):
            for j, voicing_curr in enumerate(candidate_voicings[i]):
                best_score = 0.0
                best_parent = None

                # Check all previous voicings
                for k, voicing_prev in enumerate(candidate_voicings[i - 1]):
                    # Voice leading quality between voicings
                    vl_quality = calculate_voice_leading_quality(voicing_prev, voicing_curr)

                    # Total score = previous path + current voice leading
                    score = dp[i - 1][k] + vl_quality

                    if score > best_score:
                        best_score = score
                        best_parent = k

                dp[i][j] = best_score
                parent[i][j] = best_parent

        # Backtrack to find best path
        # Find best voicing for last chord
        best_last_idx = max(range(len(candidate_voicings[-1])), key=lambda j: dp[-1][j])

        # Reconstruct path
        path = []
        current_idx = best_last_idx

        for i in range(n - 1, -1, -1):
            path.append(candidate_voicings[i][current_idx])
            if i > 0:
                current_idx = parent[i][current_idx]

        path.reverse()
        return path

    def _score_suggestion_with_voicing(
        self,
        suggestion: ChordSuggestion,
        previous_voicing: Optional[ChordVoicing],
        **kwargs
    ) -> float:
        """
        Score a suggestion considering voicing quality.

        Extends base scoring with voicing-aware voice leading.
        """
        # Get base score
        base_score = super()._score_suggestion(suggestion, **kwargs)

        if previous_voicing is None:
            return base_score

        # Generate best voicing for suggested chord
        suggested_voicings = self.voicing_generator.generate_voicings(
            suggestion.suggested_chord,
            n_voicings=1,
            previous_voicing=previous_voicing
        )

        if not suggested_voicings:
            return base_score

        # Calculate voice leading quality
        vl_quality = calculate_voice_leading_quality(
            previous_voicing,
            suggested_voicings[0]
        )

        # Combine scores (weighted)
        return 0.7 * base_score + 0.3 * vl_quality
```

### 2.3 Usage Examples

#### Example 1: Basic Voicing Generation

```python
from halmoni.core import Chord, Note
from halmoni.core.voicing import VoicingGenerator

# Create voicing generator for jazz piano
generator = VoicingGenerator(
    style="jazz",
    instrument="piano",
    min_note=Note("E", 2),
    max_note=Note("C", 6)
)

# Generate voicings for Cmaj7
chord = Chord.from_symbol("Cmaj7")
voicings = generator.generate_voicings(chord, n_voicings=5)

for i, voicing in enumerate(voicings):
    print(f"{i+1}. {voicing}")
    print(f"   Type: {voicing.voicing_type.value}")
    print(f"   Notes: {[str(n.pitch) for n in sorted(voicing.notes)]}")
    print(f"   Span: {voicing.span} semitones")
    print()

# Output:
# 1. ChordVoicing(Cmaj7, [E3, G3, B3, D4], drop_2)
#    Type: drop_2
#    Notes: ['E3', 'G3', 'B3', 'D4']
#    Span: 10 semitones
#
# 2. ChordVoicing(Cmaj7, [E3, B3, D4, G4], rootless)
#    Type: rootless
#    Notes: ['E3', 'B3', 'D4', 'G4']
#    Span: 16 semitones
# ...
```

#### Example 2: Voice Leading Aware Reharmonization

```python
from halmoni import Score
from halmoni.reharmonization import VoicingAwareReharmonizer

# Load score
score = Score.from_midi("my-song.mid")

# Create voicing-aware reharmonizer
reharmonizer = VoicingAwareReharmonizer(
    voicing_style="jazz",
    instrument="piano"
)

# Reharmonize with voicing awareness
new_score, voicing_sequence = reharmonizer.reharmonize(
    score,
    style="jazz",
    complexity=0.7
)

# Display voicing sequence
print("Voicing Sequence:")
for i, voicing in enumerate(voicing_sequence):
    chord = new_score.progression.chords[i]
    notes = [str(n.pitch) for n in sorted(voicing.notes)]
    print(f"{i+1}. {chord.symbol:8s} -> {', '.join(notes):20s} ({voicing.voicing_type.value})")

# Analyze voice leading quality
from halmoni.core.voicing import calculate_voice_leading_quality

total_quality = 0.0
for i in range(len(voicing_sequence) - 1):
    quality = calculate_voice_leading_quality(
        voicing_sequence[i],
        voicing_sequence[i + 1]
    )
    total_quality += quality
    print(f"  {i+1} -> {i+2}: {quality:.2f}")

avg_quality = total_quality / (len(voicing_sequence) - 1)
print(f"\nAverage voice leading quality: {avg_quality:.2f}")
```

#### Example 3: Export Voicings to MIDI

```python
from halmoni.core.voicing import ChordVoicing
from mido import MidiFile, MidiTrack, Message

def export_voicing_sequence_to_midi(
    voicing_sequence: List[ChordVoicing],
    durations: List[float],  # in beats
    output_path: str,
    tempo: int = 120
):
    """
    Export a voicing sequence to a MIDI file.

    Useful for hearing the voicing sequence.
    """
    midi = MidiFile()
    track = MidiTrack()
    midi.tracks.append(track)

    # Set tempo
    track.append(Message('program_change', program=0, time=0))  # Piano

    current_time = 0
    ticks_per_beat = midi.ticks_per_beat

    for voicing, duration in zip(voicing_sequence, durations):
        # Note on messages
        for voiced_note in voicing.notes:
            track.append(Message(
                'note_on',
                note=voiced_note.pitch.midi_number,
                velocity=80,
                time=0 if current_time == 0 else 0  # First note gets current_time
            ))

        # Wait for duration
        duration_ticks = int(duration * ticks_per_beat)

        # Note off messages
        for i, voiced_note in enumerate(voicing.notes):
            track.append(Message(
                'note_off',
                note=voiced_note.pitch.midi_number,
                velocity=0,
                time=duration_ticks if i == 0 else 0
            ))

        current_time += duration_ticks

    midi.save(output_path)

# Usage
export_voicing_sequence_to_midi(
    voicing_sequence,
    durations=[1.0] * len(voicing_sequence),  # Quarter notes
    output_path="voicing_sequence.mid"
)
```

### 2.4 Implementation Tasks

**Week 1: Core Voicing Data Structures**
- [ ] Implement `VoicingType` enum
- [ ] Implement `VoicedNote` dataclass
- [ ] Implement `ChordVoicing` dataclass
- [ ] Implement `calculate_voice_leading_quality()`
- [ ] Unit tests (30+ test cases)

**Week 2: Voicing Generation**
- [ ] Implement `VoicingGenerator` skeleton
- [ ] Implement drop-2 voicing generation
- [ ] Implement rootless voicing generation
- [ ] Implement close/open position generation
- [ ] Unit tests for each voicing type

**Week 3: Style-Specific Voicings**
- [ ] Implement `_generate_jazz_voicings()`
- [ ] Implement `_generate_classical_voicings()`
- [ ] Implement `_generate_pop_voicings()`
- [ ] Implement quartal voicing generation
- [ ] Implement spread voicing generation
- [ ] Unit tests

**Week 4: Instrument Constraints**
- [ ] Implement piano playability checking
- [ ] Implement guitar playability checking
- [ ] Implement register filtering
- [ ] Unit tests

**Week 5: Voicing Sequence Optimization**
- [ ] Implement `_find_optimal_voice_mapping()`
- [ ] Implement `_generate_voicing_sequence()` with DP
- [ ] Implement parallel 5th/octave detection
- [ ] Integration tests

**Week 6: Integration with Reharmonizer**
- [ ] Implement `VoicingAwareReharmonizer`
- [ ] Integrate voicing scoring into suggestion evaluation
- [ ] Implement MIDI export for voicings
- [ ] Integration tests

**Week 7-8: Polish & Documentation**
- [ ] Error handling and edge cases
- [ ] Performance optimization
- [ ] Complete documentation
- [ ] Create examples
- [ ] Create tutorial notebook

---

## Part 3: Combined Usage

### Example: Full Production Workflow

```python
from halmoni import Score
from halmoni.reharmonization import InteractiveReharmonizer, VoicingAwareReharmonizer

# Load original score
original = Score.from_midi("song.mid", manual_key="C Major")

# Phase 1: Interactive reharmonization
interactive = InteractiveReharmonizer(original, style="jazz", complexity=0.7)

# Define sections
interactive.define_section("intro", 0, 8)
interactive.define_section("verse", 8, 24)
interactive.define_section("chorus", 24, 40)

# Reharmonize intro conservatively
intro_suggestions = interactive.reharmonize_section("intro")
for sug in intro_suggestions[:3]:
    if sug.confidence > 0.7:
        interactive.accept_suggestion(sug)

# Lock intro
interactive.lock_range(0, 8)

# Reharmonize verse with more complexity
verse_suggestions = interactive.get_suggestions_for_range(8, 24)
for sug in verse_suggestions[:5]:
    preview = interactive.preview_suggestion(sug)
    # User reviews and accepts
    interactive.accept_suggestion(sug)

# Get intermediate result
intermediate_score = interactive.finalize()

# Phase 2: Voicing optimization
voicing_aware = VoicingAwareReharmonizer(
    voicing_style="jazz",
    instrument="piano"
)

# Generate optimal voicings
final_score, voicing_sequence = voicing_aware.reharmonize(
    intermediate_score,
    style="jazz",
    complexity=0.7
)

# Export results
# 1. Export score to MIDI
final_score.export_to_midi("final_reharmonization.mid")

# 2. Export voicings separately
export_voicing_sequence_to_midi(
    voicing_sequence,
    durations=[c.duration for c in final_score.progression.chords],
    output_path="voicings.mid"
)

# 3. Generate PDF with notation (future feature)
# final_score.export_to_pdf("final_reharmonization.pdf", show_voicings=True)

# 4. Generate analysis report
changes = interactive.compare_with_original()
print(f"Total changes: {len(changes)}")
for pos, orig, new, reason in changes:
    voicing = voicing_sequence[pos]
    print(f"{pos}: {orig} → {new} ({reason})")
    print(f"   Voicing: {[str(n.pitch) for n in sorted(voicing.notes)]}")
```

---

## Part 4: Testing & Validation

### Unit Tests

**Interactive Reharmonization:**
- [ ] State serialization/deserialization
- [ ] Undo/redo functionality
- [ ] Lock/unlock positions
- [ ] Section management
- [ ] Suggestion caching
- [ ] Preview without modification

**Voicing Generation:**
- [ ] All voicing types generate correctly
- [ ] Instrument constraints work
- [ ] Register filtering works
- [ ] Voice leading calculation accurate
- [ ] DP voicing sequence finds optimal path

### Integration Tests

- [ ] Interactive + voicing-aware workflow
- [ ] Save/load session preserves state
- [ ] Large progressions (100+ chords) perform acceptably
- [ ] Edge cases (single chord, empty progression)

### Musical Validation

- [ ] Jazz voicings sound jazzy (subjective review)
- [ ] Classical voicings follow SATB rules
- [ ] Voice leading is smooth (no jumps > octave without reason)
- [ ] Parallel 5ths/octaves detected correctly

---

## Part 5: Documentation Deliverables

- [ ] API reference for all new classes
- [ ] Tutorial: "Interactive Reharmonization Workflow"
- [ ] Tutorial: "Understanding Voicings"
- [ ] Example notebook: "Reharmonizing a Jazz Standard"
- [ ] Example notebook: "Classical Voice Leading"
- [ ] Performance benchmarks

---

## Timeline Summary

| Feature | Weeks | Dependencies |
|---------|-------|--------------|
| Interactive/Incremental Reharmonization | 4 | Core implementation (Phases 1-3) |
| Voicing Awareness | 8 | Core implementation (Phases 1-3) |
| Integration & Polish | 2 | Both features complete |
| **Total** | **14 weeks** | |

---

## Future Extensions (v1.3+)

1. **Real-time collaboration** - Multiple users in same session
2. **AI-assisted voicing** - ML model suggests voicings based on style
3. **Automatic voice leading smoothing** - Post-process to fix awkward voice leading
4. **Guitar/bass tablature generation** - Convert voicings to TAB notation
5. **Orchestration** - Distribute voicings across multiple instruments
