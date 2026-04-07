"""Tests for the Flask API endpoints."""

import json
from unittest.mock import patch

import pytest

from app import database
from app.server import app


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    """Use a temporary database for each test."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_db()
    yield db_path


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ── Static routes ──────────────────────────────────────────────────────

def test_index(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"YouTube Analytics" in resp.data


def test_static_css(client):
    resp = client.get("/style.css")
    assert resp.status_code == 200


def test_static_js(client):
    resp = client.get("/app.js")
    assert resp.status_code == 200


# ── POST /api/videos ──────────────────────────────────────────────────

def test_videos_no_ids(client):
    resp = client.post("/api/videos", json={"video_ids": []})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_videos_scrape_mode(client):
    fake_result = {
        "video_id": "abc123",
        "title": "Scraped Video",
        "channel_title": "Channel",
        "view_count": 100,
        "like_count": 5,
        "comment_count": 2,
        "thumbnail_url": "",
        "published_at": "",
    }
    with patch("app.server.scrape_video", return_value=fake_result):
        resp = client.post(
            "/api/videos",
            json={"video_ids": ["abc123"], "method": "scrape"},
        )
    data = resp.get_json()
    assert resp.status_code == 200
    assert len(data["videos"]) == 1
    assert data["videos"][0]["title"] == "Scraped Video"
    assert data["source"] == "scrape"


def test_videos_scrape_failure(client):
    with patch("app.server.scrape_video", return_value=None):
        resp = client.post(
            "/api/videos",
            json={"video_ids": ["bad_id"], "method": "scrape"},
        )
    data = resp.get_json()
    assert resp.status_code == 200
    assert len(data["videos"]) == 0
    assert "bad_id" in data["errors"]


def test_videos_api_no_key(client):
    resp = client.post(
        "/api/videos",
        json={"video_ids": ["abc"], "method": "api"},
    )
    assert resp.status_code == 400
    assert "API key" in resp.get_json()["error"]


def test_videos_api_with_key(client):
    fake_results = [
        {
            "video_id": "xyz",
            "title": "API Video",
            "channel_title": "Ch",
            "view_count": 500,
            "like_count": 20,
            "comment_count": 3,
            "thumbnail_url": "",
            "published_at": "",
        }
    ]
    with patch("app.server.fetch_videos_api", return_value=fake_results):
        resp = client.post(
            "/api/videos",
            json={"video_ids": ["xyz"], "method": "api"},
            headers={"X-API-Key": "test_key"},
        )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["videos"][0]["title"] == "API Video"
    assert data["source"] == "api"


def test_videos_url_parsing(client):
    """Ensure full YouTube URLs get parsed into IDs."""
    with patch("app.server.scrape_video", return_value=None):
        resp = client.post(
            "/api/videos",
            json={
                "video_ids": [
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10",
                    "https://youtu.be/jNQXAC9IVRw?si=abc",
                ],
                "method": "scrape",
            },
        )
    data = resp.get_json()
    # Both should appear in errors since scrape returned None
    assert "dQw4w9WgXcQ" in data["errors"]
    assert "jNQXAC9IVRw" in data["errors"]


# ── GET /api/videos/<id>/history ───────────────────────────────────────

def test_video_history(client):
    database.save_video_snapshot(
        {"video_id": "hist1", "view_count": 100}, source="api"
    )
    database.save_video_snapshot(
        {"video_id": "hist1", "view_count": 200}, source="api"
    )

    resp = client.get("/api/videos/hist1/history")
    data = resp.get_json()
    assert resp.status_code == 200
    assert len(data["history"]) == 2


def test_video_history_empty(client):
    resp = client.get("/api/videos/noexist/history")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["history"] == []


# ── POST /api/channels/lookup ─────────────────────────────────────────

def test_channel_lookup_no_id(client):
    resp = client.post("/api/channels/lookup", json={"channel_id": ""})
    assert resp.status_code == 400


def test_channel_lookup_scrape(client):
    fake_channel = {
        "channel_id": "UC999",
        "channel_title": "Scraped Channel",
        "subscriber_count": 1000,
        "video_count": 10,
        "view_count": 50000,
        "thumbnail_url": "",
    }
    with patch("app.server.scrape_channel", return_value=fake_channel):
        resp = client.post(
            "/api/channels/lookup",
            json={"channel_id": "UC999", "method": "scrape"},
        )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["channel"]["channel_title"] == "Scraped Channel"


def test_channel_lookup_not_found(client):
    with patch("app.server.scrape_channel", return_value=None):
        resp = client.post(
            "/api/channels/lookup",
            json={"channel_id": "UCfail", "method": "scrape"},
        )
    assert resp.status_code == 404


# ── POST /api/channels/search ─────────────────────────────────────────

def test_channel_search_no_key(client):
    resp = client.post("/api/channels/search", json={"query": "test"})
    assert resp.status_code == 400
    assert "API key" in resp.get_json()["error"]


def test_channel_search_no_query(client):
    resp = client.post(
        "/api/channels/search",
        json={"query": ""},
        headers={"X-API-Key": "key"},
    )
    assert resp.status_code == 400


def test_channel_search_success(client):
    fake_results = [
        {"channel_id": "UC1", "channel_title": "Found", "thumbnail_url": ""}
    ]
    with patch("app.server.search_channel_by_name", return_value=fake_results):
        resp = client.post(
            "/api/channels/search",
            json={"query": "test"},
            headers={"X-API-Key": "key"},
        )
    data = resp.get_json()
    assert resp.status_code == 200
    assert len(data["results"]) == 1


# ── GET /api/channels/<id>/history ─────────────────────────────────────

def test_channel_history(client):
    database.save_channel_snapshot(
        {
            "channel_id": "UCh",
            "channel_title": "Ch",
            "subscriber_count": 100,
            "video_count": 5,
            "view_count": 1000,
            "thumbnail_url": "",
        }
    )
    resp = client.get("/api/channels/UCh/history")
    data = resp.get_json()
    assert resp.status_code == 200
    assert len(data["history"]) == 1


# ── GET /api/channels/tracked ─────────────────────────────────────────

def test_tracked_channels_empty(client):
    resp = client.get("/api/channels/tracked")
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["channels"] == []


# ── DELETE /api/channels/<id>/track ────────────────────────────────────

def test_untrack_channel(client):
    database.save_channel_snapshot(
        {
            "channel_id": "UCdel",
            "channel_title": "Del",
            "subscriber_count": 0,
            "video_count": 0,
            "view_count": 0,
            "thumbnail_url": "",
        }
    )
    resp = client.delete("/api/channels/UCdel/track")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    tracked = client.get("/api/channels/tracked").get_json()["channels"]
    assert not any(ch["channel_id"] == "UCdel" for ch in tracked)
