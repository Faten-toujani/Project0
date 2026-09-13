"""Run every item against a model and save one immutable JSON per call.

run.py never scores anything. score.py and cost.py read only from results/raw/,
so a parser bug costs nothing to fix - you re-score, you do not re-pay.

Usage:
    python src/run.py --all
    python src/run.py --model opus --split dev
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

import prompt as P

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results" / "raw"
load_dotenv(ROOT / ".env")

MODELS = {
    "opus":  {"kind": "anthropic", "name": "claude-opus-5"},
    "haiku": {"kind": "anthropic", "name": "claude-haiku-4-5-20251001"},
    "local": {"kind": "ollama",    "name": "qwen2.5-coder:3b"},
}

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_OPTIONS = {
    "temperature": P.TEMPERATURE,
    "seed": 0,
    "num_ctx": 4096,
    "num_predict": P.MAX_OUTPUT_TOKENS,
}


def load_items(split):
    path = ROOT / "data" / ("items.jsonl" if split == "test" else "dev.jsonl")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

def call_anthropic(client, model_name, text):
    """Returns (output_text, input_tokens, output_tokens).

    Note: anthropic SDK v1.0 removed temperature/top_p/top_k from messages.create().
    Current models reject non-default sampling values, so the API models run at
    their default sampling. Only max_tokens is controllable across all three.
    """
    msg = client.messages.create(
        model=model_name,
        max_tokens=P.MAX_OUTPUT_TOKENS,
        messages=[{"role": "user", "content": text}],
    )
    out = "".join(b.text for b in msg.content if b.type == "text")
    return out, msg.usage.input_tokens, msg.usage.output_tokens


def call_ollama(model_name, text):
    r = requests.post(OLLAMA_URL, timeout=180, json={
        "model": model_name,
        "prompt": text,
        "stream": False,
        "options": OLLAMA_OPTIONS,
    })
    r.raise_for_status()
    d = r.json()
    return d["response"], d.get("prompt_eval_count", 0), d.get("eval_count", 0)


def run_model(key, split):
    cfg = MODELS[key]
    items = load_items(split)
    outdir = RAW / split / key
    outdir.mkdir(parents=True, exist_ok=True)

    client = None
    if cfg["kind"] == "anthropic":
        import anthropic
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise SystemExit("ANTHROPIC_API_KEY missing - copy .env.example to .env")
        client = anthropic.Anthropic()
    else:
        # Warm-up: the first call after a cold start includes ~10s of model load.
        # That is a real cost but a one-off, so we exclude it from the timed run
        # and say so in the report.
        print("  warming up local model ...")
        call_ollama(cfg["name"], P.build(items[0]["question"]))

    print(f"{key} ({cfg['name']}) on {split}: {len(items)} items")
    for i, item in enumerate(items, 1):
        text = P.build(item["question"])
        record = {
            "item_id": item["id"],
            "tier": item["tier"],
            "split": split,
            "model_key": key,
            "model_name": cfg["name"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt_chars": len(text),
        }
        t0 = time.perf_counter()
        try:
            if cfg["kind"] == "anthropic":
                out, tin, tout = call_anthropic(client, cfg["name"], text)
            else:
                out, tin, tout = call_ollama(cfg["name"], text)
            record.update(output=out, input_tokens=tin, output_tokens=tout, error=None)
        except Exception as e:
            # A failed call is not a free pass: it is scored as wrong.
            record.update(output="", input_tokens=0, output_tokens=0,
                          error=f"{type(e).__name__}: {e}")
        record["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)

        (outdir / f"{item['id']}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        flag = "ERR" if record["error"] else "   "
        print(f"  [{i:>2}/{len(items)}] {item['id']:<7} {record['latency_ms']:>8.0f} ms {flag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS) + ["all"], default="all")
    ap.add_argument("--split", choices=["dev", "test"], default="test")
    ap.add_argument("--all", action="store_true", help="all models on the test split")
    a = ap.parse_args()

    split = "test" if a.all else a.split
    keys = list(MODELS) if (a.all or a.model == "all") else [a.model]
    for k in keys:
        run_model(k, split)


if __name__ == "__main__":
    main()
