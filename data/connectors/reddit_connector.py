import praw
from datetime import datetime, timezone
from django.conf import settings


def _get_reddit():
    if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
        return None
    return praw.Reddit(
        client_id=settings.REDDIT_CLIENT_ID,
        client_secret=settings.REDDIT_CLIENT_SECRET,
        user_agent=settings.REDDIT_USER_AGENT,
    )


def _extract_ticker_symbols(text, ticker_symbols):
    found = set()
    text_upper = text.upper()
    for sym in ticker_symbols:
        if f"${sym}" in text_upper or f" {sym} " in text_upper:
            found.add(sym)
    return found


def fetch_posts(subreddits, tickers, limit=100):
    reddit = _get_reddit()
    if reddit is None:
        return []

    ticker_symbols = {t.symbol for t in tickers}
    ticker_map = {t.symbol: t for t in tickers}

    results = []
    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=limit):
                text = f"{post.title} {post.selftext}"
                found = _extract_ticker_symbols(text, ticker_symbols)
                if not found:
                    continue
                created_dt = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                for sym in found:
                    results.append({
                        "subreddit": sub_name,
                        "post_id": post.id,
                        "title": post.title,
                        "body": post.selftext[:2000],
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "created_at": created_dt,
                        "url": f"https://reddit.com{post.permalink}",
                        "ticker": ticker_map.get(sym),
                    })
        except Exception:
            continue

    return results