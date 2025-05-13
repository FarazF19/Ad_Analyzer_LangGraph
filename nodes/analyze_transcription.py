from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import os
from typing import Dict, Any

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Resolve project directories
ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPT_DIR = ROOT_DIR / "transcriptions"
ANALYSIS_DIR = ROOT_DIR / "transcription_analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_transcript_text(text: str) -> str:
    """
    Sends transcription text to GPT for structured analysis (e.g. tone, hook, CTA).
    Returns a clean bullet list string.
    """
    prompt = f"""
Aap aik marketing strategist hain jo aik ad ki Urdu transcript ka jaiza le rahe hain. Aapko yeh batana hai ke is ad mein kon kon se selling techniques use hui hain. Jaise ke:

- Emotional kahani sunana
- Social proof (reviews ya testimonials ka zikr)
- Urgency (limited time ya "abhi khareedain" ka lafz)
- Risk reversal (e.g. "agar pasand na aaye to paisay wapas")
- Viewer se direct connection ("aap ke liye", "aap jaise log")
- Mukabla ya farq dikhana (e.g. "doosri brands se behtar")

Bullets mein jawaab dein — sirf unhi cheezon ka zikr karein jo is transcript mein hain.

Transcript:
{text}
"""

    system_prompt = "You are a helpful assistant that gives only keywords as a return, in English, with one point per line using dashes. Do not include markdown or JSON."

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Error analyzing transcription: {e}")
        return None

def analyze_all_transcriptions(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph-compatible node that analyzes each transcription in state["transcriptions"]
    and saves analysis as plain .txt file (one per transcription).
    """
    results = []
    transcriptions = state.get("transcriptions", [])

    if not transcriptions:
        print("[⚠️] No transcriptions found in state. Skipping analysis.")
        state["transcription_analysis"] = []
        return state

    for item in transcriptions:
        filename = item.get("file")
        text = item.get("text")

        if not filename or not text:
            print(f"[⚠️] Missing data in item: {item}")
            continue

        analysis_path = ANALYSIS_DIR / f"{Path(filename).stem}_analysis.txt"
        if analysis_path.exists():
            print(f"[⏩] Skipping {filename} (already analyzed)")
            with open(analysis_path, "r", encoding="utf-8") as f:
                analysis = f.read()
            results.append({
                "file": filename,
                "analysis": analysis
            })
            continue

        print(f"[🧠] Analyzing transcription: {filename}")
        analysis_text = analyze_transcript_text(text)

        if analysis_text:
            with open(analysis_path, "w", encoding="utf-8") as f:
                f.write(analysis_text)
            print(f"[✅] Saved analysis: {analysis_path}")
            results.append({
                "file": filename,
                "analysis": analysis_text
            })

    state["transcription_analysis"] = results
    return state
