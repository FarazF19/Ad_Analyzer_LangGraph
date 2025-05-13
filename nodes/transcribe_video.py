from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import os
from typing import Dict, Any

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Resolve the root directory (project root where .env is)
ROOT_DIR = Path(__file__).resolve().parent.parent
VIDEO_DIR = ROOT_DIR / "tmp_videos"
TRANSCRIPT_DIR = ROOT_DIR / "transcriptions"
TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)

def transcribe_video(video_path: Path) -> str:
    """
    Transcribes an Urdu video using Whisper and returns the transcription text.
    """
    try:
        with open(video_path, "rb") as f:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ur",
                prompt="This is a Pakistani Urdu advertisement. You may find words like Oud-al-abraj, outlet, purchase, online etc. Transcribe the spoken content in Urdu script."
            )
        return response.text.strip()
    except Exception as e:
        print(f"❌ Failed to transcribe {video_path.name}: {e}")
        return None

def transcribe_all_videos(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph-compatible node to transcribe all videos and update the state with results.
    """
    results = []
    video_paths = state.get("downloaded_videos", [])

    if not video_paths:
        print("[⚠️] No video paths found in state. Skipping transcription.")
        state["transcriptions"] = []
        return state

    for video_file in video_paths:
        video_file = Path(video_file)
        transcript_path = TRANSCRIPT_DIR / f"{video_file.stem}.txt"

        if transcript_path.exists():
            print(f"[⏩] Skipping {video_file.name} (already transcribed)")
            with open(transcript_path, "r", encoding="utf-8") as f:
                results.append({
                    "file": video_file.name,
                    "text": f.read().strip()
                })
            continue

        print(f"[🎙️] Transcribing: {video_file.name}")
        text = transcribe_video(video_file)

        if text:
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[✅] Saved: {transcript_path}")
            results.append({"file": video_file.name, "text": text})

    state["transcriptions"] = results
    return state
