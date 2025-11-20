"""
Adam Stark chord detector implementation in Python.
Based on: https://github.com/adamstark/Chord-Detector-and-Chromagram

Original C++ implementation by Adam Stark, converted to Python for halmoni library.
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
from ..core import Note, Chord


class AdamStarkChordDetector:
    """
    Chord detector based on Adam Stark's chromagram-based algorithm.
    
    This implementation converts the original C++ algorithm to Python,
    using chromagram analysis to detect chord types and root notes.
    """
    
    def __init__(self):
        """Initialize the chord detector with chord profiles."""
        self.chord_profiles = {}
        self.chord_names = [
            'N',      # No chord
            'C',      # Major
            'Cm',     # Minor
            'Cdim',   # Diminished
            'Caug',   # Augmented
            'Csus2',  # Suspended 2nd
            'Csus4',  # Suspended 4th
            'Cmaj7',  # Major 7th
            'Cm7',    # Minor 7th
            'C7'      # Dominant 7th
        ]
        
        self.num_chords_in_classifier = len(self.chord_names)
        self.num_semitones = 12
        
        self._make_chord_profiles()
    
    def _make_chord_profiles(self) -> None:
        """Create chord profiles for all chord types and roots."""
        # Initialize profiles array
        self.chord_profiles = np.zeros((self.num_chords_in_classifier * self.num_semitones, self.num_semitones))
        
        # Chord interval patterns (semitones from root)
        chord_intervals = {
            0: [],                    # No chord
            1: [0, 4, 7],            # Major
            2: [0, 3, 7],            # Minor  
            3: [0, 3, 6],            # Diminished
            4: [0, 4, 8],            # Augmented
            5: [0, 2, 7],            # Sus2
            6: [0, 5, 7],            # Sus4
            7: [0, 4, 7, 11],        # Major 7th
            8: [0, 3, 7, 10],        # Minor 7th
            9: [0, 4, 7, 10]         # Dominant 7th
        }
        
        # Create profiles for each chord type and root
        for chord_type in range(self.num_chords_in_classifier):
            intervals = chord_intervals.get(chord_type, [])
            
            for root in range(self.num_semitones):
                profile_index = chord_type * self.num_semitones + root
                
                # Set profile values for chord tones
                for interval in intervals:
                    note_index = (root + interval) % self.num_semitones
                    self.chord_profiles[profile_index, note_index] = 1.0
    
    def detect_chord(self, chromagram: np.ndarray) -> Tuple[str, float]:
        """
        Detect chord from chromagram.
        
        Args:
            chromagram: 12-element array representing pitch class strengths
            
        Returns:
            Tuple of (chord_name, confidence_score)
        """
        if len(chromagram) != self.num_semitones:
            raise ValueError("Chromagram must have 12 elements")
        
        # Normalize chromagram
        chroma_sum = np.sum(chromagram)
        if chroma_sum == 0:
            return 'N', 0.0
        
        normalized_chroma = chromagram / chroma_sum
        
        # Remove some 5th note energy (as in original implementation)
        processed_chroma = self._remove_fifth_energy(normalized_chroma)
        
        # Calculate scores for all chord types and roots
        chord_scores = self._calculate_all_chord_scores(processed_chroma)
        
        # Find best match (minimum score in original algorithm)
        best_chord_index = np.argmin(chord_scores)
        best_score = chord_scores[best_chord_index]
        
        # Convert index to chord type and root
        chord_type = best_chord_index // self.num_semitones
        root_note = best_chord_index % self.num_semitones
        
        # Generate chord name
        chord_name = self._get_chord_name(chord_type, root_note)
        
        # Convert score to confidence (lower score = higher confidence in original)
        confidence = max(0.0, 1.0 - best_score)
        
        return chord_name, confidence
    
    def _remove_fifth_energy(self, chromagram: np.ndarray) -> np.ndarray:
        """
        Remove some energy from perfect 5th intervals to improve detection.
        
        This follows the original implementation's approach to reduce
        harmonic interference from perfect fifths.
        """
        processed = chromagram.copy()
        
        for i in range(self.num_semitones):
            fifth_index = (i + 7) % self.num_semitones
            # Reduce 5th energy by 20% (arbitrary factor from original)
            processed[fifth_index] *= 0.8
        
        return processed
    
    def _calculate_all_chord_scores(self, chromagram: np.ndarray) -> np.ndarray:
        """Calculate scores for all chord types and roots."""
        num_profiles = self.num_chords_in_classifier * self.num_semitones
        scores = np.zeros(num_profiles)
        
        for i in range(num_profiles):
            scores[i] = self._calculate_chord_score(chromagram, i)
        
        return scores
    
    def _calculate_chord_score(self, chromagram: np.ndarray, profile_index: int) -> float:
        """
        Calculate score for a specific chord profile.
        
        Lower scores indicate better matches (as in original implementation).
        """
        profile = self.chord_profiles[profile_index]
        
        # Calculate difference between chromagram and profile
        # Using sum of squared differences
        score = np.sum((chromagram - profile) ** 2)
        
        return score
    
    def _get_chord_name(self, chord_type: int, root_note: int) -> str:
        """Generate chord name from type and root."""
        if chord_type >= len(self.chord_names):
            return 'N'
        
        if chord_type == 0:  # No chord
            return 'N'
        
        # Note names
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        root_name = note_names[root_note]
        
        # Get chord quality suffix
        chord_template = self.chord_names[chord_type]
        chord_suffix = chord_template[1:]  # Remove 'C' from template
        
        return root_name + chord_suffix
    
    def detect_chord_from_notes(self, notes: List[Note]) -> Tuple[Optional[Chord], float]:
        """
        Detect chord from Note objects by creating chromagram.
        
        Args:
            notes: List of Note objects
            
        Returns:
            Tuple of (Chord object or None, confidence)
        """
        if not notes:
            return None, 0.0
        
        # Create chromagram from notes
        chromagram = self._notes_to_chromagram(notes)
        
        # Detect chord
        chord_name, confidence = self.detect_chord(chromagram)
        
        if chord_name == 'N':
            return None, confidence
        
        # Convert chord name to Chord object
        try:
            chord = self._chord_name_to_object(chord_name)
            return chord, confidence
        except ValueError:
            return None, 0.0
    
    def detect_chord_from_midi_notes(self, midi_notes: List[Dict]) -> Tuple[Optional[Chord], float]:
        """
        Detect chord from MIDI note dictionaries.
        
        Args:
            midi_notes: List of MIDI note dictionaries
            
        Returns:
            Tuple of (Chord object or None, confidence)
        """
        if not midi_notes:
            return None, 0.0
        
        # Convert to Note objects
        notes = []
        for midi_note in midi_notes:
            try:
                note = Note(midi_note['midi_note'])
                notes.append(note)
            except (ValueError, KeyError):
                continue
        
        return self.detect_chord_from_notes(notes)
    
    def _notes_to_chromagram(self, notes: List[Note]) -> np.ndarray:
        """Convert list of notes to chromagram."""
        chromagram = np.zeros(self.num_semitones)
        
        for note in notes:
            pitch_class = note.midi_number % self.num_semitones
            chromagram[pitch_class] += 1.0
        
        return chromagram
    
    def _chord_name_to_object(self, chord_name: str) -> Chord:
        """Convert chord name string to Chord object."""
        if chord_name == 'N' or not chord_name:
            raise ValueError("Invalid chord name")
        
        # Parse root note
        if len(chord_name) < 1:
            raise ValueError("Invalid chord name")
        
        root_str = chord_name[0]
        remainder = chord_name[1:]
        
        # Handle accidentals
        if remainder and remainder[0] in '#b':
            root_str += remainder[0]
            remainder = remainder[1:]
        
        root_note = Note(root_str, 4)  # Default octave 4
        
        # Map chord suffixes to qualities
        quality_map = {
            '': 'major',
            'm': 'minor',
            'dim': 'diminished',
            'aug': 'augmented',
            'sus2': 'sus2',
            'sus4': 'sus4',
            'maj7': 'major7',
            'm7': 'minor7',
            '7': 'dominant7'
        }
        
        if remainder in quality_map:
            quality = quality_map[remainder]
        else:
            raise ValueError(f"Unknown chord quality: {remainder}")
        
        return Chord(root_note, quality)
    
    def create_chromagram_from_audio_spectrum(self, spectrum: np.ndarray, 
                                            sample_rate: float,
                                            reference_frequency: float = 440.0) -> np.ndarray:
        """
        Create chromagram from audio spectrum (for future audio processing).
        
        Args:
            spectrum: Frequency spectrum (FFT output)
            sample_rate: Audio sample rate
            reference_frequency: Reference frequency for A4
            
        Returns:
            12-element chromagram
        """
        # This is a placeholder for future audio processing capabilities
        # For now, just return empty chromagram
        return np.zeros(self.num_semitones)
    
    def batch_detect_chords(self, chromagrams: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        Detect chords from multiple chromagrams.
        
        Args:
            chromagrams: List of chromagram arrays
            
        Returns:
            List of (chord_name, confidence) tuples
        """
        results = []
        
        for chromagram in chromagrams:
            chord_name, confidence = self.detect_chord(chromagram)
            results.append((chord_name, confidence))
        
        return results
    
    def get_chord_profile(self, chord_name: str) -> Optional[np.ndarray]:
        """
        Get the chromagram profile for a specific chord.
        
        Args:
            chord_name: Chord name (e.g., 'C', 'Am', 'F#dim')
            
        Returns:
            Chromagram profile or None if chord not found
        """
        try:
            # Parse chord name to get type and root
            chord = self._chord_name_to_object(chord_name)
            
            # Find matching chord type
            quality_to_type = {
                'major': 1,
                'minor': 2,
                'diminished': 3,
                'augmented': 4,
                'sus2': 5,
                'sus4': 6,
                'major7': 7,
                'minor7': 8,
                'dominant7': 9
            }
            
            chord_type = quality_to_type.get(chord.quality)
            if chord_type is None:
                return None
            
            # Get root note index
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            root_index = note_names.index(chord.root.pitch_class)
            
            # Calculate profile index
            profile_index = chord_type * self.num_semitones + root_index
            
            return self.chord_profiles[profile_index]
            
        except (ValueError, KeyError):
            return None