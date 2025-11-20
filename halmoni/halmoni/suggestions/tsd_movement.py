"""Functional harmony (Tonic-Subdominant-Dominant) movement strategy implementation."""

from typing import List, Optional, Tuple
from .base_strategy import ChordSuggestionStrategy, ChordSuggestion
from ..core import Chord, Key, ChordProgression


class TSDMovementStrategy(ChordSuggestionStrategy):
    """Suggests chords based on functional harmony principles."""
    
    # Functional groups for major and minor keys
    FUNCTIONAL_GROUPS = {
        'major': {
            'tonic': [1, 6, 3],      # I, vi, iii
            'subdominant': [4, 2],   # IV, ii
            'dominant': [5, 7]       # V, vii°
        },
        'minor': {
            'tonic': [1, 6, 3],          # i, VI, III
            'subdominant': [4, 2, 6],    # iv, ii°, VI (also subdominant in minor)
            'dominant': [5, 7]           # V, vii°
        }
    }
    
    # Preferred functional progressions (from → to)
    PREFERRED_PROGRESSIONS = [
        ('tonic', 'subdominant', 0.9),      # T → S (strong)
        ('subdominant', 'dominant', 1.0),   # S → D (strongest)
        ('dominant', 'tonic', 1.0),         # D → T (strongest)
        ('tonic', 'dominant', 0.7),         # T → D (direct, less common)
        ('subdominant', 'tonic', 0.6),      # S → T (plagal)
        ('dominant', 'subdominant', 0.3),   # D → S (retrograde, avoid)
    ]
    
    def get_strategy_name(self) -> str:
        """Return the strategy name."""
        return "TSDMovement"
    
    def suggest(self, progression: ChordProgression, 
                key: Optional[Key] = None) -> List[ChordSuggestion]:
        """Generate functional harmony suggestions."""
        suggestions = []
        analysis_key = key or progression.key
        
        if not analysis_key:
            return suggestions
        
        # Analyze current functional progression
        functional_analysis = self._analyze_functional_progression(progression, analysis_key)
        
        # Suggest improvements to functional flow
        for i, (chord, function) in enumerate(functional_analysis):
            improvement_suggestions = self._suggest_functional_improvements(
                progression, i, function, analysis_key
            )
            suggestions.extend(improvement_suggestions)
        
        # Suggest additional chords to complete functional patterns
        completion_suggestions = self._suggest_functional_completions(
            progression, functional_analysis, analysis_key
        )
        suggestions.extend(completion_suggestions)
        
        return sorted(suggestions, key=lambda x: x.confidence, reverse=True)
    
    def _analyze_functional_progression(self, progression: ChordProgression, 
                                      key: Key) -> List[Tuple[Chord, str]]:
        """Analyze the functional progression of chords."""
        functional_analysis = []
        
        for chord in progression.chords:
            function = self._get_harmonic_function(chord, key)
            functional_analysis.append((chord, function))
        
        return functional_analysis
    
    def _suggest_functional_improvements(self, progression: ChordProgression, 
                                       position: int, current_function: str, 
                                       key: Key) -> List[ChordSuggestion]:
        """Suggest improvements to strengthen functional harmony."""
        suggestions = []
        current_chord = progression.chords[position]
        
        # Skip if function is unknown
        if current_function == 'unknown':
            return suggestions
        
        # Get current chord's degree
        degree = self._get_scale_degree(current_chord, key)
        
        if degree and current_function in self.FUNCTIONAL_GROUPS[key.mode]:
            # Suggest stronger functional alternatives within the same function
            functional_group = self.FUNCTIONAL_GROUPS[key.mode][current_function]
            
            for alt_degree in functional_group:
                if alt_degree != degree:
                    try:
                        alt_chord = key.get_chord_for_degree(alt_degree)
                        if alt_chord != current_chord:
                            confidence = self._calculate_functional_confidence(
                                current_chord, alt_chord, current_function, key, position
                            )
                            
                            if confidence > 0.6:  # Only suggest if reasonably confident
                                reasoning = self._get_functional_improvement_reasoning(
                                    current_chord, alt_chord, current_function, alt_degree
                                )
                                
                                voice_leading_quality = self._calculate_voice_leading_quality(
                                    current_chord, alt_chord
                                )
                                
                                suggestions.append(ChordSuggestion(
                                    chord=alt_chord,
                                    confidence=confidence,
                                    reasoning=reasoning,
                                    position=float(position),
                                    voice_leading_quality=voice_leading_quality
                                ))
                    except Exception:
                        continue
        
        return suggestions
    
    def _suggest_functional_completions(self, progression: ChordProgression,
                                      functional_analysis: List[Tuple[Chord, str]],
                                      key: Key) -> List[ChordSuggestion]:
        """Suggest additional chords to complete functional patterns."""
        suggestions = []
        
        # Look for incomplete or weak functional progressions
        for i in range(len(functional_analysis) - 1):
            current_function = functional_analysis[i][1]
            next_function = functional_analysis[i + 1][1]
            
            # Check if we should insert a chord between these functions
            if self._should_insert_functional_bridge(current_function, next_function):
                bridge_suggestions = self._get_functional_bridge_suggestions(
                    current_function, next_function, key, i
                )
                suggestions.extend(bridge_suggestions)
        
        # Suggest cadential completions
        cadential_suggestions = self._suggest_cadential_completions(
            progression, functional_analysis, key
        )
        suggestions.extend(cadential_suggestions)
        
        return suggestions
    
    def _should_insert_functional_bridge(self, func1: str, func2: str) -> bool:
        """Determine if a bridge chord would improve functional flow."""
        
        # Skip unknown functions
        if func1 == 'unknown' or func2 == 'unknown':
            return False
        
        # Check if this progression is weak and could use strengthening
        weak_progressions = [
            ('tonic', 'dominant'),      # Could use subdominant bridge
            ('dominant', 'subdominant'), # Retrograde - could use tonic bridge
            ('tonic', 'tonic'),         # Static - needs motion
            ('subdominant', 'subdominant'), # Static - needs motion
            ('dominant', 'dominant'),   # Static - needs resolution
        ]
        
        return (func1, func2) in weak_progressions
    
    def _get_functional_bridge_suggestions(self, func1: str, func2: str, 
                                         key: Key, position: int) -> List[ChordSuggestion]:
        """Get specific bridge chord suggestions."""
        suggestions = []
        
        # Tonic to dominant: insert subdominant
        if func1 == 'tonic' and func2 == 'dominant':
            subdominant_degrees = self.FUNCTIONAL_GROUPS[key.mode]['subdominant']
            
            for degree in subdominant_degrees:
                try:
                    bridge_chord = key.get_chord_for_degree(degree)
                    
                    suggestions.append(ChordSuggestion(
                        chord=bridge_chord,
                        confidence=0.8,
                        reasoning=f"Subdominant bridge chord to strengthen T-S-D progression",
                        position=position + 0.5,
                        voice_leading_quality=0.8
                    ))
                except Exception:
                    continue
        
        # Dominant to subdominant (retrograde): insert tonic
        elif func1 == 'dominant' and func2 == 'subdominant':
            tonic_degrees = self.FUNCTIONAL_GROUPS[key.mode]['tonic']
            
            for degree in tonic_degrees[:1]:  # Just suggest primary tonic
                try:
                    bridge_chord = key.get_chord_for_degree(degree)
                    
                    suggestions.append(ChordSuggestion(
                        chord=bridge_chord,
                        confidence=0.7,
                        reasoning=f"Tonic resolution before subdominant to avoid retrograde motion",
                        position=position + 0.5,
                        voice_leading_quality=0.75
                    ))
                except Exception:
                    continue
        
        return suggestions
    
    def _suggest_cadential_completions(self, progression: ChordProgression,
                                     functional_analysis: List[Tuple[Chord, str]],
                                     key: Key) -> List[ChordSuggestion]:
        """Suggest chords to complete cadential patterns."""
        suggestions = []
        
        # Check if progression lacks a strong cadence
        if len(functional_analysis) >= 2:
            last_two_functions = [fa[1] for fa in functional_analysis[-2:]]
            
            # If we don't end with dominant-tonic, suggest completion
            if last_two_functions != ['dominant', 'tonic']:
                
                # If we end on dominant, suggest tonic resolution
                if functional_analysis[-1][1] == 'dominant':
                    try:
                        tonic_chord = key.get_chord_for_degree(1)  # Primary tonic
                        
                        suggestions.append(ChordSuggestion(
                            chord=tonic_chord,
                            confidence=0.9,
                            reasoning="Tonic resolution to complete dominant-tonic cadence",
                            position=float(len(progression.chords)),
                            voice_leading_quality=0.95
                        ))
                    except Exception:
                        pass
                
                # If we don't have dominant before the end, suggest V-I cadence
                elif 'dominant' not in last_two_functions:
                    try:
                        dominant_chord = key.get_chord_for_degree(5)  # V chord
                        
                        suggestions.append(ChordSuggestion(
                            chord=dominant_chord,
                            confidence=0.85,
                            reasoning="Dominant chord to prepare final cadence",
                            position=float(len(progression.chords)),
                            voice_leading_quality=0.8
                        ))
                    except Exception:
                        pass
        
        return suggestions
    
    def _calculate_functional_confidence(self, current_chord: Chord, 
                                       suggested_chord: Chord, function: str,
                                       key: Key, position: int) -> float:
        """Calculate confidence for functional harmony suggestion."""
        base_confidence = 0.6
        
        # Get suggested chord's degree
        suggested_degree = self._get_scale_degree(suggested_chord, key)
        
        if not suggested_degree:
            return base_confidence
        
        # Higher confidence for primary chords of each function
        primary_degrees = {
            'tonic': 1,       # I chord is strongest tonic
            'subdominant': 4, # IV chord is strongest subdominant  
            'dominant': 5     # V chord is strongest dominant
        }
        
        if function in primary_degrees and suggested_degree == primary_degrees[function]:
            base_confidence += 0.2
        
        # Boost confidence for common substitutions
        common_substitutions = {
            'tonic': [6],      # vi for I
            'subdominant': [2], # ii for IV
            'dominant': []      # V is usually best
        }
        
        if (function in common_substitutions and 
            suggested_degree in common_substitutions[function]):
            base_confidence += 0.15
        
        # Consider voice leading
        voice_leading = self._calculate_voice_leading_quality(current_chord, suggested_chord)
        
        # Good voice leading boosts confidence
        final_confidence = base_confidence + (voice_leading * 0.15)
        
        return min(0.95, final_confidence)
    
    def _get_functional_improvement_reasoning(self, current_chord: Chord, 
                                            suggested_chord: Chord, 
                                            function: str, suggested_degree: int) -> str:
        """Generate reasoning for functional improvements."""
        
        degree_names = {1: 'I', 2: 'ii', 3: 'iii', 4: 'IV', 5: 'V', 6: 'vi', 7: 'vii°'}
        degree_name = degree_names.get(suggested_degree, str(suggested_degree))
        
        base_reasoning = f"Stronger {function} function using {degree_name} chord"
        
        # Add specific reasoning for common substitutions
        if function == 'tonic' and suggested_degree == 1:
            base_reasoning += " - primary tonic provides strongest sense of resolution"
        elif function == 'subdominant' and suggested_degree == 4:
            base_reasoning += " - IV chord provides classic subdominant sound"
        elif function == 'subdominant' and suggested_degree == 2:
            base_reasoning += " - ii chord adds sophistication to subdominant function"
        elif function == 'dominant' and suggested_degree == 5:
            base_reasoning += " - V chord provides strongest dominant drive"
        elif function == 'tonic' and suggested_degree == 6:
            base_reasoning += " - vi chord as relative minor provides gentle tonic function"
        
        return base_reasoning