# YouTube Analytics Tracker

A web application for tracking YouTube video performance and channel growth over time. Supports both the official YouTube Data API v3 and web scraping as data sources.

## Features

- **Video Performance Lookup** -- Enter video IDs or full YouTube URLs to retrieve view counts, likes, and comment counts
- **Channel Growth Tracking** -- Monitor subscriber counts, video counts, and total views over time with historical charts
- **Dual Data Sources** -- Use the official YouTube Data API v3 (requires API key) or web scraping via yt-dlp/requests (no key needed)
- **Historical Snapshots** -- All lookups are stored in SQLite so you can track metrics growth over time
- **Interactive Charts** -- Chart.js-powered visualizations for video and channel performance trends
- **Responsive Dark UI** -- YouTube-inspired dark theme that works on desktop and mobile

## Quick Start

### With Docker (recommended)

```bash
docker compose up --build
```

The app will be available at `http://localhost:5000`.

To pass a YouTube API key:

```bash
YOUTUBE_API_KEY=your_key_here docker compose up --build
```

### Without Docker

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python run.py
```

Open `http://localhost:5000` in your browser.

## Configuration

| Method | Description |
|---|---|
| **API Key in UI** | Paste your YouTube Data API v3 key into the header bar |
| **Environment variable** | Set `YOUTUBE_API_KEY` before starting the app |
| **No key needed** | Select "Scrape Only" mode -- uses yt-dlp or requests |

### Fetch Modes

- **Auto** (default) -- Uses the API if a key is available, falls back to scraping
- **API Only** -- Requires a valid YouTube Data API v3 key
- **Scrape Only** -- Uses yt-dlp first, then falls back to requests + BeautifulSoup

## API Endpoints

### Videos

| Endpoint | Method | Description |
|---|---|---|
| `/api/videos` | POST | Look up stats for a list of video IDs |
| `/api/videos/<id>/history` | GET | Get historical snapshots for a video |

**POST /api/videos** body:
```json
{
  "video_ids": ["dQw4w9WgXcQ", "jNQXAC9IVRw"],
  "method": "auto"
}
```

### Channels

| Endpoint | Method | Description |
|---|---|---|
| `/api/channels/lookup` | POST | Look up channel stats by ID |
| `/api/channels/search` | POST | Search channels by name (API only) |
| `/api/channels/<id>/history` | GET | Get historical snapshots for a channel |
| `/api/channels/tracked` | GET | List all tracked channels |
| `/api/channels/<id>/track` | DELETE | Remove a channel from tracking |

## Project Structure

```
youtube-analytics/
├── app/
│   ├── __init__.py
│   ├── server.py          # Flask app and API routes
│   ├── database.py        # SQLite database layer
│   ├── youtube_api.py     # YouTube Data API v3 client
│   ├── scraper.py         # yt-dlp and requests scraping fallback
│   ├── requirements.txt   # Python dependencies
│   └── static/
│       ├── index.html     # Dashboard UI
│       ├── style.css      # Dark theme styles
│       └── app.js         # Frontend logic and charts
├── tests/
│   ├── __init__.py
│   ├── test_database.py   # Database unit tests
│   ├── test_scraper.py    # Scraper unit tests
│   └── test_server.py     # API endpoint tests
├── Dockerfile
├── docker-compose.yml
├── run.py                 # App entry point
└── README.md
```

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Getting a YouTube Data API Key

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the **YouTube Data API v3**
4. Go to **Credentials** and create an **API key**
5. Paste the key into the app's header bar or set it as `YOUTUBE_API_KEY`

## License

MIT
