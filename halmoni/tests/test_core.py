"""Comprehensive tests for core music theory classes."""

import pytest
from halmoni import Note, Interval, Chord, Scale, Key, ChordProgression, ChordVoicing


class TestNote:
    """Tests for the Note class."""

    def test_note_creation_from_string(self) -> None:
        """Test creating a note from pitch class and octave."""
        note = Note('C', 4)
        assert note.pitch_class == 'C'
        assert note.octave == 4
        assert note.midi_number == 60

    def test_note_creation_from_midi(self) -> None:
        """Test creating a note from MIDI number."""
        note = Note(60)
        assert note.midi_number == 60
        assert note.pitch_class == 'C'
        assert note.octave == 4

    def test_note_with_sharps(self) -> None:
        """Test notes with sharp accidentals."""
        note = Note('F#', 4)
        assert note.pitch_class == 'F#'
        assert note.midi_number == 66

    def test_note_with_flats(self) -> None:
        """Test notes with flat accidentals."""
        note = Note('Bb', 3)
        assert note.pitch_class == 'Bb'
        assert note.midi_number == 46

    def test_note_frequency(self) -> None:
        """Test frequency calculation (A4 = 440Hz)."""
        a4 = Note('A', 4)
        assert abs(a4.frequency - 440.0) < 0.01

    def test_note_transpose(self) -> None:
        """Test transposing notes."""
        c4 = Note('C', 4)
        d4 = c4.transpose(2)
        assert d4.midi_number == 62
        assert d4.pitch_class == 'D'

    def test_note_transpose_out_of_range(self) -> None:
        """Test transpose raises error when out of MIDI range."""
        note = Note(120)
        with pytest.raises(ValueError):
            note.transpose(10)

    def test_enharmonic_equivalent(self) -> None:
        """Test getting enharmonic equivalents."""
        c_sharp = Note('C#', 4)
        d_flat = c_sharp.enharmonic_equivalent()
        assert d_flat is not None
        assert d_flat.pitch_class == 'Db'
        assert d_flat.midi_number == c_sharp.midi_number

    def test_natural_note_no_enharmonic(self) -> None:
        """Test that natural notes have no enharmonic equivalent."""
        c = Note('C', 4)
        assert c.enharmonic_equivalent() is None

    def test_note_comparison(self) -> None:
        """Test note comparison operators."""
        c4 = Note('C', 4)
        c5 = Note('C', 5)
        d4 = Note('D', 4)

        assert c4 < c5
        assert c4 < d4
        assert not c4 < c4

    def test_note_equality(self) -> None:
        """Test note equality."""
        c4_1 = Note('C', 4)
        c4_2 = Note(60)
        assert c4_1 == c4_2

    def test_note_hashing(self) -> None:
        """Test that notes can be hashed."""
        note_set = {Note('C', 4), Note('D', 4), Note('C', 4)}
        assert len(note_set) == 2

    def test_note_string_representation(self) -> None:
        """Test note string representations."""
        note = Note('F#', 4)
        assert str(note) == 'F#4'
        assert 'F#' in repr(note)

    def test_invalid_pitch_class(self) -> None:
        """Test that invalid pitch classes raise errors."""
        with pytest.raises(ValueError):
            Note('H', 4)
        with pytest.raises(ValueError):
            Note('C##', 4)

    def test_invalid_octave(self) -> None:
        """Test that invalid octaves raise errors."""
        with pytest.raises(ValueError):
            Note('C', -1)
        with pytest.raises(ValueError):
            Note('C', 11)

    def test_missing_octave(self) -> None:
        """Test that missing octave raises error."""
        with pytest.raises(ValueError):
            Note('C')


