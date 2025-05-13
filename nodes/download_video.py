import os
import requests
from pathlib import Path
from typing import Dict, Any

# Temp directory to store downloaded videos
TMP_DIR = Path("tmp_videos")
TMP_DIR.mkdir(exist_ok=True)

def is_valid_mp4(file_path: Path) -> bool:
    """Check if the file exists and is a non-zero MP4 file."""
    return file_path.exists() and file_path.stat().st_size > 0 and file_path.suffix == ".mp4"

def download_videos(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Downloads Facebook ad videos only if not already cached.
    
    Args:
        state (dict): LangGraph state, must include 'video_urls'.

    Returns:
        dict: Updated state with 'video_paths'.
    """
    video_list = state.get("video_urls", [])
    saved_paths = []

    if not video_list:
        print("[⚠️] No video URLs in state. Skipping download.")
        state["video_paths"] = []
        return state

    for video in video_list:
        video_id = video.get("video_id")
        source_url = video.get("source")

        if not video_id or not source_url:
            print(f"[SKIP] Missing data: video_id={video_id}, source_url={source_url}")
            continue

        filename = TMP_DIR / f"video_{video_id}.mp4"

        # --- Skip if already downloaded ---
        if is_valid_mp4(filename):
            print(f"[✅] Cached: {filename}")
            saved_paths.append(str(filename))
            continue

        # --- Download if not cached ---
        try:
            response = requests.get(source_url, stream=True, timeout=20)
            response.raise_for_status()

            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f"[💾] Downloaded: {filename}")
            saved_paths.append(str(filename))

        except requests.exceptions.RequestException as e:
            print(f"[❌] Failed to download video_id={video_id}: {e}")

    state["downloaded_videos"] = saved_paths
    return state
