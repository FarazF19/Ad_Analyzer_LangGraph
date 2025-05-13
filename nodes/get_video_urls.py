import requests
import os
from dotenv import load_dotenv
from nodes.get_ads import get_facebook_ads  # This should now return state with "ads" key

load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

def get_video_urls_from_ads(state: dict) -> dict:
    """
    Extracts video URLs for each ad with a video creative.

    Args:
        state (dict): Current LangGraph state, should include "ads".

    Returns:
        dict: Updated state with video URL info.
    """
    try:
        ads = state.get("ads", [])
        if not ads:
            print("[⚠️] No ads found in state. Cannot extract video URLs.")
            state["video_urls"] = []
            return state

        video_urls = []

        for ad in ads:
            creative = ad.get("creative", {})
            video_id = (
                creative
                .get("object_story_spec", {})
                .get("video_data", {})
                .get("video_id")
            )

            if not video_id:
                print(f"[SKIP] No video ID found for ad_id {ad.get('id')}")
                continue

            video_url = f"https://graph.facebook.com/v19.0/{video_id}"
            params = {
                "access_token": ACCESS_TOKEN,
                "fields": "source,permalink_url"
            }

            try:
                response = requests.get(video_url, params=params)
                response.raise_for_status()
                data = response.json()

                video_info = {
                    "ad_id": ad.get("id"),
                    "video_id": video_id,
                    "source": data.get("source"),
                    "permalink_url": data.get("permalink_url")
                }

                video_urls.append(video_info)

            except requests.exceptions.RequestException as e:
                print(f"[WARN] Failed for video_id {video_id}: {e}")
                video_urls.append({
                    "video_id": video_id,
                    "error": str(e)
                })

        print(f"[🔗] Found video URLs for {len(video_urls)} ads.")
        state["video_urls"] = video_urls
        return state

    except Exception as e:
        print(f"[❌] Unexpected error in get_video_urls_from_ads: {e}")
        state["error"] = str(e)
        return state
