"""Tests for the database module."""

import os
import tempfile
import pytest

from app import database


@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    """Use a temporary database for each test."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_db()
    yield db_path


# ── Schema ─────────────────────────────────────────────────────────────

def test_init_db_creates_tables():
    conn = database.get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    names = {row["name"] for row in tables}
    conn.close()
    assert "video_snapshots" in names
    assert "channel_snapshots" in names
    assert "tracked_channels" in names


def test_init_db_is_idempotent():
    database.init_db()
    database.init_db()
    conn = database.get_db()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    assert len(tables) >= 3


# ── Video snapshots ────────────────────────────────────────────────────

def test_save_and_retrieve_video_snapshot():
    video = {
        "video_id": "abc123",
        "title": "Test Video",
        "channel_title": "Test Channel",
        "view_count": 1000,
        "like_count": 50,
        "comment_count": 10,
        "thumbnail_url": "https://img.youtube.com/vi/abc123/hqdefault.jpg",
        "published_at": "2024-01-01T00:00:00Z",
    }
    database.save_video_snapshot(video, source="api")

    history = database.get_video_history("abc123")
    assert len(history) == 1
    row = history[0]
    assert row["video_id"] == "abc123"
    assert row["title"] == "Test Video"
    assert row["view_count"] == 1000
    assert row["like_count"] == 50
    assert row["comment_count"] == 10
    assert row["source"] == "api"
    assert row["fetched_at"] is not None


def test_multiple_video_snapshots_ordered():
    for i in range(3):
        database.save_video_snapshot(
            {"video_id": "vid1", "view_count": i * 100}, source="scrape"
        )
    history = database.get_video_history("vid1")
    assert len(history) == 3
    assert history[0]["view_count"] == 0
    assert history[2]["view_count"] == 200


def test_video_history_empty():
    history = database.get_video_history("nonexistent")
    assert history == []


# ── Channel snapshots ──────────────────────────────────────────────────

def test_save_and_retrieve_channel_snapshot():
    channel = {
        "channel_id": "UC123",
        "channel_title": "My Channel",
        "subscriber_count": 5000,
        "video_count": 42,
        "view_count": 100000,
        "thumbnail_url": "https://example.com/thumb.jpg",
    }
    database.save_channel_snapshot(channel, source="api")

    history = database.get_channel_history("UC123")
    assert len(history) == 1
    assert history[0]["subscriber_count"] == 5000
    assert history[0]["video_count"] == 42


def test_channel_snapshot_auto_tracks():
    channel = {
        "channel_id": "UC456",
        "channel_title": "Auto Tracked",
        "subscriber_count": 100,
        "video_count": 5,
        "view_count": 1000,
        "thumbnail_url": "",
    }
    database.save_channel_snapshot(channel)

    tracked = database.get_tracked_channels()
    ids = [ch["channel_id"] for ch in tracked]
    assert "UC456" in ids


def test_channel_history_empty():
    history = database.get_channel_history("nonexistent")
    assert history == []


# ── Tracked channels ──────────────────────────────────────────────────

def test_remove_tracked_channel():
    channel = {
        "channel_id": "UCremove",
        "channel_title": "Remove Me",
        "subscriber_count": 0,
        "video_count": 0,
        "view_count": 0,
        "thumbnail_url": "",
    }
    database.save_channel_snapshot(channel)
    assert any(
        ch["channel_id"] == "UCremove" for ch in database.get_tracked_channels()
    )

    database.remove_tracked_channel("UCremove")
    assert not any(
        ch["channel_id"] == "UCremove" for ch in database.get_tracked_channels()
    )


def test_tracked_channels_preserves_added_at():
    channel = {
        "channel_id": "UCkeep",
        "channel_title": "First Name",
        "subscriber_count": 100,
        "video_count": 1,
        "view_count": 50,
        "thumbnail_url": "",
    }
    database.save_channel_snapshot(channel)
    tracked = database.get_tracked_channels()
    original_added = next(
        ch["added_at"] for ch in tracked if ch["channel_id"] == "UCkeep"
    )

    # Save again with updated title
    channel["channel_title"] = "Updated Name"
    database.save_channel_snapshot(channel)
    tracked = database.get_tracked_channels()
    updated = next(ch for ch in tracked if ch["channel_id"] == "UCkeep")
    assert updated["added_at"] == original_added
    assert updated["channel_title"] == "Updated Name"
