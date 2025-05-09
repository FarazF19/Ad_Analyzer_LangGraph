
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("FB_AD_ACCOUNT_ID")

## This function fetches Facebook Ads data from the Graph API.

def get_facebook_ads():
    """
    Fetch Facebook Ads data from Graph API.

    Returns:
        dict: A dictionary with raw ad JSON data or error info.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/{AD_ACCOUNT_ID}/ads"
        params = {
            "access_token": ACCESS_TOKEN,
            "fields": ",".join([
                "id",
                "name",
                "ad_active_time",
                "adlabels",
                "campaign{id,name}",
                "adset{id,name,targeting}",
                "creative{id,video_id,effective_object_story_id,object_story_spec}",
                "status"
            ])
        }

        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise if 4xx or 5xx

        data = response.json()

       
        with open("ads.json", "w") as f:
            json.dump(data.get("data", []), f, indent=2)
 

        print(f"[INFO] Retrieved {len(data.get('data', []))} ads from Meta.")
        return {"ads": data.get("data", [])}

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request to Facebook Ads API failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"[ERROR] Unexpected error occurred: {e}")
        return {"error": str(e)}
