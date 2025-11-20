"""Chromatic approach chord strategy implementation."""

from typing import List, Dict, Optional, Tuple
from .base_strategy import ChordSuggestionStrategy, ChordSuggestion
from ..core import Chord, Key, ChordProgression, Interval


class ChromaticApproachStrategy(ChordSuggestionStrategy):
    """Suggests chromatic passing and approach chords."""
    
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "ChromaticApproach"
    
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate chromatic approach chord suggestions."""
        suggestions = []
        analysis_key = key or progression.key
        
        if not analysis_key:
            return suggestions
        
        # Look for opportunities between existing chords
        for i in range(len(progression.chords) - 1):
            current_chord = progression.chords[i]
            next_chord = progression.chords[i + 1]
            
            # Calculate root movement
            root_interval = Interval.from_notes(current_chord.root, next_chord.root)
            
            # Suggest passing chords for appropriate intervals
            if self._should_suggest_passing_chord(root_interval, current_chord, next_chord):
                passing_suggestions = self._generate_passing_chords(
                    current_chord, next_chord, analysis_key, i
                )
                suggestions.extend(passing_suggestions)
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _should_suggest_passing_chord(self, interval: Interval, 
                                    chord1: Chord, chord2: Chord) -> bool:
        """Determine if a passing chord would be beneficial."""
        semitones = abs(interval.semitones)
        
        # Good candidates for passing chords:
        # - Whole step or larger (but not too large)
        # - Descending motion is particularly good for passing chords
        # - Avoid suggesting for very small or very large intervals
        
        if 2 <= semitones <= 7:  # Whole step to perfect 5th
            return True
        
        # Perfect 5th motion (especially descending) is excellent for passing chords
        if semitones in [5, 7]:  # P4 or P5
            return True
        
        return False
    
    def _generate_passing_chords(self, chord1: Chord, chord2: Chord, 
                               key: Key, position: int) -> List[ChordSuggestion]:
        """Generate chromatic passing chord suggestions."""
        suggestions = []
        
        root_interval = Interval.from_notes(chord1.root, chord2.root)
        semitone_distance = root_interval.semitones
        
        # For descending motion by whole step or more
        if semitone_distance <= -2:
            suggestions.extend(self._generate_descending_passing_chords(
                chord1, chord2, key, position, abs(semitone_distance)
            ))
        
        # For ascending motion by whole step or more
        elif semitone_distance >= 2:
            suggestions.extend(self._generate_ascending_passing_chords(
                chord1, chord2, key, position, semitone_distance
            ))
        
        return suggestions
    
    def _generate_descending_passing_chords(self, chord1: Chord, chord2: Chord,
                                          key: Key, position: int,
                                          distance: int) -> List[ChordSuggestion]:
        """Generate passing chords for descending motion."""
        suggestions = []
        
        # Try chromatic passing chord (semitone below chord1)
        passing_root = chord1.root.transpose(-1)
        
        passing_chord_options = self._get_passing_chord_qualities(
            passing_root, chord1, chord2, key, 'descending'
        )
        
        for chord_quality, confidence_mod, reasoning_suffix in passing_chord_options:
            try:
                passing_chord = Chord(passing_root, chord_quality)
                
                # Calculate base confidence
                base_confidence = 0.75 * confidence_mod
                
                # Boost confidence for smooth voice leading
                voice_leading_quality = self._calculate_voice_leading_quality(
                    chord1, passing_chord
                )
                
                # Check voice leading to second chord too
                voice_leading_quality2 = self._calculate_voice_leading_quality(
                    passing_chord, chord2
                )
                
                # Average the voice leading qualities
                avg_voice_leading = (voice_leading_quality + voice_leading_quality2) / 2
                
                confidence = min(0.95, base_confidence + avg_voice_leading * 0.2)
                
                reasoning = f"Chromatic passing chord connecting {chord1.symbol} to {chord2.symbol}"
                if reasoning_suffix:
                    reasoning += f" - {reasoning_suffix}"
                
                suggestions.append(ChordSuggestion(
                    chord=passing_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=position + 0.5,  # Between chords
                    voice_leading_quality=avg_voice_leading
                ))
                
            except Exception:
                continue
        
        # For larger descending intervals, try multiple passing chords
        # if distance >= 4:  # Major third or larger
        #     suggestions.extend(self._generate_sequential_passing_chords(
        #         chord1, chord2, key, position, 'descending'
        #     ))
        
        return suggestions
    
    def _generate_ascending_passing_chords(self, chord1: Chord, chord2: Chord,
                                         key: Key, position: int,
                                         distance: int) -> List[ChordSuggestion]:
        """Generate passing chords for ascending motion."""
        suggestions = []
        
        # Try chromatic passing chord (semitone above chord1)
        passing_root = chord1.root.transpose(1)
        
        passing_chord_options = self._get_passing_chord_qualities(
            passing_root, chord1, chord2, key, 'ascending'
        )
        
        for chord_quality, confidence_mod, reasoning_suffix in passing_chord_options:
            try:
                passing_chord = Chord(passing_root, chord_quality)
                
                base_confidence = 0.7 * confidence_mod  # Slightly lower for ascending
                
                voice_leading_quality = self._calculate_voice_leading_quality(
                    chord1, passing_chord
                )
                voice_leading_quality2 = self._calculate_voice_leading_quality(
                    passing_chord, chord2
                )
                
                avg_voice_leading = (voice_leading_quality + voice_leading_quality2) / 2
                confidence = min(0.9, base_confidence + avg_voice_leading * 0.2)
                
                reasoning = f"Chromatic approach chord from {chord1.symbol} to {chord2.symbol}"
                if reasoning_suffix:
                    reasoning += f" - {reasoning_suffix}"
                
                suggestions.append(ChordSuggestion(
                    chord=passing_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=position + 0.5,
                    voice_leading_quality=avg_voice_leading
                ))
                
            except Exception:
                continue
        
        return suggestions
    
    def _get_passing_chord_qualities(self, root, chord1: Chord, chord2: Chord, 
                                   key: Key, direction: str) -> List[Tuple[str, float, str]]:
        """Determine appropriate qualities for passing chords."""
        qualities = []
        
        # Diminished seventh chords are excellent passing chords
        qualities.append(('diminished7', 1.0, 'creates smooth voice leading'))
        
        # Dominant seventh for strong forward motion
        qualities.append(('dominant7', 0.85, 'provides forward harmonic drive'))
        
        # Half-diminished for softer color
        qualities.append(('half_diminished7', 0.75, 'adds sophisticated harmonic color'))
        
        # Minor for smoother color in certain contexts
        if self._is_minor_passing_appropriate(root, chord1, chord2, key):
            qualities.append(('minor', 0.65, 'creates gentle chromatic motion'))
        
        # Major triads can work in some contexts
        if self._is_major_passing_appropriate(root, chord1, chord2, key):
            qualities.append(('major', 0.6, 'provides bright passing harmony'))
        
        # Special case: if passing chord could function as secondary dominant
        if self._could_be_secondary_dominant(root, chord2, key):
            qualities.append(('dominant7', 0.9, 'functions as secondary dominant'))
        
        return qualities
    
    def _is_minor_passing_appropriate(self, root, chord1: Chord, 
                                    chord2: Chord, key: Key) -> bool:
        """Check if minor quality is appropriate for passing chord."""
        # Minor passing chords work well when they create stepwise motion
        # in the bass and don't clash with the harmonic context
        
        # Check if the passing chord root is in the key
        try:
            if key.contains_note(root):
                return True
        except:
            pass
        
        return False
    
    def _is_major_passing_appropriate(self, root, chord1: Chord,
                                    chord2: Chord, key: Key) -> bool:
        """Check if major quality is appropriate for passing chord."""
        # Major passing chords work in certain modal contexts
        
        # Check if this would be a diatonic major chord
        try:
            degree = key.scale.get_note_degree(root)
            if degree and degree in [1, 4, 5]:  # Natural major chord degrees
                return True
        except:
            pass
        
        return False
    
    def _could_be_secondary_dominant(self, root, target_chord: Chord, key: Key) -> bool:
        """Check if passing chord could function as secondary dominant."""
        # Check if the root is a perfect 5th above the target chord's root
        try:
            interval_to_target = Interval.from_notes(root, target_chord.root)
            if abs(interval_to_target.simple_semitones) == 7:  # Perfect 5th down (or 4th up)
                return True
        except:
            pass
        
        return False
    
    def _generate_sequential_passing_chords(self, chord1: Chord, chord2: Chord,
                                          key: Key, position: int,
                                          direction: str) -> List[ChordSuggestion]:
        """Generate multiple passing chords for large intervals."""
        suggestions = []
        
        # For now, focus on single passing chords
        # This could be extended to generate sequences of passing chords
        # for very large intervals (e.g., descending chromatic sequences)
        
        return suggestions