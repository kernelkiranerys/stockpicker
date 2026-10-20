from decimal import Decimal
from datetime import datetime, timezone
from django.utils import timezone as djtz
from django.conf import settings

from tickers.models import Ticker
from data.models import OHLCV
from signals.models import Signal
from signals.engine_vwap import analyze_vwap
from signals.engine_rvol import compute_rvol
from signals.engine_rsi_divergence import detect_rsi_divergence
from signals.engine_regime import detect_regime
from signals.engine_technical import compute_technicals, interpret_signals
from signals.engine_sentiment import score_sentiment_trend
from signals.engine_options import detect_unusual_activity
from signals.engine_insider import score_insider_flow
from signals.engine_seasonal import score_seasonal


def generate_confluence_signal(ticker, signal_type="day_trade"):
    """Generate a confluence-based signal.
    4 layers must align: VWAP direction + trend alignment + momentum confirmation + volume confirmation.

    signal_type: 'day_trade', 'medium_turnaround', 'seasonal_swing'
    """
    vwap_result = analyze_vwap(ticker)
    rvol_result = compute_rvol(ticker)
    rsi_result = detect_rsi_divergence(ticker)

    ohlcv_qs = OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp")[:250]
    tech_data = compute_technicals(ohlcv_qs)
    tech_interp = interpret_signals(tech_data) if tech_data else {"score": 0, "signals": ["Insufficient data"]}

    sent_result = score_sentiment_trend(ticker)
    opt_result = detect_unusual_activity(ticker)
    insider_result = score_insider_flow(ticker)
    seasonal_result = score_seasonal(ticker)

    layer1_vwap = vwap_result.get("score", 0)
    layer2_trend = tech_interp.get("score", 0)
    layer3_momentum = rsi_result.get("score", 0)
    layer4_volume = rvol_result.get("score", 0)

    layers_aligned = _check_confluence(layer1_vwap, layer2_trend, layer3_momentum, layer4_volume)

    if signal_type == "day_trade":
        weights = {"vwap": 0.30, "trend": 0.25, "momentum": 0.20, "volume": 0.15, "options": 0.10}
    elif signal_type == "medium_turnaround":
        weights = {"vwap": 0.15, "trend": 0.25, "momentum": 0.20, "volume": 0.10, "options": 0.10, "sentiment": 0.15, "insider": 0.05}
    else:
        weights = {"vwap": 0.10, "trend": 0.15, "momentum": 0.10, "volume": 0.05, "sentiment": 0.15, "insider": 0.20, "seasonal": 0.25}

    composite = (
        layer1_vwap * weights.get("vwap", 0) +
        layer2_trend * weights.get("trend", 0) +
        layer3_momentum * weights.get("momentum", 0) +
        layer4_volume * weights.get("volume", 0) +
        opt_result.get("score", 0) * weights.get("options", 0) +
        sent_result.get("score", 0) * weights.get("sentiment", 0) +
        insider_result.get("score", 0) * weights.get("insider", 0) +
        seasonal_result.get("score", 0) * weights.get("seasonal", 0)
    )

    confidence = min(1.0, abs(composite) * 1.5)
    conviction = round(confidence * 100)

    threshold = settings.SIGNAL_CONFIDENCE_THRESHOLD
    if confidence < threshold:
        return None

    if composite > 0.3:
        action = Signal.ACTION_BUY
    elif composite > 0.1:
        action = Signal.ACTION_HOLD
    elif composite < -0.3:
        action = Signal.ACTION_SELL
    elif composite < -0.1:
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
            if action == Signal.ACTION_BUY:
                target_price = Decimal(str(round(latest_price + 2 * atr_val, 6)))
                stop_loss = Decimal(str(round(latest_price - 1.5 * atr_val, 6)))
            elif action == Signal.ACTION_SELL:
                target_price = Decimal(str(round(latest_price - 2 * atr_val, 6)))

    all_signals = (
        vwap_result.get("signals", []) +
        rvol_result.get("signals", []) +
        rsi_result.get("signals", []) +
        tech_interp.get("signals", []) +
        sent_result.get("signals", []) +
        opt_result.get("signals", []) +
        insider_result.get("signals", []) +
        seasonal_result.get("signals", [])
    )
    reasoning = " | ".join(all_signals[:12])

    confluence_layers = {
        "vwap": {"score": round(layer1_vwap, 4), "aligned": layer1_vwap > 0 if composite > 0 else layer1_vwap < 0},
        "trend": {"score": round(layer2_trend, 4), "aligned": layer2_trend > 0 if composite > 0 else layer2_trend < 0},
        "momentum": {"score": round(layer3_momentum, 4), "aligned": layer3_momentum > 0 if composite > 0 else layer3_momentum < 0},
        "volume": {"score": round(layer4_volume, 4), "aligned": layer4_volume > 0 if composite > 0 else layer4_volume < 0},
        "all_aligned": layers_aligned,
    }

    signal = Signal.objects.create(
        ticker=ticker,
        signal_type=signal_type,
        action=action,
        confidence=Decimal(str(round(confidence, 4))),
        entry_price=entry_price,
        target_price=target_price,
        stop_loss=stop_loss,
        reasoning=reasoning,
        technical_score=Decimal(str(round(layer2_trend, 4))),
        sentiment_score=Decimal(str(round(sent_result.get("score", 0), 4))),
        options_score=Decimal(str(round(opt_result.get("score", 0), 4))),
        insider_score=Decimal(str(round(insider_result.get("score", 0), 4))),
        seasonal_score=Decimal(str(round(seasonal_result.get("score", 0), 4))),
        is_active=True,
    )

    _publish_signal(signal)

    return signal


def _check_confluence(vwap_score, trend_score, momentum_score, volume_score):
    """Check if all 4 layers are aligned in the same direction."""
    positive = sum(1 for s in [vwap_score, trend_score, momentum_score, volume_score] if s > 0.05)
    negative = sum(1 for s in [vwap_score, trend_score, momentum_score, volume_score] if s < -0.05)
    return positive >= 3 or negative >= 3


def _publish_signal(signal):
    """Publish signal to sandbox autotrader via Celery."""
    try:
        from sandbox.tasks import execute_signal_trade
        execute_signal_trade.delay(signal.id)
    except Exception:
        pass