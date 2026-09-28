"""Groq LLM client (OpenAI-compatible). Used for extraction, briefs and follow-ups.
The MEMORY lives in Hindsight (see memory.py); Groq only does the language work."""
import os
import re
import json
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")


def chat(system: str, user: str, json_mode: bool = False, temperature: float = 0.3) -> str:
    if not GROQ_KEY:
        raise RuntimeError("GROQ_API_KEY not set — add it to backend/.env")
    body = {
        "model": MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    r = requests.post(
        GROQ_URL,
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json=body,
        timeout=90,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def chat_json(system: str, user: str) -> dict:
    """Force a JSON object out of the model, tolerant of stray fences/prose."""
    txt = chat(system, user, json_mode=True)
    try:
        return json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.S)
        return json.loads(m.group(0)) if m else {}
