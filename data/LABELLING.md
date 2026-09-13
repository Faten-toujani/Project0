# Labelling note

## Where the data came from

The database is original to this project. `build_db.py` generates `veloflux.db` from a
fixed seed (496), so a clean clone reproduces it byte-for-byte. Eight tables: 12 stations,
8 models, 200 bikes, 300 members, 4,000 trips, 1,848 payments, 260 maintenance records.

We deliberately did **not** use Chinook or Spider. Both have been public for years and
appear throughout model training data, so scores on them measure memorisation as much as
SQL ability — which would compress the gap between the three models and leave nothing to
report. The task is Spider-style; the schema is new.

The cost of this choice, stated plainly: all 60 questions were written by one author in
one phrasing style. Spider's questions are crowd-written and more linguistically varied.
Our results therefore generalise to this question style, not to all natural-language SQL.

## Difficulty tiers

Items are stratified so that accuracy can be read as a curve rather than a single number.

| Tier | Items | What it requires |
|---|---|---|
| 1 | 10 | Single table: `WHERE`, `ORDER BY`, `LIMIT`, one aggregate |
| 2 | 15 | One or two joins, `GROUP BY`, `HAVING`, `LEFT JOIN` semantics |
| 3 | 25 | Window functions, CTEs, correlated subqueries, self-joins, anti-joins, date arithmetic, top-N-per-group |

This distribution is v2. The v1 pilot used 20/20/10 and all three models scored 20/20 on
tier 1 — forty of fifty items separated nothing. The rebalance is documented in
`postmortem.md`; the pilot item set is preserved as `items_v1.jsonl`.

The schema contains deliberate traps: `trip.end_station_id` and
`maintenance.resolved_on` / `.cost` are nullable (an `INNER JOIN` or a bare `COUNT(*)`
silently gives the wrong answer), `member.referred_by` is a self-referencing foreign key,
and `name` appears on three tables while `city` appears on two.

## How the labels were checked

**Machine validation — all 60 items.** `validate_items.py` rejects any gold query that:

1. errors,
2. returns zero rows (an empty result is too easy to hit by accident),
3. has a tie at an `ORDER BY ... LIMIT` cut-off, making the expected answer ambiguous,
4. is **join-sensitive** without the question disambiguating — if swapping `JOIN` for
   `LEFT JOIN` changes the result, the wording must state whether unmatched rows are
   included.

All 60 pass. Check 4 was added after the v1 pilot, where a gold query used an inner join
that silently dropped a whole plan with no payments; both API models produced the
left-join reading and were marked wrong for being right. Every v2 question that touches a
join now states its own semantics explicitly.

**Independent human re-derivation — not performed.** The brief asks that two people check
every label. This is a solo project, so a genuinely independent second reading was not
available, and we do not claim one. The automated checks above are the primary control.
This is a real limitation: an error in a gold query is indistinguishable from a model
failure, which is exactly what happened in v1 and was caught only because all three models
failed the same item identically.

## Dev / test split

- `dev.jsonl` (10 items) — used while writing and fixing the prompt and parser.
- `items.jsonl` (50 items) — run once. The prompt was not changed after seeing any test
  result.

One disclosed exception: a parser defect was fixed after the v1 test run (it took the
first `SELECT` substring, which broke on an output prefixed `"SELECT statement:"`). Both
scores are reported in `postmortem.md`. The fix is model-agnostic and was applied
identically to all three.

## Known limitation of execution-based scoring

Scoring compares result sets, not SQL text, because infinitely many queries are
equivalent. This means execution accuracy is an **upper bound** on correctness: a wrong
query can coincidentally return the right rows. We reduce this by requiring every gold
query to return at least one row, but we do not eliminate it. An observed instance: on a
rounding item whose true value happened to be exact, a model that omitted the required
`ROUND()` was still scored correct.
