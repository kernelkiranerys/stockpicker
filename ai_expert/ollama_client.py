import json
import urllib.request
import urllib.error
from django.conf import settings


def chat(model, system, prompt, temperature=0.3, num_predict=800):
    """Call Ollama chat API. Returns response content string."""
    host = settings.OLLAMA_HOST
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
    }
    try:
        req = urllib.request.Request(
            f"{host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
        return data.get("message", {}).get("content", "")
    except Exception as e:
        return f"[Ollama error: {e}]"


def embed(model, text):
    """Call Ollama embeddings API. Returns embedding vector list."""
    host = settings.OLLAMA_HOST
    payload = {"model": model, "prompt": text}
    try:
        req = urllib.request.Request(
            f"{host}/api/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        return data.get("embedding", [])
    except Exception:
        return []


def get_available_models():
    """List available Ollama models."""
    host = settings.OLLAMA_HOST
    try:
        req = urllib.request.Request(f"{host}/api/tags")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []