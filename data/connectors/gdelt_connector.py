import requests
from datetime import datetime, timezone, timedelta
from django.conf import settings


def fetch_news(tickers):
    results = []
    today = datetime.now(timezone.utc)
    from_date = (today - timedelta(days=3)).strftime("%Y-%m-%d")

    for ticker in tickers:
        symbol = ticker.yf_symbol if hasattr(ticker, "yf_symbol") else ticker.symbol
        name = ticker.name if hasattr(ticker, "name") else symbol
        queries = [f"${symbol}", name, symbol]
        for query in queries[:1]:
            try:
                resp = requests.get(
                    "https://api.gdeltproject.org/api/v2/doc/doc",
                    params={
                        "query": f'"{query}" stock',
                        "mode": "rss",
                        "maxrecords": 5,
                        "format": "rss",
                        "startdatetime": from_date.replace("-", "") + "000000",
                        "enddatetime": today.strftime("%Y%m%d") + "000000",
                    },
                    timeout=10,
                )
                if resp.status_code != 200:
                    continue
                import feedparser
                feed = feedparser.parse(resp.content)
                for entry in feed.entries[:3]:
                    pub_dt = datetime.now(timezone.utc)
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        import time as _time
                        pub_dt = datetime.fromtimestamp(_time.mktime(entry.published_parsed), tz=timezone.utc)
                    results.append({
                        "headline": entry.get("title", ""),
                        "summary": entry.get("summary", ""),
                        "url": entry.get("link", ""),
                        "source": "GDELT",
                        "published_at": pub_dt,
                        "ticker": ticker.symbol,
                        "raw": {"title": entry.get("title", ""), "link": entry.get("link", "")},
                    })
            except Exception:
                continue

    return results