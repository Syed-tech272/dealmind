"""The memory core — Hindsight (Vectorize).

Everything the agent 'knows' across the whole deal pipeline lives in ONE memory
bank, so it can learn ACROSS deals. This is the heart of the project.

Sync helpers (retain/recall) are for standalone scripts like seed.py.
Async helpers (aretain/arecall/areflect) are used by the FastAPI server so the
Hindsight aiohttp client runs on the server's own event loop.
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

try:
    from hindsight_client import Hindsight
except Exception:
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


def _md(deal_id, deal_name, outcome, kind):
    md = {}
    if deal_id:
        md["deal_id"] = deal_id
    if deal_name:
        md["deal_name"] = deal_name
    if outcome:
        md["outcome"] = outcome
    if kind:
        md["kind"] = kind
    return md or None


def _parse(res):
    out = []
    for r in getattr(res, "results", []) or []:
        out.append({
            "text": getattr(r, "text", str(r)),
            "type": getattr(r, "type", None),
            "metadata": getattr(r, "metadata", {}) or {},
        })
    return out


# ---- sync (standalone scripts / seed) ----
def retain(content, context=None, deal_id=None, deal_name=None, outcome=None, kind=None, document_id=None):
    client().retain(bank_id=BANK, content=content, context=context or "",
                    metadata=_md(deal_id, deal_name, outcome, kind), document_id=document_id)


# ---- async (FastAPI server) ----
async def aretain(content, context=None, deal_id=None, deal_name=None, outcome=None, kind=None, document_id=None):
    await client().aretain(bank_id=BANK, content=content, context=context or "",
                           metadata=_md(deal_id, deal_name, outcome, kind), document_id=document_id)


async def arecall(query, budget="high", max_tokens=2048):
    res = await client().arecall(bank_id=BANK, query=query, budget=budget, max_tokens=max_tokens)
    return _parse(res)


async def areflect(query, context=None, budget="mid"):
    a = await client().areflect(bank_id=BANK, query=query, budget=budget, context=context or "")
    return getattr(a, "text", "")


async def ahealth():
    try:
        await client().arecall(bank_id=BANK, query="ping", budget="low", max_tokens=64)
        return True
    except Exception:
        return False
