# How I gave my sales agent a memory that learns across deals with Hindsight

A few days ago my sales agent told me to beat a pricing objection on a deal called *Acme Robotics* by walking the buyer through a three‑year total‑cost‑of‑ownership model — because that's exactly how we'd won a **completely different** account months earlier. I never pointed it at that other deal. It went and found the winning move on its own, and in the same breath it warned me *not* to open with a discount, because discounting early is precisely how we'd lost a third account.

That was the moment the project clicked for me. Most "AI for sales" is a chatbot with a system prompt. What I actually wanted was an agent that **remembers every deal my team has ever run** and gets sharper with each one. This is the story of building that, and the one design decision — and one nasty bug — that made it work.

## What the system does

DealMind is a deal‑intelligence assistant for B2B reps. It does three things, and every one of them is really a memory operation:

- **Log a call.** You paste raw, messy call notes. An LLM pulls out the structured facts — objections, competitors, stakeholders, price signals, next steps — and each fact is written to memory.
- **Brief me.** Before a call, one click produces a pre‑call battle plan: where the deal stands, the open objections, the key people, and — the part I care about — the tactics that won *similar* deals in the past.
- **Draft follow‑up.** It writes a personalised email grounded in everything it remembers about that specific deal.

The stack is deliberately boring where it can be: a FastAPI backend, a single‑page UI with no build step, SQLite as the plain CRM shell, and [Groq](https://groq.com) running `gpt-oss-120b` for the language work. The interesting part is the memory layer, which is [Hindsight](https://hindsight.vectorize.io/).

## The one idea that matters: a single, shared memory bank

The temptation with agent memory is to scope it per‑conversation or per‑entity: one memory store per deal. That gives you recall, but it doesn't give you *learning*. A brief for the Acme deal that can only see Acme's own history is just a nicer CRM.

So I did the opposite. Every memory — across every deal, won or lost — lives in **one Hindsight memory bank** for the whole sales org, tagged with metadata about which deal it came from and how that deal ended. Knowledge becomes cumulative and cross‑deal. A brand‑new rep inherits the entire team's hard‑won experience on day one.

The Hindsight wrapper is tiny. `retain` writes a memory; `recall` does semantic search over the bank:

```python
async def aretain(content, deal_id=None, deal_name=None, outcome=None, kind=None):
    await client().aretain(
        bank_id=BANK, content=content,
        metadata={"deal_id": deal_id, "deal_name": deal_name,
                  "outcome": outcome, "kind": kind},
    )

async def arecall(query, budget="high", max_tokens=2048):
    res = await client().arecall(bank_id=BANK, query=query,
                                 budget=budget, max_tokens=max_tokens)
    return [{"text": r.text, "type": r.type, "metadata": r.metadata or {}}
            for r in res.results]
```

That `outcome` on the metadata — `won` / `lost` / `open` — turns out to be the whole game.

## Cross‑deal recall, in one function

Here's the part I'm proud of. When you ask for a brief, the agent runs **two** recalls. The first is scoped to the current deal. The second deliberately searches the *entire* bank for winning moves against the kinds of objections this deal is facing, and then filters out the current deal so it can only surface lessons from *other* accounts:

```python
async def brief(deal):
    name = deal["name"]
    own = await memory.arecall(
        f"{name} objections competitors pricing stakeholders next step")

    cross = await memory.arecall(
        "how we handled and WON deals with objections about "
        "price, competitor, timing, security, ROI")
    cross = [m for m in cross
             if (m.get("metadata") or {}).get("deal_name") != name]

    ctx = f"THIS DEAL:\n{lines(own)}\n\nWINNING MOVES FROM OTHER DEALS:\n{lines(cross)}"
    return {"brief": await llm.chat(BRIEF_SYS, ctx), "own": own, "cross": cross}
```

The LLM never has to hold the whole pipeline in its context window. Hindsight does the remembering; the model just does the writing. That separation is the thing I'd underline for anyone building agents right now: **don't make the model your memory.** Retrieval that actually understands your history is a different job, and it's the one that makes the agent feel like it's learning.

## Before and after

The before/after is stark, and it's the demo I show people.

Open a fresh deal with no logged calls and ask for a brief, and you get something generic: "confirm the stakeholders, understand their timeline." Useful‑ish. A better‑than‑nothing checklist.

Now open Acme — a deal that's logged a few calls, whose buyer keeps comparing us to a competitor on price and is asking for a SOC 2 report — and the brief changes character completely:

- *Beat the price objection the way we won **Globex**: a 3‑year TCO model plus a case study, not a discount.*
- *Send the SOC 2 report early, like we did on **Initech**, and offer the on‑prem option.*
- *Prove ROI with a 30‑day POC tied to metrics — that's what closed **Wayne**.*
- *⚠️ Do not discount early. That's how we lost **Vandelay**.*

None of those accounts are Acme. The agent reached across the bank and assembled a playbook from four different deals — including a loss it correctly reframed as a warning. That is [agent memory](https://vectorize.io/what-is-agent-memory) doing something a system prompt simply cannot.

## The bug that ate an afternoon

Honesty section, because the guide of building this wasn't clean.

My first version used the synchronous Hindsight client directly inside my FastAPI handlers. It worked in a standalone script, it worked on the first request, and then it blew up on the second with:

```
RuntimeError: Timeout context manager should be used inside a task
```

FastAPI runs sync endpoints in a threadpool, and the underlying `aiohttp` session the client creates gets bound to the event loop of the first thread that touches it. The next request lands on a different worker, tries to reuse that session, and `aiohttp`'s timeout machinery — which expects to be inside a running task — throws. Classic "works once" concurrency trap.

The fix was to stop fighting it and go async end‑to‑end. Hindsight ships async variants of every method (`aretain`, `arecall`, `areflect`), so I made my memory layer, my agent functions, and my endpoints all `async`, and let the client run on FastAPI's own loop. Seeding scripts stay synchronous because they run in their own process. An hour of confusion, a five‑line mental model, a clean fix.

## What I'd tell you if you're building this

- **Store the lesson, not just the fact.** "The buyer objected on price" is weak. "We won this account after the price objection by showing a 3‑year TCO model" is a memory that changes a future call. I explicitly write those won/lost resolution memories, and they're what `recall` surfaces when it matters.
- **Metadata is how you get cross‑entity learning.** Tagging every memory with the deal and its outcome is what lets one recall pull *only* winning moves from *other* deals. Without it you get a blur; with it you get a playbook.
- **Let the memory layer enrich.** I wrote plain sentences; Hindsight structured, timestamped, and expanded them into higher‑level facts I didn't author. Recall returned more than I put in, in a good way.
- **Keep the model dumb about state.** The agent is stateless between requests. All the intelligence that feels like "it's getting to know my pipeline" lives in Hindsight, not in a growing prompt.

If you want to build on the same memory layer, the [Hindsight repo](https://github.com/vectorize-io/hindsight) and its [docs](https://hindsight.vectorize.io/) are the place to start. The mental shift — from "AI that answers" to "AI that remembers, and therefore learns" — is smaller to implement than I expected, and much bigger in what it unlocks.

My agent stopped being a chatbot the day it started bringing me tactics from deals I'd forgotten. That's the difference memory makes.
