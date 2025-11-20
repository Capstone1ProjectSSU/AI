"""
Utilities for unified chord format handling
Provides conversions between different chord formats and unified representation
"""
import sys
import os
from typing import List, Dict, Any, Optional, Tuple

# Add noten to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../noten/src'))

try:
    from noten import parse, calculate_durations
    NOTEN_AVAILABLE = True
except ImportError:
    NOTEN_AVAILABLE = False
    print("Warning: noten library not available")


def create_noten_from_chords(
    chords: List[Dict[str, Any]],
    key: Optional[str] = None,
    time_signature: str = "4/4"
) -> str:
    """
    Convert chord progression to noten format string

    Args:
        chords: List of chord dicts with 'symbol' and 'duration'
        key: Key signature (e.g., 'C major')
        time_signature: Time signature (default '4/4')

    Returns:
        Noten format string
    """
    lines = []

    # Add metadata
    if key:
        lines.append(f"{{key: {key}}}")
    lines.append(f"{{time: {time_signature}}}")
    lines.append("")

    # Convert chords to measures
    # For simplicity, we'll put 4 beats per measure
    numerator = int(time_signature.split('/')[0])
    current_measure = []
    current_beats = 0.0

    for chord_data in chords:
        symbol = chord_data['symbol']
        duration = chord_data.get('duration', 1.0)

        # Add chord to measure
        current_measure.append(symbol)

        # Add continuation markers for duration > 1
        if duration > 1:
            for _ in range(int(duration) - 1):
                current_measure.append('.')

        current_beats += duration

        # Start new measure when we reach the time signature numerator
        if current_beats >= numerator:
            measure_str = "| " + " ".join(current_measure) + " |"
            lines.append(measure_str)
            current_measure = []
            current_beats = 0.0

    # Add remaining chords if any
    if current_measure:
        # Pad with continuation markers if needed
        while current_beats < numerator:
            current_measure.append('.')
            current_beats += 1
        measure_str = "| " + " ".join(current_measure) + " |"
        lines.append(measure_str)

    return "\n".join(lines)


def parse_noten_to_time_chord_pairs(noten_string: str) -> Tuple[List[Dict[str, Any]], Optional[dict], Optional[str], Optional[str]]:
    """
    Parse noten format string to time-chord pairs

    Args:
        noten_string: Noten format string

    Returns:
        Tuple of (time_chord_pairs, ast_dict, key, time_signature)
    """
    if not NOTEN_AVAILABLE:
        raise ImportError("noten library is not available")

    # Parse noten string
    ast = parse(noten_string)
    ast_dict = ast.to_dict()

    # Calculate durations to get time-chord pairs
    events = calculate_durations(ast_dict)

    # Extract metadata
    key = None
    time_signature = None

    for item in ast_dict.get('body', []):
        if item.get('type') == 'Annotation':
            content = item.get('content', '')
            if content.startswith('key:'):
                key = content.replace('key:', '').strip()
            elif content.startswith('time:'):
                time_signature = content.replace('time:', '').strip()

    # Convert events to time-chord pairs
    time_chord_pairs = []
    for event in events:
        if 'chord' in event:
            time_chord_pairs.append({
                'time': event['time'],
                'chord': event['chord'],
                'duration': event['duration']
            })

    return time_chord_pairs, ast_dict, key, time_signature


def chords_to_time_pairs(chords: List[Dict[str, Any]], start_time: float = 0.0) -> List[Dict[str, Any]]:
    """
    Convert simple chord list to time-chord pairs

    Args:
        chords: List of chord dicts with 'symbol' and 'duration'
        start_time: Starting time in beats

    Returns:
        List of time-chord pairs
    """
    time_chord_pairs = []
    current_time = start_time

    for chord_data in chords:
        symbol = chord_data['symbol']
        duration = chord_data.get('duration', 1.0)

        time_chord_pairs.append({
            'time': current_time,
            'chord': symbol,
            'duration': duration
        })

        current_time += duration

    return time_chord_pairs


def create_unified_progression(
    chords: List[Dict[str, Any]] = None,
    noten_string: str = None,
    key: Optional[str] = None,
    time_signature: str = "4/4"
) -> Dict[str, Any]:
    """
    Create unified chord progression format

    Args:
        chords: List of chord dicts (if converting from simple format)
        noten_string: Noten format string (if already in noten format)
        key: Key signature
        time_signature: Time signature

    Returns:
        Unified progression dict with noten AST and time-chord pairs
    """
    if noten_string and NOTEN_AVAILABLE:
        # Parse from noten string
        time_chord_pairs, ast_dict, parsed_key, parsed_time_sig = parse_noten_to_time_chord_pairs(noten_string)

        # Use parsed metadata if not provided
        if parsed_key and not key:
            key = parsed_key
        if parsed_time_sig and not time_signature:
            time_signature = parsed_time_sig

        return {
            'key': key,
            'timeSignature': time_signature,
            'notenAst': ast_dict,
            'notenString': noten_string,
            'timeChordPairs': time_chord_pairs
        }

    elif chords:
        # Convert from simple chord format
        time_chord_pairs = chords_to_time_pairs(chords)

        # Create noten string if library is available
        noten_str = None
        ast_dict = None
        if NOTEN_AVAILABLE:
            try:
                noten_str = create_noten_from_chords(chords, key, time_signature)
                ast = parse(noten_str)
                ast_dict = ast.to_dict()
            except Exception as e:
                print(f"Warning: Failed to create noten format: {e}")

        return {
            'key': key,
            'timeSignature': time_signature,
            'notenAst': ast_dict,
            'notenString': noten_str,
            'timeChordPairs': time_chord_pairs
        }

    else:
        raise ValueError("Either chords or noten_string must be provided")
