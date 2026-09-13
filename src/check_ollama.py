import requests, time

t0 = time.perf_counter()
r = requests.post("http://localhost:11434/api/generate", json={
    "model": "qwen2.5-coder:3b",
    "prompt": "Return only a SQL statement that selects the number 1.",
    "stream": False,
    "options": {"temperature": 0, "seed": 0, "num_ctx": 4096, "num_predict": 256},
}).json()

print("wall ms      ", round((time.perf_counter() - t0) * 1000))
print("response     ", r["response"].strip()[:120])
print("prompt tokens", r["prompt_eval_count"])
print("gen tokens   ", r["eval_count"])
print("tokens/sec   ", round(r["eval_count"] / (r["eval_duration"] / 1e9), 1))