class TestInterval:
    """Tests for the Interval class."""

    def test_interval_creation(self) -> None:
        """Test creating an interval from semitones."""
        interval = Interval(7)
        assert interval.semitones == 7
        assert interval.simple_semitones == 7

    def test_interval_from_notes(self) -> None:
        """Test creating interval from two notes."""
        c4 = Note('C', 4)
        g4 = Note('G', 4)
        interval = Interval.from_notes(c4, g4)
        assert interval.semitones == 7

    def test_interval_names(self) -> None:
        """Test interval name properties."""
        p5 = Interval(7)
        assert p5.name == "Perfect 5th"
        assert p5.short_name == "P5"

    def test_interval_from_name(self) -> None:
        """Test creating interval from name."""
        p5 = Interval.from_name('P5')
        assert p5.semitones == 7

        m3 = Interval.from_name('m3')
        assert m3.semitones == 3

        M7 = Interval.from_name('M7')
        assert M7.semitones == 11

    def test_compound_intervals(self) -> None:
        """Test compound intervals (over an octave)."""
        interval = Interval(14)  # Major 9th
        assert interval.octaves == 1
        assert interval.simple_semitones == 2

    def test_interval_inversion(self) -> None:
        """Test interval inversion."""
        p5 = Interval(7)
        p4 = p5.invert()
        assert p4.simple_semitones == 5

    def test_interval_addition(self) -> None:
        """Test adding intervals."""
        m3 = Interval(3)
        M3 = Interval(4)
        p5 = m3.add(M3)
        assert p5.semitones == 7

    def test_interval_subtraction(self) -> None:
        """Test subtracting intervals."""
        p5 = Interval(7)
        M3 = Interval(4)
        m3 = p5.subtract(M3)
        assert m3.semitones == 3

    def test_interval_consonance(self) -> None:
        """Test interval consonance checking."""
        assert Interval(0).is_consonant()  # Unison
        assert Interval(4).is_consonant()  # M3
        assert Interval(7).is_consonant()  # P5
        assert not Interval(1).is_consonant()  # m2
        assert not Interval(6).is_consonant()  # Tritone

    def test_interval_perfect(self) -> None:
        """Test perfect interval checking."""
        assert Interval(0).is_perfect()  # Unison
        assert Interval(5).is_perfect()  # P4
        assert Interval(7).is_perfect()  # P5
        assert not Interval(4).is_perfect()  # M3

    def test_interval_equality(self) -> None:
        """Test interval equality."""
        i1 = Interval(7)
        i2 = Interval.from_name('P5')
        assert i1 == i2

    def test_interval_hashing(self) -> None:
        """Test interval hashing."""
        interval_set = {Interval(7), Interval(5), Interval(7)}
        assert len(interval_set) == 2

    def test_interval_from_name_diminished(self) -> None:
        """Test creating diminished intervals."""
        dim5 = Interval.from_name('d5')
        assert dim5.semitones == 6  # Tritone

    def test_interval_from_name_augmented(self) -> None:
        """Test creating augmented intervals."""
        aug4 = Interval.from_name('A4')
        assert aug4.semitones == 6  # Tritone

    def test_interval_from_name_compound(self) -> None:
        """Test creating compound intervals (> octave)."""
        ninth = Interval.from_name('M9')
        assert ninth.semitones == 14  # Octave + major 2nd

    def test_interval_from_name_invalid_quality(self) -> None:
        """Test that invalid quality raises error."""
        with pytest.raises(ValueError):
            Interval.from_name('X5')  # Invalid quality

    def test_interval_from_name_invalid_number(self) -> None:
        """Test that invalid interval number raises error."""
        with pytest.raises(ValueError):
            Interval.from_name('M')  # No number

    def test_interval_octaves_property(self) -> None:
        """Test getting octaves from interval."""
        octave = Interval(12)
        assert octave.octaves == 1

        two_octaves = Interval(24)
        assert two_octaves.octaves == 2

    def test_interval_short_name(self) -> None:
        """Test getting short interval names."""
        p5 = Interval(7)
        assert p5.short_name == 'P5'

        m3 = Interval(3)
        assert m3.short_name == 'm3'

    def test_interval_string_representation(self) -> None:
        """Test interval string representations."""
        p5 = Interval(7)
        assert 'Perfect 5th' in str(p5) or '5' in str(p5)
        assert 'Interval' in repr(p5)

    def test_interval_from_name_perfect_unison(self) -> None:
        """Test creating perfect unison."""
        unison = Interval.from_name('P1')
        assert unison.semitones == 0

    def test_interval_from_name_octave(self) -> None:
        """Test creating octave."""
        octave = Interval.from_name('P8')
        assert octave.semitones == 12

    def test_interval_from_name_cannot_make_perfect(self) -> None:
        """Test that certain intervals cannot be perfect."""
        with pytest.raises(ValueError):
            Interval.from_name('P3')  # 3rd cannot be perfect

    def test_interval_from_name_cannot_make_minor(self) -> None:
        """Test that certain intervals cannot be minor."""
        with pytest.raises(ValueError):
            Interval.from_name('m5')  # 5th cannot be minor (it's dim or aug)

    def test_interval_simple_semitones_property(self) -> None:
        """Test simple semitones property."""
        ninth = Interval(14)  # Compound interval
        assert ninth.simple_semitones == 2  # Within octave
        assert ninth.octaves == 1


