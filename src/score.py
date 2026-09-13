"""Score raw responses by executing them. Never calls an API.

One parser, one comparison rule, applied identically to all three models.

Usage:  python src/score.py [--split test]
"""
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "veloflux.db"
RAW = ROOT / "results" / "raw"

# A bad query can produce a cartesian join over 4000 x 300 rows and hang.
# Abort after a fixed number of VM steps instead of waiting.
MAX_VM_STEPS = 4_000_000
FLOAT_DP = 4

FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.S | re.I)
START = re.compile(r"\b(SELECT|WITH)\b", re.I)


def parse_candidates(text: str):
    """All plausible SQL starts, in order. Model-agnostic."""
    if not text or not text.strip():
        return []
    m = FENCE.search(text)
    if m:
        text = m.group(1)
    text = text.replace("`", " ")
    out = []
    for m in START.finditer(text):
        sql = text[m.start():].strip().split(";")[0].strip()
        if sql:
            out.append(sql)
    return out


def pick_sql(con, candidates):
    """First candidate SQLite can compile. EXPLAIN prepares without running."""
    for sql in candidates:
        try:
            con.execute("EXPLAIN " + sql).fetchone()
            return sql
        except Exception:
            continue
    return candidates[0] if candidates else None



def normalise(rows):
    """Make result sets comparable: column names and float noise are not differences."""
    out = []
    for row in rows:
        cells = []
        for v in row:
            if isinstance(v, float):
                cells.append(round(v, FLOAT_DP))
            elif isinstance(v, int) and not isinstance(v, bool):
                cells.append(float(v))       # 1 and 1.0 are the same answer
            else:
                cells.append(v)
        out.append(tuple(cells))
    return out


def execute(con, sql):
    con.set_progress_handler(lambda: 1, MAX_VM_STEPS)   # returning 1 aborts
    try:
        return con.execute(sql).fetchall(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        con.set_progress_handler(None, 0)


def compare(gold, pred, order_matters):
    if gold is None or pred is None:
        return False
    if len(gold) != len(pred):
        return False
    if gold and pred and len(gold[0]) != len(pred[0]):
        return False
    g, p = normalise(gold), normalise(pred)
    if order_matters:
        return g == p
    return sorted(g, key=repr) == sorted(p, key=repr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    a = ap.parse_args()

    items = {json.loads(l)["id"]: json.loads(l) for l in
             (ROOT / "data" / ("items.jsonl" if a.split == "test" else "dev.jsonl"))
             .read_text(encoding="utf-8").splitlines() if l}

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    gold_cache = {i: execute(con, it["gold_sql"])[0] for i, it in items.items()}

    rows = []
    for model_dir in sorted((RAW / a.split).iterdir()):
        if not model_dir.is_dir():
            continue
        for f in sorted(model_dir.glob("*.json")):
            rec = json.loads(f.read_text(encoding="utf-8"))
            item = items[rec["item_id"]]
            sql = pick_sql(con, parse_candidates(rec["output"]))
            if rec["error"]:
                status, pred, err = "api_error", None, rec["error"]
            elif sql is None:
                status, pred, err = "parse_error", None, "no SQL found in output"
            else:
                pred, err = execute(con, sql)
                status = "exec_error" if pred is None else (
                    "correct" if compare(gold_cache[rec["item_id"]], pred,
                                         item["order_matters"]) else "wrong")

            rows.append({
                "item_id": rec["item_id"], "tier": rec["tier"],
                "model_key": rec["model_key"], "model_name": rec["model_name"],
                "status": status, "correct": int(status == "correct"),
                "latency_ms": rec["latency_ms"],
                "input_tokens": rec["input_tokens"], "output_tokens": rec["output_tokens"],
                "predicted_sql": (sql or "").replace("\n", " ")[:500],
                "error": (err or "")[:300],
            })
    con.close()

    out = ROOT / "results" / "per_item.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out}  ({len(rows)} rows)\n")

    for key in sorted({r["model_key"] for r in rows}):
        sub = [r for r in rows if r["model_key"] == key]
        n = sum(r["correct"] for r in sub)
        counts = {s: sum(1 for r in sub if r["status"] == s)
                  for s in ("parse_error", "exec_error", "api_error")}
        tiers = {t: (sum(r["correct"] for r in sub if r["tier"] == t),
                     sum(1 for r in sub if r["tier"] == t)) for t in (1, 2, 3)}
        print(f"{key:<6} {n}/{len(sub)}   "
              f"T1 {tiers[1][0]}/{tiers[1][1]}  T2 {tiers[2][0]}/{tiers[2][1]}  "
              f"T3 {tiers[3][0]}/{tiers[3][1]}   {counts}")
        for r in [r for r in sub if r["status"] != "correct"][:3]:
            print(f"       WRONG {r['item_id']} ({r['status']}): {r['predicted_sql'][:110]}")
        print()


if __name__ == "__main__":
    main()
