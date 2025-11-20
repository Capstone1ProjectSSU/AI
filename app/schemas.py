from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ChartFormat(str, Enum):
    JSON = "json"
    TXT = "txt"
    NOTEN = "noten"


class Error(BaseModel):
    code: str = Field(..., example="INVALID_INPUT")
    message: str
    details: Optional[dict[str, Any]] = None


class JobEnqueueResponse(BaseModel):
    jobId: str
    status: JobStatus = JobStatus.QUEUED
    queuedAt: Optional[datetime] = None


class JobStatusResponse(BaseModel):
    jobId: str
    status: JobStatus
    progressPercent: Optional[float] = Field(None, ge=0, le=100)
    queuedAt: Optional[datetime] = None
    startedAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    error: Optional[Error] = None


# Audio Separation
class AudioSeparationRequest(BaseModel):
    instruments: list[str] = Field(..., description="List of instruments to separate")


class SeparatedAudio(BaseModel):
    instrument: str
    url: str
    format: str = "opus"


class AudioSeparationResult(BaseModel):
    jobId: str
    outputs: list[SeparatedAudio]


# Audio Transcription
class AudioTranscriptionRequest(BaseModel):
    instrument: str = Field(..., description="Instrument name for transcription")


class AudioTranscriptionResult(BaseModel):
    jobId: str
    transcriptionUrl: str
    format: str = "mid"


# Chord Recognition
class ChordRecognitionRequest(BaseModel):
    format: ChartFormat = ChartFormat.JSON


class ChordRecognitionResult(BaseModel):
    jobId: str
    chordProgressionUrl: str
    format: ChartFormat
    unifiedProgression: Optional['UnifiedChordProgression'] = None


# E2E Base Ready for Reharmonization
class E2EBaseRequest(BaseModel):
    instrument: str = Field(..., description="Instrument name")


class E2EBaseResult(BaseModel):
    jobId: str
    transcriptionUrl: str
    separatedAudioUrl: str
    chordProgressionUrl: str
    format: ChartFormat = ChartFormat.JSON


# Easier Chord Recommendation
class EasierChordRequest(BaseModel):
    targetInstrument: str = Field(..., description="Target instrument name")
    format: ChartFormat = ChartFormat.JSON


class EasierChordResult(BaseModel):
    jobId: str
    easierChordProgressionUrl: str
    format: ChartFormat
    unifiedProgression: Optional['UnifiedChordProgression'] = None


# Alternative Chord Recommendation (Operation - synchronous)
class AlternativeChordRequest(BaseModel):
    chordIndex: int = Field(..., description="Index of the chord to substitute", ge=0)


class AlternativeChord(BaseModel):
    chord: str
    confidence: float = Field(..., ge=0, le=1)
    reasoning: str


class AlternativeChordResponse(BaseModel):
    originalChord: str
    alternatives: list[AlternativeChord]


# Unified Chord Format
class TimeChordPair(BaseModel):
    time: float = Field(..., description="Time in beats")
    chord: str = Field(..., description="Chord symbol")
    duration: float = Field(..., description="Duration in beats")


class UnifiedChordProgression(BaseModel):
    key: Optional[str] = None
    timeSignature: Optional[str] = None
    notenAst: Optional[dict] = Field(None, description="Noten format AST")
    notenString: Optional[str] = Field(None, description="Noten format string")
    timeChordPairs: list[TimeChordPair] = Field(..., description="Time-chord pairs")


# Chord Complexification
class ChordComplexificationRequest(BaseModel):
    targetStyle: str = Field(..., description="Target style for complexification (e.g., 'jazz', 'gospel', 'bossa nova')")
    format: ChartFormat = ChartFormat.NOTEN


class ChordComplexificationResult(BaseModel):
    jobId: str
    complexifiedChordProgressionUrl: str
    format: ChartFormat
    unifiedProgression: Optional[UnifiedChordProgression] = None
