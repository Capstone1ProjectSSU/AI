"""Scale class for representing musical scales."""

from typing import List, Dict, Optional
from .note import Note
from .interval import Interval


class Scale:
    """Represents a musical scale with a tonic and interval pattern."""
    
    SCALE_PATTERNS = {
        'major': [0, 2, 4, 5, 7, 9, 11],
        'natural_minor': [0, 2, 3, 5, 7, 8, 10],
        'harmonic_minor': [0, 2, 3, 5, 7, 8, 11],
        'melodic_minor': [0, 2, 3, 5, 7, 9, 11],
        'dorian': [0, 2, 3, 5, 7, 9, 10],
        'phrygian': [0, 1, 3, 5, 7, 8, 10],
        'lydian': [0, 2, 4, 6, 7, 9, 11],
        'mixolydian': [0, 2, 4, 5, 7, 9, 10],
        'locrian': [0, 1, 3, 5, 6, 8, 10],
        'chromatic': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        'pentatonic_major': [0, 2, 4, 7, 9],
        'pentatonic_minor': [0, 3, 5, 7, 10],
        'blues': [0, 3, 5, 6, 7, 10],
        'whole_tone': [0, 2, 4, 6, 8, 10],
        'diminished_hw': [0, 1, 3, 4, 6, 7, 9, 10],  # Half-whole diminished
        'diminished_wh': [0, 2, 3, 5, 6, 8, 9, 11],  # Whole-half diminished
    }
    
    MODE_NAMES = {
        0: 'ionian',      # Major
        1: 'dorian',
        2: 'phrygian', 
        3: 'lydian',
        4: 'mixolydian',
        5: 'aeolian',     # Natural minor
        6: 'locrian'
    }
    
    SCALE_DEGREES = ['1', 'b2', '2', 'b3', '3', '4', 'b5', '5', 'b6', '6', 'b7', '7']
    
    def __init__(self, tonic: Note, scale_type: str):
        """
        Initialize a Scale.
        
        Args:
            tonic: Tonic (root) note of the scale
            scale_type: Type of scale (e.g., 'major', 'minor', 'dorian')
        """
        self.tonic = tonic
        self.scale_type = scale_type
        
        if scale_type not in self.SCALE_PATTERNS:
            raise ValueError(f"Unknown scale type: {scale_type}")
    
    @classmethod
    def major(cls, tonic: Note) -> 'Scale':
        """Create a major scale."""
        return cls(tonic, 'major')
    
    @classmethod
    def minor(cls, tonic: Note) -> 'Scale':
        """Create a natural minor scale."""
        return cls(tonic, 'natural_minor')
    
    @classmethod
    def from_mode(cls, tonic: Note, mode: int, parent_scale: str = 'major') -> 'Scale':
        """
        Create a scale from a mode of another scale.
        
        Args:
            tonic: Tonic note of the mode
            mode: Mode number (0-6 for major scale modes)
            parent_scale: Parent scale type
        """
        if parent_scale not in cls.SCALE_PATTERNS:
            raise ValueError(f"Unknown parent scale: {parent_scale}")
        
        parent_pattern = cls.SCALE_PATTERNS[parent_scale]
        if mode >= len(parent_pattern):
            raise ValueError(f"Mode {mode} not valid for {parent_scale}")
        
        # Rotate the pattern to start from the mode degree
        mode_pattern = []
        mode_root = parent_pattern[mode]
        
        for degree in parent_pattern[mode:] + parent_pattern[:mode]:
            interval = (degree - mode_root) % 12
            mode_pattern.append(interval)
        
        # Create a new scale type name
        if parent_scale == 'major' and mode in cls.MODE_NAMES:
            mode_name = cls.MODE_NAMES[mode]
        else:
            mode_name = f"{parent_scale}_mode_{mode}"
        
        # Temporarily add this pattern to available patterns
        original_patterns = cls.SCALE_PATTERNS.copy()
        cls.SCALE_PATTERNS[mode_name] = mode_pattern
        
        try:
            scale = cls(tonic, mode_name)
            scale._is_mode = True
            scale._parent_scale = parent_scale
            scale._mode_number = mode
            return scale
        finally:
            # Restore original patterns
            cls.SCALE_PATTERNS = original_patterns
    
    @property
    def pattern(self) -> List[int]:
        """Get the interval pattern in semitones."""
        return self.SCALE_PATTERNS[self.scale_type]
    
    @property
    def notes(self) -> List[Note]:
        """Get all notes in the scale."""
        notes = []
        for semitones in self.pattern:
            note = self.tonic.transpose(semitones)
            notes.append(note)
        return notes
    
    @property
    def pitch_classes(self) -> List[str]:
        """Get pitch classes in the scale."""
        return [note.pitch_class for note in self.notes]
    
    def get_degree(self, degree: int) -> Note:
        """Get a specific scale degree (1-based)."""
        if not 1 <= degree <= len(self.pattern):
            raise ValueError(f"Degree {degree} not valid for {len(self.pattern)}-note scale")
        return self.notes[degree - 1]
    
    def get_note_degree(self, note: Note) -> Optional[int]:
        """Get the degree of a note in the scale (1-based)."""
        note_pitch_class = note.pitch_class
        for i, scale_note in enumerate(self.notes):
            if scale_note.pitch_class == note_pitch_class:
                return i + 1
        return None
    
    def contains_note(self, note: Note) -> bool:
        """Check if a note belongs to the scale."""
        return note.pitch_class in self.pitch_classes
    
    def get_chord_for_degree(self, degree: int, chord_type: str = 'triad') -> 'Chord':
        """
        Get the chord built on a specific scale degree.
        
        Args:
            degree: Scale degree (1-based)
            chord_type: Type of chord ('triad', 'seventh')
        """
        from .chord import Chord
        
        root = self.get_degree(degree)
        
        if chord_type == 'triad':
            # Build triad using 1st, 3rd, 5th degrees
            degrees = [0, 2, 4]  # Scale positions relative to root
        elif chord_type == 'seventh':
            # Build seventh chord using 1st, 3rd, 5th, 7th degrees
            degrees = [0, 2, 4, 6]
        else:
            raise ValueError(f"Unknown chord type: {chord_type}")
        
        chord_notes = []
        scale_notes = self.notes
        scale_length = len(scale_notes)
        root_index = degree - 1
        
        for deg_offset in degrees:
            note_index = (root_index + deg_offset) % scale_length
            chord_notes.append(scale_notes[note_index])
        
        # Determine chord quality based on intervals
        intervals = []
        for note in chord_notes[1:]:
            interval = Interval.from_notes(root, note)
            intervals.append(interval.simple_semitones)
        
        # Map intervals to chord quality
        if len(intervals) == 2:  # Triad
            if intervals == [4, 7]:
                quality = 'major'
            elif intervals == [3, 7]:
                quality = 'minor'
            elif intervals == [3, 6]:
                quality = 'diminished'
            elif intervals == [4, 8]:
                quality = 'augmented'
            else:
                quality = 'major'  # Default fallback
        elif len(intervals) == 3:  # Seventh chord
            if intervals == [4, 7, 11]:
                quality = 'major7'
            elif intervals == [3, 7, 10]:
                quality = 'minor7'
            elif intervals == [4, 7, 10]:
                quality = 'dominant7'
            elif intervals == [3, 6, 10]:
                quality = 'half_diminished7'
            elif intervals == [3, 6, 9]:
                quality = 'diminished7'
            else:
                quality = 'dominant7'  # Default fallback
        else:
            quality = 'major'  # Default fallback
        
        return Chord(root, quality)
    
    def get_relative_scale(self, scale_type: str) -> 'Scale':
        """Get a relative scale (same notes, different tonic)."""
        if scale_type not in self.SCALE_PATTERNS:
            raise ValueError(f"Unknown scale type: {scale_type}")
        
        target_pattern = self.SCALE_PATTERNS[scale_type]
        current_notes = self.notes
        
        # Find which note in current scale could be the tonic of target scale
        for i, potential_tonic in enumerate(current_notes):
            # Check if starting from this note gives us the target pattern
            test_notes = current_notes[i:] + current_notes[:i]
            test_intervals = []
            
            for j in range(1, len(test_notes)):
                interval = Interval.from_notes(test_notes[0], test_notes[j])
                test_intervals.append(interval.simple_semitones)
            
            # Add the tonic (0) at the beginning
            test_pattern = [0] + test_intervals
            
            if test_pattern[:len(target_pattern)] == target_pattern:
                return Scale(potential_tonic, scale_type)
        
        raise ValueError(f"Cannot find relative {scale_type} scale")
    
    def get_parallel_scale(self, scale_type: str) -> 'Scale':
        """Get a parallel scale (same tonic, different pattern)."""
        return Scale(self.tonic, scale_type)
    
    def __str__(self) -> str:
        """String representation of the scale."""
        return f"{self.tonic.pitch_class} {self.scale_type.replace('_', ' ').title()}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Scale({self.tonic.pitch_class}, '{self.scale_type}')"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on tonic and scale type."""
        if not isinstance(other, Scale):
            return NotImplemented
        return self.tonic == other.tonic and self.scale_type == other.scale_type
    
    def __hash__(self) -> int:
        """Hash based on tonic and scale type."""
        return hash((self.tonic, self.scale_type))