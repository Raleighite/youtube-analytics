"""Flask web application for YouTube Analytics Tracker."""

import os
from flask import Flask, jsonify, request, send_from_directory

from .database import (
    init_db,
    save_video_snapshot,
    save_channel_snapshot,
    get_video_history,
    get_channel_history,
    get_tracked_channels,
    remove_tracked_channel,
)
from .youtube_api import fetch_videos_api, fetch_channel_api, search_channel_by_name
from .scraper import scrape_video, scrape_channel

app = Flask(__name__, static_folder="static")

# Initialize database on startup
init_db()


def _get_api_key():
    """Get API key from request header or environment variable."""
    return request.headers.get("X-API-Key") or os.environ.get("YOUTUBE_API_KEY", "")


# ── Static files ──────────────────────────────────────────────────────────


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(app.static_folder, path)


# ── Video endpoints ───────────────────────────────────────────────────────


@app.route("/api/videos", methods=["POST"])
def lookup_videos():
    """Look up video stats for a list of video IDs.

    JSON body: { "video_ids": ["abc123", ...], "method": "api" | "scrape" | "auto" }
    """
    data = request.get_json(force=True)
    video_ids = data.get("video_ids", [])
    method = data.get("method", "auto")

    if not video_ids:
        return jsonify({"error": "No video IDs provided"}), 400

    # Clean IDs (handle full URLs)
    clean_ids = []
    for vid in video_ids:
        vid = vid.strip()
        if "youtube.com" in vid or "youtu.be" in vid:
            # Extract ID from URL
            if "v=" in vid:
                vid = vid.split("v=")[1].split("&")[0]
            elif "youtu.be/" in vid:
                vid = vid.split("youtu.be/")[1].split("?")[0]
        if vid:
            clean_ids.append(vid)

    results = []
    errors = []
    api_key = _get_api_key()

    if method == "api" or (method == "auto" and api_key):
        if not api_key:
            return jsonify({"error": "No API key provided. Set X-API-Key header or YOUTUBE_API_KEY env var."}), 400
        try:
            results = fetch_videos_api(api_key, clean_ids)
            source = "api"
        except Exception as e:
            if method == "api":
                return jsonify({"error": f"YouTube API error: {str(e)}"}), 500
            # Fall through to scraping on auto
            method = "scrape"

    if method == "scrape" or (method == "auto" and not api_key):
        source = "scrape"
        for vid_id in clean_ids:
            result = scrape_video(vid_id)
            if result:
                results.append(result)
            else:
                errors.append(vid_id)

    # Save snapshots
    for r in results:
        save_video_snapshot(r, source=source)

    return jsonify({"videos": results, "errors": errors, "source": source})


@app.route("/api/videos/<video_id>/history")
def video_history(video_id):
    """Get historical snapshots for a video."""
    history = get_video_history(video_id)
    return jsonify({"video_id": video_id, "history": history})


# ── Channel endpoints ─────────────────────────────────────────────────────


@app.route("/api/channels/lookup", methods=["POST"])
def lookup_channel():
    """Look up channel stats.

    JSON body: { "channel_id": "UCxxx", "method": "api" | "scrape" | "auto" }
    """
    data = request.get_json(force=True)
    channel_id = data.get("channel_id", "").strip()
    method = data.get("method", "auto")

    if not channel_id:
        return jsonify({"error": "No channel ID provided"}), 400

    api_key = _get_api_key()
    result = None
    source = "api"

    if method == "api" or (method == "auto" and api_key):
        if not api_key:
            return jsonify({"error": "No API key provided."}), 400
        try:
            result = fetch_channel_api(api_key, channel_id)
            source = "api"
        except Exception as e:
            if method == "api":
                return jsonify({"error": f"YouTube API error: {str(e)}"}), 500
            method = "scrape"

    if result is None and (method == "scrape" or (method == "auto" and not api_key)):
        result = scrape_channel(channel_id)
        source = "scrape"

    if not result:
        return jsonify({"error": f"Could not fetch data for channel {channel_id}"}), 404

    save_channel_snapshot(result, source=source)
    return jsonify({"channel": result, "source": source})


@app.route("/api/channels/search", methods=["POST"])
def search_channel():
    """Search for channels by name (API only).

    JSON body: { "query": "channel name" }
    """
    data = request.get_json(force=True)
    query = data.get("query", "").strip()
    api_key = _get_api_key()

    if not query:
        return jsonify({"error": "No search query provided"}), 400
    if not api_key:
        return jsonify({"error": "Channel search requires an API key."}), 400

    try:
        results = search_channel_by_name(api_key, query)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/channels/<channel_id>/history")
def channel_history(channel_id):
    """Get historical snapshots for a channel."""
    history = get_channel_history(channel_id)
    return jsonify({"channel_id": channel_id, "history": history})


@app.route("/api/channels/tracked")
def tracked_channels():
    """Get all tracked channels."""
    channels = get_tracked_channels()
    return jsonify({"channels": channels})


@app.route("/api/channels/<channel_id>/track", methods=["DELETE"])
def untrack_channel(channel_id):
    """Remove a channel from tracking."""
    remove_tracked_channel(channel_id)
    return jsonify({"ok": True})


# ── Run ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
