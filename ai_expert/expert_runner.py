from decimal import Decimal
from datetime import datetime, timezone
from django.utils import timezone as djtz
from django.conf import settings

from tickers.models import Ticker
from data.models import OHLCV, Fundamental, NewsArticle, InsiderTrade, OptionsSnapshot
from signals.models import TechnicalIndicator, Signal
from sentiment.models import DailySentimentAggregate
from ai_expert.models import AIExpertReport
from ai_expert.ollama_client import chat
from ai_expert.prompt_templates import SYSTEM_PROMPT, build_user_prompt
from ai_expert.output_parser import parse_expert_output


def run_expert(ticker, signal_type, model=None):
    """Run the AI expert pipeline for a single ticker.
    Gathers data → RAG retrieval → prompt → LLM → parse → store.
    Returns AIExpertReport instance.
    """
    if model is None:
        model = settings.OLLAMA_MODEL_FAST

    data_snapshot = _gather_data(ticker)
    knowledge_chunks = _retrieve_knowledge(signal_type, data_snapshot)

    lessons_context = ""
    try:
        from feedback.prompt_injector import build_lessons_context
        lessons_context = build_lessons_context(limit=10)
    except Exception:
        pass

    prompt = build_user_prompt(ticker, signal_type, data_snapshot, knowledge_chunks, lessons_context)

    is_deep = "14b" in model
    num_predict = 1200 if is_deep else 600
    raw_output = chat(model, SYSTEM_PROMPT, prompt, temperature=0.3, num_predict=num_predict)

    parsed = parse_expert_output(raw_output)

    report = AIExpertReport.objects.create(
        ticker=ticker,
        report_type="deep" if is_deep else "fast",
        signal_type=signal_type,
        summary=parsed["summary"],
        sentiment_score=Decimal(str(parsed["sentiment_score"])),
        sentiment_reasoning=parsed["sentiment_reasoning"],
        action=parsed["action"],
        action_reasoning=parsed["action_reasoning"],
        confidence=Decimal(str(parsed["confidence"])),
        key_risks=parsed["key_risks"],
        cited_chunks=parsed["cited_knowledge"],
        data_snapshot=data_snapshot,
        model_name=model,
    )

    from sentiment.models import SentimentScore
    SentimentScore.objects.create(
        ticker=ticker,
        source="ai_expert",
        score=Decimal(str(parsed["sentiment_score"])),
        confidence=Decimal(str(parsed["confidence"])),
        timestamp=djtz.now(),
        raw_text=parsed["summary"][:500],
        raw_meta={"report_id": report.id, "action": parsed["action"]},
    )

    return report


