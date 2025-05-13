import cv2
import base64
from pathlib import Path
from typing import Dict, Any

# Define paths
ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR = ROOT_DIR / "tmp_videos"
FRAMES_DIR = ROOT_DIR / "extracted_frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

def convert_frame_to_base64(frame):
    """Converts an OpenCV frame to Base64-encoded string."""
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    return base64.b64encode(buffer).decode('utf-8')

def extract_evenly_distributed_frames_from_video(video_path: Path, max_frames: int = 5) -> list[str]:
    """
    Extracts up to `max_frames` evenly distributed frames from a video.
    Returns a list of Base64-encoded JPEG images.
    """
    capture = cv2.VideoCapture(str(video_path))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        print(f"[⚠️] No frames in video: {video_path.name}")
        return []

    step = max(1, total_frames // max_frames)
    base64_frames = []

    output_dir = FRAMES_DIR / video_path.stem

    if output_dir.exists() and any(output_dir.glob("*.jpg")):
        print(f"[✔️] Frames already extracted for {video_path.name}, skipping.")
        return []

    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, total_frames, step):
        capture.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = capture.read()

        if ret:
            frame_path = output_dir / f"frame_{len(base64_frames) + 1}.jpg"
            cv2.imwrite(str(frame_path), frame)

            frame_b64 = convert_frame_to_base64(frame)
            base64_frames.append(frame_b64)

        if len(base64_frames) >= max_frames:
            break

    capture.release()
    return base64_frames

def extract_all_videos_as_base64_frames(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph-compatible node to extract frames from all videos in tmp_videos directory
    and return the frames as Base64-encoded strings.
    """
    results = []
    video_paths = state.get("downloaded_videos", [])

    if not video_paths:
        print("[⚠️] No video paths found in state. Skipping frame extraction.")
        state["extracted_frames"] = []
        return state

    for video_file in video_paths:
        video_file = Path(video_file)

        print(f"[📽️] Extracting frames from {video_file.name}")
        frames_b64 = extract_evenly_distributed_frames_from_video(video_file)

        if frames_b64:
            results.append({
                "video": video_file.name,
                "frames": frames_b64
            })

    state["extracted_frames"] = results
    return state
