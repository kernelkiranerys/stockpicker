from decimal import Decimal
from datetime import datetime, timezone
from django.utils import timezone as djtz
from django.conf import settings

from tickers.models import Ticker
from data.models import OHLCV
from signals.models import Signal, TechnicalIndicator
from signals.engine_technical import compute_technicals, interpret_signals
from signals.engine_sentiment import score_sentiment_trend
from signals.engine_options import detect_unusual_activity
from signals.engine_insider import score_insider_flow
from signals.engine_seasonal import score_seasonal


WEIGHTS = {
    "day_trade": {
        "technical": 0.40,
        "sentiment": 0.20,
        "options": 0.25,
        "insider": 0.05,
        "seasonal": 0.10,
    },
    "medium_turnaround": {
        "technical": 0.35,
        "sentiment": 0.30,
        "options": 0.15,
        "insider": 0.10,
        "seasonal": 0.10,
    },
    "seasonal_swing": {
        "technical": 0.20,
        "sentiment": 0.25,
        "options": 0.10,
        "insider": 0.20,
        "seasonal": 0.25,
    },
}


def generate_signal(ticker, signal_type):
    """Generate a composite signal for a ticker.
    Returns a Signal object or None if insufficient data / below threshold.
    """
    weights = WEIGHTS.get(signal_type, WEIGHTS["medium_turnaround"])

    ohlcv_qs = OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:250]

    tech_data = compute_technicals(ohlcv_qs)
    if tech_data:
        tech_interp = interpret_signals(tech_data)
        tech_score = tech_interp["score"]
        tech_signals = tech_interp["signals"]

        TechnicalIndicator.objects.create(
            ticker=ticker,
            rsi_14=tech_data.get("rsi_14"),
            macd=tech_data.get("macd"),
            macd_signal=tech_data.get("macd_signal"),
            macd_histogram=tech_data.get("macd_histogram"),
            ema_9=tech_data.get("ema_9"),
            ema_21=tech_data.get("ema_21"),
            ema_50=tech_data.get("ema_50"),
            ema_200=tech_data.get("ema_200"),
            bollinger_upper=tech_data.get("bollinger_upper"),
            bollinger_lower=tech_data.get("bollinger_lower"),
            bollinger_mid=tech_data.get("bollinger_mid"),
            adx=tech_data.get("adx"),
            atr=tech_data.get("atr"),
            volume_sma_20=tech_data.get("volume_sma_20"),
        )
    else:
        tech_score = 0
        tech_signals = ["Insufficient data for technical analysis"]

    sent_result = score_sentiment_trend(ticker)
    sent_score = sent_result["score"]

    opt_result = detect_unusual_activity(ticker)
    opt_score = opt_result["score"]

    insider_result = score_insider_flow(ticker)
    insider_score = insider_result["score"]

    seasonal_result = score_seasonal(ticker)
    seasonal_score = seasonal_result["score"]

    composite_score = (
        tech_score * weights["technical"] +
        sent_score * weights["sentiment"] +
        opt_score * weights["options"] +
        insider_score * weights["insider"] +
        seasonal_score * weights["seasonal"]
    )

    confidence = min(1.0, abs(composite_score) * 1.5)
    threshold = settings.SIGNAL_CONFIDENCE_THRESHOLD

    if confidence < threshold:
        return None

    if composite_score > 0.3:
        action = Signal.ACTION_BUY
    elif composite_score > 0.1:
        action = Signal.ACTION_HOLD
    elif composite_score < -0.3:
        action = Signal.ACTION_SELL
    elif composite_score < -0.1:
        action = Signal.ACTION_TRIM
    else:
        action = Signal.ACTION_HOLD

    latest_price = float(ticker.last_price) if ticker.last_price else None
    entry_price = Decimal(str(latest_price)) if latest_price else None
    target_price = None
    stop_loss = None
    if latest_price and tech_data:
        atr_val = float(tech_data.get("atr") or 0)
        if atr_val > 0:
            if action in (Signal.ACTION_BUY,):
                target_price = Decimal(str(round(latest_price + 2 * atr_val, 6)))
                stop_loss = Decimal(str(round(latest_price - 1.5 * atr_val, 6)))
            elif action == Signal.ACTION_SELL:
                target_price = Decimal(str(round(latest_price - 2 * atr_val, 6)))

    all_signals = tech_signals + sent_result["signals"] + opt_result["signals"] + insider_result["signals"] + seasonal_result["signals"]
    reasoning = " | ".join(all_signals[:10])

    signal = Signal.objects.create(
        ticker=ticker,
        signal_type=signal_type,
        action=action,
        confidence=Decimal(str(round(confidence, 4))),
        entry_price=entry_price,
        target_price=target_price,
        stop_loss=stop_loss,
        reasoning=reasoning,
        technical_score=Decimal(str(round(tech_score, 4))),
        sentiment_score=Decimal(str(round(sent_score, 4))),
        options_score=Decimal(str(round(opt_score, 4))),
        insider_score=Decimal(str(round(insider_score, 4))),
        seasonal_score=Decimal(str(round(seasonal_score, 4))),
        is_active=True,
    )

    _publish_signal(signal)

    return signal


def _publish_signal(signal):
    """Publish signal to the sandbox autotrader via Celery."""
    try:
        from sandbox.tasks import execute_signal_trade
        execute_signal_trade.delay(signal.id)
    except Exception:
        pass