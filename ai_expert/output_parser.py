import json
import re


def parse_expert_output(raw_text):
    """Parse LLM JSON output into structured fields.
    Handles markdown code fences and malformed JSON gracefully.
    """
    defaults = {
        "summary": "",
        "sentiment_score": 0.0,
        "sentiment_reasoning": "",
        "action": "HOLD",
        "action_reasoning": "",
        "confidence": 0,
        "conviction": 0,
        "confluence_assessment": "",
        "key_risks": [],
        "cited_knowledge": [],
        "lesson_applied": "",
    }

    if not raw_text or not raw_text.strip():
        return defaults

    # Strip markdown code fences
    text = raw_text.strip()
    fence_pattern = r"```(?:json)?\s*(.*?)\s*```"
    matches = re.findall(fence_pattern, text, re.DOTALL)
    if matches:
        text = matches[0].strip()
    else:
        # Try to find JSON object in the text
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            text = text[json_start:json_end]

    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return defaults

    result = defaults.copy()
    result["summary"] = str(data.get("summary", ""))
    result["sentiment_reasoning"] = str(data.get("sentiment_reasoning", ""))
    result["action_reasoning"] = str(data.get("action_reasoning", ""))

    try:
        score = float(data.get("sentiment_score", 0))
        result["sentiment_score"] = max(-1.0, min(1.0, score))
    except (ValueError, TypeError):
        result["sentiment_score"] = 0.0

    try:
        conf = float(data.get("confidence", 0))
        result["confidence"] = max(0, min(100, int(conf)))
    except (ValueError, TypeError):
        result["confidence"] = 0

    try:
        conv = float(data.get("conviction", data.get("confidence", 0)))
        result["conviction"] = max(0, min(100, int(conv)))
    except (ValueError, TypeError):
        result["conviction"] = result["confidence"]

    result["confluence_assessment"] = str(data.get("confluence_assessment", ""))
    result["lesson_applied"] = str(data.get("lesson_applied", ""))

    action = str(data.get("action", "HOLD")).upper().strip()
    if action in ("BUY", "SELL", "HOLD", "TRIM"):
        result["action"] = action

    risks = data.get("key_risks", [])
    if isinstance(risks, list):
        result["key_risks"] = [str(r) for r in risks[:10]]

    cited = data.get("cited_knowledge", [])
    if isinstance(cited, list):
        result["cited_knowledge"] = [str(c) for c in cited[:20]]

    return result