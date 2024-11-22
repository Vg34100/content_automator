# processing_status.py - for main-v2.py

from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

class ProcessingStatus(Enum):
    PENDING = "pending"
    TRANSCRIBED = "transcribed"
    METADATA_GENERATED = "metadata_generated"
    READY_TO_UPLOAD = "ready_to_upload"
    UPLOADED = "uploaded"
    FAILED = "failed"

@dataclass
class VideoProcessingInfo:
    video_path: str
    channel_code: str
    status: ProcessingStatus
    transcript: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    upload_date: Optional[datetime] = None
    video_id: Optional[str] = None
    error: Optional[str] = None
    last_updated: datetime = datetime.now()