# Project 0 — Bake-Off: Text-to-SQL across three models

CS496 AI Engineering · Mediterranean Institute of Technology · Fall 2026

**Task.** Given a natural-language question and a fixed SQLite schema, produce one SQL
query. An answer is correct if executing it returns the same result set as the gold
query. 50 test items, stratified across three difficulty tiers.

**Models compared** (all with the same prompt, temperature 0, same output-token limit,
same parser, same 50 items in the same order):

| Role | Model | Run date |
|---|---|---|
| Top API | `claude-opus-5` | TODO |
| Cheap API | `claude-haiku-4-5-20251001` | TODO |
| Open weights, self-hosted | `qwen2.5-coder:3b` (Q4_K_M) via Ollama 0.33.3 | TODO |

## Setup

```bash
python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt && cp .env.example .env
```

Then put your key in `.env`, and make sure Ollama is serving `qwen2.5-coder:3b`
locally (`ollama pull qwen2.5-coder:3b`).

## Run

```bash
python src/run.py --all && python src/score.py && python src/cost.py
```

`run.py` writes one immutable JSON per call to `results/raw/`. `score.py` and
`cost.py` read only from `results/raw/` — re-scoring never costs another API call.

## Results

TODO — filled from `results/summary.csv` after the run.

| Model | Correct /50 | Parse errors | Refusals/timeouts | p50 ms | p95 ms | Cost /1k req |
|---|---|---|---|---|---|---|
| claude-opus-5 | | | | | | |
| claude-haiku-4-5 | | | | | | |
| qwen2.5-coder:3b | | | | | | |

Accuracy by tier:

| Model | Tier 1 /20 | Tier 2 /20 | Tier 3 /10 |
|---|---|---|---|
| claude-opus-5 | | | |
| claude-haiku-4-5 | | | |
| qwen2.5-coder:3b | | | |

## Data

`data/veloflux.db` — an e-bike rental network, 8 tables, built deterministically by
`data/build_db.py` (seed 496). The schema is original to this project so that no model
has seen it during training; see `data/LABELLING.md` for why that matters and how the
gold queries were checked.

- `data/items.jsonl` — 50 test items (frozen; the prompt was never tuned against these)
- `data/dev.jsonl` — 10 dev items (used to debug the prompt and parser)

## Repo layout

```
data/     schema, database builder, items, label validator
src/      prompt, run, score, cost
results/  raw/ (one JSON per call), per_item.csv, summary.csv, hardware.md
```

## Contributions

TODO — one entry per member, naming what they actually did.

- **NAME** —
- **NAME** —
- **NAME** —
- **NAME** —
