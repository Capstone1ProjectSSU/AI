"""Instrument-specific difficulty analysis modules."""

from .guitar import GuitarDifficulty
from .piano import PianoDifficulty
from .bass import BassDifficulty

__all__ = [
    "GuitarDifficulty",
    "PianoDifficulty",
    "BassDifficulty",
]