from feedback.models import LessonLearned, TradeReview
from ai_expert.ollama_client import chat
from signals.models import Signal
from data.models import OHLCV
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone as djtz
import json


def review_failed_trades(lookback_days=7):
    """Weekly: Review failed trades and extract lessons via LLM reflection.

    For each failed trade:
    1. Fetch the context the LLM used at the time
    2. Ask the LLM: "This trade failed. Here is the context you used. What did you miss?"
    3. Store the reflection as a LessonLearned
    4. These lessons will be injected into future prompts
    """
    cutoff = djtz.now() - timedelta(days=lookback_days)

    recent_signals = Signal.objects.filter(
        created_at__gte=cutoff,
        action__in=["BUY", "SELL", "TRIM"],
    ).order_by("-created_at")[:50]

    lessons_created = 0

    for signal in recent_signals:
        entry = float(signal.entry_price) if signal.entry_price else 0
        if entry <= 0:
            continue

        bars_after = list(OHLCV.objects.filter(
            ticker=signal.ticker, interval="1d",
            timestamp__gte=signal.created_at,
        ).order_by("timestamp")[:14])

        if not bars_after:
            continue

        exit_price = float(bars_after[-1].close)
        pnl_pct = (exit_price - entry) / entry * 100

        if signal.action == "BUY":
            is_win = pnl_pct > 0
        elif signal.action in ("SELL", "TRIM"):
            is_win = pnl_pct < 0
        else:
            continue

        if is_win:
            continue

        context = _build_context_for_review(signal)
        reflection = _ask_llm_for_reflection(signal, context, pnl_pct)

        if reflection:
            lesson = LessonLearned.objects.create(
                lesson=reflection.get("lesson", "")[:500],
                context=context[:2000],
                ticker_symbol=signal.ticker.symbol,
                signal_type=signal.signal_type,
                trade_date=signal.created_at.date(),
                pnl_pct=Decimal(str(round(pnl_pct, 4))),
                llm_reflection=reflection.get("full_analysis", ""),
            )

            TradeReview.objects.create(
                signal_id=signal.id,
                ticker_symbol=signal.ticker.symbol,
                action=signal.action,
                entry_price=signal.entry_price,
                exit_price=Decimal(str(round(exit_price, 6))),
                pnl_pct=Decimal(str(round(pnl_pct, 4))),
                outcome="loss",
                context_snapshot=context,
                llm_analysis=reflection.get("full_analysis", ""),
                lesson=lesson,
            )

            lessons_created += 1

    return lessons_created


def get_active_lessons(limit=10):
    """Get active lessons to inject into AI expert prompts."""
    return list(LessonLearned.objects.filter(is_active=True).order_by("-created_at")[:limit])


def _build_context_for_review(signal):
    """Rebuild the context that was available at signal creation time."""
    parts = [
        f"Signal: {signal.action} {signal.ticker.symbol}",
        f"Type: {signal.signal_type}",
        f"Confidence: {signal.confidence}",
        f"Entry Price: {signal.entry_price}",
        f"Technical Score: {signal.technical_score}",
        f"Sentiment Score: {signal.sentiment_score}",
        f"Options Score: {signal.options_score}",
        f"Insider Score: {signal.insider_score}",
        f"Seasonal Score: {signal.seasonal_score}",
        f"Reasoning: {signal.reasoning}",
    ]
    return "\n".join(parts)


def _ask_llm_for_reflection(signal, context, pnl_pct):
    """Ask the LLM to reflect on why a trade failed."""
    prompt = f"""A trade was taken that resulted in a LOSS of {pnl_pct:.2f}%.

Here is the context that was available when the signal was generated:

{context}

Analyze why this trade failed. Consider:
1. What signal was misleading or weak?
2. What data point was missing from the analysis?
3. What macro or regime factor was not considered?
4. Was the timing wrong?

Return JSON: {{"lesson": "<one-sentence lesson>", "full_analysis": "<detailed analysis>"}}"""

    model = settings.OLLAMA_MODEL_FAST
    raw = chat(model, "You are a trading analyst reviewing failed trades for learning purposes.", prompt, temperature=0.3, num_predict=400)

    try:
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except (json.JSONDecodeError, ValueError):
        pass
    return {"lesson": raw[:500], "full_analysis": raw}