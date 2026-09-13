# Project 0 — Bake-Off: Text-to-SQL across three models

CS496 AI Engineering · Mediterranean Institute of Technology · Fall 2026

**Task.** Given a natural-language question and a fixed SQLite schema, produce one SQL
query. An answer is correct if executing it returns the same result set as the gold
query. 50 test items, stratified across three difficulty tiers.

**Models compared** — same prompt, same item order, same parser, same output-token
limit, sequential calls, no retries:

| Role | Model | Run date |
|---|---|---|
| Top API | `claude-opus-5` | 13 Sep 2026 |
| Cheap API | `claude-haiku-4-5-20251001` | 13 Sep 2026 |
| Open weights, self-hosted | `qwen2.5-coder:3b` (Q4_K_M), Ollama 0.33.3 | 13 Sep 2026 |

## Setup

```bash
python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt && cp .env.example .env
```

(macOS/Linux: `.venv/bin/activate`.) Put your key in `.env`, and make sure Ollama is
serving the local model: `ollama pull qwen2.5-coder:3b`.

## Run

```bash
python src/run.py --all && python src/score.py && python src/cost.py
```

`run.py` writes one immutable JSON per call to `results/raw/`. `score.py` and `cost.py`
read only from `results/raw/` — re-scoring never costs another API call.

## Results (n = 50)

| Model | Correct | 95% CI | Parse err | Exec err | API err | p50 ms | p95 ms | $/1k req |
|---|---|---|---|---|---|---|---|---|
| claude-opus-5 | 47/50 | 84–98% | 1 | 1 | 0 | 2,336 | 4,936 | $9.33 |
| claude-haiku-4-5 | 43/50 | 74–93% | 0 | 4 | 0 | 1,200 | 1,795 | $0.97 |
| qwen2.5-coder:3b | 32/50 | 50–76% | 0 | 5 | 0 | 3,370 | 4,543 | $0.039 |

Accuracy by tier — this is where the models actually differ:

| Model | Tier 1 /10 | Tier 2 /15 | Tier 3 /25 |
|---|---|---|---|
| claude-opus-5 | 10 | 14 | 23 |
| claude-haiku-4-5 | 10 | 15 | 18 |
| qwen2.5-coder:3b | 10 | 13 | 9 |

On tiers 1–2 combined the three models score 24/25, 25/25 and 23/25 — statistically
indistinguishable. All separation is in tier 3.

**Choice: Claude Haiku 4.5.** 1.9× faster at p50, 9.6× cheaper than Opus, and it matches
Opus on the 25 tier-1 and tier-2 items. We would switch to Opus if tier-3-style queries
exceeded about a fifth of traffic, or if a wrong answer carried real cost. Full reasoning
in `report.pdf`.

## Pilot run (v1)

An earlier run with an easier item set (tiers 20/20/10) is preserved in the repo:
`data/items_v1.jsonl`, `data/items_src_v1.py`, `results/raw/test_v1/`,
`results/per_item_v1.csv`, `results/summary_v1.csv`. It produced Haiku 49, Opus 47,
local 44, with all three scoring 20/20 on tier 1 — no discriminative power. v2
rebalanced toward tier 3. See `postmortem.md`.

## Data

`data/veloflux.db` — an e-bike rental network, 8 tables, built deterministically by
`data/build_db.py` (seed 496). The schema is original to this project so that no model
has seen it in training; see `data/LABELLING.md`.

- `data/items.jsonl` — 50 test items (frozen; the prompt was never tuned against these)
- `data/dev.jsonl` — 10 dev items (used to debug the prompt and parser)
- `data/validate_items.py` — rejects gold queries that error, return nothing, have a tie
  at a `LIMIT` cut-off, or are join-sensitive without the question disambiguating

## Repo layout

```
data/     schema, database builder, items, label validator
src/      prompt.py, run.py, score.py, cost.py
results/  raw/ (one JSON per call), per_item.csv, summary.csv, hardware.md
```

## Contributions

Solo project — all work by Faten Toujani: schema and data generation, item authoring and
validation, harness (`run.py`, `score.py`, `cost.py`), both runs, analysis, report and
postmortem.
