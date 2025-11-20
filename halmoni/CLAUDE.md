# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**halmoni** is a production-ready music creative coding support library for chord analysis, progression suggestions, and instrument difficulty analysis. It's implemented in Python 3.12+ and uses `music21`, `mido`, and `numpy` as core dependencies.

The project is inspired by the Musicant library (Haskell) but adapted for Python with a focus on practical music composition and analysis workflows.

## Development Commands

### Setup
```bash
# Install dependencies (requires Python 3.12+)
uv sync

# Install development dependencies
uv sync --dev
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_<module>.py

# Run tests with verbose output
pytest -v

# Run tests for a specific function/class
pytest tests/test_<module>.py::test_function_name
```

### Code Quality
```bash
# Format code with Black
black halmoni/ tests/

# Type checking with mypy
mypy halmoni/

# Run pre-commit hooks manually
pre-commit run --all-files
```

### Running Examples
```bash
# Run chord suggestion examples
uv run examples/chord_suggestions_example.py

# Run main entry point
uv run main.py
```

## Architecture Overview

### Core Module Structure

The library is organized into four main modules:

1. **`halmoni/core/`** - Fundamental music theory classes
   - `Note`, `Interval`, `Chord`, `Scale`, `Key` - Basic music theory primitives
   - `ChordProgression` - Sequence of chords with timing and analysis capabilities
   - `ChordVoicing`, `ChordInversion` - Specific voicings and inversions
   - All core classes support rich comparison, hashing, and string representations

2. **`halmoni/analysis/`** - MIDI analysis and chord/key detection
   - `MIDIAnalyzer` - Loads and preprocesses MIDI files, extracts notes, quantizes timing
   - `ChordDetector` - Detects chords from simultaneous notes
   - `KeyDetector` - Statistical key detection using Krumhansl-Schmuckler profiles
   - `AdamStarkChordDetector` - Alternative chord detection algorithm

3. **`halmoni/suggestions/`** - Chord progression enhancement strategies
   - `ChordSuggestionEngine` - Main orchestration engine coordinating all strategies
   - Six suggestion strategies implementing the Strategy pattern:
     - `BorrowedChordStrategy` - Modal interchange from parallel modes
     - `ChromaticApproachStrategy` - Chromatic passing and approach chords
     - `NeapolitanStrategy` - Neapolitan sixth chords for pre-dominant function
     - `SubV7Strategy` - Tritone substitutions for jazz harmony
     - `SuspendStrategy` - Suspension chords for added tension
     - `TSDMovementStrategy` - Functional harmony patterns (Tonic-Subdominant-Dominant)
   - All strategies inherit from `ChordSuggestionStrategy` base class
   - Each suggestion includes confidence score, reasoning, position, and voice leading quality

4. **`halmoni/instruments/`** - Instrument-specific difficulty analysis
   - `GuitarDifficulty` - Analysis for 5-string guitar (fret span, barre chords, fingering)
   - `PianoDifficulty` - Piano hand span and voice distribution analysis
   - `BassDifficulty` - 4-string bass position and string crossing analysis

### Key Design Patterns

**Strategy Pattern**: All chord suggestion strategies implement the `ChordSuggestionStrategy` abstract base class with a `suggest()` method. This allows the `ChordSuggestionEngine` to coordinate multiple strategies uniformly.

**Data Classes**: `ChordSuggestion` uses `@dataclass` for clean, immutable suggestion objects with confidence, reasoning, position, and voice leading quality.

**Functional Analysis**: The `Key` class provides `analyze_chord()` method that returns harmonic analysis including degree, function (tonic/subdominant/dominant), and whether the chord is diatonic.

**Voice Leading Quality**: Strategies calculate voice leading quality based on common tone retention and root motion, preferring smooth voice leading (stepwise motion, perfect 4th/5th).

## Important Implementation Details

### Chord Progression Analysis
- `ChordProgression` supports both creation from symbols (`from_symbols()`) and Roman numerals (`from_roman_numerals()`)
- Progressions track durations for each chord (defaults to 1.0 beat per chord)
- The `get_chord_transitions()` method analyzes root movement between adjacent chords
- Voice leading analysis (`analyze_voice_leading()`) can work with or without explicit voicings

