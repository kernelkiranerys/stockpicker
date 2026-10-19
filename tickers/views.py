from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from tickers.models import Ticker
from data.models import OHLCV, NewsArticle, InsiderTrade, OptionsSnapshot
from signals.models import Signal, TechnicalIndicator
from sentiment.models import DailySentimentAggregate
from ai_expert.models import AIExpertReport


def ticker_list(request):
    tickers = Ticker.objects.filter(is_active=True).select_related("sector", "exchange").order_by("symbol")
    paginator = Paginator(tickers, 50)
    page = request.GET.get("page", 1)
    page_obj = paginator.get_page(page)
    return render(request, "tickers/list.html", {"page_obj": page_obj})


def ticker_detail(request, symbol):
    ticker = get_object_or_404(Ticker, symbol=symbol)
    ohlcv = list(OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:200])
    ohlcv.reverse()
    latest_signal = Signal.objects.filter(ticker=ticker).order_by("-created_at").first()
    latest_report = AIExpertReport.objects.filter(ticker=ticker).order_by("-created_at").first()
    latest_technical = TechnicalIndicator.objects.filter(ticker=ticker).order_by("-timestamp").first()
    news = NewsArticle.objects.filter(ticker=ticker).order_by("-published_at")[:10]
    insiders = InsiderTrade.objects.filter(ticker=ticker).order_by("-filing_date")[:10]
    options = OptionsSnapshot.objects.filter(ticker=ticker).order_by("-timestamp").first()
    sentiment_timeline = DailySentimentAggregate.objects.filter(ticker=ticker).order_by("-date")[:30]
    sentiment_timeline = list(reversed(sentiment_timeline))
    return render(request, "tickers/detail.html", {
        "ticker": ticker,
        "ohlcv": ohlcv,
        "latest_signal": latest_signal,
        "latest_report": latest_report,
        "latest_technical": latest_technical,
        "news": news,
        "insiders": insiders,
        "options": options,
        "sentiment_timeline": sentiment_timeline,
    })


def ticker_refresh(request, symbol):
    ticker = get_object_or_404(Ticker, symbol=symbol)
    from data.connectors.yfinance_connector import fetch_current_price
    try:
        price = fetch_current_price(ticker)
        if price:
            from django.utils import timezone
            ticker.last_price = price
            ticker.last_price_updated = timezone.now()
            ticker.save(update_fields=["last_price", "last_price_updated"])
    except Exception:
        pass
    latest_signal = Signal.objects.filter(ticker=ticker).order_by("-created_at").first()
    return render(request, "tickers/_price_card.html", {
        "ticker": ticker,
        "latest_signal": latest_signal,
    })