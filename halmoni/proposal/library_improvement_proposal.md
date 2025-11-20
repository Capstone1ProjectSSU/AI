# Proposal: Evolving the `halmoni` Library for Musicians and Developers

## 1. High-Level Vision

The `halmoni` library has a strong foundation for music analysis and suggestion. The next stage of its evolution should focus on creating a higher-level, more intuitive API that abstracts away common boilerplate code. The goal is to empower developers to "think like musicians." Instead of manually programming every step of a complex task like reharmonization, developers should be able to use a simple, expressive API that handles the underlying music theory complexity for them.

---

## 2. Developer Experience (DX) Improvements

Our work on the demo script highlighted several areas where the developer experience could be significantly streamlined.

### Problem 1: Manual and Verbose MIDI Processing
*   **Our Use Case:** To get a usable chord progression, we had to manually chain together several objects: `MIDIAnalyzer` -> `group_simultaneous_notes` -> `ChordDetector` -> `ChordProgression`. We also had to manually calculate the duration of each chord to align it with the melody. This is a lot of work for what should be a single, common operation.
*   **Proposal: Introduce a unified `Score` object and high-level constructors.**
    *   Create a new top-level object, `halmoni.Score`, that serves as the primary container for all information related to a piece of music.
    *   This object would be instantiated with a high-level constructor: `score = halmoni.Score.from_midi("path/to/file.mid")`.
    *   This single call would automatically handle MIDI parsing, note grouping, chord detection, melody extraction, and duration calculation. The resulting `score` object would contain easily accessible attributes like:
        *   `score.progression: ChordProgression`
        *   `score.melody: List[NoteEvent]`
        *   `score.key: Key` (from a more robust detection)
        *   `score.metadata: Dict` (tempo, time signature, etc.)

### Problem 2: Disconnected and Unaware Core Objects
*   **Our Use Case:** The `ChordProgression` object had no intrinsic knowledge of the melody being played over it. We had to pass the melody and progression around as separate variables and manually align them.
*   **Proposal: The `Score` object would link components.** By having the `Score` object contain both the progression and the melody, these elements are intrinsically linked. This makes melody-aware operations (like checking for clashes) much cleaner and more robust.

### Problem 3: Unintuitive `Note` Initialization
*   **Our Use Case:** Our script failed twice because the `Note()` constructor was stricter than expected, first requiring a `Note` object instead of a string, and then requiring an explicit octave. For many music theory operations (like defining a key), the octave is irrelevant.
*   **Proposal: Create more forgiving or context-specific initializers.**
    *   The `Note()` constructor could default to a standard octave (e.g., 4) when one isn't provided.
    *   Better yet, provide a clear factory function like `Note.from_pitch_class("C")` for contexts where the octave is not needed.

---

## 3. Music Theory & Reharmonization Engine Improvements

The demo script's evolution from a single-chord substitution to a theory-aware beam search shows the need for more powerful, built-in music theory concepts.

### Problem 1: Reharmonization Logic is the User's Responsibility
*   **Our Use Case:** We had to design and implement a sophisticated beam search, a multi-part scoring function, and all the rules for functional harmony and melodic clashes directly in our demo script. This places an enormous burden on the developer and requires them to be a music theory expert.
*   **Proposal: Create a high-level, built-in `Reharmonizer` engine.**
    *   This engine would encapsulate the complex logic we built. The user would simply interact with a high-level API.
    *   The workflow would be simple and expressive:
        ```python
        from halmoni import Score, Reharmonizer

        # Load the score, which contains progression, melody, key, etc.
        score = Score.from_midi("path/to/file.mid", manual_key="G Major")

        # Create a reharmonizer and apply a style
        reharm_engine = Reharmonizer(score)
        jazzy_score = reharm_engine.reharmonize(style="jazz", complexity=0.7)
        ```
    *   The `style` parameter could select different sets of suggestion strategies and scoring weights (e.g., "jazz", "classical", "pop"). The `complexity` parameter would control how far from the original progression the result can deviate.

### Problem 2: Simplistic Functional Analysis
*   **Our Use Case:** We implemented a basic `get_harmonic_function` helper that only returned "Tonic," "Subdominant," or "Dominant." This is a good start, but it misses the richness of harmonic analysis.
*   **Proposal: Enhance `Key.analyze_chord()` to return a rich analysis object.**
    *   Instead of a simple string, `key.analyze_chord(chord)` should return a `ChordAnalysis` object with structured data, such as:
        *   `analysis.roman_numeral: str` (e.g., "V7/IV")
        *   `analysis.function: str` (e.g., "Secondary Dominant")
        *   `analysis.is_diatonic: bool`
        *   `analysis.is_borrowed: bool`
    *   This would allow the internal `Reharmonizer` engine to make much more intelligent decisions, like rewarding a `V7/V -> V -> I` progression.

### Problem 3: Opaque Chord Suggestions
*   **Our Use Case:** The `ChordSuggestion` object's `reasoning` is just a string. Our code can't programmatically understand *why* a chord was suggested. We had to add a `last_strategy` variable to our beam search to penalize repetition.
*   **Proposal: Add structured metadata to `ChordSuggestion`.**
    *   The `ChordSuggestion` dataclass should be expanded to include structured data that the reharmonization engine can use for scoring.
        ```python
        from dataclasses import dataclass

        @dataclass
        class ChordSuggestion:
            # ... existing fields
            strategy_source: str
            # NEW: Add structured reason
            substitution_type: str  # e.g., "TritoneSub", "ModalBorrowing", "Suspension"
            target_chord: Chord    # The chord it is intended to replace
        ```
    *   This makes it trivial for the internal engine to implement rules like "don't use two tritone substitutions in a row."

---

## 4. The "Future DX": What the Demo Script *Should* Look Like

By implementing these proposals, the complex, multi-step script we built could be reduced to this elegant and expressive ideal:

```python
from halmoni import Score, Reharmonizer, Key

# 1. Load the piece and specify the key, letting Halmoni handle the details.
score = Score.from_midi(
    "examples/ode-to-joy-easy-variation.mid",
    manual_key=Key.from_string("G Major")
)

# 2. Create a reharmonizer and generate a new, jazzier score.
# The complex logic is now encapsulated inside the library.
reharmonizer = Reharmonizer(score)
jazzy_score = reharmonizer.reharmonize(style="jazz", complexity=0.7)

# 3. Print the results.
print(f"Original Progression: {score.progression}")
print(f"Jazzier Progression:  {jazzy_score.progression}")
```

This proposed direction would make `halmoni` dramatically more powerful and easier to use, appealing to both developers who want a simple API and music theorists who want assurance of a rigorous underlying model.
