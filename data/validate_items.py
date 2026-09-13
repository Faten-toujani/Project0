"""Check every gold query before it is allowed into the test set.

Rejects:
  - queries that error
  - queries returning zero rows (an empty result is too easy to hit by accident)
  - LIMIT-with-ORDER-BY queries where a tie at the cut-off makes the answer ambiguous
Warns on:
  - single-cell answers of 0 or 1 (guessable, inflates execution accuracy)
"""
import json
import re
import sqlite3

from items_src import DEV, TEST

DB = "veloflux.db"


def run(con, sql):
    return con.execute(sql).fetchall()


def tie_at_cutoff(con, sql):
    """For ORDER BY ... LIMIT n, check row n and row n+1 differ on the sort key."""
    m = re.search(r"\bLIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?\s*$", sql, re.I)
    if not m or "ORDER BY" not in sql.upper():
        return False
    n, off = int(m.group(1)), int(m.group(2) or 0)
    wider = re.sub(r"\bLIMIT\s+\d+(?:\s+OFFSET\s+\d+)?\s*$", f"LIMIT {n + off + 1}", sql, flags=re.I)
    rows = run(con, wider)
    if len(rows) < n + off + 1:
        return False
    return rows[n + off - 1][1:] == rows[n + off][1:] if len(rows[0]) > 1 else \
        rows[n + off - 1] == rows[n + off]


def main():
    con = sqlite3.connect(DB)
    bad, warn = [], []
    for label, items in (("DEV", DEV), ("TEST", TEST)):
        for iid, tier, order_matters, question, sql in items:
            try:
                rows = run(con, sql)
            except Exception as e:
                bad.append(f"{iid}: ERROR {e}")
                continue
            if len(rows) == 0:
                bad.append(f"{iid}: EMPTY result")
                continue
            if order_matters and tie_at_cutoff(con, sql):
                bad.append(f"{iid}: TIE at LIMIT cut-off -> ambiguous")
            if len(rows) == 1 and len(rows[0]) == 1 and rows[0][0] in (0, 1, None):
                warn.append(f"{iid}: guessable single value {rows[0][0]!r}")
        print(f"{label}: {len(items)} items")
    print()
    for b in bad:
        print("FAIL ", b)
    for w in warn:
        print("WARN ", w)
    if not bad:
        print("all gold queries OK")

    # difficulty sanity: how many rows / columns does each tier return
    print("\nresult shape by tier:")
    for tier in (1, 2, 3):
        sizes = []
        for iid, t, om, q, sql in TEST:
            if t == tier:
                r = run(con, sql)
                sizes.append(len(r))
        print(f"  tier {tier}: {len(sizes)} items, rows returned min={min(sizes)} "
              f"median={sorted(sizes)[len(sizes)//2]} max={max(sizes)}")
    con.close()


if __name__ == "__main__":
    main()
