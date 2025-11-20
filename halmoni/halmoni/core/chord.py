"""Chord-related classes for representing musical chords and voicings."""

from typing import List, Optional, Set, Tuple, Dict
from .note import Note
from .interval import Interval


class Chord:
    """Represents a musical chord with root, quality, and extensions."""
    
    CHORD_TONES = {
        'major': [0, 4, 7],
        'minor': [0, 3, 7], 
        'diminished': [0, 3, 6],
        'augmented': [0, 4, 8],
        'major7': [0, 4, 7, 11],
        'minor7': [0, 3, 7, 10],
        'dominant7': [0, 4, 7, 10],
        'diminished7': [0, 3, 6, 9],
        'half_diminished7': [0, 3, 6, 10],
        'major9': [0, 4, 7, 11, 2],
        'minor9': [0, 3, 7, 10, 2],
        'dominant9': [0, 4, 7, 10, 2],
        'major11': [0, 4, 7, 11, 2, 5],
        'minor11': [0, 3, 7, 10, 2, 5],
        'dominant11': [0, 4, 7, 10, 2, 5],
        'major13': [0, 4, 7, 11, 2, 5, 9],
        'minor13': [0, 3, 7, 10, 2, 5, 9],
        'dominant13': [0, 4, 7, 10, 2, 5, 9],
        'sus2': [0, 2, 7],
        'sus4': [0, 5, 7],
    }
    
    CHORD_SYMBOLS = {
        'major': '',
        'minor': 'm',
        'diminished': 'dim',
        'augmented': 'aug',
        'major7': 'maj7',
        'minor7': 'm7',
        'dominant7': '7',
        'diminished7': 'dim7',
        'half_diminished7': 'm7b5',
        'major9': 'maj9',
        'minor9': 'm9',
        'dominant9': '9',
        'major11': 'maj11',
        'minor11': 'm11',
        'dominant11': '11',
        'major13': 'maj13',
        'minor13': 'm13',
        'dominant13': '13',
        'sus2': 'sus2',
        'sus4': 'sus4',
    }
    
    def __init__(self, root: Note, quality: str, bass: Optional[Note] = None):
        """
        Initialize a Chord.
        
        Args:
            root: Root note of the chord
            quality: Chord quality (e.g., 'major', 'minor7', 'dominant9')
            bass: Bass note for slash chords (optional)
        """
        self.root = root
        self.quality = quality
        self.bass = bass or root
        
        if quality not in self.CHORD_TONES:
            raise ValueError(f"Unknown chord quality: {quality}")
    
    @classmethod
    def from_symbol(cls, symbol: str, octave: int = 4) -> 'Chord':
        """
        Create a chord from chord symbol notation.
        
        Args:
            symbol: Chord symbol (e.g., 'Cmaj7', 'Am', 'G7/B')
            octave: Octave for the root note
        """
        # Handle slash chords
        if '/' in symbol:
            chord_part, bass_part = symbol.split('/')
            bass_note = Note(bass_part, octave)
        else:
            chord_part = symbol
            bass_note = None
        
        # Parse root note
        if len(chord_part) < 1:
            raise ValueError("Invalid chord symbol")
        
        root_str = chord_part[0]
        remainder = chord_part[1:]
        
        # Handle accidentals
        if remainder and remainder[0] in '#b':
            root_str += remainder[0]
            remainder = remainder[1:]
        
        root_note = Note(root_str, octave)
        
        # Parse quality
        quality = cls._parse_quality(remainder)
        
        return cls(root_note, quality, bass_note)
    
    @classmethod
    def _parse_quality(cls, quality_str: str) -> str:
        """Parse chord quality from string."""
        quality_map = {
            '': 'major',
            'M': 'major',
            'maj': 'major',
            'm': 'minor',
            'min': 'minor',
            'dim': 'diminished',
            '°': 'diminished',
            'aug': 'augmented',
            '+': 'augmented',
            '7': 'dominant7',
            'maj7': 'major7',
            'M7': 'major7',
            'm7': 'minor7',
            'min7': 'minor7',
            'dim7': 'diminished7',
            '°7': 'diminished7',
            'm7b5': 'half_diminished7',
            'ø7': 'half_diminished7',
            '9': 'dominant9',
            'maj9': 'major9',
            'M9': 'major9',
            'm9': 'minor9',
            '11': 'dominant11',
            'maj11': 'major11',
            'm11': 'minor11',
            '13': 'dominant13',
            'maj13': 'major13',
            'm13': 'minor13',
            'sus2': 'sus2',
            'sus4': 'sus4',
        }
        
        if quality_str in quality_map:
            return quality_map[quality_str]
        
        raise ValueError(f"Unknown chord quality: {quality_str}")
    
    @property
    def notes(self) -> List[Note]:
        """Get all notes in the chord."""
        intervals = self.CHORD_TONES[self.quality]
        notes = []
        
        for interval_semitones in intervals:
            note = self.root.transpose(interval_semitones)
            notes.append(note)
        
        return notes
    
    @property
    def pitch_classes(self) -> Set[str]:
        """Get unique pitch classes in the chord."""
        return {note.pitch_class for note in self.notes}
    
    @property
    def symbol(self) -> str:
        """Get chord symbol representation."""
        symbol = self.root.pitch_class + self.CHORD_SYMBOLS[self.quality]
        
        if self.bass != self.root:
            symbol += f"/{self.bass.pitch_class}"
        
        return symbol
    
    def contains_note(self, note: Note) -> bool:
        """Check if chord contains a specific note (by pitch class)."""
        return note.pitch_class in self.pitch_classes
    
    def get_chord_tone_function(self, note: Note) -> Optional[str]:
        """Get the function of a note in the chord (root, third, fifth, etc.)."""
        if not self.contains_note(note):
            return None
        
        interval = Interval.from_notes(self.root, note)
        semitones = interval.simple_semitones
        
        function_map = {
            0: "root",
            1: "b9",
            2: "9", 
            3: "b3" if self.quality in ['minor', 'minor7', 'minor9', 'minor11', 'minor13'] else "3",
            4: "3" if self.quality not in ['minor', 'minor7', 'minor9', 'minor11', 'minor13'] else "#3",
            5: "11",
            6: "b5",
            7: "5",
            8: "b13",
            9: "13",
            10: "b7",
            11: "7"
        }
        
        return function_map.get(semitones, "unknown")
    
    def invert(self, inversion: int = 1) -> 'ChordInversion':
        """Create a chord inversion."""
        return ChordInversion(self, inversion)
    
    def __str__(self) -> str:
        """String representation of the chord."""
        return self.symbol
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Chord({self.root.pitch_class}, '{self.quality}')"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on root, quality, and bass."""
        if not isinstance(other, Chord):
            return NotImplemented
        return (self.root == other.root and 
                self.quality == other.quality and 
                self.bass == other.bass)
    
    def __hash__(self) -> int:
        """Hash based on root, quality, and bass."""
        return hash((self.root, self.quality, self.bass))


