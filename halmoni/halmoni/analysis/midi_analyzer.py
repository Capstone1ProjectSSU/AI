"""MIDI file analysis and preprocessing utilities."""

from typing import List, Dict, Tuple, Optional, Set
import mido
import numpy as np
from ..core import Note, Chord


class MIDIAnalyzer:
    """Analyzes MIDI files and extracts musical information."""
    
    def __init__(self, quantization: float = 0.25, min_velocity: int = 20):
        """
        Initialize MIDI analyzer.
        
        Args:
            quantization: Time quantization in beats (0.25 = 16th notes)
            min_velocity: Minimum velocity to consider a note active
        """
        self.quantization = quantization
        self.min_velocity = min_velocity
    
    def load_midi_file(self, filepath: str) -> Dict[str, any]:
        """
        Load and analyze a MIDI file.
        
        Args:
            filepath: Path to MIDI file
            
        Returns:
            Dictionary with MIDI analysis data
        """
        try:
            midi_file = mido.MidiFile(filepath)
        except Exception as e:
            raise ValueError(f"Could not load MIDI file: {e}")
        
        analysis = {
            'filename': filepath,
            'ticks_per_beat': midi_file.ticks_per_beat,
            'tempo': 120,  # Default, will be updated if tempo changes found
            'time_signature': (4, 4),  # Default
            'tracks': [],
            'notes': [],
            'tempo_changes': [],
            'time_signature_changes': []
        }
        
        # Process each track
        for track_idx, track in enumerate(midi_file.tracks):
            track_analysis = self._analyze_track(track, midi_file.ticks_per_beat, track_idx)
            analysis['tracks'].append(track_analysis)
            analysis['notes'].extend(track_analysis['notes'])
            
            # Update global tempo and time signature from first occurrences
            if track_analysis['tempo_changes'] and not analysis['tempo_changes']:
                analysis['tempo'] = track_analysis['tempo_changes'][0]['tempo']
                analysis['tempo_changes'] = track_analysis['tempo_changes']
            
            if track_analysis['time_signature_changes'] and not analysis['time_signature_changes']:
                analysis['time_signature'] = track_analysis['time_signature_changes'][0]['time_signature']
                analysis['time_signature_changes'] = track_analysis['time_signature_changes']
        
        # Sort notes by time
        analysis['notes'] = sorted(analysis['notes'], key=lambda n: n['start_time'])
        
        return analysis
    
    def _analyze_track(self, track: mido.MidiTrack, ticks_per_beat: int, track_idx: int) -> Dict[str, any]:
        """Analyze a single MIDI track."""
        track_analysis = {
            'track_index': track_idx,
            'track_name': '',
            'channel': None,
            'notes': [],
            'tempo_changes': [],
            'time_signature_changes': [],
            'active_notes': {}  # For tracking note on/off events
        }
        
        current_time = 0
        current_tempo = 500000  # Default tempo (120 BPM in microseconds)
        
        for msg in track:
            current_time += msg.time
            
            if msg.type == 'track_name':
                track_analysis['track_name'] = msg.name
            
            elif msg.type == 'set_tempo':
                tempo_bpm = mido.tempo2bpm(msg.tempo)
                track_analysis['tempo_changes'].append({
                    'time': current_time,
                    'tempo': tempo_bpm
                })
                current_tempo = msg.tempo
            
            elif msg.type == 'time_signature':
                track_analysis['time_signature_changes'].append({
                    'time': current_time,
                    'time_signature': (msg.numerator, msg.denominator)
                })
            
            elif msg.type == 'note_on' and msg.velocity >= self.min_velocity:
                # Convert ticks to beats
                time_beats = mido.tick2second(current_time, ticks_per_beat, current_tempo) * (current_tempo / 500000) * 2
                
                note_data = {
                    'midi_note': msg.note,
                    'velocity': msg.velocity,
                    'channel': msg.channel,
                    'start_time': time_beats,
                    'end_time': None  # Will be set by note_off
                }
                
                # Store in active notes for when we get the note_off
                key = (msg.channel, msg.note)
                track_analysis['active_notes'][key] = note_data
                
                if track_analysis['channel'] is None:
                    track_analysis['channel'] = msg.channel
            
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in track_analysis['active_notes']:
                    note_data = track_analysis['active_notes'][key]
                    time_beats = mido.tick2second(current_time, ticks_per_beat, current_tempo) * (current_tempo / 500000) * 2
                    note_data['end_time'] = time_beats
                    note_data['duration'] = time_beats - note_data['start_time']
                    
                    track_analysis['notes'].append(note_data)
                    del track_analysis['active_notes'][key]
        
        # Handle any remaining active notes (treat as ending at track end)
        for note_data in track_analysis['active_notes'].values():
            note_data['end_time'] = current_time
            note_data['duration'] = current_time - note_data['start_time']
            track_analysis['notes'].append(note_data)
        
        return track_analysis
    
    def quantize_timing(self, notes: List[Dict], quantization: Optional[float] = None) -> List[Dict]:
        """
        Quantize note timings to the nearest grid subdivision.
        
        Args:
            notes: List of note dictionaries
            quantization: Quantization value in beats (uses instance default if None)
        """
        quant = quantization or self.quantization
        quantized_notes = []
        
        for note in notes:
            quantized_note = note.copy()
            
            # Quantize start time
            quantized_start = round(note['start_time'] / quant) * quant
            quantized_note['start_time'] = quantized_start
            
            # Quantize duration, but ensure minimum duration
            original_duration = note['duration']
            quantized_duration = max(quant, round(original_duration / quant) * quant)
            quantized_note['duration'] = quantized_duration
            quantized_note['end_time'] = quantized_start + quantized_duration
            
            quantized_notes.append(quantized_note)
        
        return quantized_notes
    
    def group_simultaneous_notes(self, notes: List[Dict], tolerance: float = 0.1) -> List[List[Dict]]:
        """
        Group notes that occur simultaneously (within tolerance).
        
        Args:
            notes: List of note dictionaries
            tolerance: Time tolerance for grouping (in beats)
            
        Returns:
            List of note groups (each group is a list of simultaneous notes)
        """
        if not notes:
            return []
        
        # Sort notes by start time
        sorted_notes = sorted(notes, key=lambda n: n['start_time'])
        
        groups = []
        current_group = [sorted_notes[0]]
        current_time = sorted_notes[0]['start_time']
        
        for note in sorted_notes[1:]:
            if abs(note['start_time'] - current_time) <= tolerance:
                # Add to current group
                current_group.append(note)
            else:
                # Start new group
                groups.append(current_group)
                current_group = [note]
                current_time = note['start_time']
        
        # Add the last group
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def extract_melody_line(self, notes: List[Dict]) -> List[Dict]:
        """
        Extract the melody line (highest notes) from a collection of notes.
        
        Args:
            notes: List of note dictionaries
            
        Returns:
            List of melody notes
        """
        note_groups = self.group_simultaneous_notes(notes)
        melody_notes = []
        
        for group in note_groups:
            # Find the highest note in each group
            highest_note = max(group, key=lambda n: n['midi_note'])
            melody_notes.append(highest_note)
        
        return melody_notes
    
    def extract_bass_line(self, notes: List[Dict]) -> List[Dict]:
        """
        Extract the bass line (lowest notes) from a collection of notes.
        
        Args:
            notes: List of note dictionaries
            
        Returns:
            List of bass notes
        """
        note_groups = self.group_simultaneous_notes(notes)
        bass_notes = []
        
        for group in note_groups:
            # Find the lowest note in each group
            lowest_note = min(group, key=lambda n: n['midi_note'])
            bass_notes.append(lowest_note)
        
        return bass_notes
    
    def get_active_notes_at_time(self, notes: List[Dict], time: float) -> List[Dict]:
        """
        Get all notes that are active at a specific time.
        
        Args:
            notes: List of note dictionaries
            time: Time point to check
            
        Returns:
            List of active notes
        """
        active_notes = []
        
        for note in notes:
            if note['start_time'] <= time < note['end_time']:
                active_notes.append(note)
        
        return active_notes
    
    def get_time_windows(self, notes: List[Dict], window_size: float) -> List[Tuple[float, List[Dict]]]:
        """
        Divide notes into time windows for analysis.
        
        Args:
            notes: List of note dictionaries
            window_size: Size of each window in beats
            
        Returns:
            List of (window_start_time, notes_in_window) tuples
        """
        if not notes:
            return []
        
        # Find the time range
        start_time = min(note['start_time'] for note in notes)
        end_time = max(note['end_time'] for note in notes)
        
        windows = []
        current_time = start_time
        
        while current_time < end_time:
            window_end = current_time + window_size
            
            # Find notes that are active during this window
            window_notes = []
            for note in notes:
                # Note is in window if it overlaps with the window time range
                if note['start_time'] < window_end and note['end_time'] > current_time:
                    window_notes.append(note)
            
            if window_notes:  # Only add non-empty windows
                windows.append((current_time, window_notes))
            
            current_time += window_size
        
        return windows
    
    def convert_to_note_objects(self, midi_notes: List[Dict]) -> List[Note]:
        """
        Convert MIDI note dictionaries to Note objects.
        
        Args:
            midi_notes: List of MIDI note dictionaries
            
        Returns:
            List of Note objects
        """
        note_objects = []
        
        for midi_note in midi_notes:
            try:
                note = Note(midi_note['midi_note'])
                note_objects.append(note)
            except ValueError:
                # Skip invalid MIDI notes
                continue
        
        return note_objects
    
    def get_pitch_class_histogram(self, notes: List[Dict]) -> Dict[str, int]:
        """
        Create a histogram of pitch classes in the notes.
        
        Args:
            notes: List of note dictionaries
            
        Returns:
            Dictionary mapping pitch classes to occurrence counts
        """
        histogram = {}
        
        for note_dict in notes:
            try:
                note = Note(note_dict['midi_note'])
                pitch_class = note.pitch_class
                histogram[pitch_class] = histogram.get(pitch_class, 0) + 1
            except ValueError:
                continue
        
        return histogram
    
    def detect_key_signature(self, notes: List[Dict]) -> Tuple[str, str]:
        """
        Simple key detection based on pitch class histogram.
        
        Args:
            notes: List of note dictionaries
            
        Returns:
            Tuple of (tonic, mode) representing the detected key
        """
        histogram = self.get_pitch_class_histogram(notes)
        
        if not histogram:
            return ('C', 'major')  # Default fallback
        
        # Major key profiles (Krumhansl-Schmuckler)
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        chromatic_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        
        # Create histogram vector
        histogram_vector = [histogram.get(note, 0) for note in chromatic_notes]
        
        # Normalize
        total = sum(histogram_vector)
        if total == 0:
            return ('C', 'major')
        
        histogram_vector = [x / total for x in histogram_vector]
        
        best_correlation = -1
        best_key = ('C', 'major')
        
        # Test all major keys
        for i, tonic in enumerate(chromatic_notes):
            # Rotate profile to match this tonic
            rotated_profile = major_profile[i:] + major_profile[:i]
            correlation = np.corrcoef(histogram_vector, rotated_profile)[0, 1]
            
            if not np.isnan(correlation) and correlation > best_correlation:
                best_correlation = correlation
                best_key = (tonic, 'major')
        
        # Test all minor keys
        for i, tonic in enumerate(chromatic_notes):
            rotated_profile = minor_profile[i:] + minor_profile[:i]
            correlation = np.corrcoef(histogram_vector, rotated_profile)[0, 1]
            
            if not np.isnan(correlation) and correlation > best_correlation:
                best_correlation = correlation
                best_key = (tonic, 'minor')
        
        return best_key