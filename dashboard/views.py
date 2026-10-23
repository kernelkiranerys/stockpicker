from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from tickers.models import Ticker, Watchlist
from data.models import OHLCV, MacroIndicator, NewsArticle, InsiderTrade, OptionsSnapshot
from signals.models import Signal, TechnicalIndicator
from sentiment.models import DailySentimentAggregate
from ai_expert.models import AIExpertReport


def market_overview(request):
    watchlist = Watchlist.objects.first()
    watchlist_tickers = watchlist.tickers.select_related("sector", "exchange").all() if watchlist else []
    return render(request, "dashboard/overview.html", {
        "watchlist_count": Watchlist.objects.count(),
        "ticker_count": Ticker.objects.filter(is_active=True).count(),
        "signal_count": Signal.objects.filter(is_active=True).count(),
        "ai_report_count": AIExpertReport.objects.count(),
        "macros": MacroIndicator.objects.all()[:10],
        "watchlist_tickers": watchlist_tickers,
    })


def watchlist(request):
    wl = Watchlist.objects.prefetch_related("tickers__sector", "tickers__exchange").first()
    if not wl:
        return render(request, "dashboard/watchlist.html", {"watchlist": None})
    tickers = list(wl.tickers.all())
    ticker_ids = [t.id for t in tickers]
    latest_signals = {}
    for sig in Signal.objects.filter(ticker_id__in=ticker_ids).order_by("ticker_id", "-created_at"):
        if sig.ticker_id not in latest_signals:
            latest_signals[sig.ticker_id] = sig
    latest_reports = {}
    for rep in AIExpertReport.objects.filter(ticker_id__in=ticker_ids).order_by("ticker_id", "-created_at"):
        if rep.ticker_id not in latest_reports:
            latest_reports[rep.ticker_id] = rep
    ticker_rows = []
    for t in tickers:
        ticker_rows.append({
            "ticker": t,
            "signal": latest_signals.get(t.id),
            "report": latest_reports.get(t.id),
        })
    return render(request, "dashboard/watchlist.html", {
        "watchlist": wl,
        "ticker_rows": ticker_rows,
    })


def industry_rotation(request):
    from tickers.models import Sector
    sectors = Sector.objects.all()
    sector_data = []
    for sector in sectors:
        tickers = Ticker.objects.filter(sector=sector, is_active=True)
        ticker_count = tickers.count()
        avg_change = 0
        for t in tickers[:20]:
            latest = OHLCV.objects.filter(ticker=t, interval="1d").order_by("-timestamp").first()
            prev = OHLCV.objects.filter(ticker=t, interval="1d").order_by("-timestamp")[1:2]
            if latest and prev:
                prev_close = float(prev[0].close)
                if prev_close > 0:
                    avg_change += (float(latest.close) - prev_close) / prev_close * 100
        if ticker_count > 0:
            avg_change /= min(ticker_count, 20)
        sector_data.append({
            "sector": sector,
            "ticker_count": ticker_count,
            "avg_change": round(avg_change, 2),
        })
    return render(request, "dashboard/rotation.html", {"sector_data": sector_data})