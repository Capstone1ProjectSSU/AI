"""Pytest configuration and fixtures for halmoni tests."""

import pytest
from halmoni import Note, Chord, Key, ChordProgression, Interval


@pytest.fixture
def c_major_key() -> Key:
    """Fixture for C major key."""
    return Key(Note('C', 4), 'major')


@pytest.fixture
def a_minor_key() -> Key:
    """Fixture for A minor key."""
    return Key(Note('A', 4), 'minor')


@pytest.fixture
def simple_progression() -> ChordProgression:
    """Fixture for simple I-vi-IV-V progression in C major."""
    return ChordProgression.from_symbols(['C', 'Am', 'F', 'G'])


@pytest.fixture
def jazz_progression() -> ChordProgression:
    """Fixture for jazz ii-V-I progression."""
    return ChordProgression.from_symbols(['Dm7', 'G7', 'Cmaj7'])


@pytest.fixture
def c_note() -> Note:
    """Fixture for middle C."""
    return Note('C', 4)


@pytest.fixture
def c_major_chord() -> Chord:
    """Fixture for C major chord."""
    return Chord.from_symbol('C')


@pytest.fixture
def g7_chord() -> Chord:
    """Fixture for G7 chord."""
    return Chord.from_symbol('G7')
