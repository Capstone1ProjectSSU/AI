"""Base classes for chord suggestion strategies."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..core import Chord, Key, ChordProgression, Interval


@dataclass
class ChordSuggestion:
    """Represents a chord suggestion with confidence and reasoning."""
    chord: Chord
    confidence: float  # 0.0 to 1.0
    reasoning: str
    position: float  # Where to insert/replace in progression (can be fractional for insertions)
    voice_leading_quality: float  # 0.0 to 1.0
    strategy_source: Optional[str] = None


class ChordSuggestionStrategy(ABC):
    """Base class for all chord suggestion strategies."""
    
    @abstractmethod
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate chord suggestions for the given progression."""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this strategy."""
        pass
    
    def _calculate_voice_leading_quality(self, chord1: Chord, chord2: Chord) -> float:
        """Calculate voice leading quality between two chords."""
        # Get pitch classes of both chords
        pc1 = chord1.pitch_classes
        pc2 = chord2.pitch_classes
        
        # Count common tones
        common_tones = len(pc1.intersection(pc2))
        max_possible_common = min(len(pc1), len(pc2))
        
        if max_possible_common == 0:
            return 0.5  # Neutral quality
        
        # Base quality on common tone retention
        common_tone_ratio = common_tones / max_possible_common
        
        # Calculate root motion quality
        root_interval = Interval.from_notes(chord1.root, chord2.root)
        root_motion_semitones = abs(root_interval.simple_semitones)
        
        # Consider the shorter distance (interval or its inversion)
        effective_semitones = min(root_motion_semitones, 12 - root_motion_semitones)
        
        # Prefer smaller intervals (better voice leading)
        root_motion_quality = 1.0 - (effective_semitones / 12.0)
        
        # Strong root motions (P4, P5) get bonus
        if root_motion_semitones in [5, 7]:  # P4, P5
            root_motion_quality += 0.2
        elif root_motion_semitones in [1, 2]:  # Stepwise motion
            root_motion_quality += 0.1
        elif root_motion_semitones in [3, 4]: # 3rds
            root_motion_quality += 0.15
        
        # Combine factors
        voice_leading_quality = (common_tone_ratio * 0.6 + root_motion_quality * 0.4)
        
        return min(1.0, max(0.0, voice_leading_quality))
    
    def _get_scale_degree(self, note: Chord, key: Key) -> Optional[int]:
        """Get the scale degree of a chord root in the given key."""
        try:
            return key.scale.get_note_degree(note.root)
        except:
            return None
    
    def _is_diatonic_chord(self, chord: Chord, key: Key) -> bool:
        """Check if a chord is diatonic to the given key."""
        analysis = key.analyze_chord(chord)
        return analysis['is_diatonic']
    
    def _get_harmonic_function(self, chord: Chord, key: Key) -> str:
        """Get the harmonic function of a chord in the given key."""
        analysis = key.analyze_chord(chord)
        return analysis.get('function', 'unknown')
    
    def _is_cadential_position(self, progression: ChordProgression, position: int) -> bool:
        """Check if position is in a cadential context."""
        # Last two positions are considered cadential
        return position >= len(progression.chords) - 2
    
    def _get_next_chord(self, progression: ChordProgression, position: int) -> Optional[Chord]:
        """Get the chord that follows the given position."""
        if position < len(progression.chords) - 1:
            return progression.chords[position + 1]
        return None
    
    def _get_previous_chord(self, progression: ChordProgression, position: int) -> Optional[Chord]:
        """Get the chord that precedes the given position."""
        if position > 0:
            return progression.chords[position - 1]
        return None