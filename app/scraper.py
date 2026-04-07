"""Web scraping fallback for fetching YouTube data without an API key.

Uses yt-dlp for reliable metadata extraction.
Falls back to requests + BeautifulSoup if yt-dlp is unavailable.
"""

import json
import re
import subprocess

import requests
from bs4 import BeautifulSoup

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


def _parse_count(text):
    """Parse abbreviated counts like '1.2M' or '345K' into integers."""
    if not text:
        return 0
    text = text.strip().replace(",", "")
    multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
    for suffix, mult in multipliers.items():
        if text.upper().endswith(suffix):
            try:
                return int(float(text[:-1]) * mult)
            except ValueError:
                return 0
    try:
        return int(text)
    except ValueError:
        return 0


def scrape_video_ytdlp(video_id):
    """Use yt-dlp to extract video metadata (no download)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--no-playlist",
                url,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        return {
            "video_id": video_id,
            "title": data.get("title"),
            "channel_title": data.get("uploader") or data.get("channel"),
            "view_count": data.get("view_count", 0) or 0,
            "like_count": data.get("like_count", 0) or 0,
            "comment_count": data.get("comment_count", 0) or 0,
            "thumbnail_url": data.get("thumbnail", ""),
            "published_at": data.get("upload_date", ""),
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return None


def scrape_video_requests(video_id):
    """Scrape video page with requests + regex as a last resort."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Try to extract from the initial data JSON embedded in the page
        match = re.search(r"var ytInitialPlayerResponse\s*=\s*(\{.*?\});", html)
        player_data = json.loads(match.group(1)) if match else {}

        match2 = re.search(r"var ytInitialData\s*=\s*(\{.*?\});", html)
        initial_data = json.loads(match2.group(1)) if match2 else {}

        # Title from player response
        title = (
            player_data.get("videoDetails", {}).get("title", "")
            or _extract_meta(html, "og:title")
        )
        channel = player_data.get("videoDetails", {}).get("author", "")
        view_count = int(
            player_data.get("videoDetails", {}).get("viewCount", 0) or 0
        )
        thumbnail = (
            player_data.get("videoDetails", {})
            .get("thumbnail", {})
            .get("thumbnails", [{}])[-1]
            .get("url", "")
        )

        # Try to extract likes from initial data
        like_count = _extract_likes(initial_data)
        comment_count = _extract_comment_count(initial_data)

        return {
            "video_id": video_id,
            "title": title,
            "channel_title": channel,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "thumbnail_url": thumbnail,
            "published_at": "",
        }
    except Exception:
        return None


def _extract_meta(html, prop):
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("meta", property=prop)
    return tag["content"] if tag and tag.get("content") else ""


def _extract_likes(initial_data):
    """Best-effort extraction of like count from ytInitialData."""
    try:
        raw = json.dumps(initial_data)
        # Look for accessibility text like "1,234 likes"
        match = re.search(r'"accessibilityText":"([\d,]+)\s+likes?"', raw)
        if match:
            return int(match.group(1).replace(",", ""))
        # Look for the toggle button label
        match = re.search(r'"toggledText".*?"simpleText":"([\d,.KMB]+)"', raw)
        if match:
            return _parse_count(match.group(1))
    except Exception:
        pass
    return 0


def _extract_comment_count(initial_data):
    """Best-effort extraction of comment count from ytInitialData."""
    try:
        raw = json.dumps(initial_data)
        match = re.search(r'"commentCount".*?"simpleText":"([\d,]+)"', raw)
        if match:
            return int(match.group(1).replace(",", ""))
    except Exception:
        pass
    return 0


def scrape_video(video_id):
    """Try yt-dlp first, fall back to requests scraping."""
    result = scrape_video_ytdlp(video_id)
    if result:
        return result
    return scrape_video_requests(video_id)


def scrape_channel(channel_id):
    """Scrape channel page for subscriber/video counts."""
    url = f"https://www.youtube.com/channel/{channel_id}"
    try:
        # Try yt-dlp first
        result = subprocess.run(
            [
                "yt-dlp",
                "--dump-json",
                "--no-download",
                "--playlist-items",
                "0",
                f"{url}/videos",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout.strip().split("\n")[0])
            return {
                "channel_id": channel_id,
                "channel_title": data.get("channel") or data.get("uploader", ""),
                "subscriber_count": data.get("channel_follower_count", 0) or 0,
                "video_count": 0,
                "view_count": 0,
                "thumbnail_url": data.get("channel_url", ""),
            }
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

    # Fallback: requests
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
        html = resp.text

        match = re.search(r"var ytInitialData\s*=\s*(\{.*?\});", html)
        if not match:
            return None
        data = json.loads(match.group(1))
        raw = json.dumps(data)

        title = _extract_meta(html, "og:title") or ""

        sub_match = re.search(
            r'"subscriberCountText".*?"simpleText":"([\d,.KMB]+)\s*subscribers?"', raw
        )
        sub_count = _parse_count(sub_match.group(1)) if sub_match else 0

        return {
            "channel_id": channel_id,
            "channel_title": title,
            "subscriber_count": sub_count,
            "video_count": 0,
            "view_count": 0,
            "thumbnail_url": "",
        }
    except Exception:
        return None
