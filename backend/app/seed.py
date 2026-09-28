"""Seed realistic pipeline data + rich memories into Hindsight.

Run:  python -m app.seed     (from the backend/ folder, with .env loaded)

The point: several PAST WON deals carry explicit 'we won after objection X by
doing Y' memories. The open deals (esp. Acme Robotics) face the SAME objections,
so brief() recalls those winning moves ACROSS deals — the demo's wow moment.
"""
import time
from . import db, memory

DEALS = [
    # ---- WON deals: each carries a winning-move memory (cross-deal gold) ----
    dict(id="globex", name="Globex Manufacturing", company="Globex", value=84000,
         stage="Closed Won", outcome="won", contact="Priya Nair (VP Ops)", persona="Ops",
         mem=[
           "On the Globex deal, the buyer objected we were too expensive vs Databricks.",
           "We WON Globex by dropping the price war and showing a 3-year total-cost-of-ownership model plus a manufacturing case study — value beat the sticker price.",
           "Globex champion Priya Nair (VP Ops) cared about downtime reduction, not features.",
         ]),
    dict(id="initech", name="Initech Platform", company="Initech", value=120000,
         stage="Closed Won", outcome="won", contact="Sam Okafor (CISO)", persona="Security",
         mem=[
           "On the Initech deal, the blocker was security & compliance — they demanded SOC2 and data-residency guarantees.",
           "We WON Initech by sending the SOC2 Type II report early, offering an on-prem deployment option, and booking a 30-min security review call with their CISO.",
           "Initech's CISO Sam Okafor became a champion once data residency was in writing.",
         ]),
    dict(id="umbrella", name="Umbrella Health", company="Umbrella", value=66000,
         stage="Closed Won", outcome="won", contact="Dr. Lena Fox (COO)", persona="Exec",
         mem=[
           "On the Umbrella Health deal, the objection was 'no budget this quarter' (timing).",
           "We WON Umbrella by proposing a phased rollout: a small paid Q1 pilot that fit the current budget, expanding at renewal.",
         ]),
    dict(id="stark", name="Stark Industries", company="Stark", value=210000,
         stage="Closed Won", outcome="won", contact="Nina Ross (Head of Data)", persona="Data",
         mem=[
           "On the Stark Industries deal, they were already using Tableau and saw no reason to switch.",
           "We WON Stark with a live side-by-side bake-off on their own data and migration credits to remove switching cost.",
         ]),
    dict(id="wayne", name="Wayne Enterprises", company="Wayne", value=155000,
         stage="Closed Won", outcome="won", contact="Marcus Bell (VP Analytics)", persona="Data",
         mem=[
           "On the Wayne Enterprises deal, the objection was that ROI was unproven.",
           "We WON Wayne with a 30-day POC tied to three agreed success metrics — once the metrics hit, procurement moved fast.",
         ]),

    # ---- LOST deals: anti-patterns worth remembering ----
    dict(id="vandelay", name="Vandelay Industries", company="Vandelay", value=48000,
         stage="Closed Lost", outcome="lost", contact="George Costanza (Proc.)", persona="Procurement",
         mem=[
           "On the Vandelay deal, the objection was price.",
           "We LOST Vandelay because we discounted early instead of proving value — the discount signalled our price wasn't real and they pushed for more.",
         ]),
    dict(id="gekko", name="Gekko Capital", company="Gekko", value=98000,
         stage="Closed Lost", outcome="lost", contact="Bud Fox (IT Dir.)", persona="Security",
         mem=[
           "On the Gekko Capital deal, security review dragged on for weeks.",
           "We LOST Gekko because the security questionnaire response was slow — a competitor with a ready trust-center won on speed.",
         ]),

    # ---- OPEN deals: the demo targets ----
    dict(id="acme", name="Acme Robotics", company="Acme", value=140000,
         stage="Negotiation", outcome="open", contact="Ravi Menon (VP Engineering)", persona="Eng",
         mem=[
           "On the Acme Robotics deal, VP Engineering Ravi Menon is our champion and loves the product.",
           "On the Acme Robotics deal, the buyer objected that we're too expensive compared to Databricks.",
           "On the Acme Robotics deal, their CFO is a blocker and is pushing back on price.",
           "On the Acme Robotics deal, procurement asked whether we have SOC2 and where data is stored.",
           "Acme's next step: a pricing + security call next week to get CFO sign-off.",
         ]),
    dict(id="hooli", name="Hooli Data Cloud", company="Hooli", value=175000,
         stage="Negotiation", outcome="open", contact="Gavin Lee (Dir. Data)", persona="Data",
         mem=[
           "On the Hooli deal, they are already standardised on Tableau and question the ROI of switching.",
           "On the Hooli deal, the director wants proof before committing budget.",
         ]),
    dict(id="soylent", name="Soylent Foods", company="Soylent", value=59000,
         stage="Proposal", outcome="open", contact="Mia Chen (Analytics Lead)", persona="Data",
         mem=[
           "On the Soylent Foods deal, the concern is timing — budget may not open until next quarter.",
         ]),
    dict(id="cyberdyne", name="Cyberdyne Systems", company="Cyberdyne", value=90000,
         stage="Discovery", outcome="open", contact="Sarah Kim (Data Eng Mgr)", persona="Eng",
         mem=[
           "On the Cyberdyne deal, early discovery — they're evaluating build-vs-buy for an analytics layer.",
         ]),
    dict(id="piedpiper", name="Pied Piper", company="Pied Piper", value=42000,
         stage="Discovery", outcome="open", contact="Richard H. (CTO)", persona="Eng",
         mem=[
           "On the Pied Piper deal, the CTO is technical and wants to see architecture and compression benchmarks.",
         ]),
]


def run(with_memory=True):
    db.init()
    seeded_mem = 0
    for d in DEALS:
        d = dict(d)
        mems = d.pop("mem", [])
        d["created"] = time.time()
        db.upsert_deal(d)
        db.add_event(d["id"], "seed", f"Imported {d['name']} ({d['stage']})")
        if with_memory:
            for i, line in enumerate(mems):
                try:
                    memory.retain(line, context=f"{d['name']} history",
                                  deal_id=d["id"], deal_name=d["name"],
                                  outcome=d["outcome"], kind="seed",
                                  document_id=f"{d['id']}-m{i}")
                    seeded_mem += 1
                except Exception as e:
                    print("  ! memory retain failed:", e)
    print(f"Seeded {len(DEALS)} deals, {seeded_mem} memories into Hindsight bank '{memory.BANK}'.")


if __name__ == "__main__":
    run()
