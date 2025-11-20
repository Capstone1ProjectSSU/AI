"""
Halmoni - Production-ready music creative coding support library

Provides chord analysis, progression suggestions, and instrument difficulty analysis.
"""

__version__ = "0.1.0"

from .core import Note, Interval, Chord, Scale, Key, ChordProgression, ChordVoicing
from .analysis import MIDIAnalyzer, ChordDetector, KeyDetector, AdamStarkChordDetector
from .instruments import GuitarDifficulty, PianoDifficulty, BassDifficulty
from .suggestions import (
    ChordSuggestion,
    ChordSuggestionEngine,
    BorrowedChordStrategy,
    ChromaticApproachStrategy,
    NeapolitanStrategy,
    SubV7Strategy,
    SuspendStrategy,
    TSDMovementStrategy,
)

__all__ = [
    "Note",
    "Interval", 
    "Chord",
    "Scale",
    "Key",
    "ChordProgression",
    "ChordVoicing",
    "MIDIAnalyzer",
    "ChordDetector",
    "KeyDetector",
    "AdamStarkChordDetector",
    "GuitarDifficulty",
    "PianoDifficulty",
    "BassDifficulty",
    "ChordSuggestion",
    "ChordSuggestionEngine",
    "BorrowedChordStrategy",
    "ChromaticApproachStrategy",
    "NeapolitanStrategy",
    "SubV7Strategy",
    "SuspendStrategy",
    "TSDMovementStrategy",
]