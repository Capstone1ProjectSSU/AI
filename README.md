# HiServer - Music Processing API

A FastAPI + Celery server for long-running music processing tasks including audio separation, transcription, chord recognition, and recommendations.

## Features

### Queueable Tasks (Async)
- **Audio Separation**: Separate audio into instrument stems (drums, bass, vocals, etc.)
- **Audio Transcription**: Convert audio to MIDI using Basic Pitch or YourMT3
- **Chord Recognition**: Detect chords from MIDI files
- **E2E Base Ready**: Complete pipeline (separation + transcription + chord recognition)
- **Easier Chord Recommendation**: Suggest simpler chord alternatives for instruments

### Immediate Operations (Sync)
- **Alternative Chord Recommendation**: Get alternative chord suggestions for a specific position

## Architecture

- **FastAPI**: REST API server
- **Celery**: Distributed task queue for long-running jobs
- **Redis**: Message broker and result backend
- **hiscore**: Audio separation and transcription library
- **halmoni**: Chord analysis and suggestion library

## Prerequisites

- Python 3.12+
- Docker (for Redis)
- FFmpeg (for audio processing)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Copy environment file:
```bash
cp .env.example .env
```

3. Start Redis:
```bash
docker-compose up -d
```

## Running the Server

### Option 1: Using startup scripts

Terminal 1 - Start FastAPI server:
```bash
./start_server.sh
```

Terminal 2 - Start Celery worker:
```bash
./start_worker.sh
```

### Option 2: Manual start

Terminal 1 - FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 - Celery worker:
```bash
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Usage Examples

### Audio Separation

1. Enqueue task:
```bash
curl -X POST "http://localhost:8000/tasks/audio-separation/enqueue" \
  -F "audio_file=@song.mp3" \
  -F "instruments=bass,drums,vocals"
```

2. Check status:
```bash
curl "http://localhost:8000/tasks/audio-separation/status/{jobId}"
```

3. Get result:
```bash
curl "http://localhost:8000/tasks/audio-separation/result/{jobId}"
```

### Audio Transcription

```bash
curl -X POST "http://localhost:8000/tasks/audio-transcription/enqueue" \
  -F "audio_file=@bass.wav" \
  -F "instrument=bass" \
  -F "engine=basic-pitch"
```

### Chord Recognition

```bash
curl -X POST "http://localhost:8000/tasks/chord-recognition/enqueue" \
  -F "midi_file=@transcription.mid" \
  -F "format=json"
```

### E2E Base Ready for Reharmonization

```bash
curl -X POST "http://localhost:8000/tasks/e2e-base-ready/enqueue" \
  -F "audio_file=@song.mp3" \
  -F "instrument=bass"
```

### Alternative Chord Recommendation (Immediate)

```bash
curl -X POST "http://localhost:8000/operations/alternative-chord-recommendation" \
  -F "chord_file=@chords.json" \
  -F "chord_index=2"
```

## Task Status Flow

1. **queued**: Task is waiting in the queue
2. **processing**: Task is currently being executed
3. **completed**: Task finished successfully
4. **failed**: Task encountered an error

## Project Structure

```
hiserver/
├── app/
│   ├── main.py              # FastAPI application
│   ├── celery_app.py        # Celery configuration
│   ├── config.py            # Settings and configuration
│   ├── schemas.py           # Pydantic models
│   └── tasks/
│       ├── audio_tasks.py   # Audio processing tasks
│       └── chord_tasks.py   # Chord analysis tasks
├── halmoni/                 # Chord analysis library
├── hiscore/                 # Audio processing library
├── uploads/                 # Uploaded files (auto-created)
├── outputs/                 # Task results (auto-created)
├── docker-compose.yml       # Redis container
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## API Endpoints

### Tasks (Async)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks/audio-separation/enqueue` | POST | Enqueue audio separation |
| `/tasks/audio-separation/status/{jobId}` | GET | Get separation status |
| `/tasks/audio-separation/result/{jobId}` | GET | Get separation result |
| `/tasks/audio-transcription/enqueue` | POST | Enqueue transcription |
| `/tasks/audio-transcription/status/{jobId}` | GET | Get transcription status |
| `/tasks/audio-transcription/result/{jobId}` | GET | Get transcription result |
| `/tasks/chord-recognition/enqueue` | POST | Enqueue chord recognition |
| `/tasks/chord-recognition/status/{jobId}` | GET | Get recognition status |
| `/tasks/chord-recognition/result/{jobId}` | GET | Get recognition result |
| `/tasks/e2e-base-ready/enqueue` | POST | Enqueue E2E pipeline |
| `/tasks/e2e-base-ready/status/{jobId}` | GET | Get E2E status |
| `/tasks/e2e-base-ready/result/{jobId}` | GET | Get E2E result |
| `/tasks/easier-chord-recommendation/enqueue` | POST | Enqueue easier chords |
| `/tasks/easier-chord-recommendation/status/{jobId}` | GET | Get recommendation status |
| `/tasks/easier-chord-recommendation/result/{jobId}` | GET | Get recommendation result |

### Operations (Sync)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/operations/alternative-chord-recommendation` | POST | Get chord alternatives |

### Utility

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |

## Configuration

Edit `.env` file to customize:

- `CELERY_BROKER_URL`: Redis connection URL
- `CELERY_RESULT_BACKEND`: Result storage backend
- `UPLOAD_DIR`: Directory for uploaded files
- `OUTPUT_DIR`: Directory for task outputs
- `MAX_FILE_SIZE`: Maximum upload file size (bytes)

## Development

### Running tests
```bash
pytest
```

### Code formatting
```bash
black app/
```

### Type checking
```bash
mypy app/
```

## Troubleshooting

### Redis connection error
- Ensure Redis is running: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`

### Task not processing
- Verify Celery worker is running
- Check worker logs for errors
- Ensure Redis connection is working

### File upload errors
- Check file size limits
- Verify supported audio formats
- Ensure upload directory has write permissions

## License

See project license file.
