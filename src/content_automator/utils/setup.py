import os
from datetime import datetime
from logging import FileHandler, Formatter, getLogger

def setup_logging(base_path: str):
    """Set up logging configuration."""
    log_dir = os.path.join(base_path, "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir,
        f"video_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    file_handler = FileHandler(log_file)
    file_handler.setFormatter(Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    
    logger = getLogger()
    logger.addHandler(file_handler)
    
    return logger