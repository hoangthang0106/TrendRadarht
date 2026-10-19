# YouTube regional trend RSS

This small bridge exposes official YouTube Data API regional popular-video charts as RSS feeds for TrendRadar.

## Regions

The Docker stack enables US, GB, JP, KR, TH, IN, BR, and VN. Each feed item links to the original YouTube video page. These are country-specific popular-video charts, not a claim that every social platform is covered.

## One-time API key setup

1. In Google Cloud Console, create or select a project.
2. Enable **YouTube Data API v3** for that project.
3. Create an API key and restrict it to the YouTube Data API.
4. In Portainer, edit the TrendRadar stack and add a stack environment variable named `YOUTUBE_API_KEY` with that key.
5. Redeploy the stack.

The key is passed to the container through Compose and is not stored in this repository. If the key is absent, feeds return empty lists; check `http://youtube-trends:8000/_health` from inside the Docker network or the container logs to confirm key status.

The API's `videos.list` method costs one quota unit per request. At the default 30-minute TrendRadar schedule, eight regions need about 384 requests per day, within Google's published default 10,000 units per day for other API methods. Quota allocations may change.

## Local check

After the stack starts, check:

- `http://youtube-trends:8000/_health`
- `http://youtube-trends:8000/rss/US`
- `http://youtube-trends:8000/rss/JP`
