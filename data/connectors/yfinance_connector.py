import yfinance as yf
import pandas as pd
from decimal import Decimal
from datetime import datetime, timezone
from django.utils import timezone as djtz


def fetch_ohlcv(ticker, interval="1d", period="1y"):
    yf_ticker = yf.Ticker(ticker.yf_symbol)
    hist = yf_ticker.history(period=period, interval=interval)
    results = []
    for ts, row in hist.iterrows():
        if hasattr(ts, "to_pydatetime"):
            dt = ts.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = timezone.utc.localize(datetime.utcnow())
        results.append({
            "ticker": ticker,
            "timestamp": dt,
            "interval": interval,
            "open": Decimal(str(row.get("Open", 0))),
            "high": Decimal(str(row.get("High", 0))),
            "low": Decimal(str(row.get("Low", 0))),
            "close": Decimal(str(row.get("Close", 0))),
            "volume": int(row.get("Volume", 0)),
            "source": "yfinance",
        })
    return results


def fetch_intraday_ohlcv(ticker, interval="15m"):
    return fetch_ohlcv(ticker, interval=interval, period="5d")


def fetch_fundamentals(ticker):
    yf_ticker = yf.Ticker(ticker.yf_symbol)
    info = yf_ticker.info or {}
    return {
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "peg_ratio": info.get("pegRatio"),
        "ps_ratio": info.get("priceToSalesTrailing12Months"),
        "pb_ratio": info.get("priceToBook"),
        "debt_to_equity": info.get("debtToEquity"),
        "current_ratio": info.get("currentRatio"),
        "quick_ratio": info.get("quickRatio"),
        "revenue_growth": info.get("revenueGrowth"),
        "earnings_growth": info.get("earningsGrowth"),
        "profit_margin": info.get("profitMargins"),
        "free_cash_flow": info.get("freeCashflow"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "raw_info": info,
    }


def fetch_option_chain(ticker):
    yf_ticker = yf.Ticker(ticker.yf_symbol)
    expirations = yf_ticker.options
    if not expirations:
        return {}
    nearest = expirations[0]
    chain = yf_ticker.option_chain(nearest)
    calls = chain.calls
    puts = chain.puts

    call_volume = int(calls["volume"].sum()) if "volume" in calls else 0
    put_volume = int(puts["volume"].sum()) if "volume" in puts else 0
    call_oi = int(calls["openInterest"].sum()) if "openInterest" in calls else 0
    put_oi = int(puts["openInterest"].sum()) if "openInterest" in puts else 0
    pcr = put_volume / call_volume if call_volume > 0 else 0

    total_oi = call_oi + put_oi
    total_vol = call_volume + put_volume
    vol_oi = total_vol / total_oi if total_oi > 0 else 0

    iv_values = []
    if "impliedVolatility" in calls:
        iv_values.extend(calls["impliedVolatility"].dropna().tolist())
    if "impliedVolatility" in puts:
        iv_values.extend(puts["impliedVolatility"].dropna().tolist())
    avg_iv = sum(iv_values) / len(iv_values) if iv_values else 0

    unusual = vol_oi > 2.0 or any(
        (row.get("volume", 0) > 3 * row.get("openInterest", 1))
        for _, row in calls.iterrows()
    ) or any(
        (row.get("volume", 0) > 3 * row.get("openInterest", 1))
        for _, row in puts.iterrows()
    )

    return {
        "expiry": nearest,
        "call_volume": call_volume,
        "put_volume": put_volume,
        "call_open_interest": call_oi,
        "put_open_interest": put_oi,
        "put_call_ratio": Decimal(str(round(pcr, 4))),
        "vol_oi_ratio": Decimal(str(round(vol_oi, 4))),
        "implied_volatility": Decimal(str(round(avg_iv, 4))),
        "unusual_activity": unusual,
        "calls_raw": calls.to_dict("records") if not calls.empty else [],
        "puts_raw": puts.to_dict("records") if not puts.empty else [],
    }


def fetch_benchmark(benchmark_symbol="SPY", interval="1d", period="1y"):
    class FakeTicker:
        yf_symbol = benchmark_symbol
    return fetch_ohlcv(FakeTicker(), interval=interval, period=period)


def fetch_current_price(ticker):
    yf_ticker = yf.Ticker(ticker.yf_symbol)
    hist = yf_ticker.history(period="1d", interval="1m")
    if hist.empty:
        hist = yf_ticker.history(period="5d", interval="15m")
    if hist.empty:
        return None
    latest = hist.iloc[-1]
    return Decimal(str(latest.get("Close", 0)))


def fetch_intraday_bars(ticker, interval="1m", period="1d"):
    """Fetch 1-min or 5-min intraday bars for VWAP calculation.
    interval: '1m' or '5m'
    period: '1d' (single day) or '5d' (for multi-day VWAP)
    Returns list of bar dicts with timestamp, open, high, low, close, volume.
    """
    yf_ticker = yf.Ticker(ticker.yf_symbol)
    hist = yf_ticker.history(period=period, interval=interval)
    bars = []
    for ts, row in hist.iterrows():
        if hasattr(ts, "to_pydatetime"):
            dt = ts.to_pydatetime()
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = timezone.utc.localize(datetime.utcnow())
        bars.append({
            "timestamp": dt,
            "open": float(row.get("Open", 0)),
            "high": float(row.get("High", 0)),
            "low": float(row.get("Low", 0)),
            "close": float(row.get("Close", 0)),
            "volume": int(row.get("Volume", 0)),
        })
    return bars


def compute_vwap(bars):
    """Compute VWAP from a list of intraday bar dicts.
    Returns (vwap_value, bars_with_vwap) where each bar has a cumulative vwap.
    """
    if not bars:
        return 0, []

    cumulative_pv = 0.0
    cumulative_vol = 0
    bars_with_vwap = []

    for bar in bars:
        typical_price = (bar["high"] + bar["low"] + bar["close"]) / 3
        pv = typical_price * bar["volume"]
        cumulative_pv += pv
        cumulative_vol += bar["volume"]
        vwap = cumulative_pv / cumulative_vol if cumulative_vol > 0 else bar["close"]
        bar["vwap"] = round(vwap, 6)
        bars_with_vwap.append(bar)

    current_vwap = bars_with_vwap[-1]["vwap"] if bars_with_vwap else 0
    return current_vwap, bars_with_vwap


def compute_anchored_vwap(bars, anchor_index=0):
    """Compute anchored VWAP from a specific bar index.
    anchor_index: 0 = session open, or any other bar index for event-anchored.
    """
    if not bars or anchor_index >= len(bars):
        return 0, []

    anchored_bars = bars[anchor_index:]
    return compute_vwap(anchored_bars)