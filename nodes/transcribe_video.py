from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import os

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Resolve the root directory (project root where .env is)
ROOT_DIR = Path(__file__).resolve().parent.parent  # move up from nodes/
VIDEO_DIR = ROOT_DIR / "tmp_videos"
TRANSCRIPT_DIR = ROOT_DIR / "transcriptions"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

def transcribe_video(video_path: Path) -> str:
    """
    Transcribes an Urdu video using Whisper and returns the transcription text.

    Args:
        video_path (Path): Path to the video file

    Returns:
        str: Transcribed Urdu text
    """
    try:
        with open(video_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ur",
                prompt="This is a Pakistani Urdu advertisement.You may find words like Oud-al-abraj,outlet,purchase,online etc. Transcribe the spoken content in Urdu script."
            )
        return response.text.strip()

    except Exception as e:
        print(f"Failed to transcribe {video_path.name}: {e}")
        return None

def transcribe_all_videos():
    """
    Transcribes all videos in tmp_videos/ if not already transcribed.
    Saves each result in transcriptions/ and returns all results as a list.

    Returns:
        list[dict]: [{"file": ..., "text": ...}, ...]
    """
    results = []

    for video_file in VIDEO_DIR.glob("*.mp4"):
        transcript_path = TRANSCRIPT_DIR / f"{video_file.stem}.txt"

        if transcript_path.exists():
            print(f"[⏩] Skipping {video_file.name} (already transcribed)")
            continue

        print(f"[🎙️] Transcribing: {video_file.name}")
        text = transcribe_video(video_file)

        if text:
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[✅] Saved: {transcript_path}")

            results.append({"file": video_file.name, "text": text})

    return results