### MIDI Analysis Pipeline
- `MIDIAnalyzer.load_midi_file()` returns a comprehensive analysis dict with tracks, notes, tempo, and time signature
- Notes are quantized using `quantize_timing()` with configurable grid (default 0.25 beats = 16th notes)
- `group_simultaneous_notes()` groups notes within tolerance (default 0.1 beats) for chord detection
- `get_time_windows()` divides MIDI into analysis windows for progression extraction

### Suggestion Engine Workflow
1. Create `ChordProgression` from symbols or MIDI analysis
2. Instantiate `ChordSuggestionEngine()`
3. Call `get_suggestions(progression, key)` to get all suggestions ranked by confidence
4. Optional: Filter by strategy using `strategy_filter=['SubV7', 'BorrowedChord']`
5. Optional: Get suggestions for specific position with `get_suggestions_for_position(progression, position, key)`
6. Use `analyze_progression_potential()` to identify improvement areas

### Chord Symbol Parsing
- Supports multiple notation styles: 'Cmaj7', 'CM7', 'C', 'Am7', 'Gdim7', 'C/E' (slash chords)
- Accidentals: Use '#' and 'b' (e.g., 'C#', 'Bb')
- Extensions: maj7, m7, 7, dim7, m7b5, 9, 11, 13, sus2, sus4
- Symbol parsing is case-sensitive for major/minor distinction

### Type Annotations
- The codebase uses strict type annotations (required by mypy configuration)
- All functions must have complete type hints: parameters, return types, and Optional[] where applicable
- Use `List`, `Dict`, `Tuple`, `Optional`, `Set` from typing module
- Use `-> None` for functions with no return value

## Common Development Patterns

### Adding a New Suggestion Strategy
1. Create new file in `halmoni/suggestions/` (e.g., `my_strategy.py`)
2. Inherit from `ChordSuggestionStrategy` base class
3. Implement `suggest(progression, key)` returning `List[ChordSuggestion]`
4. Implement `get_strategy_name()` returning a descriptive string
5. Add to `ChordSuggestionEngine.__init__()` strategies list
6. Export in `halmoni/suggestions/__init__.py`
7. Add to `halmoni/__init__.py` for top-level imports

### Working with Chord Qualities
- Internal quality names: 'major', 'minor', 'dominant7', 'major7', etc. (see `Chord.CHORD_TONES`)
- Symbols for display: '', 'm', '7', 'maj7', etc. (see `Chord.CHORD_SYMBOLS`)
- Always use internal quality names in constructors: `Chord(root, 'dominant7')`
- Use `Chord.from_symbol('G7')` for parsing user input

### Voice Leading Calculations
- Common tones improve voice leading quality (more weight: 0.6)
- Root motion quality favors stepwise motion and perfect intervals (weight: 0.4)
- Use `_calculate_voice_leading_quality(chord1, chord2)` from base strategy
- Voice leading quality ranges from 0.0 (poor) to 1.0 (excellent)

## Testing Guidelines

- Test files should mirror the module structure: `tests/test_core.py`, `tests/test_analysis.py`, etc.
- Use pytest fixtures for commonly used test objects (keys, progressions, chords)
- Music theory tests should verify both mathematical correctness and musical conventions
- When testing suggestions, verify confidence scores are reasonable (0.0-1.0) and reasoning is descriptive
- MIDI analysis tests should use small synthetic MIDI files (check if `tests/fixtures/` exists)

## Notes for Development

- **No tests directory yet**: The project structure includes `testpaths = ["tests"]` in pyproject.toml but tests haven't been created. Start with core music theory tests.
- **Instruments module incomplete**: `GuitarDifficulty`, `PianoDifficulty`, and `BassDifficulty` classes are exported but implementations need to be verified/created.
- **Reference implementation**: See `claude_plan.md` for the full implementation roadmap and architecture decisions.
- **Music21 integration**: The library uses music21 as a foundation but extends it significantly. Avoid tight coupling to music21 internals.
- **Strict mypy configuration**: All code must pass strict type checking (see `[tool.mypy]` in pyproject.toml).
