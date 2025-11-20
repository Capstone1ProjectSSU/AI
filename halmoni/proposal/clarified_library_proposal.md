# Clarified Proposal for the Evolution of the `halmoni` Library

This document provides a detailed technical specification for the next generation of the `halmoni` library, based on the initial proposal and the subsequent review. It aims to provide clear answers to the open questions and serve as a guide for implementation.

---

## 1. Core API and Data Models

### 1.1. The `Score` Object: A Unified Representation

The library will introduce a new top-level object, `halmoni.Score`, to act as a unified container for all musical information.

**Responsibilities:**
- The primary entry point for users will be `Score.from_midi(filepath, **kwargs)`.
- This constructor will be responsible for parsing the MIDI file, including all metadata, and performing an initial analysis to populate its attributes.

**Attributes:**
- `score.progression: ChordProgression`: The detected chord progression.
- `score.melodies: Dict[int, List[NoteEvent]]`: A dictionary mapping track indices to their melodic lines.
- `score.key: Key`: The detected or specified key of the piece.
- `score.metadata: Metadata`: A structured dataclass for song metadata.
- `score.warnings: List[str]`: A list of human-readable warnings generated during analysis (e.g., low key-detection confidence).

**MIDI Handling:**
- **Multi-track Files:** `from_midi` will support multi-track files. It will use heuristics to auto-detect roles (e.g., highest pitch track as primary melody, channel 10 as percussion). These can be overridden by the user: `Score.from_midi(..., melody_track_id=2, harmony_track_ids=[0, 1])`.
- **Percussion:** Percussion tracks (channel 10) will be ignored for harmonic analysis but will be noted in the metadata.

### 1.2. Data Structures

**`Metadata` Dataclass:**
To avoid ambiguity, `score.metadata` will be a dataclass:
```python
from dataclasses import dataclass
from typing import Optional, List, Tuple

@dataclass
class Metadata:
    title: Optional[str]
    composer: Optional[str]
    copyright: Optional[str]
    track_names: List[str]
    initial_tempo: float
    initial_time_signature: Tuple[int, int]
```

**`NoteEvent` Dataclass:**
This object represents a single melodic event.
```python
@dataclass
class NoteEvent:
    pitch: Note
    start_time: float  # in beats
    duration: float    # in beats
    velocity: int      # 0-127
    track_id: int
```
- Simultaneous notes (e.g., octaves) will be stored as multiple `NoteEvent` objects with identical timestamps.

**`PitchClass` Type:**
To improve type safety and clarity, a `PitchClass` type will be introduced for contexts where octave is irrelevant (e.g., Key definition).
```python
from typing import NewType
PitchClass = NewType('PitchClass', str) # With validation logic
```

**`Note` Constructor:**
- The `Note` constructor will be updated to accept a single string (e.g., `"C4"`) for convenience.
- `Note("C", 4)` will remain the primary constructor.
- A new factory method, `Note.from_pitch_class(pitch_class: PitchClass, octave: int = 4)`, will be added for clarity.

---

## 2. The `Reharmonizer` Engine

The core reharmonization logic will be encapsulated in a new `halmoni.Reharmonizer` class.

### 2.1. Architecture and Interface

- **Design:** The engine will be immutable. The `reharmonize()` method will always return a *new* `Score` object, leaving the original untouched.
- **Primary Method:** `reharmonizer.reharmonize(style: Union[str, StyleProfile], complexity: float) -> Score`
- **Parameters:**
    - `style`: A string enum (`"jazz"`, `"classical"`, `"pop"`, `"rock"`) or a custom `StyleProfile` object provided by the user.
    - `complexity` (0.0 to 1.0): A float that primarily acts as a multiplier on the confidence of more chromatic or "distant" suggestions.
        - `0.0`: Makes only essential diatonic changes to improve functional harmony (e.g., fixing a `iii-IV` progression). The original progression is returned if it's already functionally sound.
        - `1.0`: Applies no penalty to even the most chromatic suggestions, allowing for maximum harmonic exploration.

### 2.2. Style Profiles

A `StyleProfile` is a dataclass that defines the "personality" of the reharmonizer.

**`StyleProfile` Dataclass:**
```python
@dataclass
class StyleProfile:
    # Strategy activation (0.0 = off, 1.0 = fully active)
    tsd_movement_weight: float = 1.0
    neapolitan_weight: float = 0.0
    borrowed_chord_weight: float = 0.5
    subv7_weight: float = 0.0
    suspend_weight: float = 0.5
    chromatic_approach_weight: float = 0.2

    # Scoring function weights
    functional_adherence: float = 1.0 # How strictly to follow T-S-D rules
    melodic_clash_penalty: float = 20.0
    repetition_penalty: float = 0.3

    # Style-specific rules
    allow_dominant_to_subdominant: bool = False
```

