from openai import OpenAI
from pathlib import Path
import base64
import json
import os
from dotenv import load_dotenv

# Load API key
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
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_frame(image_path: Path) -> str:
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

def analyze_all_frames():
    """
    Analyzes all frame images in subfolders of extracted_frames/
    and saves a JSON file per video in frame_analysis/.
    """
    if not FRAMES_DIR.exists():
        print("[⚠️] extracted_frames directory does not exist.")
        return

    for video_folder in FRAMES_DIR.iterdir():
        if not video_folder.is_dir():
            continue  # Skip anything that's not a subfolder

        video_id = video_folder.name
        print(f"[🎞️] Analyzing frames for: {video_id}")

        analysis = {}
        for frame_path in sorted(video_folder.glob("*.jpg")):
            print(f"[🧠] Analyzing: {frame_path.name}")
            result = analyze_frame(frame_path)
            analysis[frame_path.name] = result

        # Save analysis for this video
        output_path = ANALYSIS_DIR / f"{video_id}_analysis.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"[✅] Saved: {output_path}")

