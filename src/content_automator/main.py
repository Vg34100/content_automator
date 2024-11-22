"""Main module for {{project_name}}."""

# main.py

import json
import os
from datetime import datetime, timedelta
import time
from typing import Dict, List
from pathlib import Path
import re
from logging import getLogger, FileHandler, Formatter

from core.upload import get_authenticated_service, upload_video_with_retries
from core.transcribe import transcribe_video

from core.processor import VideoProcessor, ProcessingStatus

import core.metadata as generate_metadata

from models.processing import VideoProcessingInfo

from utils.helpers import log_info, log_warning, log_error

class VideoUploadManager:
    def __init__(self, base_path: str):
        """Initialize the VideoUploadManager with proper logging and directory setup."""
        self.base_path = Path(base_path)
        self.setup_logging()
        
        log_info("Initializing VideoUploadManager")
        
        # Initialize paths
        self.output_json_path = os.getenv("INPUT_PATH")
        # self.channel_codes = ['VGO', 'VGL', 'BBG', 'BBP']
        self.channel_codes = os.getenv("CHANNEL_CODES")
        
        # Initialize video processor
        self.processor = VideoProcessor(base_path)
        
        log_info(f"Initialized with base path: {base_path}")
    
    def load_saved_state(self):
        """Load existing transcripts and metadata from saved state."""
        for video_path, info in self.processor.processing_status.items():
            if info.transcript:
                transcript_file = self.processor.transcripts_path / f"{Path(video_path).stem}.txt"
                if transcript_file.exists():
                    with open(transcript_file, 'r', encoding='utf-8') as f:
                        info.transcript = f.read()
                        
            if info.metadata:
                metadata_file = self.processor.metadata_path / f"{Path(video_path).stem}.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        info.metadata = json.load(f)
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_dir = self.base_path / "data/logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"video_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        file_handler = FileHandler(log_file)
        file_handler.setFormatter(Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        logger = getLogger()
        logger.addHandler(file_handler)
        
    def parse_video_sequence(self, video_path: str) -> tuple:
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
        
    def sort_videos_by_sequence(self, videos: List[str]) -> List[str]:
        """Sort videos by their series and sequence number."""
        def get_sort_key(video_path):
            series_id, sequence_num = self.parse_video_sequence(video_path)
            return (series_id or "", sequence_num or float('inf'))
            
        return sorted(videos, key=get_sort_key)
        
    def calculate_publish_date(self, video_path: str, base_date: datetime) -> datetime:
        """Calculate publish date based on video sequence."""
        series_id, sequence_num = self.parse_video_sequence(video_path)
        if series_id is None:
            log_warning(f"Could not parse sequence info for {video_path}")
            return base_date
            
        # Adjust date based on sequence number (subtract 1 since sequence starts at 1)
        return base_date + timedelta(days=(sequence_num - 1))

    def load_video_list(self) -> Dict[str, List[str]]:
        """Load and categorize videos from the JSON file."""
        log_info("Loading video list")
        
        if not self.output_json_path.exists():
            log_error(f"Video list not found: {self.output_json_path}")
            raise FileNotFoundError(f"Video list not found: {self.output_json_path}")
            
        with open(self.output_json_path, 'r') as f:
            video_list = json.load(f)
            
        categorized_videos = {code: [] for code in self.channel_codes}
        
        for video in video_list:
            video_path = self.base_path / video
            if not video_path.exists():
                log_warning(f"Video file not found: {video_path}")
                continue
                
            for code in self.channel_codes:
                if f'[{code}]' in video_path.name:
                    categorized_videos[code].append(video_path)
                    break
                    
        log_info(f"Found {sum(len(v) for v in categorized_videos.values())} videos across {len(self.channel_codes)} channels")
        return categorized_videos
        
    def process_videos(self):
        """Main function to process all videos."""
        log_info("Starting video processing")
        
        # Load and categorize videos
        videos_by_channel = self.load_video_list()
        print(videos_by_channel)
        input("OK?")
        
        series_code = input("Input series code: ")
        
        # Set up models only if needed for transcription
        whisper_model = None
        
        # First pass: Process all videos
        for channel_code, videos in videos_by_channel.items():
            log_info(f"Processing channel: {channel_code}")
            
            # Sort videos by sequence
            sorted_videos = self.sort_videos_by_sequence(videos)
            print(sorted_videos)
            
            for video_path in sorted_videos:
                video_path_str = str(video_path)
                
                # Get current status from saved state
                if video_path_str in self.processor.processing_status:
                    current_status = self.processor.processing_status[video_path_str].status
                    print(f"found status as {current_status}")
                else:
                    # Initialize with PENDING instead of NEW
                    self.processor.processing_status[video_path_str] = VideoProcessingInfo(
                        video_path=video_path_str,
                        channel_code=channel_code,
                        status=ProcessingStatus.PENDING
                    )
                    current_status = ProcessingStatus.PENDING
                
                if current_status == ProcessingStatus.READY_TO_UPLOAD:
                    log_info(f"Video already processed: {video_path}")
                    continue
                
                try:
                    # Initialize Whisper model only when needed
                    if current_status == ProcessingStatus.PENDING and not whisper_model:
                        log_info("Setting up Whisper model")
                        whisper_model = transcribe_video.setup_whisper_model()
                    
                    # 1. Transcribe video if needed
                    if current_status == ProcessingStatus.PENDING:
                        log_info(f"Transcribing video: {video_path}")
                        transcript_result = transcribe_video.transcribe_video(
                            video_path_str,
                            whisper_model
                        )
                        self.processor.save_transcript(
                            video_path_str,
                            transcript_result['text']
                        )
                        self.processor.update_video_status(
                            video_path_str,
                            ProcessingStatus.TRANSCRIBED,
                            channel_code=channel_code,
                            transcript=transcript_result['text']
                        )
                        current_status = ProcessingStatus.TRANSCRIBED
                    
                    # 2. Generate metadata if needed
                    if current_status == ProcessingStatus.TRANSCRIBED:
                        log_info(f"Generating metadata for: {video_path}")
                        metadata = generate_metadata.generate_metadata(
                            self.processor.processing_status[video_path_str].transcript,
                            channel_code,
                            series_code
                        )
                        self.processor.save_metadata(video_path_str, metadata)
                        self.processor.update_video_status(
                            video_path_str,
                            ProcessingStatus.READY_TO_UPLOAD,
                            metadata=metadata
                        )
                
                except Exception as e:
                    self.processor.update_video_status(
                        video_path_str,
                        ProcessingStatus.FAILED,
                        error=str(e)
                    )
                    log_error(f"Error processing video {video_path}: {str(e)}")
                    continue
        
        # Second pass: Upload videos in sequence
        self.upload_processed_videos()
        
    def upload_processed_videos(self):
        """Upload all videos that are ready for upload."""
        log_info("Starting video uploads")
        youtube_services = {}
        
        # Group videos by channel and sort by sequence
        videos_by_channel = {}
        for video_path, info in self.processor.processing_status.items():
            # Fix the status comparison
            if str(info.status) != str(ProcessingStatus.READY_TO_UPLOAD):
                continue
                
            if info.channel_code not in videos_by_channel:
                videos_by_channel[info.channel_code] = []
            videos_by_channel[info.channel_code].append(video_path)
        
        if not videos_by_channel:
            log_warning("No videos ready for upload found")
            return
            
        log_info(f"Found videos ready for upload in channels: {list(videos_by_channel.keys())}")
        
        # Process each channel's videos in sequence
        for channel_code, videos in videos_by_channel.items():
            log_info(f"Uploading videos for channel: {channel_code}")
            sorted_videos = self.sort_videos_by_sequence(videos)
            base_publish_date = datetime.now() + timedelta(days=365)
            
            try:
                if channel_code not in youtube_services:
                    log_info(f"Authenticating with YouTube for channel: {channel_code}")
                    youtube_services[channel_code] = get_authenticated_service(
                        channel_code
                    )[0]
                    
                for video_path in sorted_videos:
                    info = self.processor.processing_status[video_path]
                    publish_date = self.calculate_publish_date(
                        video_path,
                        base_publish_date
                    )
                    
                    log_info(f"Uploading video {video_path} scheduled for {publish_date}")
                    
                    while True:
                        try:
                            video_id = upload_video_with_retries(
                                youtube_services[channel_code],
                                video_path,
                                info.metadata,
                                "private",
                                publish_date
                            )
                            
                            if video_id:
                                self.processor.update_video_status(
                                    video_path,
                                    ProcessingStatus.UPLOADED,
                                    video_id=video_id,
                                    upload_date=publish_date
                                )
                                log_info(f"Successfully uploaded video: {info.metadata['title']}")
                                break
                                
                        except Exception as e:
                            if 'quotaExceeded' in str(e):
                                log_warning("Quota exceeded, waiting 24 hours...")
                                time.sleep(24 * 60 * 60)
                            else:
                                log_error(f"Error during upload: {str(e)}")
                                raise
                                
            except Exception as e:
                log_error(f"Error uploading channel {channel_code} videos: {str(e)}")

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    base_path = os.getenv("BASE_PATH")
    manager = VideoUploadManager(base_path)
    manager.process_videos()