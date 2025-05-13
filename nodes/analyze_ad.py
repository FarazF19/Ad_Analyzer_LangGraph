from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
import json
import re
from typing import Dict, Any

# Load API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Directories
ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPTION_DIR = ROOT_DIR / "transcription_analysis"
FRAME_ANALYSIS_DIR = ROOT_DIR / "frame_analysis"
AD_ANALYSIS_DIR = ROOT_DIR / "ad_analysis"
AD_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Prompt template
AD_ANALYSIS_PROMPT = (
    "STEP 1: Analyze the ad insights below.\n\n"
    "Ad Transcript Summary: {transcription}\n"
    "Visual Summary: {visual_summary}\n\n"
    "Now answer these clearly:\n"
    "1. What is the **main hook line or pattern** used in this ad? Why did it work?\n"
    "2. What is the **tone** of the ad (e.g., emotional, confident, hype)?\n"
    "3. What **power phrases or emotional angles** stood out?\n"
    "4. What **gestures, expressions, or camera angles or visual thing** were impactful?\n\n"
    "Important: If you include any Urdu phrases, always write them in **Roman Urdu** (Urdu written in English script like 'agar pasand na aaye to paise wapas') instead of using Urdu script. Do NOT use Urdu alphabet or Nastaliq script.\n\n"
    "Please reply in only the following JSON format:\n"
    '{{\n  "hook":"...",\n  "tone":"...",\n  "power_phrases":"...",\n  "visual":"..."\n}}'
)

def clean_json_string(text: str) -> str:
    # Remove leading/trailing whitespace and code block markers
    text = text.strip().removeprefix("```json").removesuffix("```").strip()

    # Remove line breaks in values (e.g., caused by word-wrap)
    text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)  # handle hyphenated breaks
    text = re.sub(r'\n+', ' ', text)             # replace remaining newlines with space

    # Strip trailing commas before closing braces
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    return text

def analyze_combined_ad(transcription: str, visual_summary: str) -> Dict[str, str]:
    prompt = AD_ANALYSIS_PROMPT.format(
        transcription=transcription,
        visual_summary=visual_summary
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        raw_text = response.choices[0].message.content or ""
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            print("[⚠️] Raw OpenAI response not valid JSON. Attempting cleanup...")
            cleaned = clean_json_string(raw_text)
            return json.loads(cleaned)
    except Exception as e:
        print(f"[❌] Final ad analysis error: {e}")
        return {}

def final_ad_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    transcription_results = state.get("transcription_analysis", [])
    frame_results = state.get("frame_analysis", [])
    if not transcription_results or not frame_results:
        print("[⚠️] Missing inputs — skipping ad analysis.")
        return {"final_ad_analysis": []}

    combined_results = []

    for transcript in transcription_results:
        video_name = Path(transcript.get("file", "")).stem
        transcript_text = transcript.get("analysis", "")
        if not video_name or not transcript_text:
            continue

        matching_frame = next(
            (item for item in frame_results if Path(item.get("video", "")).stem == video_name),
            None
        )
        if not matching_frame:
            continue

        visual_text = " | ".join(matching_frame.get("analysis", {}).values())
        print(f"[🧠] Running final analysis for: {video_name}")
        result = analyze_combined_ad(transcript_text, visual_text)

        if result:
            output_path = AD_ANALYSIS_DIR / f"{video_name}_final.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"[✅] Saved: {output_path.name}")
            combined_results.append({
                "video": video_name,
                "final_analysis": result
            })
        else:
            print(f"[❌] Could not generate summary for {video_name}")

    return {"final_ad_analysis": combined_results}
