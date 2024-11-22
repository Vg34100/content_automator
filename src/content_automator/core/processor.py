# video_processor.py - for main-v2.py

import json
import os
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional
import shutil
from pathlib import Path

from processing_status import ProcessingStatus, VideoProcessingInfo
from metadata_validator import MetadataValidator
from utils.general import log_error, log_warning
from utils.logging_config import setup_logging
from utils.general import log_info

class VideoProcessor:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.data_path = self.base_path / "data"
        self.outputs_path = self.data_path / "outputs"
        self.metadata_path = self.outputs_path / "metadata"
        self.transcripts_path = self.outputs_path / "transcripts"
        self.status_file = self.data_path / "processing_status.json"
        
        # Create necessary directories
        self.metadata_path.mkdir(parents=True, exist_ok=True)
        self.transcripts_path.mkdir(parents=True, exist_ok=True)
        
        self.processing_status: Dict[str, VideoProcessingInfo] = {}
        self.load_status()
        setup_logging(base_path)
        log_info("Initializing VideoProcessor")
        

    def load_status(self):
        """Load existing processing status from file."""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                data = json.load(f)
                self.processing_status = {
                    k: VideoProcessingInfo(**v) for k, v in data.items()
                }

    def save_status(self):
        """Save current processing status to file."""
        with open(self.status_file, 'w') as f:
            json.dump(
                {k: v.__dict__ for k, v in self.processing_status.items()},
                f,
                indent=2,
                default=str
            )

    def save_transcript(self, video_path: str, transcript: str):
        """Save transcript to file."""
        transcript_file = self.transcripts_path / f"{Path(video_path).stem}.txt"
        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(transcript)
        return transcript_file

    def save_metadata(self, video_path: str, metadata: Dict):
        """Save metadata to file with validation."""
        if not MetadataValidator.validate_metadata(metadata):
            log_error(f"Invalid metadata for {video_path}")
            raise ValueError("Invalid metadata")
            
        log_info(f"Saving validated metadata for {video_path}")
        metadata_file = self.metadata_path / f"{Path(video_path).stem}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        return metadata_file

    def calculate_publish_date(self, video_path: str, base_date: datetime) -> datetime:
        """Calculate publish date based on video sequence."""
        series_id, sequence_num = parse_video_sequence(video_path)
        if series_id is None:
            log_warning(f"Could not parse sequence info for {video_path}")
            return base_date
            
        # Adjust date based on sequence number (subtract 1 since sequence starts at 1)
        return base_date + timedelta(days=(sequence_num - 1))

    def update_video_status(
        self,
        video_path: str,
        status: ProcessingStatus,
        **kwargs
    ):
        """Update processing status for a video."""
        if video_path not in self.processing_status:
            self.processing_status[video_path] = VideoProcessingInfo(
                video_path=video_path,
                channel_code=kwargs.get('channel_code', ''),
                status=status
            )
        
        video_info = self.processing_status[video_path]
        video_info.status = status
        video_info.last_updated = datetime.now()
        
        for key, value in kwargs.items():
            setattr(video_info, key, value)
        
        self.save_status()
        
def parse_video_sequence(video_path: str) -> tuple:
    """
    Parse video filename to extract sequence information.
    Returns (series_identifier, sequence_number)
    """
    filename = os.path.basename(video_path)
    
    # Extract series identifier (everything before the sequence number)
    series_match = re.match(r'.*?(\[\w+\]-\[.*?\])-.*?(?:-(\d+))?\.mp4$', filename)
    if not series_match:
        return None, None
        
    series_id = series_match.group(1)
    sequence_num = int(series_match.group(2)) if series_match.group(2) else 1
    
    return series_id, sequence_num