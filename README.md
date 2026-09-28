# 🧠 DealMind — a Sales Deal-Intelligence Agent that *learns across deals*

**HackwithHyderabad 3.0 · "AI Agents That Learn Using Hindsight"**

Sales reps waste hours re-reading CRM notes before every call. DealMind is an AI
agent that **remembers every objection, competitor, stakeholder and price signal
across the entire deal cycle** — and, crucially, **learns across deals**: when a
new deal hits an objection you've beaten before, it recalls *how you won that
one* and tells the rep the play. Memory becomes intelligence.

> Not "an AI that remembers your favorite color." This is *"an AI sales assistant
> that remembers every objection a prospect raised across calls and drafts
> personalized follow-ups"* — the hackathon brief's own example of a winning idea.

---

## Why memory is the star (25% of judging)

Everything the agent knows lives in **one Hindsight memory bank** for the sales
org — so knowledge is **cumulative and cross-deal**, not siloed per chat.

| Move | What it does | Hindsight call |
|---|---|---|
| **Log a call** | Extracts objections / competitors / stakeholders / price / next-step from raw notes and writes each as an atomic memory | `retain()` |
| **Brief me** | Recalls *this* deal **and** the winning moves from *other* past deals with similar objections, then composes a pre-call brief | `recall()` (×2, incl. cross-deal) |
| **Draft follow-up** | Recalls the latest context and writes a personalised email | `recall()` |

**The wow moment:** open the **Acme Robotics** deal (objection: *"too expensive
vs Databricks"* + *"are you SOC2?"*) and hit **Brief me**. The agent pulls the
winning tactics from the **Globex** deal (won the price objection with a 3-yr TCO
model) and the **Initech** deal (won the security objection with an early SOC2
report) — deals it was never told to look at. That cross-deal recall is the
learning curve made visible.

The right-hand **🧠 Memory panel** shows exactly what the agent knows, live, and
grows every time you log a call.

---

## Stack
- **Hindsight** (`hindsight-client`) — the memory core: `retain` / `recall` / `reflect`
- **Groq** (`openai/gpt-oss-120b`) — extraction, briefs, follow-ups
- **FastAPI** backend, single-file vanilla-JS UI (no build step), **SQLite** deal shell

## Run it (Windows)
```
cd backend
setup.bat        REM venv + deps + creates .env
REM ...open .env, paste your GROQ_API_KEY + HINDSIGHT_BASE_URL/KEY...
seed.bat         REM loads the pipeline + memories into Hindsight
run.bat          REM http://localhost:8000
```
Mac/Linux:
```
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in keys
python -m app.seed
uvicorn app.main:app --port 8000
```

## Keys
- **Groq:** free key at https://groq.com
- **Hindsight Cloud:** sign up at https://ui.hindsight.vectorize.io/signup (promo `MEMHACK99` = $50 credits), or run the open-source server on `http://localhost:8888`.

## How Hindsight memory is used (submission requirement)
1. **Ingestion → `retain`:** every call note is decomposed by the LLM into atomic
   facts; each is `retain`ed into the org bank with metadata `{deal_id, deal_name,
   outcome, kind}`. Won deals also store an explicit *"we won X objection by doing
   Y"* memory.
2. **Pre-call brief → `recall` (cross-deal):** two recalls run — one scoped to the
   current deal, one that deliberately searches the whole bank for *winning moves
   against similar objections on other deals*, filtered to exclude the current
   deal. That second recall is where "learning from past interactions" happens.
3. **Follow-up → `recall`:** the latest deal context is recalled to ground a
   personalised email.
4. The **Memory panel** is a live `recall` view, so judges can *see* the memory
   that drives every output.

Pull the plug on a chatbot and it forgets you. DealMind gets **smarter with every
deal your team ever runs.**
