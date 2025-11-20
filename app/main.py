import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from celery.result import AsyncResult

from app.config import settings
from app.celery_app import celery_app
from app.schemas import (
    Error, JobEnqueueResponse, JobStatusResponse, JobStatus,
    AudioSeparationResult, AudioTranscriptionResult, ChordRecognitionResult,
    E2EBaseResult, EasierChordResult, ChordComplexificationResult,
    AlternativeChordRequest, AlternativeChordResponse, AlternativeChord,
    ChartFormat
)

# Create FastAPI app
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload and output directories
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.output_dir).mkdir(parents=True, exist_ok=True)

# Mount static files for outputs
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")


def get_job_status_from_celery(task_id: str) -> JobStatusResponse:
    """Convert Celery task state to JobStatusResponse"""
    result = AsyncResult(task_id, app=celery_app)

    status_map = {
        'PENDING': JobStatus.QUEUED,
        'STARTED': JobStatus.PROCESSING,
        'PROGRESS': JobStatus.PROCESSING,
        'SUCCESS': JobStatus.COMPLETED,
        'FAILURE': JobStatus.FAILED,
    }

    job_status = status_map.get(result.state, JobStatus.QUEUED)

    response = JobStatusResponse(
        jobId=task_id,
        status=job_status,
        updatedAt=datetime.utcnow()
    )

    if result.state == 'PROGRESS':
        meta = result.info or {}
        response.progressPercent = meta.get('percent', 0)

    if result.state == 'SUCCESS':
        response.completedAt = datetime.utcnow()
        response.progressPercent = 100

    if result.state == 'FAILURE':
        response.error = Error(
            code="TASK_FAILED",
            message=str(result.info) if result.info else "Task failed"
        )

    return response


# ============================================
# Audio Separation Endpoints
# ============================================

@app.post(
    "/tasks/audio-separation/enqueue",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"]
)
async def enqueue_audio_separation(
    audio_file: UploadFile = File(...),
    instruments: str = Form(..., description="Comma-separated list of instruments")
):
    """Enqueue audio separation task"""
    from app.tasks.audio_tasks import audio_separation_task

    # Validate file
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Save uploaded file
    file_path = Path(settings.upload_dir) / audio_file.filename
    with open(file_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)

    # Parse instruments
    instruments_list = [i.strip() for i in instruments.split(',')]

    # Enqueue task
    task = audio_separation_task.apply_async(args=[str(file_path), instruments_list])

    return JobEnqueueResponse(
        jobId=task.id,
        status=JobStatus.QUEUED,
        queuedAt=datetime.utcnow()
    )


@app.get(
    "/tasks/audio-separation/status/{jobId}",
    response_model=JobStatusResponse,
    tags=["tasks"]
)
async def get_audio_separation_status(jobId: str):
    """Get audio separation task status"""
    return get_job_status_from_celery(jobId)


@app.get(
    "/tasks/audio-separation/result/{jobId}",
    response_model=AudioSeparationResult,
    tags=["tasks"]
)
async def get_audio_separation_result(jobId: str):
    """Get audio separation result"""
    result = AsyncResult(jobId, app=celery_app)

    if result.state == 'SUCCESS':
        return AudioSeparationResult(**result.result)
    elif result.state in ['PENDING', 'STARTED', 'PROGRESS']:
        raise HTTPException(status_code=202, detail="Job not completed yet")
    else:
        raise HTTPException(status_code=404, detail="Job not found or failed")


# ============================================
# Audio Transcription Endpoints
# ============================================

@app.post(
    "/tasks/audio-transcription/enqueue",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"]
)
async def enqueue_audio_transcription(
    audio_file: UploadFile = File(...),
    instrument: str = Form(...),
    engine: str = Form("basic-pitch", description="Transcription engine")
):
    """Enqueue audio transcription task"""
    from app.tasks.audio_tasks import audio_transcription_task

    # Save uploaded file
    file_path = Path(settings.upload_dir) / audio_file.filename
    with open(file_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)

    # Enqueue task
    task = audio_transcription_task.apply_async(args=[str(file_path), instrument, engine])

    return JobEnqueueResponse(
        jobId=task.id,
        status=JobStatus.QUEUED,
        queuedAt=datetime.utcnow()
    )


@app.get(
    "/tasks/audio-transcription/status/{jobId}",
    response_model=JobStatusResponse,
    tags=["tasks"]
)
async def get_audio_transcription_status(jobId: str):
    """Get audio transcription task status"""
    return get_job_status_from_celery(jobId)


