import cv2
import base64
from pathlib import Path

# Define paths
ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR = ROOT_DIR / "tmp_videos"
FRAMES_DIR = ROOT_DIR / "extracted_frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)

def convert_frame_to_base64(frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None
    return base64.b64encode(buffer).decode('utf-8')

def extract_evenly_distributed_frames_from_video(video_path: Path, max_frames: int = 5) -> list[str]:
    """
    Extracts up to `max_frames` evenly distributed frames from a video.
    Returns a list of Base64-encoded JPEG images.

    Args:
        video_path (Path): Path to the video file.
        max_frames (int): Max number of frames to extract.

    Returns:
        list[str]: Base64-encoded frames.
    """
    capture = cv2.VideoCapture(str(video_path))
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames == 0:
        print(f"[⚠️] No frames in video: {video_path.name}")
        return []

    step = max(1, total_frames // max_frames)
    base64_frames = []

    # Create a unique output folder for this video
    output_dir = FRAMES_DIR / video_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    for i in range(0, total_frames, step):
        capture.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = capture.read()

        if ret:
            # Save the frame as an image file (optional)
            frame_path = output_dir / f"frame_{len(base64_frames) + 1}.jpg"
            cv2.imwrite(str(frame_path), frame)

            # Convert to base64
            frame_b64 = convert_frame_to_base64(frame)
            base64_frames.append(frame_b64)

        if len(base64_frames) >= max_frames:
            break

    capture.release()
    return base64_frames


def extract_all_videos_as_base64_frames():
    """
    Process all videos in tmp_videos and return base64 frames for each.

    Returns:
        list[dict]: [{"video": ..., "frames": [...]}, ...]
    """
    results = []

    for video_file in VIDEO_DIR.glob("*.mp4"):
        print(f"[📽️] Extracting frames from {video_file.name}")
        frames_b64 = extract_evenly_distributed_frames_from_video(video_file)

        if frames_b64:
            results.append({
                "video": video_file.name,
                "frames": frames_b64
            })

    return results


if __name__ == "__main__":
    output = extract_all_videos_as_base64_frames()

    if output:
        print("\n🧪 Sample Output (Base64 Frame Preview):")
        print(f"Video: {output[0]['video']}")
        print(f"Frame 1 (base64): {output[0]['frames'][0][:100]}...")
    else:
        print("[ℹ️] No frames extracted.")
