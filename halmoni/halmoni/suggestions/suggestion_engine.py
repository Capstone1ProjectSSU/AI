"""Main chord suggestion engine coordinating all strategies."""

from typing import List, Optional, Set, Dict
from .base_strategy import ChordSuggestion
from .borrowed_chord import BorrowedChordStrategy
from .chromatic_approach import ChromaticApproachStrategy
from .neapolitan import NeapolitanStrategy
from .sub_v7 import SubV7Strategy
from .suspend import SuspendStrategy
from .tsd_movement import TSDMovementStrategy
from ..core import ChordProgression, Key


class ChordSuggestionEngine:
    """Main engine coordinating all chord suggestion strategies."""
    
    def __init__(self):
        """Initialize the suggestion engine with all available strategies."""
        self.strategies = [
            BorrowedChordStrategy(),
            ChromaticApproachStrategy(),
            NeapolitanStrategy(),
            SubV7Strategy(),
            SuspendStrategy(),
            TSDMovementStrategy()
        ]
        
        self.strategy_map = {
            strategy.get_strategy_name(): strategy 
            for strategy in self.strategies
        }
    
    def get_suggestions(self, progression: ChordProgression, 
                       key: Optional[Key] = None,
                       strategy_filter: Optional[List[str]] = None,
                       max_suggestions: int = 20) -> List[ChordSuggestion]:
        """
        Get chord suggestions from all or filtered strategies.
        
        Args:
            progression: The chord progression to analyze
            key: Optional key context (uses progression.key if not provided)
            strategy_filter: List of strategy names to use (None = use all)
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of chord suggestions sorted by confidence
        """
        all_suggestions = []
        
        # Use all strategies if no filter specified
        active_strategies = self.strategies
        if strategy_filter:
            active_strategies = [
                strategy for strategy in self.strategies 
                if strategy.get_strategy_name() in strategy_filter
            ]
        
        # Collect suggestions from each strategy
        for strategy in active_strategies:
            try:
                suggestions = strategy.suggest(progression, key)
                # Tag suggestions with their source strategy
                for suggestion in suggestions:
                    suggestion.strategy_source = strategy.get_strategy_name()
                all_suggestions.extend(suggestions)
            except Exception as e:
                # Log error but continue with other strategies
                print(f"Warning: Strategy {strategy.get_strategy_name()} failed: {e}")
                continue
        
        # Remove duplicates and sort by confidence
        unique_suggestions = self._remove_duplicates(all_suggestions)
        sorted_suggestions = sorted(unique_suggestions, 
                                  key=lambda x: x.confidence, reverse=True)
        
        return sorted_suggestions[:max_suggestions]
    
    def get_suggestions_by_strategy(self, progression: ChordProgression,
                                   key: Optional[Key] = None) -> Dict[str, List[ChordSuggestion]]:
        """
        Get suggestions organized by strategy.
        
        Returns:
            Dictionary mapping strategy names to their suggestions
        """
        results = {}
        
        for strategy in self.strategies:
            strategy_name = strategy.get_strategy_name()
            try:
                suggestions = strategy.suggest(progression, key)
                results[strategy_name] = sorted(suggestions, 
                                              key=lambda x: x.confidence, reverse=True)
            except Exception as e:
                print(f"Warning: Strategy {strategy_name} failed: {e}")
                results[strategy_name] = []
        
        return results
    
    def get_suggestions_for_position(self, progression: ChordProgression,
                                   position: int,
                                   key: Optional[Key] = None,
                                   strategy_filter: Optional[List[str]] = None) -> List[ChordSuggestion]:
        """
        Get suggestions specifically for a given position in the progression.
        
        Args:
            progression: The chord progression
            position: Position index to get suggestions for
            key: Optional key context
            strategy_filter: Optional list of strategy names to use
            
        Returns:
            List of suggestions for the specified position
        """
        all_suggestions = self.get_suggestions(progression, key, strategy_filter)
        
        # Filter suggestions for the specific position
        position_suggestions = [
            suggestion for suggestion in all_suggestions
            if abs(suggestion.position - position) < 0.1  # Account for floating point precision
        ]
        
        return position_suggestions
    
    def analyze_progression_potential(self, progression: ChordProgression,
                                    key: Optional[Key] = None) -> Dict[str, any]:
        """
        Analyze a progression and identify areas with high suggestion potential.
        
        Returns:
            Dictionary with analysis of suggestion opportunities
        """
        analysis = {
            'total_suggestions': 0,
            'high_confidence_suggestions': 0,
            'strategy_coverage': {},
            'position_analysis': [],
            'improvement_areas': []
        }
        
        # Get all suggestions
        suggestions = self.get_suggestions(progression, key)
        analysis['total_suggestions'] = len(suggestions)
        
        # Count high confidence suggestions
        high_confidence = [s for s in suggestions if s.confidence >= 0.8]
        analysis['high_confidence_suggestions'] = len(high_confidence)
        
        # Analyze strategy coverage
        strategy_counts = {}
        for suggestion in suggestions:
            if hasattr(suggestion, 'strategy_source'):
                strategy = suggestion.strategy_source
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        analysis['strategy_coverage'] = strategy_counts
        
        # Analyze each position
        for i in range(len(progression.chords)):
            position_suggestions = self.get_suggestions_for_position(
                progression, i, key
            )
            
            position_analysis = {
                'position': i,
                'chord': progression.chords[i].symbol,
                'suggestion_count': len(position_suggestions),
                'max_confidence': max([s.confidence for s in position_suggestions], default=0),
                'strategies_involved': list(set([
                    getattr(s, 'strategy_source', 'unknown') 
                    for s in position_suggestions
                ]))
            }
            
            analysis['position_analysis'].append(position_analysis)
        
        # Identify improvement areas
        analysis['improvement_areas'] = self._identify_improvement_areas(
            progression, suggestions, key
        )
        
        return analysis
    
    def _remove_duplicates(self, suggestions: List[ChordSuggestion]) -> List[ChordSuggestion]:
        """Remove duplicate suggestions, keeping the highest confidence version."""
        
        # Group by chord and position
        suggestion_groups = {}
        
        for suggestion in suggestions:
            key = (suggestion.chord.symbol, suggestion.position)
            
            if key not in suggestion_groups:
                suggestion_groups[key] = suggestion
            else:
                # Keep the higher confidence suggestion
                if suggestion.confidence > suggestion_groups[key].confidence:
                    suggestion_groups[key] = suggestion
        
        return list(suggestion_groups.values())
    
    def _identify_improvement_areas(self, progression: ChordProgression,
                                   suggestions: List[ChordSuggestion],
                                   key: Optional[Key]) -> List[str]:
        """Identify areas where the progression could be improved."""
        
        improvement_areas = []
        
        # Check for positions with many high-confidence suggestions
        position_suggestion_counts = {}
        for suggestion in suggestions:
            if suggestion.confidence >= 0.8:
                pos = int(suggestion.position)
                position_suggestion_counts[pos] = position_suggestion_counts.get(pos, 0) + 1
        
        for pos, count in position_suggestion_counts.items():
            if count >= 3:  # Multiple high-confidence suggestions
                chord_symbol = progression.chords[pos].symbol if pos < len(progression.chords) else "?"
                improvement_areas.append(
                    f"Position {pos} ({chord_symbol}) has {count} high-confidence alternatives"
                )
        
        # Check for specific harmonic issues
        if key:
            # Analyze functional progression
            functions = []
            for chord in progression.chords:
                analysis = key.analyze_chord(chord)
                functions.append(analysis.get('function', 'unknown'))
            
            # Look for weak functional progressions
            if functions.count('unknown') > len(functions) / 2:
                improvement_areas.append("Many non-diatonic chords - consider key analysis")
            
            # Check for missing cadence
            if len(functions) >= 2 and functions[-2:] != ['dominant', 'tonic']:
                improvement_areas.append("Progression lacks strong cadential resolution")
        
        return improvement_areas
    
    def get_available_strategies(self) -> List[str]:
        """Get list of all available strategy names."""
        return [strategy.get_strategy_name() for strategy in self.strategies]
    
    def get_strategy_description(self, strategy_name: str) -> Optional[str]:
        """Get description of a specific strategy."""
        
        descriptions = {
            'BorrowedChord': 'Suggests chords borrowed from parallel modes and related keys',
            'ChromaticApproach': 'Suggests chromatic passing and approach chords for smooth voice leading',
            'Neapolitan': 'Suggests Neapolitan sixth chords and related pre-dominant harmonies',
            'SubV7': 'Suggests tritone substitution chords for sophisticated jazz harmony',
            'Suspend': 'Suggests suspension chords and resolution patterns for added tension',
            'TSDMovement': 'Suggests chords to strengthen functional harmony (Tonic-Subdominant-Dominant)'
        }
        
        return descriptions.get(strategy_name)