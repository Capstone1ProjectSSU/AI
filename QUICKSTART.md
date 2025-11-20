# Quick Start Guide

## Prerequisites

1. Python 3.12+
2. Docker (for Redis)
3. FFmpeg installed on system

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or using uv (recommended):

```bash
uv sync
```

### 2. Set Up Environment

```bash
cp .env.example .env
```

Edit `.env` if needed to customize settings.

### 3. Start Redis

```bash
docker-compose up -d
```

Verify Redis is running:

```bash
docker-compose ps
```

### 4. Start the Server and Worker

Open two terminal windows:

**Terminal 1 - FastAPI Server:**
```bash
./start_server.sh
```

Or manually:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Celery Worker:**
```bash
./start_worker.sh
```

Or manually:
```bash
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### 5. Verify Installation

Visit http://localhost:8000/docs to see the Swagger UI.

Check health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "hiserver"
}
```

## Testing the API

### Example 1: Audio Separation

```bash
# 1. Enqueue task
curl -X POST "http://localhost:8000/tasks/audio-separation/enqueue" \
  -F "audio_file=@your_song.mp3" \
  -F "instruments=bass,drums,vocals"

# Response: {"jobId":"abc-123","status":"queued","queuedAt":"2024-..."}

# 2. Check status (replace JOB_ID with actual ID from step 1)
curl "http://localhost:8000/tasks/audio-separation/status/JOB_ID"

# 3. Get result (when status is "completed")
curl "http://localhost:8000/tasks/audio-separation/result/JOB_ID"
```

### Example 2: E2E Pipeline

```bash
# Run complete pipeline: separation → transcription → chord recognition
curl -X POST "http://localhost:8000/tasks/e2e-base-ready/enqueue" \
  -F "audio_file=@your_song.mp3" \
  -F "instrument=bass"

# Check status
curl "http://localhost:8000/tasks/e2e-base-ready/status/JOB_ID"

# Get results
curl "http://localhost:8000/tasks/e2e-base-ready/result/JOB_ID"
```

### Example 3: Alternative Chord Recommendation (Immediate)

```bash
curl -X POST "http://localhost:8000/operations/alternative-chord-recommendation" \
  -F "chord_file=@chords.json" \
  -F "chord_index=2"
```

## Monitoring

### Check Celery Worker Status

```bash
celery -A app.celery_app inspect active
```

### Check Redis

```bash
docker exec -it hiserver_redis redis-cli ping
```

Should return: `PONG`

### View Logs

FastAPI logs appear in Terminal 1.
Celery worker logs appear in Terminal 2.

## Stopping the Services

### Stop Server and Worker

Press `Ctrl+C` in both terminal windows.

### Stop Redis

```bash
docker-compose down
```

## Common Issues

### Redis Connection Error

**Problem:** `ConnectionError: Error 111 connecting to localhost:6379`

**Solution:**
```bash
docker-compose up -d
docker-compose ps  # Verify redis is running
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'halmoni'` or `'hiscore'`

**Solution:** The server automatically adds halmoni and hiscore to Python path. Make sure you're running from the project root directory.

### File Upload Too Large

**Problem:** File upload rejected

**Solution:** Increase `MAX_FILE_SIZE` in `.env` file (default is 100MB).

## Next Steps

- Read [README.md](README.md) for detailed API documentation
- Visit http://localhost:8000/docs for interactive API documentation
- Check [api.yaml](api.yaml) for the OpenAPI specification
