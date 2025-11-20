# Expert Review of `halmoni` Chord Suggestion Strategies

This document provides a deep-dive analysis of each core suggestion strategy within the `halmoni` library. The review covers the underlying music theory, an analysis of the current implementation, its stylistic applicability, and suggestions for future improvements.

---

### 1. `TSDMovementStrategy` (Functional Harmony)

*   **Music Theory Concept:** This strategy is built on **functional harmony**, the bedrock of Western music from the 17th to the early 20th century. It classifies chords by their role: **Tonic (T)** for stability, **Subdominant (S)** for moderate tension moving away from tonic, and **Dominant (D)** for high tension resolving to tonic. The most syntactically powerful progression is `T → S → D → T`.

*   **Implementation Analysis:**
    *   **Strengths:** The strategy correctly maps diatonic scale degrees to their functions (e.g., I, vi are Tonic; IV, ii are Subdominant). Its core logic, which suggests stronger functional alternatives (like replacing `iii` with `I`) and inserting "bridge" chords to fix weak progressions (like inserting a Subdominant between a Tonic and Dominant), is excellent and mirrors how harmony is taught.
    *   **Weaknesses:** The model is rigid and stylistically biased towards the Common Practice Period. Its penalization of `D → S` (a "retrogression") is correct for classical theory but ignores the fact that this movement is a defining characteristic of modern pop and rock (e.g., the ubiquitous V-IV-I progression).

*   **Stylistic Applicability:**
    *   **Ideal for:** Analyzing and composing in the style of **Baroque/Classical/Romantic music (Bach, Mozart)**, traditional hymns, and simple folk tunes. It is a powerful tool for enforcing traditional harmonic "rules."
    *   **Problematic for:** **Modal Jazz, Blues, and most Rock music**, which often defy these functional rules. It would provide irrelevant or stylistically inappropriate suggestions for these genres.

*   **Suggested Improvements:**
    *   **Style-Dependent Syntax:** The scoring for `PREFERRED_PROGRESSIONS` should be a configurable "style profile." A "Rock" profile would not penalize the `V-IV` transition, while a "Classical" profile would.
    *   **Chromatic Function:** The strategy should be enhanced to recognize the function of chromatic chords. For example, a `V7/V` (a secondary dominant) should be identified as having a `Dominant` function, which would dramatically increase its analytical power in more complex music.

---

### 2. `NeapolitanStrategy`

*   **Music Theory Concept:** The Neapolitan Chord (N or ♭II) is a major triad built on the lowered second scale degree. It is a highly dramatic, chromatic pre-dominant chord that creates a strong desire to resolve to the Dominant (V). It is most famously used in its first inversion (N⁶) to create smooth, stepwise voice leading to the V chord.

*   **Implementation Analysis:**
    *   **Strengths:** The implementation is theoretically sound. It correctly identifies the ♭II root, prioritizes the first inversion (`neapolitan_sixth`), and boosts confidence when it precedes a Dominant chord, which is its primary use case.
    *   **Weaknesses:** The Neapolitan is a very potent and specific sound. The current implementation, if not carefully weighted, could suggest it in contexts where it would sound overly dramatic or academic.

*   **Stylistic Applicability:**
    *   **Ideal for:** **Romantic-era classical music (Beethoven, Chopin)**, dramatic film scoring, and certain subgenres of **Heavy Metal** that draw on classical harmony.
    *   **Avoid in:** **Jazz, Pop, Rock, Folk, and Blues.** A Neapolitan chord would sound exceptionally out of place in these styles. It is a "special effect" chord, not a general-purpose substitution.

*   **Suggested Improvements:**
    *   **Drastically Lower Base Confidence:** This strategy should have a very low default confidence. It should only be suggested when the engine detects other markers of a highly dramatic, minor-key context.
    *   **Mandatory Melody Check:** The defining ♭2 scale degree will clash severely with a natural 2 in the melody. The strategy should be heavily penalized or disabled entirely if this melodic clash is detected.

---

### 3. `BorrowedChordStrategy` (Modal Interchange)

*   **Music Theory Concept:** This involves "borrowing" chords from a parallel mode (e.g., using chords from C minor in the key of C major). This is a cornerstone of modern songwriting, used to add emotional depth and harmonic color without fundamentally destabilizing the key.

*   **Implementation Analysis:**
    *   **Strengths:** The code correctly implements the core concept of swapping chords with their parallel-mode counterparts. The specific inclusion of the ♭VII chord from the Mixolydian mode is a fantastic, practical addition that is highly relevant to modern pop and rock.
    *   **Weaknesses:** The current logic for when to suggest a borrowed chord is a bit general. Borrowed chords are most effective and common when they substitute for a diatonic chord that shares the same harmonic function.

*   **Stylistic Applicability:**
    *   **Ideal for:** **Pop, Rock, R&B, and Musical Theater.** The Beatles were masters of this technique. The `iv` chord in a major key is a staple of pop ballads, and the ♭VII is a defining sound of arena rock.
    *   **Also Common in:** **Jazz and late Romantic/20th-century classical music.**

