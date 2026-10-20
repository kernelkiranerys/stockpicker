from celery import shared_task
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from django.utils import timezone as djtz
from django.conf import settings

from tickers.models import Ticker, Watchlist
from data.models import (
    OHLCV, Fundamental, NewsArticle, RedditPost,
    InsiderTrade, InstitutionalHolding, OptionsSnapshot,
    MacroIndicator,
)
from data.connectors import yfinance_connector


@shared_task
def fetch_ohlcv_daily():
    tickers = Ticker.objects.filter(is_active=True)
    for ticker in tickers:
        try:
            bars = yfinance_connector.fetch_ohlcv(ticker, interval="1d", period="1y")
            for bar in bars:
                OHLCV.objects.update_or_create(
                    ticker=ticker,
                    timestamp=bar["timestamp"],
                    interval=bar["interval"],
                    defaults={k: v for k, v in bar.items() if k != "ticker"},
                )
            if bars:
                latest = bars[-1]
                ticker.last_price = latest["close"]
                ticker.last_price_updated = djtz.now()
                ticker.save(update_fields=["last_price", "last_price_updated"])
        except Exception as e:
            print(f"Error fetching OHLCV for {ticker.symbol}: {e}")


@shared_task
def fetch_ohlcv_15m():
    tickers = Ticker.objects.filter(is_active=True)
    watchlist_tickers = Ticker.objects.filter(watchlists__is_active=True).distinct()
    tickers = list(tickers[:300]) + list(watchlist_tickers)
    seen = set()
    unique_tickers = []
    for t in tickers:
        if t.id not in seen:
            seen.add(t.id)
            unique_tickers.append(t)
    for ticker in unique_tickers:
        try:
            bars = yfinance_connector.fetch_intraday_ohlcv(ticker, interval="15m")
            for bar in bars:
                OHLCV.objects.update_or_create(
                    ticker=ticker,
                    timestamp=bar["timestamp"],
                    interval=bar["interval"],
                    defaults={k: v for k, v in bar.items() if k != "ticker"},
                )
        except Exception as e:
            print(f"Error fetching 15m OHLCV for {ticker.symbol}: {e}")


@shared_task
def fetch_fundamentals():
    for ticker in Ticker.objects.filter(is_active=True):
        try:
            data = yfinance_connector.fetch_fundamentals(ticker)
            today = djtz.now().date()
            fields = {k: (Decimal(str(v)) if v is not None and k != "raw_info" else v) for k, v in data.items()}
            Fundamental.objects.update_or_create(
                ticker=ticker,
                date=today,
                defaults=fields,
            )
        except Exception as e:
            print(f"Error fetching fundamentals for {ticker.symbol}: {e}")


@shared_task
def fetch_options_data():
    for ticker in Ticker.objects.filter(is_active=True):
        try:
            data = yfinance_connector.fetch_option_chain(ticker)
            if not data:
                continue
            from datetime import date as date_cls
            expiry = date_cls.fromisoformat(data["expiry"]) if isinstance(data["expiry"], str) else data["expiry"]
            OptionsSnapshot.objects.create(
                ticker=ticker,
                expiry=expiry,
                call_volume=data["call_volume"],
                put_volume=data["put_volume"],
                call_open_interest=data["call_open_interest"],
                put_open_interest=data["put_open_interest"],
                put_call_ratio=data.get("put_call_ratio"),
                vol_oi_ratio=data.get("vol_oi_ratio"),
                implied_volatility=data.get("implied_volatility"),
                unusual_activity=data.get("unusual_activity", False),
                raw={k: (float(v) if hasattr(v, '__float__') else (v if not isinstance(v, (list, dict)) else v)) for k, v in data.items()},
            )
        except Exception as e:
            print(f"Error fetching options for {ticker.symbol}: {e}")


@shared_task
def fetch_benchmark_price():
    bars = yfinance_connector.fetch_benchmark("SPY", interval="15m", period="5d")
    try:
        spy_ticker, _ = Ticker.objects.get_or_create(
            symbol="SPY",
            defaults={"name": "SPDR S&P 500 ETF", "currency": "USD"},
        )
        for bar in bars:
            OHLCV.objects.update_or_create(
                ticker=spy_ticker,
                timestamp=bar["timestamp"],
                interval=bar["interval"],
                defaults={k: v for k, v in bar.items() if k != "ticker"},
            )
    except Exception as e:
        print(f"Error fetching SPY benchmark: {e}")


@shared_task
def fetch_insider_trades():
    from data.connectors.sec_edgar import fetch_form4
    for ticker in Ticker.objects.filter(is_active=True):
        try:
            trades = fetch_form4(ticker)
            for trade in trades:
                InsiderTrade.objects.update_or_create(
                    ticker=ticker,
                    filing_date=trade["filing_date"],
                    insider_name=trade["insider_name"],
                    transaction_type=trade["transaction_type"],
                    defaults=trade,
                )
        except Exception as e:
            print(f"Error fetching Form 4 for {ticker.symbol}: {e}")


@shared_task
def fetch_13f_holdings():
    from data.connectors.sec_edgar import fetch_13f
    for ticker in Ticker.objects.filter(is_active=True):
        try:
            holdings = fetch_13f(ticker)
            for h in holdings:
                InstitutionalHolding.objects.update_or_create(
                    ticker=ticker,
                    filing_date=h["filing_date"],
                    filer_name=h["filer_name"],
                    defaults=h,
                )
        except Exception as e:
            print(f"Error fetching 13F for {ticker.symbol}: {e}")


@shared_task
def fetch_macro_indicators():
    from data.connectors.fred_connector import fetch_indicators
    series_ids = ["DGS10", "CPIAUCSL", "FEDFUNDS", "DGS2", "DGS30", "VIXCLS"]
    try:
        indicators = fetch_indicators(series_ids)
        for ind in indicators:
            MacroIndicator.objects.update_or_create(
                name=ind["name"],
                date=ind["date"],
                defaults={
                    "value": Decimal(str(ind["value"])) if ind.get("value") else None,
                    "source": "FRED",
                    "raw": ind,
                },
            )
    except Exception as e:
        print(f"Error fetching macro indicators: {e}")


@shared_task
def fetch_news():
    from data.connectors.finnhub_connector import fetch_news as fn_fetch
    from data.connectors.gdelt_connector import fetch_news as gdelt_fetch
    tickers = list(Ticker.objects.filter(is_active=True))
    try:
        articles = fn_fetch(tickers)
        for art in articles:
            NewsArticle.objects.update_or_create(
                url=art.get("url", ""),
                published_at=art.get("published_at"),
                defaults=art,
            )
    except Exception as e:
        print(f"Finnhub news error: {e}")
    try:
        articles = gdelt_fetch(tickers)
        for art in articles:
            NewsArticle.objects.update_or_create(
                url=art.get("url", ""),
                published_at=art.get("published_at"),
                defaults=art,
            )
    except Exception as e:
        print(f"GDELT news error: {e}")


@shared_task
def fetch_reddit_posts():
    from data.connectors.reddit_connector import fetch_posts
    subreddits = ["wallstreetbets", "stocks", "investing"]
    watchlist_tickers = list(Ticker.objects.filter(watchlists__is_active=True).distinct())
    try:
        posts = fetch_posts(subreddits, watchlist_tickers, limit=100)
        for post in posts:
            RedditPost.objects.update_or_create(
                post_id=post["post_id"],
                defaults=post,
            )
    except Exception as e:
        print(f"Reddit fetch error: {e}")