"""Interval class for representing musical intervals."""

from typing import Tuple
from .note import Note


class Interval:
    """Represents a musical interval between two notes."""
    
    INTERVAL_NAMES = {
        0: "Unison",
        1: "Minor 2nd", 
        2: "Major 2nd",
        3: "Minor 3rd",
        4: "Major 3rd", 
        5: "Perfect 4th",
        6: "Tritone",
        7: "Perfect 5th",
        8: "Minor 6th",
        9: "Major 6th",
        10: "Minor 7th", 
        11: "Major 7th",
        12: "Octave"
    }
    
    INTERVAL_QUALITIES = {
        0: ("P", "Perfect"),
        1: ("m", "Minor"),
        2: ("M", "Major"), 
        3: ("m", "Minor"),
        4: ("M", "Major"),
        5: ("P", "Perfect"),
        6: ("d", "Diminished"), 
        7: ("P", "Perfect"),
        8: ("m", "Minor"),
        9: ("M", "Major"),
        10: ("m", "Minor"),
        11: ("M", "Major")
    }
    
    def __init__(self, semitones: int):
        """
        Initialize an Interval.
        
        Args:
            semitones: Number of semitones in the interval
        """
        self._semitones = semitones % 12
        self._octaves = semitones // 12
    
    @classmethod
    def from_notes(cls, note1: Note, note2: Note) -> 'Interval':
        """Create an interval from two notes."""
        semitones = note2.midi_number - note1.midi_number
        return cls(semitones)
    
    @classmethod
    def from_name(cls, name: str) -> 'Interval':
        """Create an interval from its name (e.g., 'P5', 'M3', 'm7')."""
        name = name.strip().upper()
        
        # Parse quality and number
        if len(name) < 2:
            raise ValueError(f"Invalid interval name: {name}")
        
        quality = name[0]
        try:
            number = int(name[1:])
        except ValueError:
            raise ValueError(f"Invalid interval name: {name}")
        
        # Convert to semitones based on quality and number
        base_semitones = {
            1: 0,   # Unison
            2: 2,   # Major 2nd
            3: 4,   # Major 3rd
            4: 5,   # Perfect 4th
            5: 7,   # Perfect 5th
            6: 9,   # Major 6th
            7: 11,  # Major 7th
            8: 12,  # Octave
        }
        
        # Handle compound intervals
        octaves = (number - 1) // 7
        simple_number = ((number - 1) % 7) + 1
        
        if simple_number not in base_semitones:
            raise ValueError(f"Invalid interval number: {number}")
        
        semitones = base_semitones[simple_number] + (octaves * 12)
        
        # Adjust for quality
        if quality == 'M':  # Major
            pass  # Already set to major
        elif quality == 'm':  # Minor
            if simple_number in [2, 3, 6, 7]:
                semitones -= 1
            else:
                raise ValueError(f"Cannot make {simple_number} minor")
        elif quality == 'P':  # Perfect
            if simple_number not in [1, 4, 5, 8]:
                raise ValueError(f"Cannot make {simple_number} perfect")
        elif quality == 'd':  # Diminished
            if simple_number in [1, 4, 5, 8]:
                semitones -= 1
            else:
                semitones -= 2
        elif quality == 'A':  # Augmented
            if simple_number in [1, 4, 5, 8]:
                semitones += 1
            else:
                semitones += 2
        else:
            raise ValueError(f"Invalid interval quality: {quality}")
        
        return cls(semitones)
    
    @property
    def semitones(self) -> int:
        """Get the total number of semitones."""
        return self._semitones + (self._octaves * 12)
    
    @property
    def simple_semitones(self) -> int:
        """Get the semitones within one octave (0-11)."""
        return self._semitones
    
    @property
    def octaves(self) -> int:
        """Get the number of octaves."""
        return self._octaves
    
    @property
    def name(self) -> str:
        """Get the interval name."""
        if self.simple_semitones in self.INTERVAL_NAMES:
            base_name = self.INTERVAL_NAMES[self.simple_semitones]
            if self._octaves > 0:
                return f"{base_name} + {self._octaves} octave(s)"
            return base_name
        return f"{self.semitones} semitones"
    
    @property
    def short_name(self) -> str:
        """Get the short interval name (e.g., 'P5', 'M3')."""
        quality_map = {
            0: "P1",   # Unison
            1: "m2",   # Minor 2nd
            2: "M2",   # Major 2nd
            3: "m3",   # Minor 3rd
            4: "M3",   # Major 3rd
            5: "P4",   # Perfect 4th
            6: "TT",   # Tritone
            7: "P5",   # Perfect 5th
            8: "m6",   # Minor 6th
            9: "M6",   # Major 6th
            10: "m7",  # Minor 7th
            11: "M7"   # Major 7th
        }
        
        base = quality_map.get(self.simple_semitones, f"{self.simple_semitones}st")
        if self._octaves > 0:
            return f"{base}+{self._octaves}oct"
        return base
    
    def invert(self) -> 'Interval':
        """Get the inversion of this interval."""
        inverted_semitones = (12 - self.simple_semitones) % 12
        return Interval(inverted_semitones)
    
    def add(self, other: 'Interval') -> 'Interval':
        """Add another interval to this one."""
        return Interval(self.semitones + other.semitones)
    
    def subtract(self, other: 'Interval') -> 'Interval':
        """Subtract another interval from this one."""
        return Interval(self.semitones - other.semitones)
    
    def is_consonant(self) -> bool:
        """Check if the interval is consonant."""
        consonant_intervals = {0, 3, 4, 7, 8, 9}  # Unison, m3, M3, P5, m6, M6
        return self.simple_semitones in consonant_intervals
    
    def is_perfect(self) -> bool:
        """Check if the interval is perfect."""
        perfect_intervals = {0, 5, 7}  # Unison, P4, P5
        return self.simple_semitones in perfect_intervals
    
    def __str__(self) -> str:
        """String representation of the interval."""
        return self.name
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Interval({self.semitones})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on semitones."""
        if not isinstance(other, Interval):
            return NotImplemented
        return self.semitones == other.semitones
    
    def __hash__(self) -> int:
        """Hash based on semitones."""
        return hash(self.semitones)