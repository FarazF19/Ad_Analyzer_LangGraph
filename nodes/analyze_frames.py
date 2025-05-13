from openai import OpenAI
from pathlib import Path
import base64
import json
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define directories
ROOT_DIR = Path(__file__).resolve().parent.parent
FRAMES_DIR = ROOT_DIR / "extracted_frames"
ANALYSIS_DIR = ROOT_DIR / "frame_analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Prompt
ANALYSIS_PROMPT = (
    "I want you to give me a single word that represents a characteristic of this advertising image to characterize it. "
    "Give me only the position of the person, and necessarily what they are doing (example: sitting with the object in their hands, "
    "standing explaining, crouching looking at the object) or a characteristic of the background (example: outside, package in the background, red background)."
)

def encode_image_to_base64(image_path: Path) -> str:
    """
    Converts an image to a base64 encoded string.

    Args:
        image_path (Path): Path to the image file.

    Returns:
        str: Base64 encoded string of the image.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_frame(image_path: Path) -> str:
    """
    Analyzes a single frame using GPT-4o and returns the analysis result.

    Args:
        image_path (Path): Path to the image file to analyze.

    Returns:
        str: Analysis result for the image.
    """
    image_b64 = encode_image_to_base64(image_path)
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": ANALYSIS_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
                    ]
                }
            ],
            max_tokens=50
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[❌] Error analyzing {image_path.name}: {e}")
        return "Error"

def analyze_all_frames(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph-compatible node to analyze all frames in extracted_frames/
    and skip videos that already have frame analysis.
    """
    frame_analysis_results = []

    downloaded_videos = state.get("downloaded_videos", [])
    if not downloaded_videos:
        print("[⚠️] No video files found in state. Skipping frame analysis.")
        state["frame_analysis"] = []
        return state

    video_folders = [Path(v).stem for v in downloaded_videos]

    for folder_name in video_folders:
        video_folder_path = FRAMES_DIR / folder_name
        output_path = ANALYSIS_DIR / f"{folder_name}_analysis.json"

        # ✅ Skip if analysis file already exists
        if output_path.exists():
            print(f"[⏩] Skipping {folder_name} — already analyzed.")
            with open(output_path, "r", encoding="utf-8") as f:
                existing_analysis = json.load(f)
            frame_analysis_results.append({
                "video": folder_name,
                "analysis": existing_analysis
            })
            continue

        if not video_folder_path.exists():
            print(f"[⚠️] Folder not found for {folder_name}: {video_folder_path}")
            continue

        print(f"[🎞️] Analyzing frames for: {folder_name}")
        analysis = {}

        for frame_path in sorted(video_folder_path.glob("*.jpg")):
            print(f"[🧠] Analyzing: {frame_path.name}")
            result = analyze_frame(frame_path)
            analysis[frame_path.name] = result

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)

        print(f"[✅] Saved: {output_path.name}")
        frame_analysis_results.append({
            "video": folder_name,
            "analysis": analysis
        })

    state["frame_analysis"] = frame_analysis_results
    return state



