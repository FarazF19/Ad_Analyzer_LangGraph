import os
import requests
import uuid
from pathlib import Path
from typing import List, Dict

# Create a temp directory for storing videos
TMP_DIR = Path("tmp_videos")
TMP_DIR.mkdir(exist_ok=True)


def download_videos(video_list: List[Dict[str, str]]) -> List[str]:
    """
    Downloads videos from a list of Facebook video metadata.
    
    Args:
        video_list (List[Dict]): Each dict should have 'video_id' and 'source' (download URL).
    
    Returns:
        List[str]: Paths to the saved video files.
    """
    saved_paths = []

    for video in video_list:
        video_id = video.get("video_id")
        source_url = video.get("source")

        if not source_url:
            print(f"[WARNING] Skipping video_id={video_id} - No source URL provided.")
            continue

        try:
            # Send GET request to the video source URL with streaming enabled
            response = requests.get(source_url, stream=True, timeout=15)
            response.raise_for_status()  # Raise error for bad HTTP responses

            # Create a unique filename using video_id and a short UUID
            filename = TMP_DIR / f"video_{video_id}_{uuid.uuid4().hex[:6]}.mp4"

            # Open file in binary write mode and save the video in chunks
            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"[INFO] Successfully downloaded: {filename}")
            saved_paths.append(str(filename))

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to download video_id={video_id}: {e}")

    return saved_paths
