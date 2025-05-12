from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os
import json
import re

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPTION_DIR = ROOT_DIR / "transcription_analysis"
FRAME_ANALYSIS_DIR = ROOT_DIR / "frame_analysis"
AD_ANALYSIS_DIR = ROOT_DIR / "ad_analysis"
AD_ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

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


def extract_json(content):
    """Cleans and extracts JSON from OpenAI response using regex."""
    try:
        # Remove surrounding code blocks
        content = re.sub(r"^```json|```$", "", content.strip(), flags=re.MULTILINE)

        # Collapse multi-line strings (e.g., line breaks inside values)
        content = re.sub(r"\n\s+", " ", content)

        # Remove trailing commas if any (often breaks strict JSON parsing)
        content = re.sub(r",\s*}", "}", content)
        content = re.sub(r",\s*]", "]", content)

        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"[⚠️] JSONDecodeError: {e}")
        return None

def analyze_ad(video_id, transcription, visual_summary):
    prompt = AD_ANALYSIS_PROMPT.format(
        transcription=transcription.strip(),
        visual_summary=visual_summary.strip()
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()

        if not content:
            raise ValueError("Empty response from OpenAI")

        result = extract_json(content)
        if result:
            return result
        else:
            print(f"[⚠️] Failed to extract JSON from response:\n{content}")
            return None

    except Exception as e:
        print(f"[❌] Error analyzing ad for {video_id}: {e}")
        return None

def process_all_ads():
    for txt_path in TRANSCRIPTION_DIR.glob("*.txt"):
        full_id = txt_path.stem  # e.g., video_906752448323827_f903ac_analysis
        print(f"[🎯] Processing final ad analysis for: {full_id}")

        # Get base video ID without "_analysis"
        video_id = full_id.replace("_analysis", "")

        json_path = FRAME_ANALYSIS_DIR / f"{video_id}_analysis.json"
        if not json_path.exists():
            print(f"[⚠️] Frame analysis not found for {video_id}")
            continue

        try:
            transcription = txt_path.read_text(encoding="utf-8")
            visual_data = json.loads(json_path.read_text(encoding="utf-8"))
            visual_summary = "\n".join(visual_data.values())

            result = analyze_ad(video_id, transcription, visual_summary)
            if result:
                output_path = AD_ANALYSIS_DIR / f"{video_id}_final.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"[✅] Saved final analysis for {video_id}")
            else:
                print(f"[❌] Skipping saving for {video_id}, result invalid.")
        except Exception as e:
            print(f"[❌] Unexpected error for {video_id}: {e}")


