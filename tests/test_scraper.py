"""Tests for the scraper module."""

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from app.scraper import (
    _parse_count,
    scrape_video_ytdlp,
    scrape_video_requests,
    scrape_video,
    scrape_channel,
)


# ── _parse_count ───────────────────────────────────────────────────────

class TestParseCount:
    def test_plain_number(self):
        assert _parse_count("12345") == 12345

    def test_commas(self):
        assert _parse_count("1,234,567") == 1234567

    def test_k_suffix(self):
        assert _parse_count("1.5K") == 1500

    def test_m_suffix(self):
        assert _parse_count("2.3M") == 2300000

    def test_b_suffix(self):
        assert _parse_count("1B") == 1000000000

    def test_lowercase(self):
        assert _parse_count("500k") == 500000

    def test_empty(self):
        assert _parse_count("") == 0

    def test_none(self):
        assert _parse_count(None) == 0

    def test_invalid(self):
        assert _parse_count("abc") == 0

    def test_whitespace(self):
        assert _parse_count("  42  ") == 42


# ── scrape_video_ytdlp ────────────────────────────────────────────────

class TestScrapeVideoYtdlp:
    def test_success(self):
        fake_output = json.dumps({
            "title": "Test Video",
            "uploader": "TestUser",
            "view_count": 999,
            "like_count": 55,
            "comment_count": 12,
            "thumbnail": "https://example.com/thumb.jpg",
            "upload_date": "20240101",
        })
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_output

        with patch("app.scraper.subprocess.run", return_value=mock_result):
            result = scrape_video_ytdlp("abc123")

        assert result is not None
        assert result["video_id"] == "abc123"
        assert result["title"] == "Test Video"
        assert result["view_count"] == 999
        assert result["like_count"] == 55
        assert result["comment_count"] == 12

    def test_failure_returns_none(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""

        with patch("app.scraper.subprocess.run", return_value=mock_result):
            result = scrape_video_ytdlp("bad_id")

        assert result is None

    def test_timeout_returns_none(self):
        with patch(
            "app.scraper.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="yt-dlp", timeout=30),
        ):
            result = scrape_video_ytdlp("slow_id")

        assert result is None

    def test_not_installed_returns_none(self):
        with patch(
            "app.scraper.subprocess.run", side_effect=FileNotFoundError
        ):
            result = scrape_video_ytdlp("no_ytdlp")

        assert result is None


# ── scrape_video ──────────────────────────────────────────────────────

class TestScrapeVideo:
    def test_falls_back_to_requests(self):
        with patch("app.scraper.scrape_video_ytdlp", return_value=None), \
             patch("app.scraper.scrape_video_requests", return_value={"video_id": "x"}) as mock_req:
            result = scrape_video("x")
            assert result == {"video_id": "x"}
            mock_req.assert_called_once_with("x")

    def test_uses_ytdlp_first(self):
        ytdlp_result = {"video_id": "y", "title": "from ytdlp"}
        with patch("app.scraper.scrape_video_ytdlp", return_value=ytdlp_result), \
             patch("app.scraper.scrape_video_requests") as mock_req:
            result = scrape_video("y")
            assert result["title"] == "from ytdlp"
            mock_req.assert_not_called()


# ── scrape_channel ────────────────────────────────────────────────────

class TestScrapeChannel:
    def test_ytdlp_success(self):
        fake_output = json.dumps({
            "channel": "TestChannel",
            "channel_follower_count": 10000,
        })
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = fake_output

        with patch("app.scraper.subprocess.run", return_value=mock_result):
            result = scrape_channel("UC123")

        assert result is not None
        assert result["channel_id"] == "UC123"
        assert result["channel_title"] == "TestChannel"
        assert result["subscriber_count"] == 10000

    def test_all_fail_returns_none(self):
        with patch(
            "app.scraper.subprocess.run", side_effect=FileNotFoundError
        ), patch("app.scraper.requests.get", side_effect=Exception("fail")):
            result = scrape_channel("UCfail")

        assert result is None