class TestChord:
    """Tests for the Chord class."""

    def test_chord_creation(self, c_note: Note) -> None:
        """Test creating a chord."""
        chord = Chord(c_note, 'major')
        assert chord.root == c_note
        assert chord.quality == 'major'

    def test_chord_from_symbol(self) -> None:
        """Test creating chord from symbol."""
        c_major = Chord.from_symbol('C')
        assert c_major.root.pitch_class == 'C'
        assert c_major.quality == 'major'

        dm7 = Chord.from_symbol('Dm7')
        assert dm7.root.pitch_class == 'D'
        assert dm7.quality == 'minor7'

    def test_chord_notes(self) -> None:
        """Test getting chord notes."""
        c_major = Chord.from_symbol('C')
        notes = c_major.notes
        pitch_classes = [n.pitch_class for n in notes]
        assert 'C' in pitch_classes
        assert 'E' in pitch_classes
        assert 'G' in pitch_classes

    def test_chord_symbol(self) -> None:
        """Test chord symbol generation."""
        chord = Chord.from_symbol('Gmaj7')
        assert chord.symbol == 'Gmaj7'

    def test_slash_chord(self) -> None:
        """Test slash chords."""
        chord = Chord.from_symbol('C/E')
        assert chord.root.pitch_class == 'C'
        assert chord.bass.pitch_class == 'E'
        assert chord.symbol == 'C/E'

    def test_chord_contains_note(self) -> None:
        """Test checking if chord contains a note."""
        c_major = Chord.from_symbol('C')
        assert c_major.contains_note(Note('C', 4))
        assert c_major.contains_note(Note('E', 4))
        assert not c_major.contains_note(Note('F', 4))

    def test_chord_tone_function(self) -> None:
        """Test getting chord tone function."""
        c_major = Chord.from_symbol('C')
        assert c_major.get_chord_tone_function(Note('C', 4)) == 'root'
        assert c_major.get_chord_tone_function(Note('E', 4)) == '3'
        assert c_major.get_chord_tone_function(Note('G', 4)) == '5'

    def test_extended_chords(self) -> None:
        """Test extended chords."""
        cmaj9 = Chord.from_symbol('Cmaj9')
        assert cmaj9.quality == 'major9'
        pitch_classes = cmaj9.pitch_classes
        assert 'D' in pitch_classes  # 9th

    def test_invalid_chord_quality(self) -> None:
        """Test that invalid chord quality raises error."""
        with pytest.raises(ValueError):
            Chord(Note('C', 4), 'invalid_quality')

    def test_chord_equality(self) -> None:
        """Test chord equality."""
        c1 = Chord.from_symbol('C')
        c2 = Chord.from_symbol('C')
        am = Chord.from_symbol('Am')
        assert c1 == c2
        assert c1 != am

    def test_chord_hashing(self) -> None:
        """Test that chords can be hashed."""
        chord_set = {Chord.from_symbol('C'), Chord.from_symbol('F'), Chord.from_symbol('C')}
        assert len(chord_set) == 2

    def test_chord_with_various_symbols(self) -> None:
        """Test parsing various chord symbol formats."""
        # Test different major notations
        c_maj1 = Chord.from_symbol('C')
        c_maj2 = Chord.from_symbol('CM')
        assert c_maj1.quality == c_maj2.quality

        # Test different seventh notations
        c7 = Chord.from_symbol('C7')
        assert c7.quality == 'dominant7'

        # Test sus chords
        csus4 = Chord.from_symbol('Csus4')
        assert csus4.quality == 'sus4'

    def test_chord_diminished_variations(self) -> None:
        """Test diminished chord variations."""
        cdim = Chord.from_symbol('Cdim')
        assert cdim.quality == 'diminished'

        cdim7 = Chord.from_symbol('Cdim7')
        assert cdim7.quality == 'diminished7'

        cm7b5 = Chord.from_symbol('Cm7b5')
        assert cm7b5.quality == 'half_diminished7'

    def test_chord_augmented(self) -> None:
        """Test augmented chord."""
        caug = Chord.from_symbol('Caug')
        assert caug.quality == 'augmented'

    def test_chord_get_tone_function_for_minor(self) -> None:
        """Test getting chord tone function for minor chord."""
        am = Chord.from_symbol('Am')
        assert am.get_chord_tone_function(Note('A', 4)) == 'root'
        assert am.get_chord_tone_function(Note('C', 4)) == 'b3'

    def test_chord_tone_function_non_chord_tone(self) -> None:
        """Test getting function for non-chord tone."""
        c_major = Chord.from_symbol('C')
        result = c_major.get_chord_tone_function(Note('F', 4))
        assert result is not None  # Should return some interval name

    def test_chord_inversion(self) -> None:
        """Test creating chord inversions."""
        c_major = Chord.from_symbol('C')
        first_inversion = c_major.invert(1)
        assert first_inversion.bass_note.pitch_class == 'E'

        second_inversion = c_major.invert(2)
        assert second_inversion.bass_note.pitch_class == 'G'

    def test_chord_invalid_symbol(self) -> None:
        """Test that invalid chord symbol raises error."""
        with pytest.raises(ValueError):
            Chord.from_symbol('')  # Empty symbol

    def test_chord_with_accidentals_in_symbol(self) -> None:
        """Test parsing chords with sharps and flats."""
        f_sharp = Chord.from_symbol('F#')
        assert f_sharp.root.pitch_class == 'F#'

        b_flat_m = Chord.from_symbol('Bbm')
        assert b_flat_m.root.pitch_class == 'Bb'
        assert b_flat_m.quality == 'minor'


