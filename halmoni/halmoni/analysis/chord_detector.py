"""Chord detection from MIDI notes and analysis."""

from typing import List, Dict, Tuple, Optional, Set
import numpy as np
from collections import Counter
from ..core import Note, Chord, Interval


class ChordDetector:
    """Detects chords from collections of notes."""
    
    CHORD_TEMPLATES = {
        # Triads
        'major': [0, 4, 7],
        'minor': [0, 3, 7],
        'diminished': [0, 3, 6],
        'augmented': [0, 4, 8],
        'sus2': [0, 2, 7],
        'sus4': [0, 5, 7],
        
        # Seventh chords
        'major7': [0, 4, 7, 11],
        'minor7': [0, 3, 7, 10], 
        'dominant7': [0, 4, 7, 10],
        'diminished7': [0, 3, 6, 9],
        'half_diminished7': [0, 3, 6, 10],
        'minor_major7': [0, 3, 7, 11],
        'augmented7': [0, 4, 8, 10],
        
        # Extended chords
        'major9': [0, 4, 7, 11, 2],
        'minor9': [0, 3, 7, 10, 2],
        'dominant9': [0, 4, 7, 10, 2],
        'major11': [0, 4, 7, 11, 2, 5],
        'minor11': [0, 3, 7, 10, 2, 5],
        'dominant11': [0, 4, 7, 10, 2, 5],
        'major13': [0, 4, 7, 11, 2, 5, 9],
        'minor13': [0, 3, 7, 10, 2, 5, 9],
        'dominant13': [0, 4, 7, 10, 2, 5, 9],
        
        # Altered dominants
        'dominant7b5': [0, 4, 6, 10],
        'dominant7#5': [0, 4, 8, 10],
        'dominant7b9': [0, 4, 7, 10, 1],
        'dominant7#9': [0, 4, 7, 10, 3],
        'dominant7#11': [0, 4, 7, 10, 6],
        'dominant7b13': [0, 4, 7, 10, 8],
    }
    
    def __init__(self, min_notes: int = 2, bass_weight: float = 2.0):
        """
        Initialize chord detector.
        
        Args:
            min_notes: Minimum number of notes required to detect a chord
            bass_weight: Weight factor for bass notes in root detection
        """
        self.min_notes = min_notes
        self.bass_weight = bass_weight
    
    def detect_chord_from_notes(self, notes: List[Note], 
                               bass_note: Optional[Note] = None) -> Optional[Chord]:
        """
        Detect a chord from a collection of notes.
        
        Args:
            notes: List of Note objects
            bass_note: Optional bass note for slash chords
            
        Returns:
            Detected Chord object or None if no chord found
        """
        if len(notes) < self.min_notes:
            return None
        
        # Get unique pitch classes
        pitch_classes = list(set(note.pitch_class for note in notes))
        
        if len(pitch_classes) < self.min_notes:
            return None
        
        # Convert to semitone representation
        semitones = []
        for pc in pitch_classes:
            note = Note(pc, 4)  # Use octave 4 as reference
            semitones.append(note.midi_number % 12)
        
        semitones = sorted(set(semitones))
        
        # Try to find best chord match
        best_match = self._find_best_chord_match(semitones, notes, bass_note)
        
        return best_match
    
    def detect_chord_from_midi_notes(self, midi_notes: List[Dict],
                                   consider_timing: bool = True) -> Optional[Chord]:
        """
        Detect chord from MIDI note dictionaries.
        
        Args:
            midi_notes: List of MIDI note dictionaries
            consider_timing: Whether to weight notes by duration
            
        Returns:
            Detected Chord object or None
        """
        if len(midi_notes) < self.min_notes:
            return None
        
        # Convert to Note objects
        notes = []
        weights = []
        
        for midi_note in midi_notes:
            try:
                note = Note(midi_note['midi_note'])
                notes.append(note)
                
                # Weight by duration and velocity if considering timing
                if consider_timing:
                    duration_weight = midi_note.get('duration', 1.0)
                    velocity_weight = midi_note.get('velocity', 64) / 127.0
                    weight = duration_weight * velocity_weight
                else:
                    weight = 1.0
                
                weights.append(weight)
                
            except (ValueError, KeyError):
                continue
        
        if not notes:
            return None
        
        # Find bass note (lowest note, weighted by bass_weight)
        bass_candidates = sorted(notes, key=lambda n: n.midi_number)
        bass_note = bass_candidates[0] if bass_candidates else None
        
        return self.detect_chord_from_notes(notes, bass_note)
    
    def _find_best_chord_match(self, semitones: List[int], notes: List[Note],
                              bass_note: Optional[Note] = None) -> Optional[Chord]:
        """Find the best matching chord template."""
        best_score = -1
        best_chord = None
        
        # Try each possible root note
        for root_semitone in semitones:
            # Normalize semitones relative to this root
            normalized = [(s - root_semitone) % 12 for s in semitones]
            normalized = sorted(set(normalized))
            
            # Try each chord template
            for chord_quality, template in self.CHORD_TEMPLATES.items():
                score = self._calculate_chord_score(normalized, template, notes, root_semitone)
                
                if score > best_score:
                    best_score = score
                    root_note = Note(root_semitone)
                    
                    # Handle slash chord if bass note is different from root
                    slash_bass = None
                    if bass_note and bass_note.pitch_class != root_note.pitch_class:
                        slash_bass = bass_note
                    
                    try:
                        best_chord = Chord(root_note, chord_quality, slash_bass)
                    except ValueError:
                        # Skip invalid chord qualities
                        continue
        
        # Only return chord if score is above threshold
        threshold = 0.5
        if best_score > threshold:
            return best_chord
        
        return None
    
    def _calculate_chord_score(self, normalized_semitones: List[int], 
                              template: List[int], notes: List[Note],
                              root_semitone: int) -> float:
        """Calculate how well a set of notes matches a chord template."""
        template_set = set(template)
        notes_set = set(normalized_semitones)
        
        # Basic match score: how many template notes are present
        matches = len(template_set.intersection(notes_set))
        template_size = len(template_set)
        
        if template_size == 0:
            return 0.0
        
        match_score = matches / template_size
        
        # Penalize extra notes that don't belong to the chord
        extra_notes = len(notes_set - template_set)
        total_notes = len(notes_set)
        
        if total_notes == 0:
            return 0.0
        
        extra_penalty = extra_notes / total_notes
        
        # Bonus for having the root in the bass
        bass_bonus = 0.0
        if notes:
            bass_note = min(notes, key=lambda n: n.midi_number)
            if (bass_note.midi_number % 12) == root_semitone:
                bass_bonus = 0.2
        
        # Bonus for having essential chord tones (root, third, fifth)
        essential_bonus = 0.0
        essential_tones = {0}  # Root is always essential
        
        if 3 in template or 4 in template:  # Has third
            if 3 in notes_set or 4 in notes_set:
                essential_bonus += 0.1
        
        if 7 in template:  # Has fifth
            if 7 in notes_set:
                essential_bonus += 0.1
        
        # Combine scores
        total_score = match_score - (0.5 * extra_penalty) + bass_bonus + essential_bonus
        
        return max(0.0, total_score)
    
    def detect_chord_sequence(self, note_groups: List[List[Dict]],
                            min_duration: float = 0.5) -> List[Optional[Chord]]:
        """
        Detect a sequence of chords from grouped notes.
        
        Args:
            note_groups: List of note groups (each group represents simultaneous notes)
            min_duration: Minimum duration to consider a chord valid
            
        Returns:
            List of detected chords (None for groups where no chord detected)
        """
        chords = []
        
        for group in note_groups:
            # Filter by minimum duration
            filtered_group = [note for note in group 
                            if note.get('duration', 0) >= min_duration]
            
            if len(filtered_group) >= self.min_notes:
                chord = self.detect_chord_from_midi_notes(filtered_group)
            else:
                chord = None
            
            chords.append(chord)
        
        return chords
    
    def analyze_chord_complexity(self, chord: Chord) -> Dict[str, any]:
        """
        Analyze the complexity of a detected chord.
        
        Args:
            chord: Chord to analyze
            
        Returns:
            Dictionary with complexity metrics
        """
        analysis = {
            'chord': chord,
            'num_notes': len(chord.notes),
            'has_extensions': False,
            'has_alterations': False,
            'complexity_score': 0
        }
        
        # Check for extensions (9th, 11th, 13th)
        quality = chord.quality
        if any(ext in quality for ext in ['9', '11', '13']):
            analysis['has_extensions'] = True
            analysis['complexity_score'] += 1
        
        # Check for alterations (b5, #5, b9, #9, etc.)
        if any(alt in quality for alt in ['b5', '#5', 'b9', '#9', '#11', 'b13']):
            analysis['has_alterations'] = True
            analysis['complexity_score'] += 2
        
        # Add points for seventh chords
        if '7' in quality:
            analysis['complexity_score'] += 0.5
        
        # Add points for diminished/augmented
        if quality in ['diminished', 'augmented', 'diminished7']:
            analysis['complexity_score'] += 1
        
        # Slash chord adds complexity
        if chord.bass != chord.root:
            analysis['complexity_score'] += 1
        
        return analysis
    
    def suggest_chord_alternatives(self, chord: Chord) -> List[Chord]:
        """
        Suggest alternative chord interpretations for the same notes.
        
        Args:
            chord: Original chord
            
        Returns:
            List of alternative chord interpretations
        """
        alternatives = []
        chord_notes = chord.notes
        
        # Try different root notes from the chord tones
        for note in chord_notes:
            if note.pitch_class != chord.root.pitch_class:
                try:
                    alt_chord = self.detect_chord_from_notes(chord_notes, note)
                    if alt_chord and alt_chord != chord:
                        alternatives.append(alt_chord)
                except:
                    continue
        
        # Remove duplicates
        unique_alternatives = []
        for alt in alternatives:
            if alt not in unique_alternatives:
                unique_alternatives.append(alt)
        
        return unique_alternatives
    
    def detect_chord_inversions(self, chord: Chord, voicing_notes: List[Note]) -> int:
        """
        Detect the inversion of a chord based on its voicing.
        
        Args:
            chord: Base chord
            voicing_notes: Actual notes in the voicing
            
        Returns:
            Inversion number (0 = root position, 1 = first inversion, etc.)
        """
        if not voicing_notes:
            return 0
        
        # Find the bass note
        bass_note = min(voicing_notes, key=lambda n: n.midi_number)
        bass_pitch_class = bass_note.pitch_class
        
        # Get chord tone pitch classes in order (root, third, fifth, seventh, etc.)
        chord_pitch_classes = [note.pitch_class for note in chord.notes]
        
        # Find which chord tone is in the bass
        try:
            inversion = chord_pitch_classes.index(bass_pitch_class)
            return inversion
        except ValueError:
            # Bass note not in chord tones
            return 0
    
    def analyze_voice_leading_motion(self, chord1: Chord, chord2: Chord) -> Dict[str, any]:
        """
        Analyze voice leading between two chords.
        
        Args:
            chord1: First chord
            chord2: Second chord
            
        Returns:
            Dictionary with voice leading analysis
        """
        analysis = {
            'root_motion': None,
            'common_tones': [],
            'motion_type': 'unknown',
            'voice_leading_quality': 'unknown'
        }
        
        # Calculate root motion
        root_interval = Interval.from_notes(chord1.root, chord2.root)
        analysis['root_motion'] = root_interval
        
        # Find common tones
        common_pitch_classes = chord1.pitch_classes.intersection(chord2.pitch_classes)
        analysis['common_tones'] = list(common_pitch_classes)
        
        # Classify motion type
        root_semitones = root_interval.simple_semitones
        
        if root_semitones == 0:
            analysis['motion_type'] = 'static'
        elif root_semitones in [1, 11]:  # Semitone motion
            analysis['motion_type'] = 'chromatic'
        elif root_semitones in [2, 10]:  # Whole tone motion
            analysis['motion_type'] = 'stepwise'
        elif root_semitones in [7, 5]:  # Fifth motion
            analysis['motion_type'] = 'fifth_motion'
        elif root_semitones in [4, 8]:  # Third motion
            analysis['motion_type'] = 'third_motion'
        else:
            analysis['motion_type'] = 'leap'
        
        # Evaluate voice leading quality
        num_common_tones = len(common_pitch_classes)
        if num_common_tones >= 2:
            analysis['voice_leading_quality'] = 'smooth'
        elif num_common_tones == 1:
            analysis['voice_leading_quality'] = 'moderate'
        else:
            analysis['voice_leading_quality'] = 'rough'
        
        return analysis