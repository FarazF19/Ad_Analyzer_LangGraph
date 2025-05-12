from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import os

# Load API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Directories
ROOT_DIR = Path(__file__).resolve().parent.parent
TRANSCRIPT_DIR = ROOT_DIR / "transcriptions"
ANALYSIS_DIR = ROOT_DIR / "transcription_analysis"
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

def analyze_transcription(transcript_text: str, filename: str) -> str:
    """
    Uses GPT-4o to analyze a transcription based on Urdu marketing strategy prompt.

    Returns:
        str: Analysis result
    """
    try:
        user_prompt = f"""
Aap aik marketing strategist hain jo aik ad ki Urdu transcript ka jaiza le rahe hain. Aapko yeh batana hai ke is ad mein kon kon se selling techniques use hui hain. Jaise ke:

- Emotional kahani sunana
- Social proof (reviews ya testimonials ka zikr)
- Urgency (limited time ya "abhi khareedain" ka lafz)
- Risk reversal (e.g. "agar pasand na aaye to paisay wapas")
- Viewer se direct connection ("aap ke liye", "aap jaise log")
- Mukabla ya farq dikhana (e.g. "doosri brands se behtar")

Bullets mein jawaab dein — sirf unhi cheezon ka zikr karein jo is transcript mein hain.

Transcript:
{transcript_text}
"""

        system_prompt = "You are a helpful assistant that gives only keywords as a return without markdown, in English. Be straight to the point."

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[❌] Failed to analyze {filename}: {e}")
        return None

def analyze_all_transcriptions():
    """
    Analyzes all `.txt` files in the transcriptions/ folder and saves results in analysis/ folder.
    """
    for file in TRANSCRIPT_DIR.glob("*.txt"):
        analysis_path = ANALYSIS_DIR / f"{file.stem}_analysis.txt"

        if analysis_path.exists():
            print(f"[⏩] Skipping analysis (already exists): {analysis_path.name}")
            continue

        try:
            with open(file, "r", encoding="utf-8") as f:
                transcript_text = f.read()

            print(f"[🔍] Analyzing: {file.name}")
            analysis = analyze_transcription(transcript_text, file.name)

            if analysis:
                with open(analysis_path, "w", encoding="utf-8") as out_file:
                    out_file.write(analysis)
                print(f"[✅] Saved: {analysis_path.name}")
        except Exception as e:
            print(f"[❌] Error with file {file.name}: {e}")