class TestScale:
    """Tests for the Scale class."""

    def test_scale_creation(self, c_note: Note) -> None:
        """Test creating a scale."""
        scale = Scale(c_note, 'major')
        assert scale.tonic == c_note
        assert scale.scale_type == 'major'

    def test_major_scale_pattern(self) -> None:
        """Test major scale pattern."""
        c_major = Scale.major(Note('C', 4))
        pitch_classes = c_major.pitch_classes
        expected = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        assert pitch_classes == expected

    def test_minor_scale_pattern(self) -> None:
        """Test minor scale pattern."""
        a_minor = Scale.minor(Note('A', 4))
        pitch_classes = a_minor.pitch_classes
        expected = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
        assert pitch_classes == expected

    def test_scale_get_degree(self) -> None:
        """Test getting scale degree."""
        c_major = Scale.major(Note('C', 4))
        assert c_major.get_degree(1).pitch_class == 'C'
        assert c_major.get_degree(5).pitch_class == 'G'

    def test_scale_get_note_degree(self) -> None:
        """Test getting degree of a note."""
        c_major = Scale.major(Note('C', 4))
        assert c_major.get_note_degree(Note('C', 4)) == 1
        assert c_major.get_note_degree(Note('E', 4)) == 3
        assert c_major.get_note_degree(Note('G', 4)) == 5

    def test_scale_contains_note(self) -> None:
        """Test checking if scale contains note."""
        c_major = Scale.major(Note('C', 4))
        assert c_major.contains_note(Note('D', 4))
        assert not c_major.contains_note(Note('D#', 4))

    def test_scale_chord_for_degree(self) -> None:
        """Test getting chord for scale degree."""
        c_major = Scale.major(Note('C', 4))
        chord = c_major.get_chord_for_degree(1)
        assert chord.root.pitch_class == 'C'
        assert chord.quality == 'major'

        chord_ii = c_major.get_chord_for_degree(2)
        assert chord_ii.root.pitch_class == 'D'
        assert chord_ii.quality == 'minor'

    def test_modal_scales(self) -> None:
        """Test modal scales."""
        d_dorian = Scale(Note('D', 4), 'dorian')
        expected_pattern = [0, 2, 3, 5, 7, 9, 10]
        assert d_dorian.pattern == expected_pattern

    def test_invalid_scale_type(self) -> None:
        """Test that invalid scale type raises error."""
        with pytest.raises(ValueError):
            Scale(Note('C', 4), 'invalid_scale')

    def test_scale_from_mode(self) -> None:
        """Test creating scale from mode."""
        d_dorian = Scale.from_mode(Note('D', 4), 1, 'major')  # 2nd mode of major
        assert d_dorian.tonic.pitch_class == 'D'
        # Dorian pattern: W-H-W-W-W-H-W (0,2,3,5,7,9,10)
        assert d_dorian.pattern == [0, 2, 3, 5, 7, 9, 10]

    def test_scale_from_mode_lydian(self) -> None:
        """Test creating Lydian mode."""
        f_lydian = Scale.from_mode(Note('F', 4), 3, 'major')  # 4th mode
        assert f_lydian.tonic.pitch_class == 'F'
        # Lydian has raised 4th
        pitch_classes = f_lydian.pitch_classes
        assert 'B' in pitch_classes  # Should have B natural (raised 4th)

    def test_scale_get_degree_invalid(self) -> None:
        """Test getting invalid scale degree raises error."""
        c_major = Scale.major(Note('C', 4))
        with pytest.raises(ValueError):
            c_major.get_degree(0)  # 1-based indexing
        with pytest.raises(ValueError):
            c_major.get_degree(8)  # Only 7 notes

    def test_scale_get_note_degree_not_in_scale(self) -> None:
        """Test getting degree of note not in scale."""
        c_major = Scale.major(Note('C', 4))
        result = c_major.get_note_degree(Note('C#', 4))
        assert result is None

    def test_scale_get_chord_seventh(self) -> None:
        """Test getting seventh chord for scale degree."""
        c_major = Scale.major(Note('C', 4))
        chord = c_major.get_chord_for_degree(5, 'seventh')
        assert chord.root.pitch_class == 'G'
        assert chord.quality == 'dominant7'

    def test_scale_get_chord_invalid_type(self) -> None:
        """Test getting chord with invalid chord type."""
        c_major = Scale.major(Note('C', 4))
        with pytest.raises(ValueError):
            c_major.get_chord_for_degree(1, 'invalid')

    def test_scale_get_relative_scale(self) -> None:
        """Test getting relative scale."""
        c_major = Scale.major(Note('C', 4))
        a_minor = c_major.get_relative_scale('natural_minor')
        assert a_minor.tonic.pitch_class == 'A'
        assert a_minor.scale_type == 'natural_minor'

    def test_scale_get_parallel_scale(self) -> None:
        """Test getting parallel scale."""
        c_major = Scale.major(Note('C', 4))
        c_minor = c_major.get_parallel_scale('natural_minor')
        assert c_minor.tonic.pitch_class == 'C'
        assert c_minor.scale_type == 'natural_minor'

    def test_scale_pentatonic_major(self) -> None:
        """Test pentatonic major scale."""
        c_pent = Scale(Note('C', 4), 'pentatonic_major')
        assert len(c_pent.notes) == 5
        pitch_classes = c_pent.pitch_classes
        assert 'C' in pitch_classes
        assert 'D' in pitch_classes
        assert 'E' in pitch_classes
        assert 'F' not in pitch_classes  # No half steps

    def test_scale_blues(self) -> None:
        """Test blues scale."""
        c_blues = Scale(Note('C', 4), 'blues')
        assert len(c_blues.notes) == 6
        pitch_classes = c_blues.pitch_classes
        assert 'C' in pitch_classes
        assert 'Eb' in pitch_classes or 'D#' in pitch_classes  # b3

    def test_scale_harmonic_minor(self) -> None:
        """Test harmonic minor scale."""
        a_harm_minor = Scale(Note('A', 4), 'harmonic_minor')
        pitch_classes = a_harm_minor.pitch_classes
        # Harmonic minor has raised 7th
        assert 'G#' in pitch_classes or 'Ab' in pitch_classes

    def test_scale_equality(self) -> None:
        """Test scale equality."""
        c_major1 = Scale.major(Note('C', 4))
        c_major2 = Scale.major(Note('C', 5))
        d_major = Scale.major(Note('D', 4))
        assert c_major1 == c_major2  # Same scale, different octave
        assert c_major1 != d_major

    def test_scale_string_representation(self) -> None:
        """Test scale string representation."""
        c_major = Scale.major(Note('C', 4))
        string_repr = str(c_major)
        assert 'C' in string_repr
        assert 'major' in string_repr.lower() or 'Major' in string_repr


