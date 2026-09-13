# Labelling note

## Where the data came from

The database is original to this project. `build_db.py` generates `veloflux.db` from a
fixed seed (496), so a clean clone reproduces it byte-for-byte.

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
| 1 | 20 | Single table: `WHERE`, `ORDER BY`, `LIMIT`, one aggregate |
| 2 | 20 | One or two joins, `GROUP BY`, `HAVING` |
| 3 | 10 | CTEs, correlated subqueries, self-joins, `OFFSET`, date arithmetic |

The schema contains deliberate traps: `trip.end_station_id` and
`maintenance.resolved_on` / `.cost` are nullable (an `INNER JOIN` or a `COUNT(*)`
silently gives the wrong answer), `member.referred_by` is a self-referencing foreign
key, and `name` appears on three tables while `city` appears on two.

## How the labels were checked

1. **Machine validation — all 60 items.** `validate_items.py` rejects any gold query
   that errors, returns zero rows, or has a tie at an `ORDER BY ... LIMIT` cut-off that
   would make the answer ambiguous. All 60 pass.
2. **Independent re-derivation — 15-item sample.** TODO: name the two members, the
   items checked, and any disagreements found and how they were resolved.

## Dev / test split

- `dev.jsonl` (10 items) — used while writing and fixing the prompt and parser.
- `items.jsonl` (50 items) — run once, at the end. The prompt was not changed after
  seeing test results. Tuning the prompt on test would fit it to the answer key and
  inflate every model's score by an unknown amount.

## Known limitation of execution-based scoring

Scoring compares result sets, not SQL text, because infinitely many queries are
equivalent. This means execution accuracy is an **upper bound** on correctness: a wrong
query can coincidentally return the right rows. We reduce this by requiring every gold
query to return at least one row, but we do not eliminate it.
