"""DealMind API — a Sales Deal-Intelligence agent powered by Hindsight memory."""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from . import db, agent, memory, llm
from .schemas import LogBody, FollowupBody, OutcomeBody

app = FastAPI(title="DealMind")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

WEB = os.path.join(os.path.dirname(__file__), "..", "web")

db.init()


@app.get("/health")
async def health():
    return {
        "ok": True,
        "groq_model": llm.MODEL,
        "groq_key": bool(llm.GROQ_KEY),
        "hindsight_bank": memory.BANK,
        "hindsight_url": memory.BASE,
        "memory_ok": await memory.ahealth(),
    }


@app.get("/deals")
def deals():
    return db.list_deals()


@app.get("/deals/{did}")
def deal(did: str):
    d = db.get_deal(did)
    if not d:
        raise HTTPException(404, "deal not found")
    return d


@app.post("/deals/{did}/log")
async def log(did: str, body: LogBody):
    d = db.get_deal(did)
    if not d:
        raise HTTPException(404, "deal not found")
    return await agent.log_call(d, body.notes)


@app.get("/deals/{did}/brief")
async def brief(did: str):
    d = db.get_deal(did)
    if not d:
        raise HTTPException(404, "deal not found")
    return await agent.brief(d)


@app.post("/deals/{did}/followup")
async def followup(did: str, body: FollowupBody):
    d = db.get_deal(did)
    if not d:
        raise HTTPException(404, "deal not found")
    return await agent.draft_followup(d, body.intent)


@app.get("/deals/{did}/memory")
async def mem(did: str):
    d = db.get_deal(did)
    if not d:
        raise HTTPException(404, "deal not found")
    return {"memories": await agent.memory_view(d)}


@app.post("/deals/{did}/outcome")
def outcome(did: str, body: OutcomeBody):
    db.set_outcome(did, body.outcome, body.stage)
    return {"ok": True}


@app.get("/patterns")
async def patterns(objection: str = "too expensive"):
    return {"objection": objection, "matches": await agent.win_patterns(objection)}


# ---- static UI (single page, no build step) ----
@app.get("/")
def index():
    return FileResponse(os.path.join(WEB, "index.html"))