class TestKey:
    """Tests for the Key class."""

    def test_key_creation(self, c_note: Note) -> None:
        """Test creating a key."""
        key = Key(c_note, 'major')
        assert key.tonic == c_note
        assert key.mode == 'major'

    def test_key_signature(self) -> None:
        """Test key signature calculation."""
        c_major = Key(Note('C', 4), 'major')
        assert c_major.signature == 0

        g_major = Key(Note('G', 4), 'major')
        assert g_major.signature == 1

        f_major = Key(Note('F', 4), 'major')
        assert f_major.signature == -1

    def test_key_accidentals(self) -> None:
        """Test getting accidentals in key signature."""
        g_major = Key(Note('G', 4), 'major')
        assert g_major.accidentals == ['F#']

        d_major = Key(Note('D', 4), 'major')
        assert g_major.accidentals == ['F#']
        assert d_major.accidentals == ['F#', 'C#']

    def test_relative_key(self) -> None:
        """Test getting relative key."""
        c_major = Key(Note('C', 4), 'major')
        a_minor = c_major.relative_key
        assert a_minor.tonic.pitch_class == 'A'
        assert a_minor.mode == 'minor'

    def test_parallel_key(self) -> None:
        """Test getting parallel key."""
        c_major = Key(Note('C', 4), 'major')
        c_minor = c_major.parallel_key
        assert c_minor.tonic.pitch_class == 'C'
        assert c_minor.mode == 'minor'

    def test_dominant_key(self) -> None:
        """Test getting dominant key."""
        c_major = Key(Note('C', 4), 'major')
        g_major = c_major.get_dominant_key()
        assert g_major.tonic.pitch_class == 'G'

    def test_subdominant_key(self) -> None:
        """Test getting subdominant key."""
        c_major = Key(Note('C', 4), 'major')
        f_major = c_major.get_subdominant_key()
        assert f_major.tonic.pitch_class == 'F'

    def test_closely_related_keys(self) -> None:
        """Test getting closely related keys."""
        c_major = Key(Note('C', 4), 'major')
        related = c_major.get_closely_related_keys()
        assert len(related) == 5

    def test_analyze_chord(self, c_major_key: Key) -> None:
        """Test chord analysis in key context."""
        c_chord = Chord.from_symbol('C')
        analysis = c_major_key.analyze_chord(c_chord)
        assert analysis['degree'] == 1
        assert analysis['function'] == 'tonic'
        assert analysis['is_diatonic'] is True

    def test_analyze_non_diatonic_chord(self, c_major_key: Key) -> None:
        """Test analyzing non-diatonic chord."""
        d_flat_chord = Chord.from_symbol('Db')
        analysis = c_major_key.analyze_chord(d_flat_chord)
        assert analysis['is_diatonic'] is False

    def test_key_equality(self) -> None:
        """Test key equality."""
        c1 = Key(Note('C', 4), 'major')
        c2 = Key(Note('C', 5), 'major')  # Different octave
        assert c1 == c2  # Should be equal (same pitch class)

    def test_key_from_signature(self) -> None:
        """Test creating key from signature."""
        # 1 sharp = G major
        g_major = Key.from_signature(1, 'major')
        assert g_major.tonic.pitch_class == 'G'
        assert g_major.mode == 'major'

        # 1 sharp = E minor
        e_minor = Key.from_signature(1, 'minor')
        assert e_minor.tonic.pitch_class == 'E'
        assert e_minor.mode == 'minor'

    def test_key_invalid_mode(self) -> None:
        """Test creating key with invalid mode raises error."""
        with pytest.raises(ValueError):
            Key(Note('C', 4), 'lydian')  # Only major/minor supported

    def test_key_get_seventh_chord(self, c_major_key: Key) -> None:
        """Test getting seventh chord for degree."""
        chord = c_major_key.get_seventh_chord_for_degree(5)
        assert chord.root.pitch_class == 'G'
        assert chord.quality == 'dominant7'

    def test_key_tonicize(self, c_major_key: Key) -> None:
        """Test tonicizing a scale degree."""
        # Tonicize the 5th degree (G)
        g_key = c_major_key.tonicize(5)
        assert g_key.tonic.pitch_class == 'G'
        assert g_key.mode == 'major'

    def test_key_contains_note(self, c_major_key: Key) -> None:
        """Test checking if key contains note."""
        assert c_major_key.contains_note(Note('E', 4))
        assert not c_major_key.contains_note(Note('Eb', 4))

    def test_key_accidentals_flats(self) -> None:
        """Test accidentals for flat keys."""
        f_major = Key(Note('F', 4), 'major')
        assert 'Bb' in f_major.accidentals

        bb_major = Key(Note('Bb', 4), 'major')
        assert len(bb_major.accidentals) == 2

    def test_key_string_representation(self, c_major_key: Key) -> None:
        """Test key string representation."""
        string_repr = str(c_major_key)
        assert 'C' in string_repr
        assert 'Major' in string_repr

    def test_key_analyze_chord_with_root_not_in_scale(self, c_major_key: Key) -> None:
        """Test analyzing chord with root not in scale."""
        # Db is not in C major
        chord = Chord.from_symbol('Db')
        analysis = c_major_key.analyze_chord(chord)
        assert analysis['is_diatonic'] is False
        assert analysis['degree'] is None

    def test_key_hashing(self, c_major_key: Key) -> None:
        """Test key hashing."""
        key_set = {c_major_key, Key(Note('C', 5), 'major'), Key(Note('D', 4), 'major')}
        assert len(key_set) == 2  # C major at different octaves should be same

    def test_key_repr(self, c_major_key: Key) -> None:
        """Test key repr."""
        repr_str = repr(c_major_key)
        assert 'C' in repr_str
        assert 'major' in repr_str

    def test_key_chord_for_degree(self, c_major_key: Key) -> None:
        """Test getting diatonic triads for each degree."""
        # I chord should be C major
        i_chord = c_major_key.get_chord_for_degree(1)
        assert i_chord.root.pitch_class == 'C'
        assert i_chord.quality == 'major'

        # ii chord should be D minor
        ii_chord = c_major_key.get_chord_for_degree(2)
        assert ii_chord.root.pitch_class == 'D'
        assert ii_chord.quality == 'minor'

    def test_key_analyze_non_diatonic_non_chord_tones(self, c_major_key: Key) -> None:
        """Test analysis includes non-chord tones."""
        # Chromatic chord - has notes outside key
        chord = Chord.from_symbol('Dbmaj7')
        analysis = c_major_key.analyze_chord(chord)
        assert len(analysis['non_chord_tones']) > 0