*   **Suggested Improvements:**
    *   **Function-Driven Logic:** Confidence should be significantly higher when a borrowed chord replaces a diatonic chord of the *same function* (e.g., suggesting the minor `iv` to replace the major `IV` or diatonic `ii`).
    *   **Expand Modal Palette:** The engine could be expanded to borrow from more modes, such as suggesting a major `IV` chord in a minor key (a "Dorian" sound) or a `♭VI` chord.

---

### 4. `SubV7Strategy` (Tritone Substitution)

*   **Music Theory Concept:** A dominant 7th chord can be replaced by another dominant 7th chord whose root is a tritone away (e.g., `G7` can be swapped for `D♭7`). This works because the two chords share the same critical tension notes (the 3rd and 7th), allowing them to resolve in the same way while creating a descending chromatic bass line.

*   **Implementation Analysis:**
    *   **Strengths:** The implementation is correct. It properly identifies dominant chords, calculates the substituted root, and correctly includes a check for creating smooth chromatic bass motion, which is the primary motivation for this substitution.
    *   **Weaknesses:** The `_appears_to_be_jazz_context` heuristic is too simplistic and could lead to misapplication of this very style-specific technique.

*   **Stylistic Applicability:**
    *   **Ideal for:** **Jazz (especially Bebop and later styles).** This is a defining sound of the genre.
    *   **Also Used in:** **Modern R&B, Gospel, and Fusion,** where jazz harmony has a strong influence.
    *   **Avoid in:** **Almost all other genres.** A tritone substitution would sound completely out of place and confusing in a standard rock, pop, or classical piece.

*   **Suggested Improvements:**
    *   **Explicit Stylistic Activation:** This strategy should be "off" by default and only activated when the developer explicitly requests a "jazz" reharmonization style. It is too stylistically specific for general use.
    *   **Melody-Awareness:** The substitution must be checked against the melody. A melody note of G over a G7 chord is fine, but that same G becomes a clashing ♭5 over the substituted D♭7 chord.

---

### 5. `SuspendStrategy`

*   **Music Theory Concept:** A "sus" chord creates a moment of bright, open-sounding tension by replacing the 3rd of the chord with either the 4th (`sus4`) or the 2nd (`sus2`). This tension often, but not always, "resolves" to the standard version of the chord.

*   **Implementation Analysis:**
    *   **Strengths:** The strategy correctly identifies chords that are good candidates for suspension and can generate both `sus2` and `sus4` variants.
    *   **Weaknesses:** As our use case demonstrated, without proper constraints, this strategy can be overused, leading to a monotonous sound. The key to using suspensions effectively is often in the *rhythm* of the tension and release, which is a concept the current strategy lacks.

*   **Stylistic Applicability:**
    *   **Ideal for:** **Pop, Rock, and Folk music.** `sus` chords are a staple of guitar-driven music and create a feeling of uplifting openness.
    *   **Also Common in:** **Jazz,** where the `V7sus4` chord is a common and important sound, often functioning as a combination of `ii` and `V`.

*   **Suggested Improvements:**
    *   **Prioritize Resolution:** The strategy should be heavily biased towards suggesting `sus` chords that resolve. This is better modeled as an *insertion* of a brief `sus` chord that resolves into the original chord, rather than a simple replacement.
    *   **Harmonic Rhythm:** A more advanced implementation would suggest suspensions on rhythmically weak beats that resolve on strong beats, mimicking their most common use.

---

### 6. `ChromaticApproachStrategy`

*   **Music Theory Concept:** This involves inserting a chord (often a diminished 7th or a secondary dominant) to create a smooth, chromatic bass line that "approaches" the next chord from a semitone above or below.

*   **Implementation Analysis:**
    *   **Strengths:** This is a well-implemented and powerful insertion strategy. It correctly identifies opportunities between chords and prioritizes the most effective passing chord qualities (diminished 7th and dominant 7th).
    *   **Weaknesses:** The current implementation appears to focus on single passing chords. In many styles, a sequence of two or more chromatic chords can be used to connect chords that are further apart.

*   **Stylistic Applicability:**
    *   **Ideal for:** **Jazz (especially Swing and Big Band), Musical Theater, and Ragtime.** It is fundamental to creating the sense of constant forward motion found in these styles.
    *   **Also Used in:** Some forms of **R&B and Pop**, often as part of a bassline fill.
    *   **Rare in:** Most Rock, Folk, and early Classical music.

*   **Suggested Improvements:**
    *   **Sequential Passing:** The strategy could be expanded to suggest a sequence of two or more passing chords for connecting chords with roots that are a major 3rd apart or more.
    *   **Voicing-Awareness:** The true power of this technique lies in the smooth voice leading of the upper voices, not just the bass line. A future, more advanced version would benefit greatly from being able to suggest specific chord *voicings* that ensure maximum smoothness.
