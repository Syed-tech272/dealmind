"""Local deal records + call timeline (SQLite). The MEMORY is Hindsight; this is
just the structured CRM shell so the UI has deals to click through."""
import os
import time
import json
import sqlite3

DB = os.path.join(os.path.dirname(__file__), "..", "dealmind.db")


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    c = conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS deals(
      id TEXT PRIMARY KEY, name TEXT, company TEXT, value INTEGER,
      stage TEXT, outcome TEXT, contact TEXT, persona TEXT, created REAL
    );
    CREATE TABLE IF NOT EXISTS events(
      id INTEGER PRIMARY KEY AUTOINCREMENT, deal_id TEXT, ts REAL,
      kind TEXT, summary TEXT, raw TEXT
    );
    """)
    c.commit()
    c.close()


def upsert_deal(d):
    c = conn()
    c.execute("""INSERT INTO deals(id,name,company,value,stage,outcome,contact,persona,created)
                 VALUES(?,?,?,?,?,?,?,?,?)
                 ON CONFLICT(id) DO UPDATE SET name=excluded.name,company=excluded.company,
                 value=excluded.value,stage=excluded.stage,outcome=excluded.outcome,
                 contact=excluded.contact,persona=excluded.persona""",
              (d["id"], d["name"], d["company"], d.get("value", 0), d.get("stage", "Discovery"),
               d.get("outcome", "open"), d.get("contact", ""), d.get("persona", ""),
               d.get("created", time.time())))
    c.commit()
    c.close()


def list_deals():
    c = conn()
    rows = [dict(r) for r in c.execute("SELECT * FROM deals ORDER BY created DESC")]
    for r in rows:
        r["events"] = c.execute("SELECT COUNT(*) FROM events WHERE deal_id=?", (r["id"],)).fetchone()[0]
    c.close()
    return rows


def get_deal(did):
    c = conn()
    row = c.execute("SELECT * FROM deals WHERE id=?", (did,)).fetchone()
    if not row:
        c.close()
        return None
    d = dict(row)
    d["timeline"] = [dict(e) for e in c.execute(
        "SELECT * FROM events WHERE deal_id=? ORDER BY ts", (did,))]
    c.close()
    return d


def add_event(did, kind, summary, raw=None):
    c = conn()
    c.execute("INSERT INTO events(deal_id,ts,kind,summary,raw) VALUES(?,?,?,?,?)",
              (did, time.time(), kind, summary, json.dumps(raw) if raw is not None else None))
    c.commit()
    c.close()


def set_outcome(did, outcome, stage=None):
    c = conn()
    if stage:
        c.execute("UPDATE deals SET outcome=?, stage=? WHERE id=?", (outcome, stage, did))
    else:
        c.execute("UPDATE deals SET outcome=? WHERE id=?", (outcome, did))
    c.commit()
    c.close()