class TestChordProgression:
    """Tests for the ChordProgression class."""

    def test_progression_creation(self) -> None:
        """Test creating a chord progression."""
        chords = [Chord.from_symbol('C'), Chord.from_symbol('Am'), Chord.from_symbol('F'), Chord.from_symbol('G')]
        prog = ChordProgression(chords)
        assert len(prog) == 4

    def test_progression_from_symbols(self) -> None:
        """Test creating progression from symbols."""
        prog = ChordProgression.from_symbols(['C', 'Am', 'F', 'G'])
        assert len(prog) == 4
        assert prog[0].symbol == 'C'

    def test_progression_from_roman_numerals(self, c_major_key: Key) -> None:
        """Test creating progression from Roman numerals."""
        prog = ChordProgression.from_roman_numerals(['I', 'vi', 'IV', 'V'], c_major_key)
        assert len(prog) == 4
        assert prog[0].root.pitch_class == 'C'
        assert prog[1].root.pitch_class == 'A'

    def test_progression_chord_symbols(self, simple_progression: ChordProgression) -> None:
        """Test getting chord symbols."""
        symbols = simple_progression.chord_symbols
        assert symbols == ['C', 'Am', 'F', 'G']

    def test_progression_unique_chords(self) -> None:
        """Test getting unique chords."""
        prog = ChordProgression.from_symbols(['C', 'Am', 'C', 'G'])
        unique = prog.unique_chords
        assert len(unique) == 3

    def test_progression_transpose(self, simple_progression: ChordProgression) -> None:
        """Test transposing progression."""
        interval = Interval(2)  # Whole step up
        transposed = simple_progression.transpose(interval)
        assert transposed[0].root.pitch_class == 'D'

    def test_progression_substitute_chord(self, simple_progression: ChordProgression) -> None:
        """Test substituting a chord."""
        new_chord = Chord.from_symbol('Dm')
        new_prog = simple_progression.substitute_chord(1, new_chord)
        assert new_prog[1].symbol == 'Dm'
        assert simple_progression[1].symbol == 'Am'  # Original unchanged

    def test_progression_insert_chord(self, simple_progression: ChordProgression) -> None:
        """Test inserting a chord."""
        new_chord = Chord.from_symbol('Dm')
        new_prog = simple_progression.insert_chord(1, new_chord)
        assert len(new_prog) == 5
        assert new_prog[1].symbol == 'Dm'

    def test_progression_repeat(self, simple_progression: ChordProgression) -> None:
        """Test repeating progression."""
        repeated = simple_progression.repeat(2)
        assert len(repeated) == 8

    def test_progression_extend(self) -> None:
        """Test extending progression."""
        prog1 = ChordProgression.from_symbols(['C', 'Am'])
        prog2 = ChordProgression.from_symbols(['F', 'G'])
        extended = prog1.extend(prog2)
        assert len(extended) == 4

    def test_progression_harmonic_rhythm(self, simple_progression: ChordProgression) -> None:
        """Test harmonic rhythm analysis."""
        analysis = simple_progression.analyze_harmonic_rhythm()
        assert analysis['total_duration'] == 4.0
        assert analysis['average_chord_duration'] == 1.0

    def test_progression_chord_transitions(self, simple_progression: ChordProgression) -> None:
        """Test analyzing chord transitions."""
        transitions = simple_progression.get_chord_transitions()
        assert len(transitions) == 3  # 4 chords = 3 transitions

    def test_empty_progression_raises_error(self) -> None:
        """Test that empty progression raises error."""
        with pytest.raises(ValueError):
            ChordProgression([])

    def test_progression_with_durations(self) -> None:
        """Test progression with custom durations."""
        chords = [Chord.from_symbol('C'), Chord.from_symbol('F')]
        durations = [2.0, 2.0]
        prog = ChordProgression(chords, durations=durations)
        assert prog.total_duration == 4.0

    def test_progression_durations_mismatch_error(self) -> None:
        """Test that duration count mismatch raises error."""
        chords = [Chord.from_symbol('C'), Chord.from_symbol('F')]
        durations = [2.0]  # Only 1 duration for 2 chords
        with pytest.raises(ValueError):
            ChordProgression(chords, durations=durations)

    def test_progression_get_roman_numerals(self, c_major_key: Key) -> None:
        """Test getting Roman numeral analysis."""
        prog = ChordProgression.from_symbols(['C', 'F', 'G'], key=c_major_key)
        numerals = prog.get_roman_numerals()
        assert 'I' in numerals[0]
        assert 'IV' in numerals[1]
        assert 'V' in numerals[2]

    def test_progression_get_roman_numerals_no_key_error(self) -> None:
        """Test that getting roman numerals without key raises error."""
        prog = ChordProgression.from_symbols(['C', 'F', 'G'])
        with pytest.raises(ValueError):
            prog.get_roman_numerals()

    def test_progression_analyze_voice_leading(self) -> None:
        """Test voice leading analysis."""
        prog = ChordProgression.from_symbols(['C', 'Am', 'F'])
        analysis = prog.analyze_voice_leading()
        assert 'smooth_voice_leading' in analysis
        assert 'large_leaps' in analysis
        assert 'common_tones' in analysis

    def test_progression_iterate(self, simple_progression: ChordProgression) -> None:
        """Test iterating over progression."""
        chords = list(simple_progression)
        assert len(chords) == 4

    def test_progression_indexing(self, simple_progression: ChordProgression) -> None:
        """Test indexing into progression."""
        first_chord = simple_progression[0]
        assert first_chord.symbol == 'C'

    def test_progression_set_chord(self, simple_progression: ChordProgression) -> None:
        """Test setting chord by index."""
        new_chord = Chord.from_symbol('Dm')
        simple_progression[1] = new_chord
        assert simple_progression[1].symbol == 'Dm'

    def test_progression_equality(self) -> None:
        """Test progression equality."""
        prog1 = ChordProgression.from_symbols(['C', 'F', 'G'])
        prog2 = ChordProgression.from_symbols(['C', 'F', 'G'])
        prog3 = ChordProgression.from_symbols(['C', 'F', 'Am'])
        assert prog1 == prog2
        assert prog1 != prog3

    def test_progression_string_representation(self, simple_progression: ChordProgression) -> None:
        """Test progression string representation."""
        string_repr = str(simple_progression)
        assert 'C' in string_repr
        assert '-' in string_repr  # Chords separated by dashes

    def test_progression_with_varied_durations_string(self) -> None:
        """Test progression string with non-uniform durations."""
        prog = ChordProgression.from_symbols(['C', 'F'], durations=[2.0, 1.5])
        string_repr = str(prog)
        assert 'C' in string_repr
        assert '2' in string_repr or '1.5' in string_repr or '(' in string_repr

    def test_progression_analyze_voice_leading_with_voicings(self) -> None:
        """Test voice leading analysis with custom voicings."""
        from halmoni import ChordVoicing
        prog = ChordProgression.from_symbols(['C', 'F'])
        c_voicing = ChordVoicing(prog[0], [Note('C', 3), Note('E', 3), Note('G', 3)])
        f_voicing = ChordVoicing(prog[1], [Note('C', 3), Note('F', 3), Note('A', 3)])
        analysis = prog.analyze_voice_leading(voicings=[c_voicing, f_voicing])
        assert 'smooth_voice_leading' in analysis
        assert 'common_tones' in analysis

    def test_progression_transpose_with_key(self, c_major_key: Key) -> None:
        """Test transposing progression with key."""
        prog = ChordProgression.from_symbols(['C', 'F'], key=c_major_key)
        transposed = prog.transpose(Interval(2))  # Whole step up
        assert transposed.key is not None
        assert transposed.key.tonic.pitch_class == 'D'


