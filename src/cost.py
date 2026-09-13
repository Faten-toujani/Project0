"""Build summary.csv: accuracy, latency percentiles, cost per 1k requests, break-even.

Reads results/per_item.csv only. Never calls an API.

Usage:  python src/cost.py
"""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# USD per 1M tokens, from anthropic.com/pricing. RECORD THE DATE YOU PULLED THESE.
PRICES = {
    "claude-opus-5":              {"in": 5.00, "out": 25.00},
    "claude-haiku-4-5-20251001":  {"in": 1.00, "out": 5.00},
}

# Self-hosted cost model. Fixed hourly cost, independent of how many requests you serve.
HARDWARE_COST = 900.0          # laptop purchase price, USD
AMORTISE_YEARS = 5
POWER_W = 90                   # measured draw under load
ELECTRICITY_PER_KWH = 0.21     # USD

HOURLY_HARDWARE = HARDWARE_COST / (AMORTISE_YEARS * 365 * 24)
HOURLY_POWER = (POWER_W / 1000) * ELECTRICITY_PER_KWH
HOURLY_SELF_HOST = HOURLY_HARDWARE + HOURLY_POWER


def pct(values, p):
    """Nearest-rank percentile. No numpy, no interpolation guesswork."""
    if not values:
        return 0.0
    s = sorted(values)
    k = max(0, math.ceil(p / 100 * len(s)) - 1)
    return s[k]


def wilson(k, n, z=1.96):
    """95% CI on a proportion. 50 items is thin - the interval is the honest answer."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    rows = list(csv.DictReader((ROOT / "results" / "per_item.csv").open(encoding="utf-8")))
    out = []

    for key in sorted({r["model_key"] for r in rows}):
        sub = [r for r in rows if r["model_key"] == key]
        name = sub[0]["model_name"]
        n = len(sub)
        correct = sum(int(r["correct"]) for r in sub)
        lat = [float(r["latency_ms"]) for r in sub]
        tin = sum(int(r["input_tokens"]) for r in sub)
        tout = sum(int(r["output_tokens"]) for r in sub)
        lo, hi = wilson(correct, n)

        if name in PRICES:
            p = PRICES[name]
            cost_per_req = (tin / n / 1e6) * p["in"] + (tout / n / 1e6) * p["out"]
            basis = "list price x measured tokens"
        else:
            # Self-hosted: fixed hourly cost divided by what the box can serve per hour.
            req_per_hour = 3_600_000 / (sum(lat) / n)
            cost_per_req = HOURLY_SELF_HOST / req_per_hour
            basis = f"{HOURLY_SELF_HOST:.4f} USD/h / {req_per_hour:.0f} req/h"

        out.append({
            "model_key": key, "model_name": name,
            "n": n, "correct": correct,
            "accuracy": round(correct / n, 3),
            "ci95_low": round(lo, 3), "ci95_high": round(hi, 3),
            "parse_errors": sum(1 for r in sub if r["status"] == "parse_error"),
            "exec_errors": sum(1 for r in sub if r["status"] == "exec_error"),
            "api_errors": sum(1 for r in sub if r["status"] == "api_error"),
            "t1": sum(int(r["correct"]) for r in sub if r["tier"] == "1"),
            "t2": sum(int(r["correct"]) for r in sub if r["tier"] == "2"),
            "t3": sum(int(r["correct"]) for r in sub if r["tier"] == "3"),
            "p50_ms": round(pct(lat, 50), 1), "p95_ms": round(pct(lat, 95), 1),
            "mean_in_tokens": round(tin / n, 1), "mean_out_tokens": round(tout / n, 1),
            "cost_per_1k": round(cost_per_req * 1000, 4),
            "cost_per_1k_at_100x": round(cost_per_req * 1000, 4),  # API price is linear
            "cost_basis": basis,
        })

    dest = ROOT / "results" / "summary.csv"
    with dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"wrote {dest}\n")

    for r in out:
        print(f"{r['model_key']:<6} {r['correct']}/{r['n']} "
              f"(95% CI {r['ci95_low']:.0%}-{r['ci95_high']:.0%})  "
              f"T1 {r['t1']} T2 {r['t2']} T3 {r['t3']}  "
              f"p50 {r['p50_ms']:>7.0f}ms  p95 {r['p95_ms']:>7.0f}ms  "
              f"${r['cost_per_1k']:.3f}/1k")

    # --- break-even -----------------------------------------------------
    # Self-hosting is a FIXED hourly cost. The API is purely variable.
    # So the crossover is a RATE, not a total: V* = hourly_self_host / cost_per_request.
    # Below V*, the API is cheaper. Above V*, self-hosting is - but only up to the
    # throughput ceiling of one machine.
    print(f"\nself-host fixed cost: ${HOURLY_SELF_HOST:.4f}/hour")
    local = next((r for r in out if r["model_name"] not in PRICES), None)
    for r in out:
        if r["model_name"] not in PRICES:
            continue
        c = r["cost_per_1k"] / 1000
        v_star = HOURLY_SELF_HOST / c if c else float("inf")
        print(f"  vs {r['model_key']:<6}: break-even at {v_star:,.0f} req/hour", end="")
        if local:
            ceiling = 3_600_000 / (local["p50_ms"] or 1)
            print(f"  |  our box tops out near {ceiling:,.0f} req/hour"
                  f"{'  -> self-hosting never wins on one machine' if v_star > ceiling else ''}")
        else:
            print()


if __name__ == "__main__":
    main()
