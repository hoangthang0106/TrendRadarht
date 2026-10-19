#!/usr/bin/env python3
"""RSS bridge for official YouTube popular-video charts by country."""
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
REGIONS = [x.strip().upper() for x in os.environ.get(
    "YOUTUBE_REGIONS", "US,GB,JP,KR,TH,IN,BR,VN"
).split(",") if x.strip()]
CACHE_SECONDS = int(os.environ.get("CACHE_SECONDS", "900"))
_cache = {}
NAMES = {
    "US": "United States", "GB": "United Kingdom", "JP": "Japan",
    "KR": "South Korea", "TH": "Thailand", "IN": "India",
    "BR": "Brazil", "VN": "Vietnam",
}
CATEGORIES = [("23", "Comedy"), ("24", "Entertainment")]


def get_videos(region, category_id):
    cache_key = (region, category_id)
    now = time.time()
    cached = _cache.get(cache_key)
    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]
    if not API_KEY:
        return []
    params = urllib.parse.urlencode({
        "part": "snippet,statistics",
        "chart": "mostPopular",
        "regionCode": region,
        "videoCategoryId": category_id,
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
    _cache[cache_key] = (now, videos)
    return videos


def xml_response(videos):
    root = ET.Element("rss", version="2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "YouTube popular clips - 8 countries"
    ET.SubElement(channel, "link").text = "https://www.youtube.com/feed/trending"
    ET.SubElement(channel, "description").text = (
        "Comedy and entertainment videos from regional YouTube popular charts."
    )
    ET.SubElement(channel, "language").text = "en"
    for region, category, video in videos:
        snippet = video.get("snippet", {})
        video_id = video.get("id", "")
        if not video_id:
            continue
        title = snippet.get("title", "Untitled video")
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = f"[{region}] {title}"
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
        details = [NAMES.get(region, region), category, channel_name]
        if views:
            details.append(f"{views} views")
        details.append(url)
        ET.SubElement(item, "description").text = " · ".join(details)
        ET.SubElement(item, "category").text = region
        ET.SubElement(item, "enclosure", url=f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                      type="image/jpeg", length="0")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8")


def fetch_all():
    videos = []
    seen = set()
    for region in REGIONS:
        for category_id, category_name in CATEGORIES:
            try:
                batch = get_videos(region, category_id)
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
                print(f"YouTube fetch failed for {region}/{category_id}: {exc}", flush=True)
                continue
            for video in batch:
                video_id = video.get("id")
                if video_id and video_id not in seen:
                    seen.add(video_id)
                    videos.append((region, category_name, video))
    return videos


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/_health":
            body = json.dumps({
                "ok": True,
                "api_key_configured": bool(API_KEY),
                "regions": REGIONS,
                "categories": [x[1] for x in CATEGORIES],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path != "/rss/all":
            self.send_error(404, "Use /rss/all")
            return
        try:
            body = xml_response(fetch_all())
        except Exception as exc:
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
    print(f"YouTube clip RSS listening on :8000; regions={REGIONS}; "
          f"API key configured={bool(API_KEY)}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