**Default Profiles:**
The library will ship with default profiles. For example:

| Strategy | Jazz | Classical | Pop | Rock |
|---|---|---|---|---|
| `tsd_movement_weight` | 0.6 | 1.0 | 0.8 | 0.5 |
| `neapolitan_weight` | 0.1 | 0.8 | 0.0 | 0.1 |
| `borrowed_chord_weight` | 0.9 | 0.6 | 1.0 | 1.0 |
| `subv7_weight` | 1.0 | 0.0 | 0.2 | 0.0 |
| `suspend_weight` | 0.8 | 0.3 | 1.0 | 1.0 |
| `chromatic_approach_weight`| 1.0 | 0.5 | 0.4 | 0.4 |
| `allow_dominant_to_subdominant` | True | False | True | True |

### 2.3. Internal Search and Scoring

- **Algorithm:** The internal engine will use **beam search** as the default search strategy.
- **Reproducibility:** A `seed` parameter will be available on the `reharmonize` method for reproducible results.
- **Scoring Function:** The score for each step in the beam search will be a weighted sum of several music-theoretical factors, with weights controlled by the active `StyleProfile`. The core components are:
    1.  **Suggestion Confidence:** The base score from the strategy itself.
    2.  **Voice Leading Quality:** Score based on common tones and smooth root motion.
    3.  **Functional Progression Score:** Rewards strong harmonic syntax (e.g., S->D->T).
    4.  **Melodic Consonance Score:** Applies a heavy penalty for clashes between chord tones and melody notes.
    5.  **Variety Score:** Applies a penalty for using the same `substitution_type` consecutively.

---

## 3. Enhanced Analysis and Metadata

To power the new engine, the underlying analysis objects will be enriched.

### 3.1. `ChordAnalysis` Object

The `Key.analyze_chord()` method will return a rich `ChordAnalysis` dataclass:
```python
@dataclass
class ChordAnalysis:
    roman_numeral: str
    function: str  # 'Tonic', 'Dominant', 'Subdominant', 'SecondaryDominant', 'Modal'
    is_diatonic: bool
    is_borrowed: bool
    scale_degree: int
    quality: str
    tensions: List[int]
    borrowed_from_mode: Optional[str]
    functional_strength: float # A score from 0.0 to 1.0
```

### 3.2. `ChordSuggestion` Metadata

The `ChordSuggestion` object will be updated to provide structured metadata for the scoring engine:
```python
@dataclass
class ChordSuggestion:
    # ... existing fields
    strategy_source: str
    substitution_type: str # Enum: 'TRITONE_SUB', 'MODAL_BORROWING', etc.
    target_chord: Optional[Chord] # The chord it replaces
    is_insertion: bool
```

---

## 4. Implementation Plan

### 4.1. Phased Rollout

1.  **Phase 1 (Core API):** Implement the `Score`, `Metadata`, `NoteEvent`, and `PitchClass` objects. Implement `Score.from_midi()` to handle parsing and population of these objects.
2.  **Phase 2 (Enhanced Analysis):** Upgrade `Key.analyze_chord()` to return the new `ChordAnalysis` object. Upgrade `ChordSuggestion` to include the new structured metadata.
3.  **Phase 3 (Reharmonizer MVP):** Implement the `Reharmonizer` class and the `reharmonize()` method with the internal beam search and the new multi-part scoring function. Ship with default `StyleProfile` objects for "jazz", "classical", and "pop".
4.  **Phase 4 (Advanced Features):** Implement support for custom `StyleProfile` objects. Add more advanced parameters to the `reharmonize` method for fine-grained control.
5.  **Phase 5 (Strategy Improvement):** Refine and improve the individual suggestion strategies based on the new capabilities of the engine (e.g., making `SuspendStrategy` prioritize resolution).

### 4.2. Backward Compatibility

- The existing, lower-level API (`ChordProgression.from_symbols`, etc.) will be marked as **deprecated** in the first release containing this new model.
- Clear warnings will guide users to the new `Score`-based API.
- A `MIGRATION.md` guide will be added to the repository.
- The deprecated API will be scheduled for removal in the next major version (e.g., v2.0).