@app.get(
    "/tasks/audio-transcription/result/{jobId}",
    response_model=AudioTranscriptionResult,
    tags=["tasks"]
)
async def get_audio_transcription_result(jobId: str):
    """Get audio transcription result"""
    result = AsyncResult(jobId, app=celery_app)

    if result.state == 'SUCCESS':
        return AudioTranscriptionResult(**result.result)
    elif result.state in ['PENDING', 'STARTED', 'PROGRESS']:
        raise HTTPException(status_code=202, detail="Job not completed yet")
    else:
        raise HTTPException(status_code=404, detail="Job not found or failed")


# ============================================
# Chord Recognition Endpoints
# ============================================

@app.post(
    "/tasks/chord-recognition/enqueue",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"]
)
async def enqueue_chord_recognition(
    midi_file: UploadFile = File(...),
    format: ChartFormat = Form(ChartFormat.JSON)
):
    """Enqueue chord recognition task"""
    from app.tasks.chord_tasks import chord_recognition_task

    # Save uploaded file
    file_path = Path(settings.upload_dir) / midi_file.filename
    with open(file_path, "wb") as f:
        content = await midi_file.read()
        f.write(content)

    # Enqueue task
    task = chord_recognition_task.apply_async(args=[str(file_path), format.value])

    return JobEnqueueResponse(
        jobId=task.id,
        status=JobStatus.QUEUED,
        queuedAt=datetime.utcnow()
    )


@app.get(
    "/tasks/chord-recognition/status/{jobId}",
    response_model=JobStatusResponse,
    tags=["tasks"]
)
async def get_chord_recognition_status(jobId: str):
    """Get chord recognition task status"""
    return get_job_status_from_celery(jobId)


@app.get(
    "/tasks/chord-recognition/result/{jobId}",
    response_model=ChordRecognitionResult,
    tags=["tasks"]
)
async def get_chord_recognition_result(jobId: str):
    """Get chord recognition result"""
    result = AsyncResult(jobId, app=celery_app)

    if result.state == 'SUCCESS':
        return ChordRecognitionResult(**result.result)
    elif result.state in ['PENDING', 'STARTED', 'PROGRESS']:
        raise HTTPException(status_code=202, detail="Job not completed yet")
    else:
        raise HTTPException(status_code=404, detail="Job not found or failed")


# ============================================
# E2E Base Ready for Reharmonization Endpoints
# ============================================

@app.post(
    "/tasks/e2e-base-ready/enqueue",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"]
)
async def enqueue_e2e_base_ready(
    audio_file: UploadFile = File(...),
    instrument: str = Form(...)
):
    """Enqueue E2E base ready for reharmonization task"""
    from app.tasks.chord_tasks import e2e_base_ready_task

    # Save uploaded file
    file_path = Path(settings.upload_dir) / audio_file.filename
    with open(file_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)

    # Enqueue task
    task = e2e_base_ready_task.apply_async(args=[str(file_path), instrument])

    return JobEnqueueResponse(
        jobId=task.id,
        status=JobStatus.QUEUED,
        queuedAt=datetime.utcnow()
    )


@app.get(
    "/tasks/e2e-base-ready/status/{jobId}",
    response_model=JobStatusResponse,
    tags=["tasks"]
)
async def get_e2e_base_ready_status(jobId: str):
    """Get E2E base ready task status"""
    return get_job_status_from_celery(jobId)


@app.get(
    "/tasks/e2e-base-ready/result/{jobId}",
    response_model=E2EBaseResult,
    tags=["tasks"]
)
async def get_e2e_base_ready_result(jobId: str):
    """Get E2E base ready result"""
    result = AsyncResult(jobId, app=celery_app)

    if result.state == 'SUCCESS':
        return E2EBaseResult(**result.result)
    elif result.state in ['PENDING', 'STARTED', 'PROGRESS']:
        raise HTTPException(status_code=202, detail="Job not completed yet")
    else:
        raise HTTPException(status_code=404, detail="Job not found or failed")


# ============================================
# Easier Chord Recommendation Endpoints
# ============================================

@app.post(
    "/tasks/easier-chord-recommendation/enqueue",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"]
)
async def enqueue_easier_chord_recommendation(
    chord_file: UploadFile = File(...),
    target_instrument: str = Form(...),
    format: ChartFormat = Form(ChartFormat.JSON)
):
    """Enqueue easier chord recommendation task"""
    from app.tasks.chord_tasks import easier_chord_recommendation_task

    # Save uploaded file
    file_path = Path(settings.upload_dir) / chord_file.filename
    with open(file_path, "wb") as f:
        content = await chord_file.read()
        f.write(content)

    # Enqueue task
    task = easier_chord_recommendation_task.apply_async(
        args=[str(file_path), target_instrument, format.value]
    )

    return JobEnqueueResponse(
        jobId=task.id,
        status=JobStatus.QUEUED,
        queuedAt=datetime.utcnow()
    )


