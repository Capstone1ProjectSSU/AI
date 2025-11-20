"""Key detection and tonal analysis utilities."""

from typing import List, Dict, Tuple, Optional
import numpy as np
from collections import Counter
from ..core import Note, Key, Scale, Chord


class KeyDetector:
    """Detects musical keys from notes and chord progressions."""
    
    # Krumhansl-Schmuckler key profiles
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    
    # Alternative profiles for different musical styles
    CLASSICAL_MAJOR_PROFILE = np.array([6.6, 2.0, 3.5, 2.3, 4.4, 4.1, 2.5, 5.2, 2.4, 3.7, 2.3, 2.9])
    CLASSICAL_MINOR_PROFILE = np.array([6.4, 2.7, 3.6, 5.4, 2.5, 3.5, 2.6, 4.8, 4.0, 2.7, 3.4, 3.2])
    
    FOLK_MAJOR_PROFILE = np.array([6.8, 1.5, 3.2, 2.0, 4.2, 4.3, 2.2, 5.5, 2.1, 3.4, 2.0, 2.5])
    FOLK_MINOR_PROFILE = np.array([6.5, 2.2, 3.8, 5.8, 2.2, 3.2, 2.2, 5.0, 4.3, 2.4, 3.0, 2.8])
    
    CHROMATIC_NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(self, profile_type: str = 'standard'):
        """
        Initialize key detector.
        
        Args:
            profile_type: Type of key profile to use ('standard', 'classical', 'folk')
        """
        self.profile_type = profile_type
        
        if profile_type == 'classical':
            self.major_profile = self.CLASSICAL_MAJOR_PROFILE
            self.minor_profile = self.CLASSICAL_MINOR_PROFILE
        elif profile_type == 'folk':
            self.major_profile = self.FOLK_MAJOR_PROFILE
            self.minor_profile = self.FOLK_MINOR_PROFILE
        else:
            self.major_profile = self.MAJOR_PROFILE
            self.minor_profile = self.MINOR_PROFILE
    
    def detect_key_from_notes(self, notes: List[Note], 
                            weights: Optional[List[float]] = None) -> Tuple[Key, float]:
        """
        Detect key from a collection of notes using pitch class profiles.
        
        Args:
            notes: List of Note objects
            weights: Optional weights for each note (e.g., duration, accent)
            
        Returns:
            Tuple of (detected_key, confidence_score)
        """
        if not notes:
            return Key(Note('C', 4), 'major'), 0.0
        
        # Create pitch class histogram
        histogram = self._create_pitch_class_histogram(notes, weights)
        
        # Find best key match
        best_key, best_score = self._find_best_key_match(histogram)
        
        return best_key, best_score
    
    def detect_key_from_midi_notes(self, midi_notes: List[Dict]) -> Tuple[Key, float]:
        """
        Detect key from MIDI note dictionaries.
        
        Args:
            midi_notes: List of MIDI note dictionaries with duration and velocity info
            
        Returns:
            Tuple of (detected_key, confidence_score)
        """
        if not midi_notes:
            return Key(Note('C', 4), 'major'), 0.0
        
        notes = []
        weights = []
        
        for midi_note in midi_notes:
            try:
                note = Note(midi_note['midi_note'])
                notes.append(note)
                
                # Weight by duration and velocity
                duration = midi_note.get('duration', 1.0)
                velocity = midi_note.get('velocity', 64) / 127.0
                weight = duration * velocity
                weights.append(weight)
                
            except (ValueError, KeyError):
                continue
        
        return self.detect_key_from_notes(notes, weights)
    
    def detect_key_from_chords(self, chords: List[Chord], 
                             durations: Optional[List[float]] = None) -> Tuple[Key, float]:
        """
        Detect key from a chord progression.
        
        Args:
            chords: List of Chord objects
            durations: Optional durations for chord weighting
            
        Returns:
            Tuple of (detected_key, confidence_score)
        """
        if not chords:
            return Key(Note('C', 4), 'major'), 0.0
        
        # Extract all notes from chords
        all_notes = []
        all_weights = []
        
        for i, chord in enumerate(chords):
            chord_duration = durations[i] if durations else 1.0
            
            for note in chord.notes:
                all_notes.append(note)
                all_weights.append(chord_duration)
        
        # Also analyze chord roots for additional key evidence
        root_evidence = self._analyze_chord_roots(chords, durations)
        
        # Combine note-based and chord-based analysis
        note_key, note_confidence = self.detect_key_from_notes(all_notes, all_weights)
        
        # Boost confidence if chord analysis agrees
        if root_evidence and note_key.tonic.pitch_class == root_evidence[0].tonic.pitch_class:
            combined_confidence = min(1.0, note_confidence * 1.2)
        else:
            combined_confidence = note_confidence * 0.9
        
        return note_key, combined_confidence
    
    def _create_pitch_class_histogram(self, notes: List[Note], 
                                    weights: Optional[List[float]] = None) -> np.ndarray:
        """Create a weighted pitch class histogram."""
        histogram = np.zeros(12)
        
        for i, note in enumerate(notes):
            pitch_class_index = self.CHROMATIC_NOTES.index(note.pitch_class)
            weight = weights[i] if weights else 1.0
            histogram[pitch_class_index] += weight
        
        # Normalize
        total = histogram.sum()
        if total > 0:
            histogram = histogram / total
        
        return histogram
    
    def _find_best_key_match(self, histogram: np.ndarray) -> Tuple[Key, float]:
        """Find the best matching key using correlation analysis."""
        best_correlation = -1
        best_key = Key(Note('C', 4), 'major')
        
        # Test all major keys
        for i, tonic_name in enumerate(self.CHROMATIC_NOTES):
            # Rotate the major profile to match this tonic
            rotated_profile = np.roll(self.major_profile, -i)
            rotated_profile = rotated_profile / rotated_profile.sum()  # Normalize
            
            correlation = np.corrcoef(histogram, rotated_profile)[0, 1]
            
            if not np.isnan(correlation) and correlation > best_correlation:
                best_correlation = correlation
                tonic = Note(tonic_name, 4)
                best_key = Key(tonic, 'major')
        
        # Test all minor keys
        for i, tonic_name in enumerate(self.CHROMATIC_NOTES):
            rotated_profile = np.roll(self.minor_profile, -i)
            rotated_profile = rotated_profile / rotated_profile.sum()  # Normalize
            
            correlation = np.corrcoef(histogram, rotated_profile)[0, 1]
            
            if not np.isnan(correlation) and correlation > best_correlation:
                best_correlation = correlation
                tonic = Note(tonic_name, 4)
                best_key = Key(tonic, 'minor')
        
        # Convert correlation to confidence score (0-1)
        confidence = max(0, (best_correlation + 1) / 2)  # Normalize from [-1,1] to [0,1]
        
        return best_key, confidence
    
    def _analyze_chord_roots(self, chords: List[Chord], 
                           durations: Optional[List[float]] = None) -> List[Tuple[Key, float]]:
        """Analyze chord roots for key evidence."""
        if not chords:
            return []
        
        # Count chord roots with weights
        root_weights = {}
        
        for i, chord in enumerate(chords):
            root_pc = chord.root.pitch_class
            weight = durations[i] if durations else 1.0
            root_weights[root_pc] = root_weights.get(root_pc, 0) + weight
        
        # Find most common roots
        sorted_roots = sorted(root_weights.items(), key=lambda x: x[1], reverse=True)
        
        key_candidates = []
        
        # Consider top root as potential tonic
        if sorted_roots:
            most_common_root = sorted_roots[0][0]
            tonic = Note(most_common_root, 4)
            
            # Try both major and minor
            key_candidates.append((Key(tonic, 'major'), sorted_roots[0][1]))
            key_candidates.append((Key(tonic, 'minor'), sorted_roots[0][1] * 0.8))
        
        return key_candidates
    
    def analyze_modulation(self, segments: List[List[Note]]) -> List[Tuple[Key, float]]:
        """
        Analyze key changes across different segments of music.
        
        Args:
            segments: List of note segments (each segment is a list of notes)
            
        Returns:
            List of (key, confidence) for each segment
        """
        segment_keys = []
        
        for segment in segments:
            if segment:
                key, confidence = self.detect_key_from_notes(segment)
                segment_keys.append((key, confidence))
            else:
                # Use previous key if segment is empty
                if segment_keys:
                    segment_keys.append(segment_keys[-1])
                else:
                    segment_keys.append((Key(Note('C', 4), 'major'), 0.0))
        
        return segment_keys
    
    def detect_tonicization(self, chords: List[Chord], main_key: Key) -> List[Optional[Key]]:
        """
        Detect temporary tonicizations within a progression.
        
        Args:
            chords: List of chords in progression
            main_key: Main key of the piece
            
        Returns:
            List of keys (None for chords that don't suggest tonicization)
        """
        tonicizations = []
        
        for i in range(len(chords)):
            current_chord = chords[i]
            
            # Look for dominant-type chords that could tonicize
            if current_chord.quality in ['dominant7', 'dominant9', 'dominant13']:
                # Check if next chord could be the resolution
                if i + 1 < len(chords):
                    next_chord = chords[i + 1]
                    
                    # Check for dominant-tonic relationship
                    interval = next_chord.root.midi_number - current_chord.root.midi_number
                    if interval % 12 == 7 or interval % 12 == 5:  # Perfect 5th down or 4th up
                        # Potential tonicization
                        tonicized_key = Key(next_chord.root, main_key.mode)
                        tonicizations.append(tonicized_key)
                    else:
                        tonicizations.append(None)
                else:
                    tonicizations.append(None)
            else:
                tonicizations.append(None)
        
        return tonicizations
    
    def analyze_key_stability(self, notes: List[Note], window_size: int = 20) -> List[Tuple[float, Key]]:
        """
        Analyze key stability over time using a sliding window.
        
        Args:
            notes: List of notes in chronological order
            window_size: Size of sliding window for analysis
            
        Returns:
            List of (timestamp, detected_key) pairs
        """
        if len(notes) < window_size:
            key, _ = self.detect_key_from_notes(notes)
            return [(0.0, key)]
        
        stability_analysis = []
        
        for i in range(len(notes) - window_size + 1):
            window_notes = notes[i:i + window_size]
            key, confidence = self.detect_key_from_notes(window_notes)
            
            # Use the timestamp of the middle note in the window
            middle_idx = i + window_size // 2
            timestamp = float(middle_idx)  # Simplified timestamp
            
            stability_analysis.append((timestamp, key))
        
        return stability_analysis
    
    def compare_keys(self, key1: Key, key2: Key) -> Dict[str, any]:
        """
        Compare two keys and analyze their relationship.
        
        Args:
            key1: First key
            key2: Second key
            
        Returns:
            Dictionary with relationship analysis
        """
        analysis = {
            'keys': (key1, key2),
            'relationship': 'unrelated',
            'common_notes': 0,
            'distance': 0
        }
        
        # Check for same key
        if key1 == key2:
            analysis['relationship'] = 'identical'
            analysis['common_notes'] = 7
            return analysis
        
        # Check for relative keys (same key signature)
        if key1.signature == key2.signature:
            if key1.mode != key2.mode:
                analysis['relationship'] = 'relative'
                analysis['common_notes'] = 7
            else:
                analysis['relationship'] = 'enharmonic'
                analysis['common_notes'] = 7
            return analysis
        
        # Check for parallel keys (same tonic)
        if key1.tonic.pitch_class == key2.tonic.pitch_class:
            if key1.mode != key2.mode:
                analysis['relationship'] = 'parallel'
                analysis['common_notes'] = len(set(key1.scale.pitch_classes) & 
                                               set(key2.scale.pitch_classes))
            return analysis
        
        # Check for closely related keys
        key1_related = key1.get_closely_related_keys()
        if key2 in key1_related:
            analysis['relationship'] = 'closely_related'
            analysis['common_notes'] = len(set(key1.scale.pitch_classes) & 
                                           set(key2.scale.pitch_classes))
            return analysis
        
        # Calculate distance on circle of fifths
        major_circle = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'F', 'Bb', 'Eb', 'Ab', 'Db', 'Gb']
        minor_circle = ['A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'D', 'G', 'C', 'F', 'Bb', 'Eb']
        
        try:
            if key1.mode == 'major' and key2.mode == 'major':
                pos1 = major_circle.index(key1.tonic.pitch_class)
                pos2 = major_circle.index(key2.tonic.pitch_class)
            elif key1.mode == 'minor' and key2.mode == 'minor':
                pos1 = minor_circle.index(key1.tonic.pitch_class)
                pos2 = minor_circle.index(key2.tonic.pitch_class)
            else:
                # Convert to same mode for comparison
                if key1.mode == 'major':
                    rel_key1 = key1.relative_key
                    pos1 = minor_circle.index(rel_key1.tonic.pitch_class)
                    pos2 = minor_circle.index(key2.tonic.pitch_class)
                else:
                    rel_key2 = key2.relative_key
                    pos1 = minor_circle.index(key1.tonic.pitch_class)
                    pos2 = major_circle.index(rel_key2.tonic.pitch_class)
            
            distance = min(abs(pos1 - pos2), 14 - abs(pos1 - pos2))  # Circle distance
            analysis['distance'] = distance
            
            if distance <= 2:
                analysis['relationship'] = 'closely_related'
            elif distance <= 4:
                analysis['relationship'] = 'distantly_related'
            else:
                analysis['relationship'] = 'unrelated'
                
        except ValueError:
            # Key not found in circle
            analysis['relationship'] = 'unrelated'
            analysis['distance'] = 7  # Maximum distance
        
        # Count common notes
        common_pitch_classes = set(key1.scale.pitch_classes) & set(key2.scale.pitch_classes)
        analysis['common_notes'] = len(common_pitch_classes)
        
        return analysis