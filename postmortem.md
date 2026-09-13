# Postmortem

## What went wrong

**The first test set had no discriminative power.** In the v1 pilot all three models scored
20/20 on tier 1 and 18–19/20 on tier 2. Forty of fifty items separated nothing. The brief
warns about exactly this ("If they all do, you learn nothing") and we walked into it because
we skipped proper dev-set calibration under time pressure. v2 rebalanced the tiers from
20/20/10 to 10/15/25.

**We wrote a wrong gold query using the trap we designed ourselves.** v1's t2-02 used an inner
join, which silently dropped the Basic plan (52 members, zero fee, therefore no payment rows).
Both API models used LEFT JOIN and returned all five plans — the better reading of the
question — and were marked wrong for being right. The nullable-join trap we deliberately built
into the schema caught its own authors. v2 adds a `join_sensitive` check to the validator: if
swapping JOIN for LEFT JOIN changes a gold query's result, the question must state which rows
to include, or the item is rejected.

**The output-token cap was set too low and failed silently.** At 400 tokens, Opus's v1 t3-04
answer was truncated mid-clause. It did not error — SQLite accepted the dangling `ON mt.bike_id`
as a truthy expression and returned wrong rows. A cap calibrated against a terse model (Haiku
averages 41 output tokens) invisibly penalises a verbose one (Opus averages 77, and far more on
hard items). Raised to 1000 for v2.

**Our parser had a bug that cost the top model a point.** It took the first `SELECT` it found,
so Opus's `"SELECT statement:  SELECT ROUND(...)"` was handed to SQLite as broken input. Fixed
to try every candidate start and pick the first that compiles under `EXPLAIN`. Because run and
score are separate programs and raw responses are immutable, re-scoring cost nothing — no API
calls were repeated. This disclosure matters: the fix was made after seeing test results, which
is a mild form of touching the test set, so both scores are reported (46/50 before, 47/50 after).

**The brief's "temperature 0" requirement is not satisfiable.** The Anthropic SDK removed
temperature/top_p/top_k in v1.0 (August 2026) because current models reject non-default sampling
values. Two of our three models cannot be set to temperature 0 at all. We held only max_tokens
constant.

**Ollama's documented hardware minimum was wrong for our machine.** The docs require driver
550+; ours is 497.29 and the 3B loaded fully to GPU anyway. We had planned a CPU fallback and a
driver update, and needed neither. Measured behaviour beat documentation.

## What we would do differently

Calibrate difficulty on the dev set before freezing the test set, rather than discovering the
ceiling effect after a full paid run. Set the token cap from the most verbose model's observed
output, not the median. Write the validator's ambiguity checks before writing the items, since
the check we added after the fact would have caught the defect we shipped. Print real error
messages in the harness from the start — our first API run produced ten silent `ERR` lines and
cost us a debugging cycle to discover a one-line SDK signature change.

## What we learned

**Fifty items is statistically thin.** The 95% Wilson intervals for Opus (84–98%) and Haiku
(74–93%) overlap, so we cannot claim Opus is better overall. Aggregate accuracy on n=50 cannot
resolve differences smaller than roughly ten points, and a report that declares a winner on a
four-point gap is claiming more than its data supports.

**Tiering carries the signal that the aggregate hides.** On tiers 1 and 2 the three models score
24/25, 25/25 and 23/25 — indistinguishable, with the cheapest nominally best. All separation
lives in tier 3: 23/25, 18/25, 9/25. Without the stratification we would have reported one
number and learned nothing about *where* the expensive model earns its price.

**Degradation rate is more informative than any single score.** v1 → v2, same models and schema,
harder questions: Opus 47→47, Haiku 49→43, local 44→32. How steeply a model falls as complexity
rises tells you more about deployment risk than its score on one test set.

**Separating run from score is what made recovery possible.** Two parser defects were found after
the full run. Both were fixed and re-scored for free because `run.py` writes immutable raw JSON
and never scores anything. Had scoring lived inside the run loop, each fix would have meant
another paid run and a fresh set of latency numbers.

**Cost was not the deciding variable.** Self-hosting is 25× cheaper than Haiku and beats it above
41 requests/hour, well inside one machine's capacity. It also answers 32/50 against 43/50. The
cheapest option loses 11 correct answers out of 50 to save $93 per 100,000 requests.
