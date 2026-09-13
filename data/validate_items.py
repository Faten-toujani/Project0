"""Check every gold query before it is allowed into the test set.

Rejects:
  - queries that error
  - queries returning zero rows (an empty result is too easy to hit by accident)
  - ORDER BY ... LIMIT queries with a tie at the cut-off (ambiguous answer)
  - JOIN-sensitive queries whose question does not disambiguate  <-- added after
    the v1 pilot, where a gold query silently dropped a whole group by using an
    inner join. The models used LEFT JOIN and were marked wrong for being right.
Warns on:
  - single-cell answers of 0 or 1 (guessable, inflates execution accuracy)
"""
import re
import sqlite3
from items_src import DEV, TEST

DB = "veloflux.db"
INCLUSIVE = re.compile(r"include (every|stations|models|plans|cities|those)|do not count|"
                       r"ignore (unresolved|records)|at least one|use 0|using 0|only",
                       re.I)


def run(con, sql):
    return con.execute(sql).fetchall()


def tie_at_cutoff(con, sql):
    m = re.search(r"\bLIMIT\s+(\d+)(?:\s+OFFSET\s+(\d+))?\s*$", sql, re.I)
    if not m or "ORDER BY" not in sql.upper():
        return False
    n, off = int(m.group(1)), int(m.group(2) or 0)
    wider = re.sub(r"\bLIMIT\s+\d+(?:\s+OFFSET\s+\d+)?\s*$", f"LIMIT {n + off + 1}",
                   sql, flags=re.I)
    rows = run(con, wider)
    if len(rows) < n + off + 1:
        return False
    return rows[n + off - 1][1:] == rows[n + off][1:] if len(rows[0]) > 1 else \
        rows[n + off - 1] == rows[n + off]


def join_sensitive(con, sql):
    """Does swapping inner JOIN for LEFT JOIN change the answer?

    If yes, the wording must say whether unmatched rows are included - otherwise
    two careful people give two different answers, and so do two models.
    """
    if not re.search(r"(?<!LEFT )\bJOIN\b", sql, re.I):
        return False
    alt = re.sub(r"(?<!LEFT )\bJOIN\b", "LEFT JOIN", sql, flags=re.I)
    try:
        return sorted(map(repr, run(con, sql))) != sorted(map(repr, run(con, alt)))
    except Exception:
        return False


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
            if join_sensitive(con, sql) and not INCLUSIVE.search(question):
                bad.append(f"{iid}: JOIN-SENSITIVE and question does not disambiguate")
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
    print("\nresult shape by tier:")
    for tier in (1, 2, 3):
        sizes = [len(run(con, sql)) for i, t, o, q, sql in TEST if t == tier]
        print(f"  tier {tier}: {len(sizes):>2} items, rows min={min(sizes)} "
              f"median={sorted(sizes)[len(sizes)//2]} max={max(sizes)}")
    con.close()


if __name__ == "__main__":
    main()
