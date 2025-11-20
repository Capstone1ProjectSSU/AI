"""
Example usage of the Halmoni chord suggestion system.

This demonstrates how to use the various chord suggestion strategies
to enhance chord progressions with sophisticated harmonic alternatives.
"""

from halmoni import (
    Note, Chord, Key, ChordProgression,
    ChordSuggestionEngine,
    BorrowedChordStrategy,
    ChromaticApproachStrategy,
    NeapolitanStrategy,
    SubV7Strategy,
    SuspendStrategy,
    TSDMovementStrategy
)


def basic_suggestion_example():
    """Basic example of getting chord suggestions."""
    print("=== Basic Chord Suggestion Example ===")
    
    # Create a simple progression: C - Am - F - G
    progression = ChordProgression.from_symbols(['C', 'Am', 'F', 'G'])
    key = Key(Note('C', 4), 'major')
    
    # Create suggestion engine
    engine = ChordSuggestionEngine()
    
    # Get suggestions
    suggestions = engine.get_suggestions(progression, key, max_suggestions=10)
    
    print(f"Original progression: {' - '.join(progression.chord_symbols)}")
    print(f"Key: {key}")
    print(f"\nTop suggestions:")
    
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"{i}. {suggestion.chord.symbol} at position {suggestion.position}")
        print(f"   Confidence: {suggestion.confidence:.2f}")
        print(f"   Reasoning: {suggestion.reasoning}")
        print()


def strategy_specific_examples():
    """Demonstrate each strategy individually."""
    print("=== Strategy-Specific Examples ===")
    
    # Create a ii-V-I progression in C major
    progression = ChordProgression.from_symbols(['Dm7', 'G7', 'Cmaj7'])
    key = Key(Note('C', 4), 'major')
    
    print(f"Base progression: {' - '.join(progression.chord_symbols)}")
    print(f"Key: {key}")
    print()
    
    # Test each strategy
    strategies = [
        BorrowedChordStrategy(),
        ChromaticApproachStrategy(), 
        SubV7Strategy(),
        SuspendStrategy(),
        TSDMovementStrategy()
    ]
    
    for strategy in strategies:
        print(f"--- {strategy.get_strategy_name()} Strategy ---")
        suggestions = strategy.suggest(progression, key)
        
        if suggestions:
            for suggestion in suggestions[:3]:  # Top 3 from each strategy
                print(f"• {suggestion.chord.symbol} (pos {suggestion.position})")
                print(f"  Confidence: {suggestion.confidence:.2f}")
                print(f"  {suggestion.reasoning}")
            print()
        else:
            print("  No suggestions from this strategy")
            print()


def jazz_progression_example():
    """Example with a jazz progression showing tritone substitutions."""
    print("=== Jazz Progression Example ===")
    
    # Create a jazz ii-V-I-vi progression
    progression = ChordProgression.from_symbols(['Dm7', 'G7', 'Cmaj7', 'A7'])
    key = Key(Note('C', 4), 'major')
    
    print(f"Jazz progression: {' - '.join(progression.chord_symbols)}")
    
    # Focus on SubV7 and ChromaticApproach strategies
    engine = ChordSuggestionEngine()
    suggestions = engine.get_suggestions(
        progression, 
        key, 
        strategy_filter=['SubV7', 'ChromaticApproach'],
        max_suggestions=8
    )
    
    print("Jazz-focused suggestions:")
    for suggestion in suggestions:
        print(f"• Replace {progression.chords[int(suggestion.position)].symbol} "
              f"with {suggestion.chord.symbol}")
        print(f"  {suggestion.reasoning}")
        print(f"  Confidence: {suggestion.confidence:.2f}")
        print()


def classical_progression_example():
    """Example with classical harmony showing Neapolitan and borrowed chords."""
    print("=== Classical Progression Example ===")
    
    # Create a progression in A minor
    progression = ChordProgression.from_symbols(['Am', 'F', 'G', 'Am'])
    key = Key(Note('A', 4), 'minor')
    
    print(f"Classical progression: {' - '.join(progression.chord_symbols)}")
    print(f"Key: {key}")
    
    # Focus on classical harmony strategies
    engine = ChordSuggestionEngine()
    suggestions = engine.get_suggestions(
        progression,
        key,
        strategy_filter=['Neapolitan', 'BorrowedChord', 'TSDMovement'],
        max_suggestions=6
    )
    
    print("Classical harmony suggestions:")
    for suggestion in suggestions:
        print(f"• {suggestion.chord.symbol} at position {suggestion.position}")
        print(f"  {suggestion.reasoning}")
        print(f"  Confidence: {suggestion.confidence:.2f}")
        print()