class ChordInversion:
    """Represents a chord inversion."""
    
    def __init__(self, chord: Chord, inversion: int = 0):
        """
        Initialize a chord inversion.
        
        Args:
            chord: Base chord
            inversion: Inversion number (0=root position, 1=first inversion, etc.)
        """
        self.chord = chord
        self.inversion = inversion
        
        chord_notes = chord.notes
        if inversion >= len(chord_notes):
            raise ValueError(f"Inversion {inversion} not possible for {len(chord_notes)}-note chord")
    
    @property
    def bass_note(self) -> Note:
        """Get the bass note of the inversion."""
        chord_notes = self.chord.notes
        return chord_notes[self.inversion % len(chord_notes)]
    
    @property
    def symbol(self) -> str:
        """Get symbol with inversion notation."""
        if self.inversion == 0:
            return self.chord.symbol
        
        bass_note = self.bass_note
        return f"{self.chord.symbol}/{bass_note.pitch_class}"
    
    def __str__(self) -> str:
        return self.symbol
    
    def __repr__(self) -> str:
        return f"ChordInversion({self.chord}, {self.inversion})"


class ChordVoicing:
    """Represents a specific voicing of a chord with exact pitches."""
    
    def __init__(self, chord: Chord, notes: List[Note]):
        """
        Initialize a chord voicing.
        
        Args:
            chord: Base chord
            notes: Specific notes in the voicing (with octaves)
        """
        self.chord = chord
        self.notes = sorted(notes)  # Sort by pitch height
        
        # Validate that all notes belong to the chord
        chord_pitch_classes = chord.pitch_classes
        for note in notes:
            if note.pitch_class not in chord_pitch_classes:
                raise ValueError(f"Note {note} not in chord {chord}")
    
    @property
    def bass_note(self) -> Note:
        """Get the lowest note in the voicing."""
        return self.notes[0]
    
    @property
    def soprano_note(self) -> Note:
        """Get the highest note in the voicing."""
        return self.notes[-1]
    
    @property
    def range(self) -> Interval:
        """Get the range from bass to soprano."""
        return Interval.from_notes(self.bass_note, self.soprano_note)
    
    def get_intervals_from_bass(self) -> List[Interval]:
        """Get intervals of all notes from the bass."""
        bass = self.bass_note
        return [Interval.from_notes(bass, note) for note in self.notes]
    
    def __str__(self) -> str:
        """String representation showing all notes."""
        note_names = [str(note) for note in self.notes]
        return f"{self.chord.symbol}: [{', '.join(note_names)}]"
    
    def __repr__(self) -> str:
        return f"ChordVoicing({self.chord}, {self.notes})"