import pandas as pd
import numpy as np
from decimal import Decimal
from datetime import datetime, timezone

try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False


def compute_technicals(ohlcv_qs):
    df = pd.DataFrame([
        {
            "timestamp": bar.timestamp,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": int(bar.volume),
        }
        for bar in ohlcv_qs
    ])
    if df.empty or len(df) < 30:
        return None

    df = df.sort_values("timestamp").reset_index(drop=True)
    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    result = {}

    result["ema_9"] = close.ewm(span=9, adjust=False).mean().iloc[-1]
    result["ema_21"] = close.ewm(span=21, adjust=False).mean().iloc[-1]
    result["ema_50"] = close.ewm(span=50, adjust=False).mean().iloc[-1]
    result["ema_200"] = close.ewm(span=200, adjust=False).mean().iloc[-1] if len(close) >= 200 else None

    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    result["rsi_14"] = (100 - (100 / (1 + rs))).iloc[-1]

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    macd = ema_12 - ema_26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    result["macd"] = macd.iloc[-1]
    result["macd_signal"] = macd_signal.iloc[-1]
    result["macd_histogram"] = (macd - macd_signal).iloc[-1]

    sma_20 = close.rolling(window=20).mean()
    std_20 = close.rolling(window=20).std()
    result["bollinger_mid"] = sma_20.iloc[-1]
    result["bollinger_upper"] = (sma_20 + 2 * std_20).iloc[-1]
    result["bollinger_lower"] = (sma_20 - 2 * std_20).iloc[-1]

    if HAS_TA:
        adx_indicator = ta.trend.ADXIndicator(high=high, low=low, close=close, window=14)
        result["adx"] = adx_indicator.adx().iloc[-1]
        atr_indicator = ta.volatility.AverageTrueRange(high=high, low=low, close=close, window=14)
        result["atr"] = atr_indicator.average_true_range().iloc[-1]
    else:
        result["adx"] = _compute_adx(high, low, close)
        result["atr"] = _compute_atr(high, low, close)

    result["volume_sma_20"] = volume.rolling(window=20).mean().iloc[-1]

    return {k: (Decimal(str(round(v, 6))) if v is not None and not (isinstance(v, float) and np.isnan(v)) else None) for k, v in result.items()}


def _compute_adx(high, low, close, period=14):
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr.replace(0, np.nan))
    dx = 100 * ((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.rolling(window=period).mean()
    return adx.iloc[-1]


def _compute_atr(high, low, close, period=14):
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(window=period).mean().iloc[-1]


def interpret_signals(technicals):
    if not technicals:
        return {"score": 0, "signals": []}

    score = 0
    signals = []
    rsi = float(technicals.get("rsi_14") or 0)
    ema_9 = float(technicals.get("ema_9") or 0)
    ema_21 = float(technicals.get("ema_21") or 0)
    ema_50 = float(technicals.get("ema_50") or 0)
    ema_200 = float(technicals.get("ema_200") or 0)
    macd = float(technicals.get("macd") or 0)
    macd_signal = float(technicals.get("macd_signal") or 0)
    adx = float(technicals.get("adx") or 0)

    if ema_9 > ema_21:
        score += 1
        signals.append("EMA9 > EMA21 (short-term bullish)")
    else:
        score -= 1
        signals.append("EMA9 < EMA21 (short-term bearish)")

    if ema_21 > ema_50:
        score += 1
        signals.append("EMA21 > EMA50 (medium bullish)")
    else:
        score -= 1
        signals.append("EMA21 < EMA50 (medium bearish)")

    if ema_200 and ema_50 > ema_200:
        score += 1
        signals.append("EMA50 > EMA200 (long-term bullish)")
    elif ema_200:
        score -= 1
        signals.append("EMA50 < EMA200 (long-term bearish)")

    if macd > macd_signal:
        score += 1
        signals.append("MACD > signal (bullish crossover)")
    else:
        score -= 1
        signals.append("MACD < signal (bearish crossover)")

    if rsi < 30:
        score += 1
        signals.append("RSI oversold (<30)")
    elif rsi > 70:
        score -= 1
        signals.append("RSI overbought (>70)")
    else:
        signals.append(f"RSI neutral ({rsi:.1f})")

    if adx > 25:
        signals.append(f"ADX={adx:.1f} (strong trend)")

    normalized = max(-5, min(5, score)) / 5.0
    return {"score": normalized, "signals": signals}