def progression_analysis_example():
    """Demonstrate progression analysis capabilities."""
    print("=== Progression Analysis Example ===")
    
    # Create a progression with some harmonic issues
    progression = ChordProgression.from_symbols(['C', 'C', 'Am', 'C'])  # Static progression
    key = Key(Note('C', 4), 'major')
    
    print(f"Analyzing progression: {' - '.join(progression.chord_symbols)}")
    
    engine = ChordSuggestionEngine()
    analysis = engine.analyze_progression_potential(progression, key)
    
    print(f"Total suggestions available: {analysis['total_suggestions']}")
    print(f"High confidence suggestions: {analysis['high_confidence_suggestions']}")
    print(f"\nStrategy coverage:")
    for strategy, count in analysis['strategy_coverage'].items():
        print(f"  {strategy}: {count} suggestions")
    
    print(f"\nImprovement areas:")
    for area in analysis['improvement_areas']:
        print(f"  • {area}")
    
    print(f"\nPosition analysis:")
    for pos_analysis in analysis['position_analysis']:
        print(f"  Position {pos_analysis['position']} ({pos_analysis['chord']}): "
              f"{pos_analysis['suggestion_count']} suggestions")


def contemporary_progression_example():
    """Example showing suspension and contemporary harmony."""
    print("=== Contemporary Progression Example ===")
    
    # Create a modern pop progression
    progression = ChordProgression.from_symbols(['C', 'G', 'Am', 'F'])
    key = Key(Note('C', 4), 'major')
    
    print(f"Pop progression: {' - '.join(progression.chord_symbols)}")
    
    # Focus on suspension and contemporary approaches
    engine = ChordSuggestionEngine()
    suggestions = engine.get_suggestions(
        progression,
        key,
        strategy_filter=['Suspend', 'BorrowedChord'],
        max_suggestions=8
    )
    
    print("Contemporary enhancement suggestions:")
    for suggestion in suggestions:
        pos = int(suggestion.position)
        original_chord = progression.chords[pos].symbol if pos < len(progression.chords) else "?"
        print(f"• {original_chord} → {suggestion.chord.symbol}")
        print(f"  {suggestion.reasoning}")
        print(f"  Voice leading quality: {suggestion.voice_leading_quality:.2f}")
        print()


def interactive_example():
    """Interactive example for trying different progressions."""
    print("=== Interactive Example ===")
    print("This would be an interactive session where you can input your own progressions")
    print("and get real-time suggestions. Here's how it would work:")
    print()
    
    # Simulate user input
    user_progression = ['F', 'C', 'G', 'Am']  # vi-IV-I-v in A minor or IV-I-V-vi in F major
    
    print(f"User input: {' - '.join(user_progression)}")
    
    # Try both major and minor interpretations
    for tonic, mode in [('F', 'major'), ('A', 'minor')]:
        progression = ChordProgression.from_symbols(user_progression)
        key = Key(Note(tonic, 4), mode)
        
        engine = ChordSuggestionEngine()
        suggestions = engine.get_suggestions(progression, key, max_suggestions=5)
        
        print(f"\nAs {key} progression:")
        for suggestion in suggestions[:3]:
            print(f"  • {suggestion.chord.symbol} at position {suggestion.position}")
            print(f"    {suggestion.reasoning}")


if __name__ == "__main__":
    # Run all examples
    basic_suggestion_example()
    print("\n" + "="*60 + "\n")
    
    strategy_specific_examples()
    print("\n" + "="*60 + "\n")
    
    jazz_progression_example()
    print("\n" + "="*60 + "\n")
    
    classical_progression_example()
    print("\n" + "="*60 + "\n")
    
    progression_analysis_example()
    print("\n" + "="*60 + "\n")
    
    contemporary_progression_example()
    print("\n" + "="*60 + "\n")
    
    interactive_example()
    
    print("\n" + "="*60)
    print("Examples complete! Try modifying the progressions and keys to explore more suggestions.")