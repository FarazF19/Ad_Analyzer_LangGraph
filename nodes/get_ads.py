import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")
AD_ACCOUNT_ID = os.getenv("FB_AD_ACCOUNT_ID")

def get_facebook_ads(state: dict) -> dict:
    """
    Fetch Facebook Ads data from Graph API and store it in the graph state.

    Args:
        state (dict): The current state of the graph.

    Returns:
        dict: Updated graph state including raw ad data.
    """
    try:
        url = f"https://graph.facebook.com/v19.0/act_{AD_ACCOUNT_ID}/ads"
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
        response.raise_for_status()

        data = response.json()
        ads_data = data.get("data", [])

        # Save to file for debugging
        with open("ads.json", "w") as f:
            json.dump(ads_data, f, indent=2)

        print(f"[📥] Retrieved {len(ads_data)} ads from Meta.")

        # Update state - store the ads in a list (this will be accumulated in the graph state)
        if "ads" in state:
            state["ads"].extend(ads_data)  # Accumulate the ads into the list
        else:
            state["ads"] = ads_data  # Initialize the list with the first set of ads

        return state

    except requests.exceptions.RequestException as e:
        print(f"[❌] Request to Facebook Ads API failed: {e}")
        state["error"] = str(e)
        return state

    except Exception as e:
        print(f"[❌] Unexpected error occurred: {e}")
        state["error"] = str(e)
        return state
