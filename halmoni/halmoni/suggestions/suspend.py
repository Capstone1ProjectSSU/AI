"""Suspension chord strategy implementation."""

from typing import List, Optional
from .base_strategy import ChordSuggestionStrategy, ChordSuggestion
from ..core import Chord, Key, ChordProgression


class SuspendStrategy(ChordSuggestionStrategy):
    """Suggests suspension chords and resolutions."""
    
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "Suspend"
    
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate suspension chord suggestions."""
        suggestions = []
        analysis_key = key or progression.key
        
        # Suggest suspensions for existing chords
        for i, chord in enumerate(progression.chords):
            if self._is_good_suspension_candidate(chord, analysis_key):
                suspension_suggestions = self._generate_suspensions(
                    chord, analysis_key, i
                )
                suggestions.extend(suspension_suggestions)
        
        # Suggest suspension-resolution pairs
        for i in range(len(progression.chords) - 1):
            resolution_suggestions = self._generate_suspension_resolutions(
                progression.chords[i], progression.chords[i + 1], analysis_key, i
            )
            suggestions.extend(resolution_suggestions)
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _is_good_suspension_candidate(self, chord: Chord, key: Optional[Key]) -> bool:
        """Check if chord is suitable for suspension treatment."""
        
        # Major and minor triads work excellently with suspensions
        if chord.quality in ['major', 'minor']:
            return True
        
        # Dominant chords benefit greatly from sus4
        if chord.quality in ['dominant7', 'dominant9', 'dominant11', 'dominant13']:
            return True
        
        # Major 7th and minor 7th chords can work with suspensions
        if chord.quality in ['major7', 'minor7']:
            return True
        
        return False
    
    def _generate_suspensions(self, chord: Chord, key: Optional[Key], 
                            position: int) -> List[ChordSuggestion]:
        """Generate suspension chord suggestions."""
        suggestions = []
        
        # Sus2 suggestions (2nd replacing 3rd)
        if self._can_use_sus2(chord):
            try:
                sus2_chord = Chord(chord.root, 'sus2', chord.bass)
                confidence = self._calculate_suspension_confidence(
                    chord, sus2_chord, key, position, 'sus2'
                )
                
                reasoning = self._get_suspension_reasoning(chord, 'sus2', key)
                
                voice_leading_quality = self._calculate_voice_leading_quality(
                    chord, sus2_chord
                )
                
                suggestions.append(ChordSuggestion(
                    chord=sus2_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=voice_leading_quality
                ))
                
            except Exception:
                pass
        
        # Sus4 suggestions (4th replacing 3rd)
        if self._can_use_sus4(chord):
            try:
                sus4_chord = Chord(chord.root, 'sus4', chord.bass)
                confidence = self._calculate_suspension_confidence(
                    chord, sus4_chord, key, position, 'sus4'
                )
                
                # Sus4 is particularly effective on dominant chords
                if chord.quality in ['dominant7', 'major']:
                    confidence = min(0.95, confidence + 0.1)
                
                reasoning = self._get_suspension_reasoning(chord, 'sus4', key)
                
                voice_leading_quality = self._calculate_voice_leading_quality(
                    chord, sus4_chord
                )
                
                suggestions.append(ChordSuggestion(
                    chord=sus4_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=voice_leading_quality
                ))
                
            except Exception:
                pass
        
        # Mixed suspensions for advanced harmony
        # if self._can_use_mixed_suspensions(chord):
        #     mixed_suggestions = self._generate_mixed_suspensions(chord, key, position)
        #     suggestions.extend(mixed_suggestions)
        
        return suggestions
    
    def _can_use_sus2(self, chord: Chord) -> bool:
        """Check if sus2 is appropriate for this chord."""
        # Sus2 works well with major and minor triads
        if chord.quality in ['major', 'minor']:
            return True
        
        # Also works with some seventh chords
        if chord.quality in ['major7', 'minor7']:
            return True
        
        return False
    
    def _can_use_sus4(self, chord: Chord) -> bool:
        """Check if sus4 is appropriate for this chord."""
        # Sus4 works well with most chord types
        suitable_qualities = [
            'major', 'minor', 'dominant7', 'major7', 'minor7',
            'dominant9', 'major9', 'minor9'
        ]
        
        return chord.quality in suitable_qualities
    
    def _can_use_mixed_suspensions(self, chord: Chord) -> bool:
        """Check if mixed suspensions (multiple suspended tones) are appropriate."""
        # Mixed suspensions work well with extended chords
        extended_qualities = [
            'dominant9', 'dominant11', 'dominant13',
            'major9', 'major11', 'major13',
            'minor9', 'minor11', 'minor13'
        ]
        
        return chord.quality in extended_qualities
    
    def _generate_mixed_suspensions(self, chord: Chord, key: Optional[Key],
                                  position: int) -> List[ChordSuggestion]:
        """Generate more complex suspension suggestions."""
        suggestions = []
        
        # For now, keep it simple - this could be extended to include
        # add2, add4, sus2sus4, etc. when those chord types are available
        
        return suggestions
    
    def _generate_suspension_resolutions(self, chord1: Chord, chord2: Chord, 
                                       key: Optional[Key], position: int) -> List[ChordSuggestion]:
        """Generate suspension-resolution chord pairs."""
        suggestions = []
        
        # Check if we can create a suspension that resolves to chord2
        if self._chords_suitable_for_suspension_resolution(chord1, chord2):
            
            # Try to create suspended version of chord1 that resolves to chord2
            resolving_suspension = self._create_resolving_suspension(chord1, chord2)
            
            if resolving_suspension:
                confidence = 0.85  # High confidence for proper resolutions
                
                reasoning = self._get_resolution_reasoning(chord1, chord2, resolving_suspension)
                
                suggestions.append(ChordSuggestion(
                    chord=resolving_suspension,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=0.9  # Suspensions create excellent voice leading
                ))
        
        return suggestions
    
    def _chords_suitable_for_suspension_resolution(self, chord1: Chord, chord2: Chord) -> bool:
        """Check if these chords are suitable for suspension-resolution treatment."""
        
        # Same root note is ideal for suspension resolution
        if chord1.root.pitch_class == chord2.root.pitch_class:
            return True
        
        # Related chords (sharing common tones) can work
        common_tones = chord1.pitch_classes.intersection(chord2.pitch_classes)
        if len(common_tones) >= 2:
            return True
        
        # Dominant to tonic resolution is classic
        if chord1.quality in ['dominant7', 'dominant9'] and chord2.quality in ['major', 'minor']:
            return True
        
        return False
    
    def _create_resolving_suspension(self, chord1: Chord, chord2: Chord) -> Optional[Chord]:
        """Create a suspended version of chord1 that resolves smoothly to chord2."""
        
        # If same root, try sus4 resolving to major/minor
        if chord1.root.pitch_class == chord2.root.pitch_class:
            if chord2.quality in ['major', 'minor'] and chord1.quality != 'sus4':
                try:
                    return Chord(chord1.root, 'sus4', chord1.bass)
                except:
                    pass
            
            # Try sus2 in some contexts
            if chord2.quality in ['major', 'minor'] and chord1.quality != 'sus2':
                try:
                    return Chord(chord1.root, 'sus2', chord1.bass)
                except:
                    pass
        
        return None
    
    def _calculate_suspension_confidence(self, original_chord: Chord, 
                                       suspended_chord: Chord, key: Optional[Key],
                                       position: int, sus_type: str) -> float:
        """Calculate confidence for suspension suggestion."""
        
        base_confidence_map = {
            'sus2': 0.75,
            'sus4': 0.8,   # Slightly higher - more common
        }
        
        base_confidence = base_confidence_map.get(sus_type, 0.7)
        
        # Higher confidence for functional harmony positions
        if key:
            function = self._get_harmonic_function(original_chord, key)
            if function in ['dominant', 'subdominant']:
                base_confidence += 0.15
        
        # Sus4 on dominant chords is particularly effective
        if sus_type == 'sus4' and original_chord.quality in ['dominant7', 'major']:
            base_confidence += 0.1
        
        # Contemporary music context (simplified detection)
        if original_chord.quality in ['major', 'minor']:
            base_confidence += 0.05  # Sus chords popular in contemporary music
        
        return min(0.95, base_confidence)
    
    def _get_suspension_reasoning(self, original_chord: Chord, sus_type: str, 
                                key: Optional[Key]) -> str:
        """Generate reasoning text for suspension suggestion."""
        
        chord_symbol = original_chord.symbol
        
        reasoning_map = {
            'sus2': f"Sus2 suspension of {chord_symbol} creating melodic tension and modern harmonic color",
            'sus4': f"Sus4 suspension of {chord_symbol} creating harmonic tension that resolves to the third"
        }
        
        base_reasoning = reasoning_map.get(sus_type, 
                                         f"Suspension of {chord_symbol} adding harmonic interest")
        
        # Add context about function if available
        if key:
            function = self._get_harmonic_function(original_chord, key)
            if function == 'dominant':
                base_reasoning += " - particularly effective on dominant chords"
            elif function == 'tonic':
                base_reasoning += " - adds color to tonic harmony"
        
        return base_reasoning
    
    def _get_resolution_reasoning(self, chord1: Chord, chord2: Chord, 
                                suspension_chord: Chord) -> str:
        """Generate reasoning for suspension-resolution pairs."""
        
        return (f"Suspension-resolution pattern: {suspension_chord.symbol} → {chord2.symbol} "
                f"creating smooth voice leading and harmonic motion")