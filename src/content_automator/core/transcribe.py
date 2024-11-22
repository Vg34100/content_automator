# transcribe_video.py

from datetime import datetime
import torch
import whisper
import os
from typing import Optional
from utils.helpers import log_info, log_error

def setup_whisper_model(
    model_name: str = "medium.en",
    device: Optional[str] = None
) -> whisper.Whisper:
    """
    Initialize and load the Whisper model with device optimization.
    
    Args:
        model_name: Name of the Whisper model to use
        device: Optional device specification ('cuda', 'cpu', or None for auto)
    """
    try:
        # Determine best device if none specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        log_info(f"Loading Whisper model '{model_name}' on {device}")
        
        # Load model on specified device
        model = whisper.load_model(model_name).to(device)
        
        if device == "cuda":
            # Optional: Enable TensorFloat-32 for faster processing on Ampere GPUs
            if torch.cuda.get_device_capability()[0] >= 8:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
        
        log_info(f"Successfully loaded model: {model_name}")
        return model
        
    except Exception as e:
        log_error(f"Error loading Whisper model: {e}")
        raise

def transcribe_video(
    video_path: str, 
    model: Optional[whisper.Whisper] = None,
    verbose: bool = False,
    ) -> dict:
    """
    Transcribe a video file using Whisper.
    
    Args:
        video_path: Path to the video file
        model: Optional pre-loaded Whisper model
    
    Returns:
        Dictionary containing the transcription result
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if model is None:
        model = setup_whisper_model()
    
    try:
        start_time = datetime.now()
        log_info(f"Starting transcription for: {video_path}")
        result = model.transcribe(
            video_path,
            verbose=verbose,
            language='en',
            task="transcribe"
        )
        log_info("Transcription completed successfully")
        transcription_time = datetime.now() - start_time
        # Log results
        log_info(f"Transcription completed in {transcription_time.total_seconds():.2f} seconds")
        log_info(f"Transcript length: {len(result['text'])} characters")
        log_info("First 500 characters of transcript:")
        log_info(result['text'][:500])
        return result
    except Exception as e:
        print(f"Error transcribing video: {e}")
        raise

if __name__ == "__main__":
    # Example usage
    video_path = "path/to/your/video.mp4"
    try:
        model = setup_whisper_model()
        result = transcribe_video(video_path, model)
        print("Transcription completed successfully")
        print(f"Full text: {result['text'][:500]}...")  # Print first 500 chars
    except Exception as e:
        print(f"Failed to transcribe video: {e}")