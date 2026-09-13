# Hardware and runtime settings

## Self-hosted model

- Model: `qwen2.5-coder:3b` (Q4_K_M), 2.2 GB resident
- Runtime: Ollama 0.33.3, HTTP API at `localhost:11434/api/generate`
- GPU: NVIDIA GeForce GTX 1650 Ti with Max-Q Design, 4 GB VRAM (Turing, compute 7.5)
- Driver: 497.29 (CUDA 11.5)
- `ollama ps` reported `100% GPU` at context 4096 throughout
- Settings: `temperature=0`, `seed=0`, `num_ctx=4096`, `num_predict=1000`
- Environment: `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_NUM_PARALLEL=1` (sequential calls)
- Measured throughput: 42–50 tokens/s steady state
- Measured latency: p50 3,370 ms, p95 4,543 ms over 50 sequential calls

Ollama's published requirement is NVIDIA driver 550 or newer. Ours is 497.29 — roughly
fifty major versions below that — and the model still loaded fully onto the GPU. We had
planned a CPU fallback and a driver update and needed neither. We report what we
measured, not what the documentation predicts.

A warm-up call using a representative prompt precedes the timed loop. Cold start costs
about 10 seconds (13,324 ms observed on the first item of an unwarmed run against a
2,700 ms steady state), which would otherwise distort p95 across 50 calls. The
`OLLAMA_KEEP_ALIVE=30m` setting keeps the model resident for the duration of the run.

Latency floor: a 41-token prompt took 2,518 ms and a 530-token prompt took 2,670 ms,
while generation itself accounts for roughly 200 ms. Most of each local call is fixed
per-request overhead rather than inference.

## API models

- Sequential calls, no concurrency, no retries counted in latency
- Network path: Tunis, fibre → Anthropic API
- Latency includes network round-trip and is not comparable to the self-hosted figures
  as a measure of raw inference speed
- The Anthropic SDK removed `temperature`, `top_p` and `top_k` in v1.0 (August 2026)
  because current models reject non-default sampling values, so both API models ran at
  provider defaults. Only `max_tokens` (1000) was held constant across all three models.

## Tokenisation

The same prompt is counted differently by each provider, which affects cost directly:

| Model | Mean input tokens | Mean output tokens |
|---|---|---|
| claude-opus-5 | ~1,137 | 77 |
| claude-haiku-4-5 | ~640 | 41 |
| qwen2.5-coder:3b | ~533 | 29 |

Opus counts 78% more input tokens than Haiku for byte-identical text, so part of the
9.6× cost gap between them is tokenisation rather than list price.

## Prices used in cost.py

Pulled from anthropic.com/pricing on 13 September 2026, USD per million tokens:

| Model | Input | Output |
|---|---|---|
| claude-opus-5 | 5.00 | 25.00 |
| claude-haiku-4-5-20251001 | 1.00 | 5.00 |

## Self-hosting cost model

Fixed hourly cost, independent of request volume:

- Hardware: $900 purchase (2,800 TND, 2021), amortised over 5 years → $0.0205/h
- Power: ~90 W under load at $0.21/kWh → $0.0189/h
- Total: **$0.0394/h**

Break-even is therefore a rate, not a total: V* = hourly cost ÷ cost per request.
Self-hosting becomes cheaper than Haiku above 41 req/hour and cheaper than Opus above
4 req/hour; one machine tops out near 1,068 req/hour.