class TestChordVoicing:
    """Tests for the ChordVoicing class."""

    def test_voicing_creation(self, c_major_chord: Chord) -> None:
        """Test creating a chord voicing."""
        notes = [Note('C', 3), Note('E', 3), Note('G', 3), Note('C', 4)]
        voicing = ChordVoicing(c_major_chord, notes)
        assert len(voicing.notes) == 4

    def test_voicing_bass_note(self, c_major_chord: Chord) -> None:
        """Test getting bass note."""
        notes = [Note('G', 2), Note('C', 3), Note('E', 3)]
        voicing = ChordVoicing(c_major_chord, notes)
        assert voicing.bass_note.pitch_class == 'G'

    def test_voicing_soprano_note(self, c_major_chord: Chord) -> None:
        """Test getting soprano note."""
        notes = [Note('C', 3), Note('E', 3), Note('G', 3)]
        voicing = ChordVoicing(c_major_chord, notes)
        assert voicing.soprano_note.pitch_class == 'G'

    def test_voicing_range(self, c_major_chord: Chord) -> None:
        """Test getting voicing range."""
        notes = [Note('C', 3), Note('E', 3), Note('G', 4)]
        voicing = ChordVoicing(c_major_chord, notes)
        range_interval = voicing.range
        assert range_interval.semitones >= 12  # At least an octave

    def test_voicing_intervals_from_bass(self, c_major_chord: Chord) -> None:
        """Test getting intervals from bass."""
        notes = [Note('C', 3), Note('E', 3), Note('G', 3)]
        voicing = ChordVoicing(c_major_chord, notes)
        intervals = voicing.get_intervals_from_bass()
        assert len(intervals) == 3
        assert intervals[0].semitones == 0  # Unison with bass

    def test_voicing_invalid_notes(self, c_major_chord: Chord) -> None:
        """Test that voicing with invalid notes raises error."""
        # F is not in C major chord
        notes = [Note('C', 3), Note('F', 3), Note('G', 3)]
        with pytest.raises(ValueError):
            ChordVoicing(c_major_chord, notes)

    def test_voicing_string_representation(self, c_major_chord: Chord) -> None:
        """Test voicing string representation."""
        notes = [Note('C', 3), Note('E', 3), Note('G', 3)]
        voicing = ChordVoicing(c_major_chord, notes)
        string_repr = str(voicing)
        assert 'C' in string_repr


