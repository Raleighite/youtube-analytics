"""Fetch YouTube data using the official YouTube Data API v3."""

from googleapiclient.discovery import build


def get_youtube_client(api_key):
    return build("youtube", "v3", developerKey=api_key)


def fetch_videos_api(api_key, video_ids):
    """Fetch statistics for a list of video IDs via the YouTube Data API.

    Accepts up to 50 IDs per call (API limit).
    Returns a list of dicts with video metadata and stats.
    """
    youtube = get_youtube_client(api_key)
    results = []

    # Process in batches of 50
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        response = (
            youtube.videos()
            .list(part="snippet,statistics", id=",".join(batch))
            .execute()
        )

        for item in response.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            thumbnails = snippet.get("thumbnails", {})
            thumb = (
                thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url", "")
            )
            results.append(
                {
                    "video_id": item["id"],
                    "title": snippet.get("title"),
                    "channel_title": snippet.get("channelTitle"),
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                    "thumbnail_url": thumb,
                    "published_at": snippet.get("publishedAt"),
                }
            )

    return results


def fetch_channel_api(api_key, channel_id):
    """Fetch channel statistics by channel ID."""
    youtube = get_youtube_client(api_key)

    response = (
        youtube.channels()
        .list(part="snippet,statistics", id=channel_id)
        .execute()
    )

    items = response.get("items", [])
    if not items:
        return None

    item = items[0]
    snippet = item["snippet"]
    stats = item.get("statistics", {})
    thumbnails = snippet.get("thumbnails", {})
    thumb = (
        thumbnails.get("high", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
        or thumbnails.get("default", {}).get("url", "")
    )

    return {
        "channel_id": item["id"],
        "channel_title": snippet.get("title"),
        "subscriber_count": int(stats.get("subscriberCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
        "view_count": int(stats.get("viewCount", 0)),
        "thumbnail_url": thumb,
    }


def search_channel_by_name(api_key, channel_name):
    """Search for a channel by name and return the first match's ID."""
    youtube = get_youtube_client(api_key)

    response = (
        youtube.search()
        .list(part="snippet", q=channel_name, type="channel", maxResults=5)
        .execute()
    )

    results = []
    for item in response.get("items", []):
        results.append(
            {
                "channel_id": item["snippet"]["channelId"],
                "channel_title": item["snippet"]["title"],
                "thumbnail_url": item["snippet"]
                .get("thumbnails", {})
                .get("default", {})
                .get("url", ""),
            }
        )
    return results
