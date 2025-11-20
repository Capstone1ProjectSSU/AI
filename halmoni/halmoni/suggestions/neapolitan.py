"""Neapolitan chord strategy implementation."""

from typing import List, Dict, Optional
from .base_strategy import ChordSuggestionStrategy, ChordSuggestion
from ..core import Chord, Key, ChordProgression, Note


class NeapolitanStrategy(ChordSuggestionStrategy):
    """Suggests Neapolitan sixth chords and related harmonies."""
    
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "Neapolitan"
    
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate Neapolitan chord suggestions."""
        suggestions = []
        analysis_key = key or progression.key
        
        if not analysis_key:
            return suggestions
        
        # Look for pre-dominant positions where Neapolitan chords would work
        for i, chord in enumerate(progression.chords):
            if self._is_good_neapolitan_position(progression, i, analysis_key):
                neapolitan_suggestions = self._generate_neapolitan_chords(
                    chord, analysis_key, i, progression
                )
                suggestions.extend(neapolitan_suggestions)
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _is_good_neapolitan_position(self, progression: ChordProgression, 
                                   position: int, key: Key) -> bool:
        """Identify positions suitable for Neapolitan chords."""
        current_chord = progression.chords[position]
        
        # Check current chord's function
        function = self._get_harmonic_function(current_chord, key)
        
        # Neapolitans work excellently in pre-dominant function
        if function == 'subdominant':
            return True
        
        # Check if next chord is dominant (classic Neapolitan usage)
        next_chord = self._get_next_chord(progression, position)
        if next_chord:
            next_function = self._get_harmonic_function(next_chord, key)
            if next_function == 'dominant':
                return True
        
        # Good in cadential positions (before dominant-tonic cadences)
        if self._is_cadential_position(progression, position):
            # Check if we're setting up a cadence
            if position < len(progression.chords) - 1:
                remaining_chords = progression.chords[position + 1:]
                if any(self._get_harmonic_function(c, key) == 'dominant' for c in remaining_chords):
                    return True
        
        # Neapolitans also work well replacing ii chords in ii-V-I progressions
        degree = self._get_scale_degree(current_chord, key)
        if degree == 2:  # ii chord position
            return True
        
        return False
    
    def _generate_neapolitan_chords(self, current_chord: Chord,
                                  key: Key, position: int,
                                  progression: ChordProgression) -> List[ChordSuggestion]:
        """Generate Neapolitan chord variations."""
        suggestions = []
        
        # Calculate ♭II root (minor second above tonic)
        flat_ii_root = key.tonic.transpose(1)  # Minor second up
        
        # Create basic Neapolitan chord (♭II major triad)
        try:
            neapolitan_triad = Chord(flat_ii_root, 'major')
            
            # Neapolitan sixth (first inversion - most common)
            neapolitan_sixth = self._create_neapolitan_sixth(neapolitan_triad)
            
            if neapolitan_sixth:
                confidence = self._calculate_neapolitan_confidence(
                    current_chord, neapolitan_sixth, key, position, 'sixth', progression
                )
                
                reasoning = self._get_neapolitan_reasoning(key, 'sixth')
                
                voice_leading_quality = self._calculate_voice_leading_quality(
                    current_chord, neapolitan_sixth
                )
                
                suggestions.append(ChordSuggestion(
                    chord=neapolitan_sixth,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=voice_leading_quality
                ))
            
            # Root position Neapolitan (less common but valid)
            root_position_confidence = self._calculate_neapolitan_confidence(
                current_chord, neapolitan_triad, key, position, 'root', progression
            )
            
            suggestions.append(ChordSuggestion(
                chord=neapolitan_triad,
                confidence=root_position_confidence,
                reasoning=self._get_neapolitan_reasoning(key, 'root'),
                position=float(position),
                voice_leading_quality=self._calculate_voice_leading_quality(
                    current_chord, neapolitan_triad
                )
            ))
            
            # Neapolitan seventh (♭II7) for added sophistication
            neapolitan_seventh = self._create_neapolitan_seventh(flat_ii_root)
            if neapolitan_seventh:
                seventh_confidence = self._calculate_neapolitan_confidence(
                    current_chord, neapolitan_seventh, key, position, 'seventh', progression
                )
                
                suggestions.append(ChordSuggestion(
                    chord=neapolitan_seventh,
                    confidence=seventh_confidence,
                    reasoning=self._get_neapolitan_reasoning(key, 'seventh'),
                    position=float(position),
                    voice_leading_quality=self._calculate_voice_leading_quality(
                        current_chord, neapolitan_seventh
                    )
                ))
        
        except Exception:
            pass  # Skip if chord creation fails
        
        return suggestions
    
    def _create_neapolitan_sixth(self, neapolitan_triad: Chord) -> Optional[Chord]:
        """Create Neapolitan sixth chord (first inversion)."""
        try:
            # First inversion means the third of the chord is in the bass
            chord_notes = neapolitan_triad.notes
            if len(chord_notes) >= 2:
                third_note = chord_notes[1]  # Third of the triad
                return Chord(neapolitan_triad.root, 'major', third_note)
        except Exception:
            pass
        return None
    
    def _create_neapolitan_seventh(self, flat_ii_root: Note) -> Optional[Chord]:
        """Create Neapolitan seventh chord for added color."""
        try:
            # Could be major 7th, dominant 7th, or minor 7th depending on context
            # Dominant 7th is most common for functional harmony
            return Chord(flat_ii_root, 'dominant7')
        except Exception:
            return None
    
    def _calculate_neapolitan_confidence(self, current_chord: Chord,
                                       neapolitan_chord: Chord, key: Key,
                                       position: int, chord_type: str,
                                       progression: ChordProgression) -> float:
        """Calculate confidence for Neapolitan suggestion."""

        # Base confidence varies by chord type
        base_confidence_map = {
            'sixth': 0.85,    # Most idiomatic
            'root': 0.65,     # Less common but valid
            'seventh': 0.75   # More sophisticated
        }

        base_confidence = base_confidence_map.get(chord_type, 0.7)

        # Higher confidence in minor keys (more idiomatic)
        if key.mode == 'minor':
            base_confidence += 0.1

        # Check current chord's function
        current_function = self._get_harmonic_function(current_chord, key)

        # Higher confidence if replacing subdominant function
        if current_function == 'subdominant':
            base_confidence += 0.1

        # Boost if current chord is ii chord (classic substitution)
        current_degree = self._get_scale_degree(current_chord, key)
        if current_degree == 2:
            base_confidence += 0.15

        # Analyze resolution quality in context
        resolution_analysis = self._analyze_neapolitan_resolution(
            progression, position, key
        )

        # Boost confidence for good resolutions
        if resolution_analysis['has_dominant_resolution']:
            base_confidence += 0.1  # Classic N6 → V progression

        # Add resolution quality bonus (0.0 to 0.5)
        base_confidence += resolution_analysis['resolution_quality'] * 0.2

        # Check voice leading quality
        voice_leading = self._calculate_voice_leading_quality(
            current_chord, neapolitan_chord
        )

        # Neapolitan sixth traditionally has excellent voice leading
        if chord_type == 'sixth':
            voice_leading += 0.1  # Bonus for traditional voice leading

        final_confidence = base_confidence + (voice_leading * 0.1)

        return min(0.95, final_confidence)
    
    def _get_neapolitan_reasoning(self, key: Key, chord_type: str) -> str:
        """Generate reasoning text for Neapolitan chord."""
        key_desc = f"{key.tonic.pitch_class} {key.mode}"
        
        reasoning_map = {
            'sixth': f"Neapolitan sixth chord (♭II⁶) providing dramatic pre-dominant function in {key_desc}",
            'root': f"Root position Neapolitan chord (♭II) adding harmonic color in {key_desc}",
            'seventh': f"Neapolitan seventh chord (♭II⁷) for sophisticated pre-dominant harmony in {key_desc}"
        }
        
        base_reasoning = reasoning_map.get(chord_type, 
                                         f"Neapolitan chord providing pre-dominant function in {key_desc}")
        
        # Add context about traditional usage
        if key.mode == 'minor':
            base_reasoning += " - particularly effective in minor keys"
        else:
            base_reasoning += " - borrowed from minor mode for dramatic effect"
        
        return base_reasoning
    
    def _analyze_neapolitan_resolution(self, progression: ChordProgression,
                                     position: int, key: Key) -> Dict[str, any]:
        """Analyze how well a Neapolitan would resolve in context."""
        analysis = {
            'has_dominant_resolution': False,
            'resolution_quality': 0.5,
            'creates_good_bass_line': False
        }
        
        # Check if there's a dominant chord following
        if position < len(progression.chords) - 1:
            next_chord = progression.chords[position + 1]
            next_function = self._get_harmonic_function(next_chord, key)
            
            if next_function == 'dominant':
                analysis['has_dominant_resolution'] = True
                analysis['resolution_quality'] += 0.3
                
                # Check for eventual tonic resolution
                if position < len(progression.chords) - 2:
                    final_chord = progression.chords[position + 2]
                    final_function = self._get_harmonic_function(final_chord, key)
                    if final_function == 'tonic':
                        analysis['resolution_quality'] += 0.2
        
        return analysis