class TestChordInversion:
    """Tests for ChordInversion class."""

    def test_inversion_creation(self) -> None:
        """Test creating chord inversion."""
        chord = Chord.from_symbol('C')
        inversion = chord.invert(1)
        assert inversion.inversion == 1
        assert inversion.chord == chord

    def test_root_position(self) -> None:
        """Test root position (no inversion)."""
        chord = Chord.from_symbol('C')
        root_pos = chord.invert(0)
        assert root_pos.bass_note.pitch_class == 'C'

    def test_first_inversion_bass(self) -> None:
        """Test first inversion bass note."""
        chord = Chord.from_symbol('C')
        first_inv = chord.invert(1)
        assert first_inv.bass_note.pitch_class == 'E'

    def test_second_inversion_bass(self) -> None:
        """Test second inversion bass note."""
        chord = Chord.from_symbol('C')
        second_inv = chord.invert(2)
        assert second_inv.bass_note.pitch_class == 'G'

    def test_inversion_symbol(self) -> None:
        """Test inversion symbol generation."""
        chord = Chord.from_symbol('C')
        first_inv = chord.invert(1)
        symbol = first_inv.symbol
        assert 'C' in symbol
        assert 'E' in symbol or '/' in symbol

    def test_invalid_inversion_raises_error(self) -> None:
        """Test that invalid inversion raises error."""
        chord = Chord.from_symbol('C')  # Triad has 3 notes
        with pytest.raises(ValueError):
            chord.invert(3)  # Can't have 4th inversion of triad

    def test_seventh_chord_inversions(self) -> None:
        """Test inversions of seventh chord."""
        chord = Chord.from_symbol('Cmaj7')
        third_inv = chord.invert(3)
        # 4th note is the 7th (B)
        assert third_inv.bass_note.pitch_class == 'B'

    def test_inversion_string_representation(self) -> None:
        """Test inversion string representation."""
        chord = Chord.from_symbol('C')
        inv = chord.invert(1)
        assert 'C' in str(inv)
