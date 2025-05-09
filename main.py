from nodes.get_video_urls import get_video_urls_from_ads
from nodes.download_video import download_videos

# Step 1: Get video metadata (video_id + source)
video_result = get_video_urls_from_ads()

# ✅ Extract just the list of videos
video_entries = video_result.get("videos", [])

# Step 2: Download videos
downloaded_files = download_videos(video_entries)

# Step 3: Show result
print("\nDownloaded video files:")
for path in downloaded_files:
    print(path)
