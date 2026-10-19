#!/usr/bin/env python3
"""Small RSS bridge for YouTube's regional most-popular video charts."""
import datetime as dt
import email.utils
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
REGIONS = {x.strip().upper() for x in os.environ.get(
    "YOUTUBE_REGIONS", "US,GB,JP,KR,TH,IN,BR,VN"
).split(",") if x.strip()}
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "900"))
_cache = {}
NAMES = {
    "US": "United States", "GB": "United Kingdom", "JP": "Japan",
    "KR": "South Korea", "TH": "Thailand", "IN": "India",
    "BR": "Brazil", "VN": "Vietnam",
}


def xml_response(region, videos):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = f"YouTube Trending Videos - {NAMES.get(region, region)}"
    ET.SubElement(channel, "link").text = "https://www.youtube.com/feed/trending"
    ET.SubElement(channel, "description").text = (
        f"Most popular public YouTube videos for region {region}."
    )
    ET.SubElement(channel, "language").text = region.lower()
    for video in videos:
        snippet = video.get("snippet", {})
        video_id = video.get("id", "")
        if not video_id:
            continue
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = snippet.get("title", "Untitled video")
        url = f"https://www.youtube.com/watch?v={video_id}"
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid", isPermaLink="false").text = f"youtube:{video_id}"
        published = snippet.get("publishedAt", "")
        try:
            date = dt.datetime.fromisoformat(published.replace("Z", "+00:00"))
            ET.SubElement(item, "pubDate").text = email.utils.format_datetime(date)
        except (ValueError, TypeError):
            pass
        channel_name = snippet.get("channelTitle", "")
        views = video.get("statistics", {}).get("viewCount", "")
        details = [x for x in (channel_name, f"{views} views" if views else "") if x]
        ET.SubElement(item, "description").text = " · ".join(details) + f" · {url}"
        ET.SubElement(item, "category").text = region
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")


def get_videos(region):
    now = time.time()
    cached = _cache.get(region)
    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]
    if not API_KEY:
        return []
    params = urllib.parse.urlencode({
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "maxResults": "25",
        "key": API_KEY,
    })
    req = urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/videos?" + params,
        headers={"User-Agent": "TrendRadar-RegionalVideoFeed/1.0"},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    videos = data.get("items", [])
    _cache[region] = (now, videos)
    return videos


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/_health":
            body = json.dumps({
                "ok": True,
                "api_key_configured": bool(API_KEY),
                "regions": sorted(REGIONS),
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        parts = self.path.strip("/").split("/")
        if len(parts) != 2 or parts[0] != "rss":
            self.send_error(404, "Use /rss/US")
            return
        region = parts[1].upper()
        if region not in REGIONS:
            self.send_error(404, "Region is not enabled")
            return
        try:
            body = xml_response(region, get_videos(region))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            self.send_error(502, f"YouTube Data API request failed: {exc}")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args), flush=True)


if __name__ == "__main__":
    print(f"Regional video RSS listening on :8000; regions={sorted(REGIONS)}; "
          f"API key configured={bool(API_KEY)}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
