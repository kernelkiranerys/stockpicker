import requests
from datetime import datetime, timezone, timedelta
from django.conf import settings


def fetch_news(tickers):
    api_key = settings.FINNHUB_API_KEY
    if not api_key:
        return []

    results = []
    today = datetime.now(timezone.utc)
    from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    for ticker in tickers:
        symbol = ticker.yf_symbol if hasattr(ticker, "yf_symbol") else ticker.symbol
        try:
            resp = requests.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": symbol,
                    "from": from_date,
                    "to": to_date,
                    "token": api_key,
                },
                timeout=10,
            )
            if resp.status_code != 200:
                continue
            articles = resp.json()[:20]
            for art in articles:
                pub_ts = art.get("datetime", 0)
                pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc) if pub_ts else datetime.now(timezone.utc)
                results.append({
                    "headline": art.get("headline", ""),
                    "summary": art.get("summary", ""),
                    "url": art.get("url", ""),
                    "source": art.get("source", ""),
                    "published_at": pub_dt,
                    "ticker": ticker.symbol,
                    "raw": art,
                })
        except Exception:
            continue

    return results