@app.get(
    "/tasks/easier-chord-recommendation/status/{jobId}",
    response_model=JobStatusResponse,
    tags=["tasks"]
)
async def get_easier_chord_recommendation_status(jobId: str):
    """Get easier chord recommendation task status"""
    return get_job_status_from_celery(jobId)


@app.get(
    "/tasks/easier-chord-recommendation/result/{jobId}",
    response_model=EasierChordResult,
    tags=["tasks"]
)
async def get_easier_chord_recommendation_result(jobId: str):
    """Get easier chord recommendation result"""
    result = AsyncResult(jobId, app=celery_app)

    if result.state == 'SUCCESS':
        return EasierChordResult(**result.result)
    elif result.state in ['PENDING', 'STARTED', 'PROGRESS']:
        raise HTTPException(status_code=202, detail="Job not completed yet")
    else:
        raise HTTPException(status_code=404, detail="Job not found or failed")


# ============================================
# Alternative Chord Recommendation (Operation)
# ============================================

@app.post(
    "/operations/alternative-chord-recommendation",
    response_model=AlternativeChordResponse,
    tags=["operations"]
)
async def alternative_chord_recommendation(
    chord_file: UploadFile = File(...),
    chord_index: int = Form(...)
):
    """Get alternative chord recommendations (synchronous operation)"""
    from halmoni import ChordProgression, Key, Chord, ChordSuggestionEngine
    import json

    # Read uploaded file
    content = await chord_file.read()
    text_content = content.decode('utf-8')

    # Parse chord progression
    if chord_file.filename.endswith('.json'):
        data = json.loads(text_content)
        key_str = data.get('key')
        key = Key.from_string(key_str) if key_str else Key('C', 'major')
        chord_symbols = [c['symbol'] for c in data['chords']]
    else:
        lines = text_content.split('\n')
        key = Key('C', 'major')
        for line in lines:
            if line.startswith('Key:'):
                key_str = line.replace('Key:', '').strip()
                key = Key.from_string(key_str)
                break
        chord_line = [l for l in lines if '-' in l][0] if any('-' in l for l in lines) else ''
        chord_symbols = [c.strip() for c in chord_line.split('-')]

    if chord_index < 0 or chord_index >= len(chord_symbols):
        raise HTTPException(status_code=400, detail="Invalid chord index")

    chords = [Chord.from_symbol(sym) for sym in chord_symbols]
    progression = ChordProgression(chords=chords, key=key)

    # Get suggestions for the specified position
    engine = ChordSuggestionEngine()
    suggestions = engine.get_suggestions_for_position(progression, chord_index, key)

    # Format alternatives
    alternatives = [
        AlternativeChord(
            chord=str(sug.chord),
            confidence=sug.confidence,
            reasoning=sug.reasoning
        )
        for sug in suggestions[:5]  # Top 5 alternatives
    ]

    return AlternativeChordResponse(
        originalChord=chord_symbols[chord_index],
        alternatives=alternatives
    )


# ============================================
# Chord Complexification Endpoints
# ============================================

@app.post(
    "/tasks/chord-complexification/enqueue",
    response_model=JobEnqueueResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["tasks"]
)
async def enqueue_chord_complexification(
    chord_file: UploadFile = File(...),
    target_style: str = Form(..., description="Target style (e.g., jazz, gospel, bossa nova)"),
    format: ChartFormat = Form(ChartFormat.NOTEN)
):
    """Enqueue chord complexification task using LLM"""
    from app.tasks.chord_tasks import chord_complexification_task

    # Save uploaded file
    file_path = Path(settings.upload_dir) / chord_file.filename
    with open(file_path, "wb") as f:
        content = await chord_file.read()
        f.write(content)

    # Enqueue task
    task = chord_complexification_task.apply_async(
        args=[str(file_path), target_style, format.value]
    )

    return JobEnqueueResponse(
        jobId=task.id,
        status=JobStatus.QUEUED,
        queuedAt=datetime.utcnow()
    )


@app.get(
    "/tasks/chord-complexification/status/{jobId}",
    response_model=JobStatusResponse,
    tags=["tasks"]
)
async def get_chord_complexification_status(jobId: str):
    """Get chord complexification task status"""
    return get_job_status_from_celery(jobId)


@app.get(
    "/tasks/chord-complexification/result/{jobId}",
    response_model=ChordComplexificationResult,
    tags=["tasks"]
)
async def get_chord_complexification_result(jobId: str):
    """Get chord complexification result"""
    result = AsyncResult(jobId, app=celery_app)

    if result.state == 'SUCCESS':
        return ChordComplexificationResult(**result.result)
    elif result.state in ['PENDING', 'STARTED', 'PROGRESS']:
        raise HTTPException(status_code=202, detail="Job not completed yet")
    else:
        raise HTTPException(status_code=404, detail="Job not found or failed")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "hiserver"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
