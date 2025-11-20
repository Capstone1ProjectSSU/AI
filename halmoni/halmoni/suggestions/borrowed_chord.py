"""Borrowed chord strategy implementation."""

from typing import List, Dict, Optional
from .base_strategy import ChordSuggestionStrategy, ChordSuggestion
from ..core import Chord, Key, ChordProgression


class BorrowedChordStrategy(ChordSuggestionStrategy):
    """Suggests borrowed chords from parallel and related modes."""
    
    # Common borrowed chord patterns and their typical usage
    COMMON_BORROWED_CHORDS = {
        'major_from_minor': {
            3: ('minor', 'Creates darker emotional color'),
            6: ('minor', 'Classic deceptive resolution preparation'),
            7: ('major', 'Modal mixture from natural minor'),
            4: ('minor', 'Plagal modal color'),
            2: ('diminished', 'Neapolitan preparation')
        },
        'minor_from_major': {
            1: ('major', 'Picardy third resolution'),
            4: ('major', 'Brightened subdominant'),
            5: ('major', 'Dominant in relative major'),
            3: ('major', 'Modal brightness'),
            6: ('major', 'Major submediant color')
        }
    }
    
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "BorrowedChord"
    
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate borrowed chord suggestions."""
        suggestions = []
        analysis_key = key or progression.key
        
        if not analysis_key:
            return suggestions
        
        # Analyze each position for borrowed chord opportunities
        for i, current_chord in enumerate(progression.chords):
            if self._is_good_borrowed_chord_position(progression, i, analysis_key):
                borrowed_suggestions = self._generate_borrowed_chords(
                    current_chord, analysis_key, i, progression
                )
                suggestions.extend(borrowed_suggestions)
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _is_good_borrowed_chord_position(self, progression: ChordProgression, 
                                       position: int, key: Key) -> bool:
        """Determine if position is suitable for borrowed chords."""
        current_chord = progression.chords[position]
        
        # Check if it's already a non-diatonic chord (might already be borrowed)
        if not self._is_diatonic_chord(current_chord, key):
            return False  # Don't suggest more borrowing on already borrowed chords
        
        # Borrowed chords work well in cadential positions
        if self._is_cadential_position(progression, position):
            return True
        
        # Check harmonic function - borrowed chords work well in certain functions
        function = self._get_harmonic_function(current_chord, key)
        if function in ['subdominant', 'tonic']:
            return True
        
        # Good before dominant chords (pre-dominant function)
        next_chord = self._get_next_chord(progression, position)
        if next_chord:
            next_function = self._get_harmonic_function(next_chord, key)
            if next_function == 'dominant':
                return True
        
        return False
    
    def _generate_borrowed_chords(self, current_chord: Chord, key: Key, 
                                position: int, progression: ChordProgression) -> List[ChordSuggestion]:
        """Generate specific borrowed chord suggestions."""
        suggestions = []
        
        # Get the degree of current chord in original key
        degree = self._get_scale_degree(current_chord, key)
        
        if not degree:
            return suggestions
        
        # Get parallel key (major ↔ minor)
        parallel_key = key.parallel_key
        
        # Generate borrowed chord from parallel key
        try:
            borrowed_chord = parallel_key.get_chord_for_degree(degree)
            
            # Only suggest if it's different from current chord
            if borrowed_chord != current_chord:
                confidence = self._calculate_borrowed_chord_confidence(
                    current_chord, borrowed_chord, key, position, progression
                )
                
                reasoning = self._get_borrowed_chord_reasoning(
                    degree, key.mode, parallel_key.mode
                )
                
                voice_leading_quality = self._calculate_voice_leading_quality(
                    current_chord, borrowed_chord
                )
                
                suggestions.append(ChordSuggestion(
                    chord=borrowed_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=voice_leading_quality
                ))
        
        except Exception:
            pass  # Skip if chord generation fails
        
        # Also try borrowing from other related modes (Dorian, Mixolydian)
        suggestions.extend(self._generate_modal_borrowed_chords(
            current_chord, key, degree, position, progression
        ))
        
        return suggestions
    
    def _generate_modal_borrowed_chords(self, current_chord: Chord, key: Key,
                                      degree: int, position: int, progression: ChordProgression) -> List[ChordSuggestion]:
        """Generate borrowed chords from other modes (Dorian, Mixolydian, etc.)."""
        suggestions = []
        
        # Only suggest modal borrowing for certain degrees in major keys
        if key.mode != 'major':
            return suggestions
        
        modal_suggestions = []
        
        # ♭VII from Mixolydian (very common in pop/rock)
        if degree == 7:
            try:
                # Create ♭VII chord (major chord built on ♭7 degree)
                flat_seventh_root = key.tonic.transpose(10)  # Minor 7th up
                mixolydian_chord = Chord(flat_seventh_root, 'major')
                
                confidence = self._calculate_modal_borrowed_confidence(
                    current_chord, mixolydian_chord, key, 'mixolydian'
                )
                
                reasoning = "♭VII borrowed from Mixolydian mode - common in popular music"
                
                modal_suggestions.append(ChordSuggestion(
                    chord=mixolydian_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=self._calculate_voice_leading_quality(
                        current_chord, mixolydian_chord
                    )
                ))
            except Exception:
                pass
        
        # ♭III from natural minor (also common)
        if degree == 3:
            try:
                flat_third_root = key.tonic.transpose(3)  # Minor 3rd up
                minor_borrowed_chord = Chord(flat_third_root, 'major')
                
                confidence = self._calculate_modal_borrowed_confidence(
                    current_chord, minor_borrowed_chord, key, 'natural_minor'
                )
                
                reasoning = "♭III borrowed from natural minor - adds modal color"
                
                modal_suggestions.append(ChordSuggestion(
                    chord=minor_borrowed_chord,
                    confidence=confidence,
                    reasoning=reasoning,
                    position=float(position),
                    voice_leading_quality=self._calculate_voice_leading_quality(
                        current_chord, minor_borrowed_chord
                    )
                ))
            except Exception:
                pass
        
        return modal_suggestions
    
    def _calculate_borrowed_chord_confidence(self, current_chord: Chord, 
                                           borrowed_chord: Chord, key: Key, 
                                           position: int, progression: ChordProgression) -> float:
        """Calculate confidence for borrowed chord suggestion."""
        base_confidence = 0.7
        
        # Higher confidence in minor keys (borrowed chords more idiomatic)
        if key.mode == 'minor':
            base_confidence += 0.1
        
        # Get current chord function
        function = self._get_harmonic_function(current_chord, key)
        
        # Higher confidence for certain functions
        if function == 'subdominant':
            base_confidence += 0.1  # iv chord in major is very common
        elif function == 'tonic' and position > 0:
            base_confidence += 0.05  # i chord for color
        
        # Voice leading quality affects confidence
        voice_leading = self._calculate_voice_leading_quality(current_chord, borrowed_chord)
        confidence = base_confidence + (voice_leading * 0.15)
        
        # Cadential positions get boost
        if position >= len(progression.chords) - 2:  # Approximate cadential check
            confidence += 0.1
        
        return min(0.95, confidence)
    
    def _calculate_modal_borrowed_confidence(self, current_chord: Chord,
                                           borrowed_chord: Chord, key: Key,
                                           source_mode: str) -> float:
        """Calculate confidence for modal borrowed chords."""
        base_confidence = 0.65  # Slightly lower than parallel mode borrowing
        
        # Mixolydian ♭VII is very common in popular music
        if source_mode == 'mixolydian':
            base_confidence += 0.15
        
        # Voice leading consideration
        voice_leading = self._calculate_voice_leading_quality(current_chord, borrowed_chord)
        confidence = base_confidence + (voice_leading * 0.1)
        
        return min(0.9, confidence)
    
    def _get_borrowed_chord_reasoning(self, degree: int, original_mode: str, 
                                    borrowed_mode: str) -> str:
        """Generate reasoning text for borrowed chord."""
        degree_names = {1: 'I', 2: 'ii', 3: 'iii', 4: 'IV', 5: 'V', 6: 'vi', 7: 'vii'}
        
        if original_mode == 'major' and borrowed_mode == 'minor':
            mode_desc = "natural minor"
            if degree == 4:
                return f"Borrowed iv chord from {mode_desc} - creates plagal modal color"
            elif degree == 6:
                return f"Borrowed vi chord from {mode_desc} - deceptive resolution preparation"
            elif degree == 7:
                return f"Borrowed ♭VII chord from {mode_desc} - modal mixture"
            elif degree == 3:
                return f"Borrowed iii chord from {mode_desc} - darker emotional color"
            else:
                return f"Borrowed {degree_names.get(degree, str(degree))} chord from {mode_desc}"
        
        elif original_mode == 'minor' and borrowed_mode == 'major':
            mode_desc = "parallel major"
            if degree == 1:
                return f"Picardy third - borrowed I chord from {mode_desc}"
            elif degree == 4:
                return f"Borrowed IV chord from {mode_desc} - brightened subdominant"
            elif degree == 5:
                return f"Borrowed V chord from {mode_desc} - stronger dominant"
            else:
                return f"Borrowed {degree_names.get(degree, str(degree))} chord from {mode_desc}"
        
        return f"Modal interchange from {borrowed_mode} mode"