"""Tritone substitution strategy implementation."""

from typing import List, Optional
from .base_strategy import ChordSuggestionStrategy, ChordSuggestion
from ..core import Chord, Key, ChordProgression, Note, Interval


class SubV7Strategy(ChordSuggestionStrategy):
    """Suggests tritone substitution chords."""
    
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "SubV7"
    
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate tritone substitution suggestions."""
        suggestions = []
        analysis_key = key or progression.key
        
        if not analysis_key:
            return suggestions
        
        # Look for dominant chords to substitute
        for i, chord in enumerate(progression.chords):
            if self._is_substitutable_dominant(chord, analysis_key):
                sub_suggestions = self._generate_tritone_substitutions(
                    chord, analysis_key, i, progression
                )
                suggestions.extend(sub_suggestions)
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _is_substitutable_dominant(self, chord: Chord, key: Key) -> bool:
        """Check if chord is suitable for tritone substitution."""
        # Must be a dominant seventh chord or extension
        dominant_qualities = ['dominant7', 'dominant9', 'dominant11', 'dominant13']
        
        if chord.quality not in dominant_qualities:
            return False
        
        # Analyze function in key
        function = self._get_harmonic_function(chord, key)
        
        # Most effective on dominant function chords
        if function == 'dominant':
            return True
        
        # Also works on secondary dominants (non-diatonic dominants)
        if not self._is_diatonic_chord(chord, key) and 'dominant' in chord.quality:
            return True
        
        return False
    
    def _generate_tritone_substitutions(self, dominant_chord: Chord, 
                                      key: Key, position: int,
                                      progression: ChordProgression) -> List[ChordSuggestion]:
        """Generate tritone substitution suggestions."""
        suggestions = []
        
        # Calculate tritone substitution root (6 semitones away)
        sub_root = dominant_chord.root.transpose(6)  # Tritone
        
        # Create basic substitution chord
        try:
            # Start with same quality as original
            sub_chord = Chord(sub_root, dominant_chord.quality)
            
            confidence = self._calculate_sub_confidence(
                dominant_chord, sub_chord, key, position, progression
            )
            
            reasoning = self._get_sub_reasoning(dominant_chord, sub_chord, key)
            
            voice_leading_quality = self._calculate_tritone_voice_leading(
                dominant_chord, sub_chord, progression, position
            )
            
            suggestions.append(ChordSuggestion(
                chord=sub_chord,
                confidence=confidence,
                reasoning=reasoning,
                position=float(position),
                voice_leading_quality=voice_leading_quality
            ))
            
            # Generate additional substitution variations
            additional_subs = self._generate_sub_variations(
                sub_root, dominant_chord, key, position, progression
            )
            suggestions.extend(additional_subs)
            
        except Exception:
            pass  # Skip if chord creation fails
        
        return suggestions
    
    def _generate_sub_variations(self, sub_root: Note, original_chord: Chord,
                               key: Key, position: int, progression: ChordProgression) -> List[ChordSuggestion]:
        """Generate variations of the tritone substitution."""
        variations = []
        
        # If original was simple dominant7, try extensions
        if original_chord.quality == 'dominant7':
            extension_qualities = ['dominant9', 'dominant13']
            
            for quality in extension_qualities:
                try:
                    var_chord = Chord(sub_root, quality)
                    
                    confidence = self._calculate_sub_confidence(
                        original_chord, var_chord, key, position, progression
                    ) * 0.85  # Slightly lower confidence for extensions
                    
                    reasoning = f"Tritone substitution with {quality} extension for added sophistication"
                    
                    variations.append(ChordSuggestion(
                        chord=var_chord,
                        confidence=confidence,
                        reasoning=reasoning,
                        position=float(position),
                        voice_leading_quality=0.8  # Generally good voice leading
                    ))
                    
                except Exception:
                    continue
        
        # Try altered dominants for jazz flavor
        altered_qualities = self._get_altered_dominant_qualities(original_chord)
        
        for quality, alt_description in altered_qualities:
            try:
                alt_chord = Chord(sub_root, quality)
                
                confidence = self._calculate_sub_confidence(
                    original_chord, alt_chord, key, position, progression
                ) * 0.75  # Lower confidence for altered chords
                
                reasoning = f"Altered tritone substitution ({alt_description}) for jazz harmony"
                
                variations.append(ChordSuggestion(
                    chord=alt_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=0.75
                ))
                
            except Exception:
                continue
        
        return variations
    
    def _get_altered_dominant_qualities(self, original_chord: Chord) -> List[tuple]:
        """Get altered dominant chord qualities for substitution."""
        # This is simplified - in a full implementation, we'd have more
        # sophisticated altered chord types
        
        altered_options = []
        
        # Basic altered dominants that might be supported
        if hasattr(Chord, 'CHORD_TONES'):  # Check if these qualities exist
            potential_alterations = [
                ('dominant7b5', 'with ♭5'),
                ('dominant7#5', 'with #5'),
            ]
            
            for quality, description in potential_alterations:
                if quality in Chord.CHORD_TONES:
                    altered_options.append((quality, description))
        
        return altered_options
    
    def _calculate_sub_confidence(self, original_chord: Chord, 
                                 sub_chord: Chord, key: Key, position: int,
                                 progression: Optional[ChordProgression]) -> float:
        """Calculate confidence for tritone substitution."""
        base_confidence = 0.8
        
        # Higher confidence for V7 chords (most common usage)
        original_degree = self._get_scale_degree(original_chord, key)
        if original_degree == 5:
            base_confidence += 0.1
        
        # Check for smooth bass line creation
        if progression and self._creates_smooth_bass_line(sub_chord, progression, position):
            base_confidence += 0.1
        
        # Higher confidence if resolving to tonic
        if progression and position < len(progression.chords) - 1:
            next_chord = progression.chords[position + 1]
            next_function = self._get_harmonic_function(next_chord, key)
            if next_function == 'tonic':
                base_confidence += 0.1
        
        # Jazz context detection (simplified)
        if self._appears_to_be_jazz_context(progression, key):
            base_confidence += 0.15
        
        return min(0.95, base_confidence)
    
    def _calculate_tritone_voice_leading(self, original_chord: Chord, 
                                       sub_chord: Chord, 
                                       progression: ChordProgression,
                                       position: int) -> float:
        """Calculate voice leading quality specific to tritone substitutions."""
        
        # Tritone subs share the same tritone (3rd and 7th)
        # This creates excellent voice leading by nature
        base_voice_leading = 0.85
        
        # Check resolution to next chord if it exists
        if position < len(progression.chords) - 1:
            next_chord = progression.chords[position + 1]
            
            # Tritone subs often create smoother bass motion
            orig_bass_motion = self._calculate_bass_motion_smoothness(
                original_chord, next_chord
            )
            sub_bass_motion = self._calculate_bass_motion_smoothness(
                sub_chord, next_chord
            )
            
            if sub_bass_motion > orig_bass_motion:
                base_voice_leading += 0.1  # Bonus for smoother bass line
        
        return min(1.0, base_voice_leading)
    
    def _calculate_bass_motion_smoothness(self, chord1: Chord, chord2: Chord) -> float:
        """Calculate how smooth the bass motion is between two chords."""
        try:
            interval = Interval.from_notes(chord1.root, chord2.root)
            semitones = abs(interval.simple_semitones)
            
            # Smaller intervals are smoother
            if semitones <= 2:  # Stepwise motion
                return 1.0
            elif semitones <= 4:  # Small leaps
                return 0.7
            elif semitones in [5, 7]:  # Perfect intervals
                return 0.6
            else:
                return 0.4
        except:
            return 0.5
    
    def _creates_smooth_bass_line(self, sub_chord: Chord, 
                                 progression: ChordProgression, 
                                 position: int) -> bool:
        """Check if substitution creates a smoother bass line."""
        
        # Check motion to previous chord
        if position > 0:
            prev_chord = progression.chords[position - 1]
            prev_motion = self._calculate_bass_motion_smoothness(prev_chord, sub_chord)
            if prev_motion >= 0.8:  # Very smooth
                return True
        
        # Check motion to next chord
        if position < len(progression.chords) - 1:
            next_chord = progression.chords[position + 1]
            next_motion = self._calculate_bass_motion_smoothness(sub_chord, next_chord)
            if next_motion >= 0.8:  # Very smooth
                return True
        
        return False
    
    def _appears_to_be_jazz_context(self, progression: Optional[ChordProgression], 
                                   key: Key) -> bool:
        """Simple heuristic to detect jazz-style progressions."""
        if not progression:
            return False
        
        # Look for ii-V-I patterns or extended chords
        jazz_indicators = 0
        
        for chord in progression.chords:
            # Extended chords suggest jazz
            if chord.quality in ['major7', 'minor7', 'dominant7', 'dominant9', 
                               'dominant11', 'dominant13', 'minor9', 'major9']:
                jazz_indicators += 1
        
        # If more than half the chords are extended, likely jazz context
        return jazz_indicators >= len(progression.chords) / 2
    
    def _get_sub_reasoning(self, original_chord: Chord, sub_chord: Chord, key: Key) -> str:
        """Generate reasoning text for tritone substitution."""
        
        # Get scale degree of original chord for description
        degree = self._get_scale_degree(original_chord, key)
        degree_names = {1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI', 7: 'VII'}
        degree_name = degree_names.get(degree, str(degree))
        
        base_reasoning = f"Tritone substitution of {original_chord.symbol}"
        
        if degree == 5:
            base_reasoning += f" (♭{degree_name}7 substituting V7)"
        else:
            base_reasoning += f" creating chromatic bass motion"
        
        base_reasoning += " - shares same tritone for smooth voice leading"
        
        return base_reasoning