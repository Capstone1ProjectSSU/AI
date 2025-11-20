# Proposal Review: Questions for Clarification

This document identifies ambiguous, vague, or under-specified aspects of the library improvement proposals that require clarification before implementation.

---

## 1. Score Object & API Design

### 1.1 Score Object Scope & Responsibilities
**Proposal Reference:** Section 2, Problem 1

**Questions:**
1. Should `Score.from_midi()` support multi-track MIDI files? If yes:
   - How should tracks be distinguished (melody vs. harmony vs. bass)?
   - Should the user manually specify track roles, or should heuristics auto-detect them?
   - What happens with percussion tracks?

2. What should happen when key detection confidence is low?
   - Should the method raise an error, return partial results, or fall back to C major?
   - Should there be a `confidence_threshold` parameter?

3. The `score.metadata` dict is mentioned but not specified. What fields are required?
   - tempo, time_signature (confirmed)
   - Should it include: composer, title, copyright, track names?
   - Should metadata be a structured class or remain a dict?

4. How should polyphonic melodies be handled?
   - If multiple melody lines exist, should `score.melody` be `List[List[NoteEvent]]`?
   - Should there be a `score.melodies` (plural) attribute?

### 1.2 Note and NoteEvent Representation
**Proposal Reference:** Section 2, Problem 2

**Questions:**
1. What is the structure of `NoteEvent` objects in `score.melody`?
   - Required fields: pitch, start_time, duration, velocity?
   - Should it include: articulation, dynamics, track_source?

2. How should simultaneous melody notes (e.g., octaves, harmonized melody) be represented?
   - Single `NoteEvent` with multiple pitches?
   - Multiple `NoteEvent` objects with identical timestamps?

3. Should melody extraction be smart enough to:
   - Ignore grace notes and ornaments?
   - Prioritize the highest voice in polyphony?
   - Detect and separate counter-melodies?

### 1.3 Note Constructor Changes
**Proposal Reference:** Section 2, Problem 3

**Questions:**
1. What should the default octave be and why?
   - Middle C is octave 4 in scientific pitch notation
   - Should it vary by context (e.g., bass vs. treble)?

2. Should `Note()` accept string input directly, or require explicit factory methods?
   - **Option A:** `Note("C4")` - convenient but potentially ambiguous
   - **Option B:** `Note.from_string("C4")` - explicit but verbose
   - **Option C:** Both - flexible but potentially confusing

3. For pitch-class-only contexts (like `Key.from_string("C Major")`):
   - Should a separate `PitchClass` type be created?
   - Or should `Note` have an optional octave that can be `None`?

---

## 2. Reharmonizer Engine Design

### 2.1 Core Architecture & Interface
**Proposal Reference:** Section 3, Problem 1

**Questions:**
1. Should `Reharmonizer` modify the original score or always return a new one?
   - Immutable (functional) vs. mutable (object-oriented) design?

2. The `reharmonize()` method parameters need specification:
   - **`style` parameter:** Should this be an enum, string, or custom config object?
   - **`complexity` parameter:** What does 0.0 to 1.0 mean precisely?
     - Does 0.0 mean "no changes" or "minimal safe changes"?
     - Does 1.0 mean "maximum chromatic complexity" or "maximum suggestion density"?

3. Should there be additional parameters for:
   - `preserve_melody_harmonization: bool` - avoid melody-chord clashes?
   - `preserve_functional_structure: bool` - keep T-S-D-T patterns?
   - `max_suggestions_per_chord: int` - limit the search space?
   - `prefer_insertions_vs_replacements: float` - balance between adding vs. changing?

### 2.2 Style Profiles
**Proposal Reference:** Section 3, Problem 1 & Strategy Review

**Questions:**
1. What specific strategies should be enabled/disabled for each style?

   | Strategy | Jazz | Classical | Pop | Rock | Folk |
   |----------|------|-----------|-----|------|------|
   | TSDMovement | ? | ? | ? | ? | ? |
   | Neapolitan | ? | ? | ? | ? | ? |
   | BorrowedChord | ? | ? | ? | ? | ? |
   | SubV7 | ? | ? | ? | ? | ? |
   | Suspend | ? | ? | ? | ? | ? |
   | ChromaticApproach | ? | ? | ? | ? | ? |

2. For each style, what should the default weights be?
   - Should weights sum to 1.0, or be independent multipliers?
   - Example: Jazz might weight SubV7=0.8, ChromaticApproach=0.7, but Classical might be SubV7=0.0, Neapolitan=0.6

