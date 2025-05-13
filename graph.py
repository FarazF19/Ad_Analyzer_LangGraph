from langgraph.graph import StateGraph, END
from typing import Dict, Any, Annotated
from typing_extensions import TypedDict
import operator
from pathlib import Path
from rich import print
from rich.pretty import pprint

# Output directory
FINAL_OUTPUT_DIR = Path(__file__).resolve().parent / "ad_analysis"
FINAL_OUTPUT_DIR.mkdir(exist_ok=True)

# ---- Shared Graph State ----
class GraphState(TypedDict):
    ads: Annotated[list, operator.add]
    video_urls: Annotated[list, operator.add]
    downloaded_videos: Annotated[list, operator.add]
    extracted_frames: Annotated[list, operator.add]
    transcriptions: Annotated[list, operator.add]
    transcription_analysis: Annotated[list, operator.add]
    frame_analysis: Annotated[list, operator.add]
    final_ad_analysis: list

# ---- Import all nodes ----
from nodes.get_ads import get_facebook_ads
from nodes.get_video_urls import get_video_urls_from_ads
from nodes.download_video import download_videos
from nodes.transcribe_video import transcribe_all_videos
from nodes.extract_frames import extract_all_videos_as_base64_frames
from nodes.analyze_transcription import analyze_all_transcriptions
from nodes.analyze_frames import analyze_all_frames
from nodes.analyze_ad import final_ad_analysis

# ---- Build the Graph ----
def build_graph():
    builder = StateGraph(GraphState)

    builder.add_node("Get Facebook Ads", get_facebook_ads)
    builder.add_node("Get Video URLs", get_video_urls_from_ads)
    builder.add_node("Download Video", download_videos)
    builder.add_node("Transcribe Video", transcribe_all_videos)
    builder.add_node("Extract Frames", extract_all_videos_as_base64_frames)
    builder.add_node("Analyze Transcription", analyze_all_transcriptions)
    builder.add_node("Analyze Frames", analyze_all_frames)
    builder.add_node("Analyze Ad", final_ad_analysis)

    builder.set_entry_point("Get Facebook Ads")

    builder.add_edge("Get Facebook Ads", "Get Video URLs")
    builder.add_edge("Get Video URLs", "Download Video")
    builder.add_edge("Download Video", "Transcribe Video")
    builder.add_edge("Download Video", "Extract Frames")
    builder.add_edge("Transcribe Video", "Analyze Transcription")
    builder.add_edge("Extract Frames", "Analyze Frames")
    builder.add_edge("Analyze Transcription", "Analyze Ad")
    builder.add_edge("Analyze Frames", "Analyze Ad")
    builder.add_edge("Analyze Ad", END)

    return builder.compile()

# ---- Run the Graph (to be called from main.py) ----
def run_ad_analysis_graph():
    print("[🚀] Starting Ad Analysis Graph...")
    graph = build_graph()

    # Start the graph execution
    final_state = graph.invoke({})

    print("\n[🎉] Workflow complete.")

    final_results = final_state.get("final_ad_analysis", [])
    if final_results:
        print("\n[📌] Final Ad Analysis Summary:")
        for item in final_results:
            print(f"\n🟢 [bold]{item['video']}[/bold]")
            pprint(item["final_analysis"])
    else:
        print("[⚠️] No final analysis results generated.")

    # ---- Visualize and save the graph structure ----
    print("\n[🖼️] Visualizing graph structure...")

    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        output_path = FINAL_OUTPUT_DIR / "graph_output.png"
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        print(f"[✅] Saved graph visualization to: {output_path}")
    except Exception as e:
        print(f"[❌] Graph visualization failed: {e}")
