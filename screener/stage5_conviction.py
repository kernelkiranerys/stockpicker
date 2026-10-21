from tickers.models import Ticker
from screener.models import ScreenedUniverse
from ai_expert.ollama_client import chat
from ai_expert.prompt_templates import SYSTEM_PROMPT
from django.conf import settings
from decimal import Decimal
import json
from django.utils import timezone as djtz


def run_conviction_scoring(tickers):
    """Stage 5: LLM conviction scoring 0-100 for each candidate.
    Only candidates with score > threshold (default 75) proceed to execution.

    Updates ScreenedUniverse records with conviction scores.
    Returns list of high-conviction candidates.
    """
    threshold = settings.CONVICTION_THRESHOLD
    today = djtz.now().date()
    high_conviction = []

    for ticker in tickers:
        prompt = _build_conviction_prompt(ticker)
        model = settings.OLLAMA_MODEL_FAST
        raw = chat(model, SYSTEM_PROMPT, prompt, temperature=0.2, num_predict=300)

        conviction = _parse_conviction(raw)

        try:
            result = ScreenedUniverse.objects.get(ticker=ticker, screen_date=today)
        except ScreenedUniverse.DoesNotExist:
            result = ScreenedUniverse.objects.create(ticker=ticker, screen_date=today)

        result.conviction_score = conviction
        result.save()

        if conviction >= threshold:
            high_conviction.append((ticker, conviction))

    high_conviction.sort(key=lambda x: x[1], reverse=True)
    for rank, (ticker, conviction) in enumerate(high_conviction, 1):
        result = ScreenedUniverse.objects.get(ticker=ticker, screen_date=today)
        result.rank = rank
        result.save()

    return high_conviction


def _build_conviction_prompt(ticker):
    """Build a prompt for LLM conviction scoring."""
    from data.models import OHLCV, Fundamental, NewsArticle
    from signals.models import TechnicalIndicator, Signal
    from sentiment.models import DailySentimentAggregate

    parts = [f"Stock: {ticker.symbol} ({ticker.name})"]
    parts.append(f"Sector: {ticker.sector.name if ticker.sector else 'Unknown'}")
    parts.append(f"Current Price: {ticker.last_price}")
    parts.append("")

    tech = TechnicalIndicator.objects.filter(ticker=ticker).order_by("-timestamp").first()
    if tech:
        parts.append(f"RSI: {tech.rsi_14}")
        parts.append(f"MACD: {tech.macd} (signal: {tech.macd_signal})")
        parts.append(f"EMA9: {tech.ema_9}, EMA21: {tech.ema_21}, EMA50: {tech.ema_50}")

    fund = Fundamental.objects.filter(ticker=ticker).order_by("-date").first()
    if fund:
        parts.append(f"P/E: {fund.pe_ratio}")
        parts.append(f"Revenue Growth: {fund.revenue_growth}")
        parts.append(f"Dividend Yield: {fund.dividend_yield}")

    sent = DailySentimentAggregate.objects.filter(ticker=ticker).order_by("-date").first()
    if sent:
        parts.append(f"Sentiment Composite: {sent.composite}")

    news = NewsArticle.objects.filter(ticker=ticker).order_by("-published_at")[:3]
    if news:
        parts.append("Recent News:")
        for a in news:
            parts.append(f"  - {a.headline[:100]}")

    parts.append("")
    parts.append("Based on this data, what is your conviction score (0-100) for a BUY signal?")
    parts.append("Return ONLY a JSON: {\"conviction\": <0-100>, \"reasoning\": \"...\"}")

    return "\n".join(parts)


def _parse_conviction(raw):
    """Parse conviction score from LLM output."""
    if not raw:
        return 0
    try:
        import re
        match = re.search(r'\{[^}]*"conviction"[^}]*\}', raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            score = int(data.get("conviction", 0))
            return max(0, min(100, score))
    except (json.JSONDecodeError, ValueError, KeyError):
        pass
    try:
        import re
        numbers = re.findall(r'\b(\d{1,3})\b', raw)
        if numbers:
            return max(0, min(100, int(numbers[0])))
    except Exception:
        pass
    return 0