3. Should users be able to:
   - Create custom style profiles (e.g., `style=StyleProfile.custom(...))`?
   - Mix styles (e.g., `style=["jazz", "classical"]` with blend ratio)?
   - Save and load style profiles from files?

### 2.3 Complexity Parameter Interpretation
**Proposal Reference:** Section 3, Problem 1

**Questions:**
1. Does complexity control:
   - **Option A:** Only the confidence threshold for accepting suggestions?
   - **Option B:** Both threshold AND how many substitutions/insertions to make?
   - **Option C:** The "distance" from diatonic harmony (0=all diatonic, 1=max chromatic)?

2. Should complexity be:
   - Global (one value for entire progression)?
   - Per-section (different complexity for verse vs. chorus)?
   - Time-varying (gradual increase through the piece)?

3. At `complexity=0.0`, should the reharmonizer:
   - Return the original progression unchanged?
   - Only suggest diatonic alternatives?
   - Still fix "weak" progressions (e.g., avoid iii-IV)?

### 2.4 Search Strategy & Optimization
**Proposal Reference:** Section 3, Problem 1 (beam search mentioned)

**Questions:**
1. What search algorithm should be used internally?
   - Beam search (as in the demo)?
   - Genetic algorithm?
   - Simulated annealing?
   - Greedy best-first?

2. What is the scoring function composition?
   - Weight for voice leading quality?
   - Weight for functional progression strength?
   - Weight for melody-chord consonance?
   - Weight for stylistic appropriateness?
   - Weight for variety (avoiding repetitive strategies)?

3. Should there be a timeout or max iterations parameter?
   - What if the search space is huge (e.g., 32-bar form)?

4. Should the engine support:
   - Multiple alternative outputs (e.g., return top 3 reharmonizations)?
   - A `seed` parameter for reproducibility?
   - Incremental/interactive reharmonization (user accepts/rejects, engine continues)?

---

## 3. Enhanced Chord Analysis

### 3.1 ChordAnalysis Object Structure
**Proposal Reference:** Section 3, Problem 2

**Questions:**
1. Complete specification of `ChordAnalysis` fields:
   ```python
   @dataclass
   class ChordAnalysis:
       roman_numeral: str        # e.g., "V7/IV"
       function: str             # e.g., "Secondary Dominant"
       is_diatonic: bool
       is_borrowed: bool
       # What else?
       scale_degree: int?        # Root as scale degree (1-7)?
       quality: str?             # "major", "minor", "dominant7"?
       tensions: List[int]?      # Extensions like [9, 11, 13]?
       borrowed_from_mode: Optional[str]?  # "parallel minor", "mixolydian"?
   ```

2. How should secondary function analysis work?
   - `V7/IV` has function "Secondary Dominant" - clear
   - What about `vii°7/V`? Is the function "Secondary Leading Tone"?
   - What about `IV/V` (subdominant of dominant)? How common is this?

3. Should there be a `functional_strength` score?
   - Example: `V7→I` has strength 1.0, `iii→IV` has strength 0.3?

### 3.2 Functional Analysis Expansion
**Proposal Reference:** Strategy Review, Section 1

**Questions:**
1. Should the functional system be expanded beyond T-S-D?
   - Add **Pre-Dominant** as distinct from Subdominant?
   - Add **Dominant Preparation** (e.g., `ii-V`)?
   - Add **Prolongation** (chords that extend tonic without moving)?

2. How should modal harmony (non-functional) be analyzed?
   - Example: Dorian progression `i-IV-i` has no dominant function
   - Should `analysis.function` return `"Modal"` or `"Non-Functional"`?

3. Should analysis differ between major and minor keys?
   - In minor, is `VI` (submediant) more of a tonic substitute than in major?
   - How should harmonic vs. melodic vs. natural minor affect analysis?

---

## 4. ChordSuggestion Metadata Enhancement

### 4.1 Structured Metadata Fields
**Proposal Reference:** Section 3, Problem 3

**Questions:**
1. Complete specification of new `ChordSuggestion` fields:
   ```python
   @dataclass
   class ChordSuggestion:
       # Existing fields:
       suggested_chord: Chord
       confidence: float
       reasoning: str
       position: int
       voice_leading_quality: float

       # Proposed additions:
       strategy_source: str          # e.g., "SubV7Strategy"
       substitution_type: str        # e.g., "TritoneSub", "ModalBorrowing"
       target_chord: Chord           # The chord it replaces/precedes

       # Additional needed fields?
       is_insertion: bool?           # vs. replacement?
       harmonic_function_change: Optional[str]?  # "Tonic→Dominant"
       melodic_implications: Optional[str]?  # "Avoid if melody has natural 2"
       prerequisite_suggestions: List[int]?  # Indices of suggestions this depends on
   ```

2. What should `substitution_type` values be?
   - Standardized enum or free-form strings?
   - Suggested values: `"TritoneSub"`, `"ModalBorrowing"`, `"Suspension"`, `"NeapolitanSixth"`, `"ChromaticApproach"`, `"SeconaryDominant"`?

3. How should chained suggestions be represented?
   - Example: ChromaticApproach might insert `C#dim7` between `C` and `Dm`
   - Does this create a dependency where later suggestions reference earlier ones?

### 4.2 Usage in Reharmonizer Scoring
**Proposal Reference:** Section 3, Problem 3

**Questions:**
1. What specific rules should the metadata enable?
   - "Don't use two tritone subs in a row" - clear
   - "Don't use more than one Neapolitan in 8 bars"?
   - "Prefer alternating between insertions and replacements"?
   - "Avoid consecutive suggestions from the same strategy"?

2. Should there be a `strategy_repetition_penalty` parameter?
   - How much to penalize using the same strategy consecutively?
   - Should it be exponential (e.g., 1st use: 1.0, 2nd: 0.7, 3rd: 0.4)?

---

## 5. Strategy-Specific Improvements

### 5.1 TSDMovementStrategy
**Proposal Reference:** Strategy Review, Section 1

**Questions:**
1. How should retrogression (D→S) be handled per style?
   - Classical: Strong penalty (current behavior)
   - Rock/Pop: No penalty or slight bonus?
   - Should this be a per-style config value?

2. For chromatic chord function detection:
   - Should `V7/V` be analyzed as having Dominant function? (Proposal says yes)
   - Should `V7/ii`, `V7/iii`, etc. also be analyzed functionally?
   - What about diminished seventh chords (e.g., `vii°7/V`)?

3. Should "bridge chord insertion" have limits?
   - Currently suggests inserting S between T and D
   - Should it suggest inserting multiple chords (T→S→PD→D)?
   - How to avoid over-insertion?

### 5.2 NeapolitanStrategy
**Proposal Reference:** Strategy Review, Section 2

**Questions:**
1. What is the appropriate base confidence level?
   - Current: Unknown
   - Suggested: "very low" - what number? 0.1? 0.2?

2. Melody clash detection specifics:
   - How large should the penalty be for ♭2 vs. natural 2 clash?
   - Should the strategy be completely disabled, or just confidence reduced to 0.05?

3. Should Neapolitan be suggested in major keys?
   - Theoretically valid but extremely rare
   - Should there be different confidence for major vs. minor?

### 5.3 BorrowedChordStrategy
**Proposal Reference:** Strategy Review, Section 3

**Questions:**
1. Priority for function-matching borrowing:
   - Current: General borrowed chord suggestion
   - Proposed: Higher confidence when function matches
   - How much higher? 2x? Additive +0.3 bonus?

2. Expanded modal palette specification:
   - Which modes to include: Dorian, Phrygian, Lydian, Mixolydian (covered), Aeolian?
   - Should there be a `modes` parameter to control this?
   - Example needed: "major IV in minor key (Dorian)" - should this be high confidence?

3. Should borrowing from distant modes be allowed?
   - E.g., borrowing from C Phrygian in C Major (♭II, ♭III, ♭VI, ♭VII)
   - Would this overlap with Neapolitan strategy?

### 5.4 SubV7Strategy
**Proposal Reference:** Strategy Review, Section 4

**Questions:**
1. How should "explicit stylistic activation" work?
   - Disabled by default, enabled only for `style="jazz"`?
   - Or always active but with very low confidence unless jazz context?

2. Melody-awareness specifics:
   - What intervals between melody and chord tones are considered clashes?
   - Minor 9th (♭9) is very dissonant - instant disqualification?
   - Major 7th or minor 2nd - reduced confidence or blocked?

3. Should tritone sub be suggested for:
   - Only V7→I progressions?
   - Any dominant seventh chord?
   - Secondary dominants (e.g., V7/ii)?

### 5.5 SuspendStrategy
**Proposal Reference:** Strategy Review, Section 5

**Questions:**
1. "Prioritize Resolution" - implementation approach:
   - **Option A:** Only suggest sus chords that are immediately followed by their resolution
   - **Option B:** Insert sus chord + resolution as a two-chord suggestion
   - **Option C:** Increase confidence when next chord is the resolution, but don't require it

2. Harmonic rhythm implementation:
   - The proposal mentions "rhythmically weak beats that resolve on strong beats"
   - Does `Score` object track beat positions and metric strength?
   - Should this be a future enhancement or implemented now?

3. Suspension overuse prevention:
   - What's the maximum frequency of sus chords? (e.g., no more than 30% of chords?)
   - Should there be a cooldown (e.g., at least 2 chords between sus suggestions)?

### 5.6 ChromaticApproachStrategy
**Proposal Reference:** Strategy Review, Section 6

**Questions:**
1. Sequential passing chords specification:
   - For roots a major 3rd apart (e.g., C to E), suggest two passing chords?
   - What chord qualities for the sequence?
   - Example: `C → C#dim7 → Ddim7 → E` or `C → C#7 → D7 → E`?

2. Maximum distance for chromatic approach:
   - Should there be a limit? (e.g., only for roots ≤5 semitones apart?)
   - Or should it work for any interval?

3. Voicing-awareness future plan:
   - This is marked as future enhancement
   - Should the current implementation prepare for this (e.g., extensible data structures)?
   - Or is this truly a later version 2.0 feature?

---

## 6. Implementation Priorities & Timeline

### 6.1 Phased Rollout
**General Question:**

The proposals cover a massive scope. What is the priority order?

**Suggested Phases:**
1. **Phase 1:** Core `Score` object and simplified `from_midi()` (no reharmonizer yet)
2. **Phase 2:** Enhanced `ChordAnalysis` and `ChordSuggestion` metadata
3. **Phase 3:** Basic `Reharmonizer` with single style profile
4. **Phase 4:** Multiple style profiles and complexity tuning
5. **Phase 5:** Strategy-specific improvements

**Question:** Is this phasing acceptable, or is there a different priority?

### 6.2 Backward Compatibility
**Questions:**
1. Should the current API remain available?
   - Keep `ChordProgression.from_symbols()`, etc. as-is?
   - Add new `Score`-based API alongside old API?
   - Or deprecate and remove old patterns?

2. Should there be a migration guide?
   - Document how to convert old code to new `Score`-based approach?

### 6.3 Testing & Validation Strategy
**Questions:**
1. How should reharmonization quality be validated?
   - Manual review of outputs by music theory expert?
   - Automated tests against known "good" reharmonizations?
   - User studies?

2. Should there be example/reference outputs?
   - E.g., "Here's 'Ode to Joy' reharmonized in jazz style with complexity=0.7"
   - These could serve as regression tests

---

## 7. Documentation & Examples

### 7.1 API Documentation
**Questions:**
1. What level of music theory knowledge should be assumed?
   - Should docstrings explain concepts like "Neapolitan sixth"?
   - Or assume user knows theory and just document parameters?

2. Should there be a theory glossary?
   - Separate docs explaining T-S-D, modal interchange, voice leading, etc.?

### 7.2 Example Complexity
**Questions:**
1. The "future DX" example is very simple (3 lines). Should there also be:
   - Intermediate examples showing customization?
   - Advanced examples showing custom style profiles?
   - Examples showing melody-aware reharmonization?

2. Should examples cover error cases?
   - What if MIDI has no clear chord progression?
   - What if key detection fails?
   - What if no suggestions meet the confidence threshold?

---

## Summary: High-Priority Clarifications Needed

Before implementation can begin, please provide specifications for:

1. **Score object fields** - Complete list of attributes and their types
2. **NoteEvent structure** - Required and optional fields
3. **Style profile definitions** - Which strategies enabled/disabled for jazz/classical/pop/rock/folk
4. **Complexity parameter semantics** - Precise definition of what 0.0, 0.5, and 1.0 mean
5. **ChordAnalysis complete spec** - All fields with types and meanings
6. **ChordSuggestion metadata** - All new fields with types and usage
7. **Reharmonizer search algorithm** - Which approach to use and why
8. **Implementation phasing** - Which features are MVP vs. future enhancements
9. **Default confidence values** - Specific numbers for each strategy in each style
10. **Backward compatibility policy** - Keep old API, deprecate, or break?

Please review and provide answers to these questions so implementation can proceed with confidence.
