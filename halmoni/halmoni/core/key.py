"""Key class for representing musical keys and key signatures."""

from typing import List, Dict, Optional, Tuple
from .note import Note
from .scale import Scale


class Key:
    """Represents a musical key with tonic, mode, and key signature."""
    
    MAJOR_KEY_SIGNATURES = {
        'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6, 'C#': 7,
        'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4, 'Db': -5, 'Gb': -6, 'Cb': -7
    }
    
    MINOR_KEY_SIGNATURES = {
        'A': 0, 'E': 1, 'B': 2, 'F#': 3, 'C#': 4, 'G#': 5, 'D#': 6, 'A#': 7,
        'D': -1, 'G': -2, 'C': -3, 'F': -4, 'Bb': -5, 'Eb': -6, 'Ab': -7
    }
    
    SHARPS_ORDER = ['F#', 'C#', 'G#', 'D#', 'A#', 'E#', 'B#']
    FLATS_ORDER = ['Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb', 'Fb']
    
    CIRCLE_OF_FIFTHS_MAJOR = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb']
    CIRCLE_OF_FIFTHS_MINOR = ['A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'D', 'G', 'C', 'F', 'Bb', 'Eb', 'Ab']
    
    def __init__(self, tonic: Note, mode: str = 'major'):
        """
        Initialize a Key.
        
        Args:
            tonic: Tonic note of the key
            mode: Key mode ('major' or 'minor')
        """
        self.tonic = tonic
        self.mode = mode.lower()
        
        if self.mode not in ['major', 'minor']:
            raise ValueError("Mode must be 'major' or 'minor'")
        
        self._scale = Scale(tonic, 'major' if mode == 'major' else 'natural_minor')
    
    @classmethod
    def from_signature(cls, signature: int, mode: str = 'major') -> 'Key':
        """
        Create a key from key signature.
        
        Args:
            signature: Number of sharps (positive) or flats (negative)
            mode: Key mode ('major' or 'minor')
        """
        if mode == 'major':
            sig_map = {v: k for k, v in cls.MAJOR_KEY_SIGNATURES.items()}
        else:
            sig_map = {v: k for k, v in cls.MINOR_KEY_SIGNATURES.items()}
        
        if signature not in sig_map:
            raise ValueError(f"Invalid key signature: {signature}")
        
        tonic_name = sig_map[signature]
        tonic = Note(tonic_name, 4)  # Default to octave 4
        
        return cls(tonic, mode)
    
    @property
    def scale(self) -> Scale:
        """Get the scale associated with this key."""
        return self._scale
    
    @property
    def signature(self) -> int:
        """Get the key signature (number of sharps/flats)."""
        tonic_name = self.tonic.pitch_class
        
        if self.mode == 'major':
            return self.MAJOR_KEY_SIGNATURES.get(tonic_name, 0)
        else:
            return self.MINOR_KEY_SIGNATURES.get(tonic_name, 0)
    
    @property
    def accidentals(self) -> List[str]:
        """Get the accidentals in the key signature."""
        sig = self.signature
        
        if sig > 0:
            return self.SHARPS_ORDER[:sig]
        elif sig < 0:
            return self.FLATS_ORDER[:abs(sig)]
        else:
            return []
    
    @property
    def relative_key(self) -> 'Key':
        """Get the relative major/minor key."""
        if self.mode == 'major':
            # Relative minor is a minor 6th up (or major 3rd down)
            relative_tonic = self.tonic.transpose(-3)  # Down a minor 3rd
            return Key(relative_tonic, 'minor')
        else:
            # Relative major is a minor 3rd up
            relative_tonic = self.tonic.transpose(3)  # Up a minor 3rd
            return Key(relative_tonic, 'major')
    
    @property
    def parallel_key(self) -> 'Key':
        """Get the parallel major/minor key."""
        new_mode = 'minor' if self.mode == 'major' else 'major'
        return Key(self.tonic, new_mode)
    
    def get_dominant_key(self) -> 'Key':
        """Get the dominant key (fifth above)."""
        dominant_tonic = self.tonic.transpose(7)  # Perfect 5th up
        return Key(dominant_tonic, self.mode)
    
    def get_subdominant_key(self) -> 'Key':
        """Get the subdominant key (fourth above)."""
        subdominant_tonic = self.tonic.transpose(5)  # Perfect 4th up
        return Key(subdominant_tonic, self.mode)
    
    def get_closely_related_keys(self) -> List['Key']:
        """Get all closely related keys (up to one accidental difference)."""
        related = []
        
        # Relative key
        related.append(self.relative_key)
        
        # Dominant and subdominant
        related.append(self.get_dominant_key())
        related.append(self.get_subdominant_key())
        
        # Relative keys of dominant and subdominant
        related.append(self.get_dominant_key().relative_key)
        related.append(self.get_subdominant_key().relative_key)
        
        return related
    
    def contains_note(self, note: Note) -> bool:
        """Check if a note belongs to this key."""
        return self.scale.contains_note(note)
    
    def get_chord_for_degree(self, degree: int) -> 'Chord':
        """Get the diatonic chord for a scale degree."""
        return self.scale.get_chord_for_degree(degree, 'triad')
    
    def get_seventh_chord_for_degree(self, degree: int) -> 'Chord':
        """Get the diatonic seventh chord for a scale degree."""
        return self.scale.get_chord_for_degree(degree, 'seventh')
    
    def analyze_chord(self, chord: 'Chord') -> Dict[str, any]:
        """
        Analyze a chord in the context of this key.
        
        Returns:
            Dictionary with analysis information
        """
        from .chord import Chord
        
        analysis = {
            'chord': chord,
            'is_diatonic': True,
            'degree': None,
            'function': None,
            'non_chord_tones': []
        }
        
        # Find the degree of the chord root
        root_degree = self.scale.get_note_degree(chord.root)
        analysis['degree'] = root_degree
        
        if root_degree:
            # Check if it matches the expected diatonic chord
            expected_chord = self.get_chord_for_degree(root_degree)
            
            # Compare chord tones
            chord_pitch_classes = chord.pitch_classes
            expected_pitch_classes = expected_chord.pitch_classes
            
            if chord_pitch_classes == expected_pitch_classes:
                analysis['is_diatonic'] = True
            else:
                analysis['is_diatonic'] = False
                # Find non-chord tones
                for pitch_class in chord_pitch_classes:
                    if pitch_class not in self.scale.pitch_classes:
                        analysis['non_chord_tones'].append(pitch_class)
            
            # Determine harmonic function
            if self.mode == 'major':
                if root_degree in [1]:
                    analysis['function'] = 'tonic'
                elif root_degree in [4]:
                    analysis['function'] = 'subdominant'
                elif root_degree in [5]:
                    analysis['function'] = 'dominant'
                elif root_degree in [6, 3]:
                    analysis['function'] = 'tonic'  # Relative minor/mediant
                elif root_degree in [2]:
                    analysis['function'] = 'subdominant'  # Supertonic
                elif root_degree in [7]:
                    analysis['function'] = 'dominant'  # Leading tone
            else:  # minor
                if root_degree in [1]:
                    analysis['function'] = 'tonic'
                elif root_degree in [4]:
                    analysis['function'] = 'subdominant'
                elif root_degree in [5]:
                    analysis['function'] = 'dominant'
                elif root_degree in [3, 6]:
                    analysis['function'] = 'tonic'  # Relative major/submediant
                elif root_degree in [2]:
                    analysis['function'] = 'subdominant'  # Supertonic
                elif root_degree in [7]:
                    analysis['function'] = 'dominant'  # Subtonic
        else:
            analysis['is_diatonic'] = False
        
        return analysis
    
    def tonicize(self, degree: int) -> 'Key':
        """Create a temporary key centered on a scale degree."""
        new_tonic = self.scale.get_degree(degree)
        return Key(new_tonic, self.mode)
    
    def __str__(self) -> str:
        """String representation of the key."""
        mode_str = self.mode.capitalize()
        return f"{self.tonic.pitch_class} {mode_str}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Key({self.tonic.pitch_class}, '{self.mode}')"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on tonic and mode."""
        if not isinstance(other, Key):
            return NotImplemented
        return self.tonic.pitch_class == other.tonic.pitch_class and self.mode == other.mode
    
    def __hash__(self) -> int:
        """Hash based on tonic pitch class and mode."""
        return hash((self.tonic.pitch_class, self.mode))