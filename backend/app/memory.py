"""The memory core — Hindsight (Vectorize).

Everything the agent 'knows' across the whole deal pipeline lives in ONE memory
bank, so it can learn ACROSS deals (e.g. how a 'too expensive' objection was
beaten on a past won deal). This is the heart of the project.

retain()  -> write a memory      recall() -> semantic search
reflect() -> agentic reasoning over the bank
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

try:
    from hindsight_client import Hindsight
except Exception:  # allow the app to boot even before the pkg is installed
    Hindsight = None

BASE = os.environ.get("HINDSIGHT_BASE_URL", "http://localhost:8888")
KEY = os.environ.get("HINDSIGHT_API_KEY") or None
BANK = os.environ.get("HINDSIGHT_BANK", "dealmind-northwind")

_client = None


def client():
    global _client
    if _client is None:
        if Hindsight is None:
            raise RuntimeError("hindsight-client not installed — pip install -r requirements.txt")
        kwargs = {"base_url": BASE, "timeout": 60.0}
        if KEY:
            kwargs["api_key"] = KEY
        _client = Hindsight(**kwargs)
    return _client


def retain(content, context=None, deal_id=None, deal_name=None, outcome=None,
           kind=None, document_id=None):
    """Store one memory. Metadata lets us tell which deal / outcome it came from."""
    md = {}
    if deal_id:
        md["deal_id"] = deal_id
    if deal_name:
        md["deal_name"] = deal_name
    if outcome:
        md["outcome"] = outcome
    if kind:
        md["kind"] = kind
    client().retain(bank_id=BANK, content=content, context=context or "",
                    metadata=md or None, document_id=document_id)


def recall(query, budget="high", max_tokens=2048):
    res = client().recall(bank_id=BANK, query=query, budget=budget, max_tokens=max_tokens)
    out = []
    for r in getattr(res, "results", []) or []:
        out.append({
            "text": getattr(r, "text", str(r)),
            "type": getattr(r, "type", None),
            "metadata": getattr(r, "metadata", {}) or {},
        })
    return out


def reflect(query, context=None, budget="mid"):
    a = client().reflect(bank_id=BANK, query=query, budget=budget, context=context or "")
    return getattr(a, "text", "")


def health():
    try:
        client().recall(bank_id=BANK, query="ping", budget="low", max_tokens=64)
        return True
    except Exception:
        return False
