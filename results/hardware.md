# Hardware and runtime settings

## Self-hosted model

- Model: `qwen2.5-coder:3b` (Q4_K_M), 2.2 GB resident
- Runtime: Ollama 0.33.3, HTTP API at `localhost:11434/api/generate`
- GPU: NVIDIA GeForce GTX 1650 Ti with Max-Q Design, 4 GB VRAM
- Driver: 497.29 (CUDA 11.5)
- `ollama ps` reported `100% GPU` at context 4096
- Settings: `temperature=0`, `seed=0`, `num_ctx=4096`, `num_predict=TODO`
- Environment: `OLLAMA_KEEP_ALIVE=30m`, `OLLAMA_NUM_PARALLEL=1` (sequential calls)
- Measured throughput: TODO tokens/sec (steady state, second call onward)

Note: Ollama's published requirement is driver 550+. Ours is 497.29 and the model still
loaded fully onto the GPU. We report what we measured, not what the docs predict.

## API models

- Sequential calls, no concurrency, no retries counted in latency
- Network path: TODO (city / connection type) -> Anthropic API
- Latency figures include network round-trip and are not comparable to the
  self-hosted figures as a measure of raw inference speed

## Prices used in cost.py

Pulled from anthropic.com/pricing on TODO (date), USD per million tokens:

| Model | Input | Output |
|---|---|---|
| claude-opus-5 | 5.00 | 25.00 |
| claude-haiku-4-5-20251001 | 1.00 | 5.00 |
