"""Chord progression class for representing sequences of chords."""

from typing import List, Optional, Dict, Tuple, Iterator
from .chord import Chord, ChordVoicing
from .key import Key
from .interval import Interval


class ChordProgression:
    """Represents a sequence of chords with timing and analysis capabilities."""
    
    def __init__(self, chords: List[Chord], key: Optional[Key] = None, 
                 durations: Optional[List[float]] = None):
        """
        Initialize a ChordProgression.
        
        Args:
            chords: List of chords in the progression
            key: Key context for analysis (optional)
            durations: Duration of each chord in beats (optional)
        """
        if not chords:
            raise ValueError("Chord progression cannot be empty")
        
        self.chords = chords.copy()
        self.key = key
        
        # Set default durations if not provided
        if durations is None:
            self.durations = [1.0] * len(chords)
        else:
            if len(durations) != len(chords):
                raise ValueError("Number of durations must match number of chords")
            self.durations = durations.copy()
    
    @classmethod
    def from_symbols(cls, chord_symbols: List[str], key: Optional[Key] = None,
                    durations: Optional[List[float]] = None) -> 'ChordProgression':
        """
        Create a progression from chord symbols.
        
        Args:
            chord_symbols: List of chord symbols (e.g., ['C', 'Am', 'F', 'G'])
            key: Key context
            durations: Duration of each chord
        """
        chords = [Chord.from_symbol(symbol) for symbol in chord_symbols]
        return cls(chords, key, durations)
    
    @classmethod
    def from_roman_numerals(cls, numerals: List[str], key: Key,
                           durations: Optional[List[float]] = None) -> 'ChordProgression':
        """
        Create a progression from Roman numeral analysis.
        
        Args:
            numerals: List of Roman numerals (e.g., ['I', 'vi', 'IV', 'V'])
            key: Key for Roman numeral interpretation
            durations: Duration of each chord
        """
        chords = []
        for numeral in numerals:
            chord = cls._parse_roman_numeral(numeral, key)
            chords.append(chord)
        
        return cls(chords, key, durations)
    
    @staticmethod
    def _parse_roman_numeral(numeral: str, key: Key) -> Chord:
        """Parse a Roman numeral into a chord."""
        numeral = numeral.strip()
        
        # Map Roman numerals to scale degrees
        numeral_map = {
            'I': 1, 'i': 1,
            'II': 2, 'ii': 2, 
            'III': 3, 'iii': 3,
            'IV': 4, 'iv': 4,
            'V': 5, 'v': 5,
            'VI': 6, 'vi': 6,
            'VII': 7, 'vii': 7
        }
        
        # Extract base numeral
        base_numeral = None
        for num in numeral_map.keys():
            if numeral.startswith(num):
                base_numeral = num
                break
        
        if base_numeral is None:
            raise ValueError(f"Invalid Roman numeral: {numeral}")
        
        degree = numeral_map[base_numeral]
        
        # Determine if it should be major or minor based on case and key
        if key.mode == 'major':
            # Major key: I, IV, V are major; ii, iii, vi are minor; vii is diminished
            if degree in [1, 4, 5] and base_numeral.isupper():
                chord_type = 'triad'
            elif degree in [2, 3, 6] and base_numeral.islower():
                chord_type = 'triad'
            elif degree == 7 and base_numeral.islower():
                chord_type = 'triad'  # Will be diminished from scale
            else:
                chord_type = 'triad'  # Let scale determine quality
        else:
            # Minor key: i, iv, v are minor; III, VI, VII are major; ii is diminished
            chord_type = 'triad'
        
        # Get the chord from the scale
        return key.get_chord_for_degree(degree)
    
    def __len__(self) -> int:
        """Get the number of chords in the progression."""
        return len(self.chords)
    
    def __getitem__(self, index: int) -> Chord:
        """Get a chord by index."""
        return self.chords[index]
    
    def __setitem__(self, index: int, chord: Chord) -> None:
        """Set a chord by index."""
        self.chords[index] = chord
    
    def __iter__(self) -> Iterator[Chord]:
        """Iterate over chords."""
        return iter(self.chords)
    
    @property
    def total_duration(self) -> float:
        """Get total duration of the progression."""
        return sum(self.durations)
    
    @property
    def unique_chords(self) -> List[Chord]:
        """Get unique chords in the progression."""
        seen = set()
        unique = []
        for chord in self.chords:
            if chord not in seen:
                seen.add(chord)
                unique.append(chord)
        return unique
    
    @property
    def chord_symbols(self) -> List[str]:
        """Get chord symbols for all chords."""
        return [chord.symbol for chord in self.chords]
    
    def get_roman_numerals(self, key: Optional[Key] = None) -> List[str]:
        """
        Get Roman numeral analysis of the progression.
        
        Args:
            key: Key for analysis (uses self.key if not provided)
        """
        analysis_key = key or self.key
        if analysis_key is None:
            raise ValueError("Key must be provided for Roman numeral analysis")
        
        numerals = []
        for chord in self.chords:
            analysis = analysis_key.analyze_chord(chord)
            degree = analysis.get('degree')
            
            if degree:
                if analysis_key.mode == 'major':
                    # Major key conventions
                    if degree in [1, 4, 5]:
                        numeral = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'][degree - 1]
                    else:
                        numeral = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'][degree - 1]
                else:
                    # Minor key conventions  
                    if degree in [3, 6, 7]:
                        numeral = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'][degree - 1]
                    else:
                        numeral = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'][degree - 1]
                
                # Add quality indicators for non-diatonic chords
                if not analysis['is_diatonic']:
                    numeral += "*"  # Mark as altered
                
                numerals.append(numeral)
            else:
                numerals.append(f"({chord.symbol})")  # Non-diatonic chord in parentheses
        
        return numerals
    
    def analyze_harmonic_rhythm(self) -> Dict[str, float]:
        """Analyze the harmonic rhythm of the progression."""
        total_duration = self.total_duration
        
        return {
            'total_duration': total_duration,
            'average_chord_duration': total_duration / len(self.chords),
            'fastest_change': min(self.durations),
            'slowest_change': max(self.durations),
            'rhythm_variety': len(set(self.durations))
        }
    
    def get_chord_transitions(self) -> List[Tuple[Chord, Chord, Interval]]:
        """Get all chord transitions with root movement intervals."""
        transitions = []
        
        for i in range(len(self.chords) - 1):
            current_chord = self.chords[i]
            next_chord = self.chords[i + 1]
            root_movement = Interval.from_notes(current_chord.root, next_chord.root)
            transitions.append((current_chord, next_chord, root_movement))
        
        return transitions
    
    def analyze_voice_leading(self, voicings: Optional[List[ChordVoicing]] = None) -> Dict[str, any]:
        """
        Analyze voice leading in the progression.
        
        Args:
            voicings: Specific voicings for each chord (optional)
        """
        if voicings and len(voicings) != len(self.chords):
            raise ValueError("Number of voicings must match number of chords")
        
        analysis = {
            'smooth_voice_leading': [],
            'large_leaps': [],
            'common_tones': [],
            'parallel_motion': []
        }
        
        # If no voicings provided, create simple root position triads
        if voicings is None:
            voicings = []
            for chord in self.chords:
                notes = chord.notes[:3]  # Take first 3 notes (triad)
                # Adjust octaves for reasonable spacing
                for i, note in enumerate(notes):
                    notes[i] = note.__class__(note.pitch_class, 4 + i // 3)
                voicings.append(ChordVoicing(chord, notes))
        
        # Analyze transitions between adjacent voicings
        for i in range(len(voicings) - 1):
            current = voicings[i]
            next_voicing = voicings[i + 1]
            
            # Find common tones
            common_pitch_classes = set()
            for note1 in current.notes:
                for note2 in next_voicing.notes:
                    if note1.pitch_class == note2.pitch_class:
                        common_pitch_classes.add(note1.pitch_class)
            
            analysis['common_tones'].append(len(common_pitch_classes))
            
            # Analyze voice movement (simplified - assumes same number of voices)
            if len(current.notes) == len(next_voicing.notes):
                movements = []
                for j in range(min(len(current.notes), len(next_voicing.notes))):
                    interval = Interval.from_notes(current.notes[j], next_voicing.notes[j])
                    movements.append(interval.semitones)
                    
                    # Check for large leaps (> perfect 4th)
                    if abs(interval.semitones) > 5:
                        analysis['large_leaps'].append({
                            'transition': i,
                            'voice': j,
                            'interval': interval.semitones
                        })
                
                # Check for smooth voice leading (all movements <= 2 semitones)
                smooth = all(abs(mov) <= 2 for mov in movements)
                analysis['smooth_voice_leading'].append(smooth)
        
        return analysis
    
    def transpose(self, interval: Interval) -> 'ChordProgression':
        """Transpose the entire progression by an interval."""
        transposed_chords = []
        
        for chord in self.chords:
            new_root = chord.root.transpose(interval.semitones)
            new_bass = chord.bass.transpose(interval.semitones) if chord.bass != chord.root else None
            transposed_chord = Chord(new_root, chord.quality, new_bass)
            transposed_chords.append(transposed_chord)
        
        # Transpose key if present
        new_key = None
        if self.key:
            new_tonic = self.key.tonic.transpose(interval.semitones)
            new_key = Key(new_tonic, self.key.mode)
        
        return ChordProgression(transposed_chords, new_key, self.durations)
    
    def substitute_chord(self, index: int, new_chord: Chord) -> 'ChordProgression':
        """Create a new progression with one chord substituted."""
        new_chords = self.chords.copy()
        new_chords[index] = new_chord
        return ChordProgression(new_chords, self.key, self.durations)
    
    def insert_chord(self, index: int, chord: Chord, duration: float = 1.0) -> 'ChordProgression':
        """Insert a chord at a specific position."""
        new_chords = self.chords.copy()
        new_durations = self.durations.copy()
        
        new_chords.insert(index, chord)
        new_durations.insert(index, duration)
        
        return ChordProgression(new_chords, self.key, new_durations)
    
    def extend(self, other: 'ChordProgression') -> 'ChordProgression':
        """Extend this progression with another progression."""
        extended_chords = self.chords + other.chords
        extended_durations = self.durations + other.durations
        
        # Use the key from the first progression
        return ChordProgression(extended_chords, self.key, extended_durations)
    
    def repeat(self, times: int) -> 'ChordProgression':
        """Repeat the progression a number of times."""
        if times < 1:
            raise ValueError("Repeat times must be positive")
        
        repeated_chords = self.chords * times
        repeated_durations = self.durations * times
        
        return ChordProgression(repeated_chords, self.key, repeated_durations)
    
    def __str__(self) -> str:
        """String representation showing chord symbols."""
        symbols = self.chord_symbols
        if all(d == 1.0 for d in self.durations):
            return ' - '.join(symbols)
        else:
            # Show durations
            parts = []
            for symbol, duration in zip(symbols, self.durations):
                if duration == 1.0:
                    parts.append(symbol)
                else:
                    parts.append(f"{symbol}({duration})")
            return ' - '.join(parts)
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ChordProgression({[c.symbol for c in self.chords]}, key={self.key})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on chords and durations."""
        if not isinstance(other, ChordProgression):
            return NotImplemented
        return (self.chords == other.chords and 
                self.durations == other.durations and 
                self.key == other.key)