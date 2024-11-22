# src/content_automator/config/settings.py
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # Base paths
    VIDEO_CENTER_PATH = Path(os.getenv('VIDEO_CENTER_PATH'))
    AUTH_DIRECTORY = Path(os.getenv('AUTH_DIRECTORY'))
    
    # Project paths
    BASE_DIR = Path(__file__).parent.parent.parent.parent
    OUTPUT_DIR = BASE_DIR / 'data' / 'outputs'
    LOGS_DIR = BASE_DIR / 'data' / 'logs'
    
    # Create directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)