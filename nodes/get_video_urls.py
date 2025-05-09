import requests
import os
from dotenv import load_dotenv
from nodes.get_ads import get_facebook_ads  # Importing function from get_ads.py

load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

def get_video_urls_from_ads():
    """
    Fetches all video URLs (source + permalink) for ads that contain video creatives.

    Returns:
        list[dict]: Each dict contains video_id, source, and permalink_url.
    """
    try:
        # Get all Facebook ads
        ads_result = get_facebook_ads()

        if "error" in ads_result:
            return {"error": "Failed to fetch ads: " + ads_result["error"]}

        video_urls = []

        # Extract video_id from each ad
        for ad in ads_result.get("ads", []):
            creative = ad.get("creative", {})
            # Extract video_id from nested path
            video_id = (
                creative
                .get("object_story_spec", {})
                .get("video_data", {})
                .get("video_id")
            )
            
            if not video_id:
                  print(f"[SKIP] No video ID found for ad_id {ad.get('id')}")
                  continue

            # Call Graph API to get video URL and permalink
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
                    "ad_id": ad.get("id"),        # Ad ID for reference- can be skipped
                    "video_id": video_id,         # Video ID- can be skipped
                    "source": data.get("source"),    # Video source URL-important
                    "permalink_url": data.get("permalink_url")
                }

                video_urls.append(video_info)

            except requests.exceptions.RequestException as e:
                print(f"[WARN] Failed for video_id {video_id}: {e}")
                video_urls.append({
                    "video_id": video_id,
                    "error": str(e)
                })

        print(f"[INFO] Found video URLs for {len(video_urls)} videos.")
        return {"videos": video_urls}

    except Exception as e:
        print(f"[ERROR] Unexpected error in video fetching: {e}")
        return {"error": str(e)}
    

