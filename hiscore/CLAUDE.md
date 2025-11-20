# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hi Score is an automated transcription pipeline that converts audio to tablature with customizable automatic playing difficulty reduction. The project focuses on audio-to-tablature transcription for different instruments (bass, guitar, piano, vocal).

## Development Commands

### Setup
- `uv sync` - Install dependencies using uv package manager
- `uv run python main.py --help` - Show available command line options

### Testing Audio Files
- Test audio file available: `kickback.mp3`

## Architecture

### Core Components

1. **main.py** - Entry point with CLI argument parsing and orchestration
2. **basic_pitch_onnx.py** - Simplified ONNX implementation of Basic Pitch transcription
3. **External Libraries Integration**:
   - **MVSEP-MDX23-Colab_v2/** - Audio separation models (MDX, Demucs alternatives)
   - **YourMT3/** - MT3-based transcription engine with model helper
   - **basic-pitch/** - Contains ONNX model files for Basic Pitch

### Processing Pipeline

1. **Audio Separation** (`audio_separation()`) - Uses Demucs htdemucs model to separate instruments
2. **Transcription** - Two engines available:
   - Basic Pitch ONNX (simplified implementation avoiding TensorFlow)
   - YourMT3 (model checkpoint: mc13_256_g4_all_v7_mt3f_sqr_rms_moe_wf4_n8k2_silu_rope_rp_b36_nops@last.ckpt)
3. **Note Simplification** - Placeholder for bass note difficulty reduction
4. **Tablature Rendering** - Uses MuseScore AppImage (`./bin/msscore.AppImage`)

### Key Dependencies

- PyTorch ecosystem (torch, torchaudio) for audio processing
- Demucs for audio source separation
- ONNX Runtime for Basic Pitch inference
- MuseScore AppImage for tablature generation
- librosa, soundfile for audio I/O

### Current Implementation Status

- ✅ Bass transcription (both engines)
- ❌ Guitar, piano, vocal modes (not implemented)
- ✅ Debugging support with `--keep_temp` flag
- ✅ HTML/PDF output formats

### Important File Locations

- ONNX model: `basic-pitch/basic_pitch/saved_models/icassp_2022/nmp.onnx`
- YourMT3 model checkpoint: `YourMT3/` directory
- MuseScore binary: `./bin/msscore.AppImage`
- Output directory: `output/` (configurable)

### Development Notes

- YourMT3 requires changing to its directory during model loading
- Basic Pitch ONNX avoids TensorFlow dependencies for simpler deployment
- Audio separation uses CPU by default but supports CUDA if available
- Temporary files can be preserved for debugging with `--keep_temp`