def _gather_data(ticker):
    """Gather all available data for a ticker into a snapshot dict."""
    snapshot = {}

    latest_ohlcv = OHLCV.objects.filter(ticker=ticker, interval="1d").order_by("-timestamp").first()
    if latest_ohlcv:
        snapshot["price"] = {
            "close": float(latest_ohlcv.close),
            "volume": int(latest_ohlcv.volume),
            "timestamp": latest_ohlcv.timestamp.isoformat(),
        }

    tech = TechnicalIndicator.objects.filter(ticker=ticker).order_by("-timestamp").first()
    if tech:
        snapshot["technical"] = {
            "rsi_14": float(tech.rsi_14) if tech.rsi_14 else None,
            "macd": float(tech.macd) if tech.macd else None,
            "macd_signal": float(tech.macd_signal) if tech.macd_signal else None,
            "ema_9": float(tech.ema_9) if tech.ema_9 else None,
            "ema_21": float(tech.ema_21) if tech.ema_21 else None,
            "ema_50": float(tech.ema_50) if tech.ema_50 else None,
            "ema_200": float(tech.ema_200) if tech.ema_200 else None,
            "adx": float(tech.adx) if tech.adx else None,
            "atr": float(tech.atr) if tech.atr else None,
        }

    fundamental = Fundamental.objects.filter(ticker=ticker).order_by("-date").first()
    if fundamental:
        snapshot["fundamental"] = {
            "pe_ratio": float(fundamental.pe_ratio) if fundamental.pe_ratio else None,
            "peg_ratio": float(fundamental.peg_ratio) if fundamental.peg_ratio else None,
            "market_cap": float(fundamental.market_cap) if fundamental.market_cap else None,
            "debt_to_equity": float(fundamental.debt_to_equity) if fundamental.debt_to_equity else None,
            "revenue_growth": float(fundamental.revenue_growth) if fundamental.revenue_growth else None,
            "dividend_yield": float(fundamental.dividend_yield) if fundamental.dividend_yield else None,
        }

    sentiment = DailySentimentAggregate.objects.filter(ticker=ticker).order_by("-date").first()
    if sentiment:
        snapshot["sentiment"] = {
            "composite": float(sentiment.composite),
            "news": float(sentiment.news_sentiment),
            "reddit": float(sentiment.reddit_sentiment),
            "mention_volume": sentiment.mention_volume,
        }

    options = OptionsSnapshot.objects.filter(ticker=ticker).order_by("-timestamp").first()
    if options:
        snapshot["options"] = {
            "put_call_ratio": float(options.put_call_ratio) if options.put_call_ratio else None,
            "vol_oi_ratio": float(options.vol_oi_ratio) if options.vol_oi_ratio else None,
            "implied_volatility": float(options.implied_volatility) if options.implied_volatility else None,
            "unusual_activity": options.unusual_activity,
            "expiry": options.expiry.isoformat(),
        }

    insiders = InsiderTrade.objects.filter(ticker=ticker).order_by("-filing_date")[:5]
    if insiders:
        snapshot["insider_trades"] = [
            {
                "insider": t.insider_name,
                "type": t.transaction_type,
                "shares": float(t.shares),
                "date": t.filing_date.isoformat(),
            }
            for t in insiders
        ]

    news = NewsArticle.objects.filter(ticker=ticker).order_by("-published_at")[:5]
    if news:
        snapshot["recent_news"] = [
            {"headline": a.headline, "source": a.source, "date": a.published_at.isoformat()}
            for a in news
        ]

    latest_signal = Signal.objects.filter(ticker=ticker).order_by("-created_at").first()
    if latest_signal:
        snapshot["latest_signal"] = {
            "action": latest_signal.action,
            "confidence": float(latest_signal.confidence),
            "conviction": round(float(latest_signal.confidence) * 100),
            "signal_type": latest_signal.signal_type,
            "reasoning": latest_signal.reasoning[:200],
        }

    try:
        from signals.engine_vwap import analyze_vwap
        from signals.engine_rvol import compute_rvol
        from signals.engine_rsi_divergence import detect_rsi_divergence
        vwap = analyze_vwap(ticker)
        snapshot["vwap"] = {
            "vwap": vwap.get("vwap"),
            "position": vwap.get("position"),
            "distance_pct": vwap.get("distance_pct"),
            "slope": vwap.get("slope"),
            "signals": vwap.get("signals", []),
        }
        rvol = compute_rvol(ticker)
        snapshot["rvol"] = {
            "rvol": rvol.get("rvol"),
            "trend": rvol.get("volume_trend"),
            "signals": rvol.get("signals", []),
        }
        rsi_div = detect_rsi_divergence(ticker)
        snapshot["rsi_divergence"] = {
            "divergence": rsi_div.get("divergence"),
            "trend": rsi_div.get("trend"),
            "current_rsi": rsi_div.get("current_rsi"),
            "thresholds": rsi_div.get("thresholds"),
            "signals": rsi_div.get("signals", []),
        }
    except Exception:
        pass

    try:
        from signals.engine_regime import detect_regime
        regime = detect_regime()
        snapshot["market_regime"] = {
            "regime": regime.get("regime"),
            "strategy_mode": regime.get("strategy_mode"),
            "vix": regime.get("vix"),
            "yield_delta_30d": regime.get("yield_delta_30d"),
            "signals": regime.get("signals", []),
        }
    except Exception:
        pass

    try:
        from data.connectors.openinsider_scraper import detect_cluster_buying
        cluster = detect_cluster_buying(ticker.symbol, days=30)
        snapshot["insider_cluster"] = cluster
    except Exception:
        pass

    try:
        from supplychain.models import CompanyRelationship
        rels = CompanyRelationship.objects.filter(source_ticker=ticker, is_active=True)
        if rels.exists():
            snapshot["supply_chain"] = [
                {"company": r.target_company, "type": r.relationship_type}
                for r in rels[:10]
            ]
    except Exception:
        pass

    return snapshot


def _retrieve_knowledge(signal_type, data_snapshot):
    """Retrieve relevant knowledge chunks via RAG."""
    try:
        from knowledge.rag_retrieval import retrieve
        query = _build_query(signal_type, data_snapshot)
        return retrieve(query, signal_type, top_k=5)
    except Exception:
        return []


def _build_query(signal_type, data_snapshot):
    """Build a RAG query from the data snapshot."""
    parts = []
    if "technical" in data_snapshot:
        tech = data_snapshot["technical"]
        if tech.get("rsi_14") and tech["rsi_14"] > 70:
            parts.append("overbought RSI reversal strategy")
        elif tech.get("rsi_14") and tech["rsi_14"] < 30:
            parts.append("oversold RSI bounce strategy")
        if tech.get("adx") and tech["adx"] > 25:
            parts.append("strong trend trading")

    if "sentiment" in data_snapshot:
        sent = data_snapshot["sentiment"]
        if sent.get("composite", 0) > 0.3:
            parts.append("positive sentiment momentum trading")
        elif sent.get("composite", 0) < -0.3:
            parts.append("negative sentiment risk management")

    if "options" in data_snapshot and data_snapshot["options"].get("unusual_activity"):
        parts.append("unusual options activity interpretation")

    if "insider_trades" in data_snapshot:
        parts.append("insider trading signal interpretation")

    if signal_type == "seasonal_swing":
        parts.append("seasonal swing trading sector rotation")
    elif signal_type == "day_trade":
        parts.append("day trading momentum breakout")
    else:
        parts.append("medium term swing trading")

    return " ".join(parts)