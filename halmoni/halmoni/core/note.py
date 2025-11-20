"""Note class for representing musical notes."""

from typing import Optional, Union
import re


class Note:
    """Represents a musical note with pitch class, octave, and enharmonic handling."""
    
    CHROMATIC_SCALE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    FLAT_SCALE = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    
    ENHARMONIC_MAP = {
        'C#': 'Db', 'Db': 'C#',
        'D#': 'Eb', 'Eb': 'D#', 
        'F#': 'Gb', 'Gb': 'F#',
        'G#': 'Ab', 'Ab': 'G#',
        'A#': 'Bb', 'Bb': 'A#'
    }
    
    def __init__(self, pitch: Union[str, int], octave: Optional[int] = None):
        """
        Initialize a Note.
        
        Args:
            pitch: Note name (e.g., 'C', 'F#', 'Bb') or MIDI number (0-127)
            octave: Octave number (0-10), required if pitch is string
        """
        if isinstance(pitch, int):
            if not 0 <= pitch <= 127:
                raise ValueError("MIDI pitch must be between 0 and 127")
            self._midi_number = pitch
            self._pitch_class = self.CHROMATIC_SCALE[pitch % 12]
            self._octave = pitch // 12 - 1
        else:
            self._pitch_class = self._normalize_pitch_class(pitch)
            if octave is None:
                raise ValueError("Octave must be specified when pitch is a string")
            if not 0 <= octave <= 10:
                raise ValueError("Octave must be between 0 and 10")
            self._octave = octave
            self._midi_number = self._calculate_midi_number()
    
    def _normalize_pitch_class(self, pitch: str) -> str:
        """Normalize pitch class string."""
        pitch = pitch.strip()
        if not re.match(r'^[A-G][#b]?$', pitch):
            raise ValueError(f"Invalid pitch class: {pitch}")
        return pitch
    
    def _calculate_midi_number(self) -> int:
        """Calculate MIDI number from pitch class and octave."""
        try:
            pitch_index = self.CHROMATIC_SCALE.index(self._pitch_class)
        except ValueError:
            pitch_index = self.FLAT_SCALE.index(self._pitch_class)
        return (self._octave + 1) * 12 + pitch_index
    
    @property
    def pitch_class(self) -> str:
        """Get the pitch class (e.g., 'C', 'F#')."""
        return self._pitch_class
    
    @property
    def octave(self) -> int:
        """Get the octave number."""
        return self._octave
    
    @property
    def midi_number(self) -> int:
        """Get the MIDI number (0-127)."""
        return self._midi_number
    
    @property
    def frequency(self) -> float:
        """Get the frequency in Hz (A4 = 440Hz)."""
        return 440.0 * (2.0 ** ((self._midi_number - 69) / 12.0))
    
    def enharmonic_equivalent(self) -> Optional['Note']:
        """Get the enharmonic equivalent note."""
        if self._pitch_class in self.ENHARMONIC_MAP:
            equiv_pitch = self.ENHARMONIC_MAP[self._pitch_class]
            return Note(equiv_pitch, self._octave)
        return None
    
    def transpose(self, semitones: int) -> 'Note':
        """Transpose the note by a given number of semitones."""
        new_midi = self._midi_number + semitones
        if not 0 <= new_midi <= 127:
            raise ValueError("Transposition results in MIDI number out of range")
        return Note(new_midi)
    
    def __str__(self) -> str:
        """String representation of the note."""
        return f"{self._pitch_class}{self._octave}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Note('{self._pitch_class}', {self._octave})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on MIDI number."""
        if not isinstance(other, Note):
            return NotImplemented
        return self._midi_number == other._midi_number
    
    def __hash__(self) -> int:
        """Hash based on MIDI number."""
        return hash(self._midi_number)
    
    def __lt__(self, other: 'Note') -> bool:
        """Compare notes by pitch height."""
        return self._midi_number < other._midi_number