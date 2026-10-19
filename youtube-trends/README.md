# YouTube regional video RSS

The service combines comedy and entertainment charts from the official YouTube Data API into one compact RSS feed for TrendRadar. Each item is a clickable video link and the web report shows a clickable thumbnail.

## Regions

US, GB, JP, KR, TH, IN, BR, and VN. The service reads the country-specific popular charts for Comedy and Entertainment and combines the results in one feed at `/rss/all`.

## One-time API key setup

1. In Google Cloud Console, create or select a project.
2. Enable **YouTube Data API v3**.
3. Create an API key and restrict it to the YouTube Data API.
4. In Portainer, edit the TrendRadar stack and add a stack environment variable named `YOUTUBE_API_KEY` with that key.
5. Pull and redeploy the stack.

The key is passed to the container through Compose and is not stored in this repository. If no key is configured, YouTube returns an empty feed. Check `http://youtube-trends:8000/_health` from inside the Docker network or inspect the container log to confirm key status.

The regional chart request uses one API call per country and category. With eight regions, two categories, and a 30-minute schedule, that is about 768 requests per day. Google's published default quota is 10,000 units/day for most read methods; quota allocations can change.

## Scope

This is a country-based YouTube popular-video feed, not a claim that TikTok, Instagram, VK, or every social network is already connected. Those platforms do not expose an equivalent reliable, no-login global public trend feed through the current NewsNow source list. TikTok's Research API requires an approved research application; RSSHub's current TikTok route is for a specific user timeline and relies on browser automation. Instagram hashtag/user collection is crawl restricted and may need credentials.