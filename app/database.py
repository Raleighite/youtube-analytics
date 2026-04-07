import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "youtube_analytics.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS video_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            title TEXT,
            channel_title TEXT,
            view_count INTEGER,
            like_count INTEGER,
            comment_count INTEGER,
            thumbnail_url TEXT,
            published_at TEXT,
            fetched_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'api'
        );

        CREATE TABLE IF NOT EXISTS channel_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT NOT NULL,
            channel_title TEXT,
            subscriber_count INTEGER,
            video_count INTEGER,
            view_count INTEGER,
            thumbnail_url TEXT,
            fetched_at TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'api'
        );

        CREATE TABLE IF NOT EXISTS tracked_channels (
            channel_id TEXT PRIMARY KEY,
            channel_title TEXT,
            added_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_video_snapshots_video_id
            ON video_snapshots(video_id);
        CREATE INDEX IF NOT EXISTS idx_video_snapshots_fetched_at
            ON video_snapshots(fetched_at);
        CREATE INDEX IF NOT EXISTS idx_channel_snapshots_channel_id
            ON channel_snapshots(channel_id);
        CREATE INDEX IF NOT EXISTS idx_channel_snapshots_fetched_at
            ON channel_snapshots(fetched_at);
    """)
    conn.close()


def save_video_snapshot(video_data, source="api"):
    conn = get_db()
    conn.execute(
        """INSERT INTO video_snapshots
           (video_id, title, channel_title, view_count, like_count,
            comment_count, thumbnail_url, published_at, fetched_at, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            video_data["video_id"],
            video_data.get("title"),
            video_data.get("channel_title"),
            video_data.get("view_count"),
            video_data.get("like_count"),
            video_data.get("comment_count"),
            video_data.get("thumbnail_url"),
            video_data.get("published_at"),
            datetime.utcnow().isoformat(),
            source,
        ),
    )
    conn.commit()
    conn.close()


def save_channel_snapshot(channel_data, source="api"):
    conn = get_db()
    conn.execute(
        """INSERT INTO channel_snapshots
           (channel_id, channel_title, subscriber_count, video_count,
            view_count, thumbnail_url, fetched_at, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            channel_data["channel_id"],
            channel_data.get("channel_title"),
            channel_data.get("subscriber_count"),
            channel_data.get("video_count"),
            channel_data.get("view_count"),
            channel_data.get("thumbnail_url"),
            datetime.utcnow().isoformat(),
            source,
        ),
    )
    # Upsert tracked channel
    conn.execute(
        """INSERT OR REPLACE INTO tracked_channels
           (channel_id, channel_title, added_at)
           VALUES (?, ?, COALESCE(
               (SELECT added_at FROM tracked_channels WHERE channel_id = ?),
               ?
           ))""",
        (
            channel_data["channel_id"],
            channel_data.get("channel_title"),
            channel_data["channel_id"],
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_video_history(video_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM video_snapshots
           WHERE video_id = ? ORDER BY fetched_at ASC""",
        (video_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_channel_history(channel_id):
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM channel_snapshots
           WHERE channel_id = ? ORDER BY fetched_at ASC""",
        (channel_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_tracked_channels():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tracked_channels ORDER BY added_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def remove_tracked_channel(channel_id):
    conn = get_db()
    conn.execute("DELETE FROM tracked_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()
    conn.close()
