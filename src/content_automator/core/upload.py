# upload_to_youtube.py

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timedelta
import os
from typing import Dict, Optional
import time
import socket
import ssl
from requests.exceptions import RequestException

def get_authenticated_service(channel_code: str) -> tuple:
    """
    Authenticate with YouTube API for a specific channel.
    
    Args:
        channel_code: Channel code (VGO, VGL, BBG, or BBP)
    
    Returns:
        Tuple of (youtube service object, channel_id)
    """
    auth_dir = os.getenv("AUTH_DIRECTORY", "")
    client_secrets_file = f"{auth_dir}/{channel_code}-client_secrets.json"
    
    if not os.path.exists(client_secrets_file):
        raise FileNotFoundError(f"Client secrets file not found: {client_secrets_file}")
    
    credentials = Credentials.from_authorized_user_file(client_secrets_file)
    youtube = build('youtube', 'v3', credentials=credentials)
    
    # Get channel ID
    response = youtube.channels().list(
        part='id',
        mine=True
    ).execute()
    
    channel_id = response['items'][0]['id']
    return youtube, channel_id

def upload_video(
    youtube,
    video_path: str,
    metadata: Dict[str, str],
    privacy_status: str = "private",
    publish_date: Optional[datetime] = None
) -> str:
    """
    Upload a video to YouTube with specified metadata.
    
    Args:
        youtube: Authenticated YouTube service object
        video_path: Path to video file
        metadata: Dictionary containing title, description, and tags
        privacy_status: Video privacy setting
        publish_date: Optional scheduled publish date
    
    Returns:
        Video ID of the uploaded video
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    body = {
        'snippet': {
            'title': metadata['title'],
            'description': metadata['description'],
            'tags': metadata['tags'],
            'categoryId': '20'  # Gaming category
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    # Add publish date if provided
    if publish_date:
        body['status']['publishAt'] = publish_date.isoformat() + 'Z'
    
    # Upload the video
    insert_request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(video_path, chunksize=-1, resumable=True)
    )
    
    response = None
    while response is None:
        try:
            _, response = insert_request.next_chunk()
            if response:
                print(f"Upload Complete! Video ID: {response['id']}")
                return response['id']
        except Exception as e:
            print(f"An error occurred: {e}")
            raise  # Re-raise the exception instead of break

    return None
    

def upload_video_with_retries(
    youtube,
    video_path: str,
    metadata: Dict[str, str],
    privacy_status: str = "private",
    publish_date: Optional[datetime] = None,
    max_retries: int = 3,
    chunk_size: int = 1024 * 1024  # 1MB chunks
) -> str:
    """
    Upload a video to YouTube with retry logic and better error handling.
    
    Args:
        youtube: Authenticated YouTube service object
        video_path: Path to video file
        metadata: Dictionary containing title, description, and tags
        privacy_status: Video privacy setting
        publish_date: Optional scheduled publish date
        max_retries: Maximum number of retry attempts
        chunk_size: Size of upload chunks in bytes
    
    Returns:
        Video ID of the uploaded video
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    body = {
        'snippet': {
            'title': metadata['title'],
            'description': metadata['description'],
            'tags': metadata['tags'],
            'categoryId': '20'  # Gaming category
        },
        'status': {
            'privacyStatus': privacy_status,
            'selfDeclaredMadeForKids': False
        }
    }
    
    if publish_date:
        body['status']['publishAt'] = publish_date.isoformat() + 'Z'

    retry_count = 0
    last_exception = None
    
    while retry_count < max_retries:
        try:
            # Create a new insert request for each attempt
            insert_request = youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=MediaFileUpload(
                    video_path,
                    chunksize=chunk_size,
                    resumable=True
                )
            )
            
            response = None
            last_progress = 0
            
            while response is None:
                try:
                    status, response = insert_request.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        if progress != last_progress:
                            print(f"Upload progress: {progress}%")
                            last_progress = progress
                            
                except (socket.error, ssl.SSLError, RequestException) as e:
                    print(f"Network error during chunk upload: {e}")
                    # Wait before retrying the chunk
                    time.sleep(min(2 ** retry_count, 60))
                    continue
                    
            if response:
                print(f"Upload Complete! Video ID: {response['id']}")
                return response['id']
                
        except Exception as e:
            last_exception = e
            retry_count += 1
            
            if retry_count < max_retries:
                wait_time = min(2 ** retry_count, 60)
                print(f"Attempt {retry_count} failed: {e}")
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print(f"Maximum retries ({max_retries}) reached.")
                raise Exception(f"Failed to upload video after {max_retries} attempts. Last error: {last_exception}")

    return None

if __name__ == "__main__":
    # Example usage
    channel_code = "VGL"
    video_path = "path/to/video.mp4"
    metadata = {
        "title": "Example Title",
        "description": "Example Description",
        "tags": ["tag1", "tag2"]
    }
    
    try:
        youtube, channel_id = get_authenticated_service(channel_code)
        publish_date = datetime.now() + timedelta(days=365)  # Schedule for 1 year from now
        video_id = upload_video(youtube, video_path, metadata, "private", publish_date)
        print(f"Successfully scheduled video {video_id} for {publish_date}")
    except Exception as e:
        print(f"Failed to upload video: {e}")