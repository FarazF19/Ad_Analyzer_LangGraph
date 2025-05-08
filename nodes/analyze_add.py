def analyze_ad(data: dict) -> dict:
    print("Node: Analyze Ad (Final)")
    return {
        "final_output": {
            "transcription": data.get("transcription_insights"),
            "visuals": data.get("visual_insights")
        }
    }
