"""The Deal-Intelligence agent (async).

Three moves, every one leans on Hindsight memory:
  log_call()      -> extract facts from raw notes, RETAIN them into the bank
  brief()         -> RECALL this deal + RECALL winning moves from OTHER won deals
                     -> compose a pre-call brief with tactics learned across deals
  draft_followup()-> RECALL the deal, draft a personalised email

The magic (and the demo): brief() pulls 'how we beat this objection before' from
memories that belong to *different* deals. Memory becoming intelligence.
"""
import asyncio
from . import llm, memory, db

EXTRACT_SYS = """You are a sales-ops analyst. From a rep's raw call notes, extract structured facts.
Return STRICT JSON with these keys:
{
 "summary": "one-line what happened on this call",
 "objections": ["buyer concerns, each short"],
 "competitors": ["competitor names mentioned"],
 "stakeholders": ["name - role - stance (champion/blocker/neutral)"],
 "pricing": "any pricing/budget signal, else empty",
 "sentiment": "hot | warm | cool | at-risk",
 "next_step": "the agreed or suggested next action",
 "memories": ["3-6 short, self-contained memory sentences worth remembering long-term; each MUST NAME the deal/company so it is useful when recalled months later"]
}
Only output the JSON object."""

BRIEF_SYS = """You are an elite sales strategist briefing a rep before a call.
You are given: (1) what we know about THIS deal, and (2) winning moves from OTHER past deals that faced similar objections.
Write a tight, skimmable pre-call brief in markdown with these sections:
### Where this deal stands
### Open objections & what worked elsewhere   (tie each objection to a concrete past-deal tactic when available)
### Key stakeholders
### Recommended plays for this call   (3 numbered, specific, aggressive-but-honest)
### One risk to watch
Be specific and reference the recalled facts. Do NOT invent facts that were not provided.
Use short bullet lists and numbered lists only — do NOT use markdown tables."""

FOLLOWUP_SYS = """You draft short, personalised B2B sales follow-up emails.
Use ONLY the recalled context. Reference the actual objection, competitor and next step.
Tone: warm, concise, confident, no fluff. Output just the email (Subject + body)."""


def _mem_lines(mems):
    return "\n".join(f"- {m['text']}" for m in mems) if mems else "(nothing yet)"


async def log_call(deal, notes):
    data = await asyncio.to_thread(
        llm.chat_json, EXTRACT_SYS,
        f"DEAL: {deal['name']} ({deal['company']})\n\nCALL NOTES:\n{notes}")
    for line in data.get("memories") or []:
        await memory.aretain(line, context=f"{deal['name']} call note",
                             deal_id=deal["id"], deal_name=deal["name"],
                             outcome=deal.get("outcome"), kind="call")
    for obj in data.get("objections") or []:
        await memory.aretain(f"On the {deal['name']} deal, the buyer objected: {obj}",
                             context="objection", deal_id=deal["id"], deal_name=deal["name"],
                             outcome=deal.get("outcome"), kind="objection")
    db.add_event(deal["id"], "call", data.get("summary", "Call logged"), data)
    return data


async def brief(deal):
    name = deal["name"]
    own = await memory.arecall(
        f"{name} {deal['company']} objections competitors pricing stakeholders next step", budget="high")
    cross = await memory.arecall(
        "how we handled and WON deals with objections about price, competitor, timing, security, ROI",
        budget="high")
    cross = [m for m in cross if (m.get("metadata") or {}).get("deal_name") != name]

    ctx = (f"THIS DEAL ({name} - {deal['company']}, stage {deal['stage']}, "
           f"value ${deal['value']:,}):\n{_mem_lines(own)}\n\n"
           f"WINNING MOVES FROM OTHER DEALS (learn from these):\n{_mem_lines(cross)}")
    md = await asyncio.to_thread(llm.chat, BRIEF_SYS, ctx, False, 0.35)
    return {"brief": md, "own": own, "cross": cross}


async def draft_followup(deal, intent="move the deal forward"):
    name = deal["name"]
    ctx_mems = await memory.arecall(
        f"{name} {deal['company']} latest objection next step stakeholder pricing", budget="high")
    ctx = (f"Deal: {name} ({deal['company']}). Contact: {deal.get('contact')}. "
           f"Goal of this email: {intent}.\n\nRecalled context:\n{_mem_lines(ctx_mems)}")
    email = await asyncio.to_thread(llm.chat, FOLLOWUP_SYS, ctx, False, 0.5)
    return {"email": email, "used": ctx_mems}


async def memory_view(deal):
    return await memory.arecall(f"{deal['name']} {deal['company']}", budget="high", max_tokens=3000)


async def win_patterns(objection):
    return await memory.arecall(f"how we won deals after the objection: {objection}", budget="high")
