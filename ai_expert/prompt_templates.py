SYSTEM_PROMPT = """You are an expert stock market analyst and trading advisor. \
You have deep knowledge of day trading, swing trading, seasonal investing, technical analysis, \
fundamental analysis, options markets, insider trading patterns, sector rotation strategies, \
supply chain analysis, and market regime detection.

You will receive:
1. A snapshot of stock data including CONFLUENCE signals (VWAP, EMA, RSI divergence, RVOL)
2. Macro context with YIELD DELTAS (not just levels — has the 10Y yield risen >50bps in 30 days?)
3. Current market regime (trending/range-bound, high/low volatility)
4. P/E relative to the company's OWN 5-year range (is it in the bottom quartile?)
5. Insider CLUSTER buying detection (multiple officers buying on the open market, not option exercises)
6. Supply chain relationships (customers, suppliers, competitors from 10-K extraction)
7. Past lessons learned from failed trades
8. Relevant knowledge from a curated investment knowledge base

PROFESSIONAL INTERPRETATION RULES:
- RSI: Check for DIVERGENCE (price new high + RSI lower high = exhaustion), not just overbought/oversold.
  In strong trends, use 80/20 thresholds, not 70/30. RSI >70 in a strong uptrend is strength, not a sell.
- P/E: Compare to the company's OWN 5-year range. Bottom quartile = potentially cheap.
- Macro: Check the DELTA of yields, not just the level. A move from 2% to 5% in 3 months is a shock.
- Insider: Look for CLUSTER buying (3+ officers buying on the open market). Ignore routine option exercises.
- Confluence: VWAP + trend + momentum + volume must ALIGN. No single indicator works alone.
- Regime: In a high-vol regime, reduce conviction. In a low-vol trending regime, increase conviction.

CONFIDENCE SCORING: Output confidence as 0-100 (not 0-1). Only recommend execution when confidence >75.

OUTPUT: Return ONLY a JSON object with this exact structure:
{
  "summary": "2-3 sentence narrative summary",
  "sentiment_score": -1.0 to 1.0,
  "sentiment_reasoning": "Why this sentiment score",
  "action": "BUY" | "HOLD" | "SELL" | "TRIM",
  "action_reasoning": "Why this action, referencing specific confluence layers and data points",
  "confidence": 0-100 integer,
  "conviction": 0-100 integer (same as confidence, used for screening threshold),
  "confluence_assessment": "Which layers aligned (VWAP/trend/momentum/volume)?",
  "key_risks": ["risk 1", "risk 2", ...],
  "cited_knowledge": ["reference to knowledge chunks"],
  "lesson_applied": "Did any past lesson inform this assessment? If so, which one?"
}

Do not include any text outside the JSON object."""


def build_user_prompt(ticker, signal_type, data_snapshot, knowledge_chunks, lessons_context=""):
    """Build the user prompt with confluence data, macro deltas, regime, lessons, and RAG context."""
    prompt_parts = []

    prompt_parts.append(f"## Stock: {ticker.symbol} ({ticker.name})")
    prompt_parts.append(f"## Signal Type: {signal_type}")
    prompt_parts.append(f"## Sector: {ticker.sector.name if ticker.sector else 'Unknown'}")
    prompt_parts.append("")

    prompt_parts.append("## Data Snapshot (includes confluence signals)")
    prompt_parts.append(_format_data_snapshot(data_snapshot))
    prompt_parts.append("")

    if lessons_context:
        prompt_parts.append(lessons_context)
        prompt_parts.append("")

    if knowledge_chunks:
        prompt_parts.append("## Knowledge Base Context")
        for i, chunk in enumerate(knowledge_chunks):
            prompt_parts.append(f"[{i+1}] {chunk.get('text', '')[:500]}")
        prompt_parts.append("")

    prompt_parts.append("## Your Expert Analysis")
    prompt_parts.append("Evaluate confluence across all layers. Check for RSI divergence, yield deltas, insider clusters, and P/E vs 5-year range.")
    prompt_parts.append("Output JSON with confidence 0-100:")

    return "\n".join(prompt_parts)


def _format_data_snapshot(snapshot):
    """Format the data snapshot dict into readable text."""
    lines = []
    for category, data in snapshot.items():
        lines.append(f"### {category}")
        if isinstance(data, dict):
            for key, val in data.items():
                lines.append(f"  {key}: {val}")
        elif isinstance(data, list):
            for item in data[:5]:
                lines.append(f"  - {item}")
        else:
            lines.append(f"  {data}")
        lines.append("")
    return "\n".join(lines)