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

# Define directories
ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPTION_DIR = ROOT_DIR / "transcription_analysis"
FRAME_ANALYSIS_DIR = ROOT_DIR / "frame_analysis"
AD_ANALYSIS_DIR = ROOT_DIR / "ad_analysis"
AD_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

# Ad analysis prompt
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

def clean_response_to_json(text: str) -> str:
    """
    Cleans malformed OpenAI JSON by:
    - Removing line breaks inside strings
    - Stripping trailing commas
    - Closing any missing braces
    """
    # Remove leading/trailing whitespace and rogue newlines
    text = text.strip()

    # Remove newlines within quotes (causes JSONDecodeError)
    def fix_linebreaks_in_strings(text: str) -> str:
        fixed_lines = []
        in_string = False
        current_string = ""
        for line in text.splitlines():
            if '"' in line:
                quote_count = line.count('"')
                if quote_count % 2 != 0:
                    in_string = not in_string
                if in_string:
                    current_string += line.strip()
                else:
                    current_string += line.strip()
                    fixed_lines.append(current_string)
                    current_string = ""
            else:
                if in_string:
                    current_string += line.strip()
                else:
                    fixed_lines.append(line)
        return "\n".join(fixed_lines)

    text = fix_linebreaks_in_strings(text)
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)

    # Ensure braces are balanced
    open_braces = text.count("{")
    close_braces = text.count("}")
    if close_braces < open_braces:
        text += "}" * (open_braces - close_braces)

    return text


def analyze_combined_ad(transcription: str, visual_summary: str) -> Dict[str, str]:
    prompt = AD_ANALYSIS_PROMPT.format(
        transcription=transcription,
        visual_summary=visual_summary
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )
        text = response.choices[0].message.content

        if not text:
            raise ValueError("Empty response from OpenAI")

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            print("[⚠️] Raw OpenAI response was not valid JSON. Attempting cleanup...")
            cleaned = clean_response_to_json(text)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                print("[❌] Final fallback failed. Response could not be parsed.")
                print("⛔ RAW Response:\n", text)
                return {}

    except Exception as e:
        print(f"[❌] Error during final ad analysis: {e}")
        return {}

def final_ad_analysis(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph-compatible node that merges transcription and frame insights
    into a final ad report, handling AllowMultiple inputs.
    """
    transcription_results = state.get("transcription_analysis", [])
    frame_results = state.get("frame_analysis", [])

    if not transcription_results or not frame_results:
        print("[⚠️] Missing analysis input(s) — skipping final ad analysis.")
        return {"final_ad_analysis": []}

    combined_results = []

    for transcript in transcription_results:
        video_name = Path(transcript.get("file", "")).stem
        transcript_text = transcript.get("analysis", "")

        if not video_name or not transcript_text:
            print(f"[⚠️] Invalid transcription entry: {transcript}")
            continue

        # Match frame analysis by video name
        matching_frame = next(
            (item for item in frame_results if Path(item.get("video", "")).stem == video_name),
            None
        )

        if not matching_frame:
            print(f"[⚠️] No frame analysis found for {video_name}")
            continue

        visual_text = " | ".join(matching_frame.get("analysis", {}).values())

        print(f"[🧠] Running final analysis for: {video_name}")
        summary_json = analyze_combined_ad(transcript_text, visual_text)

        if summary_json:
            output_path = AD_ANALYSIS_DIR / f"{video_name}_final.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(summary_json, f, indent=2, ensure_ascii=False)
            print(f"[✅] Final summary saved: {output_path.name}")

            combined_results.append({
                "video": video_name,
                "final_analysis": summary_json
            })
        else:
            print(f"[❌] Could not produce summary for {video_name}")

    return {"final_ad_analysis": combined_results}
