# Postmortem

> The brief: "A postmortem with no problems loses points." Write what actually went
> wrong, not a success story. Delete these quote blocks before handing in.

## What went wrong

> Candidates we already hit or expect to hit — keep the ones that are true, cut the rest,
> and add your own:
> - Ollama's docs require NVIDIA driver 550+; ours is 497.29. We planned for a CPU
>   fallback, then found it ran 100% on GPU anyway. Documented minimums were not what
>   the software enforced.
> - The 3B model wrapped its first output in backticks, so parser design became a
>   real task rather than an afterthought.
> - TODO: whatever breaks during the actual run.

## What we would do differently

> TODO

## What we learned

> Candidates:
> - 50 items is statistically thin. The 95% Wilson interval on 46/50 is roughly
>   +/-10 points, so a 3-point gap between two models is not evidence of a difference.
>   Tiered accuracy carries more signal than the aggregate.
> - Temperature 0 does not mean determinism on API models. Ollama with a fixed seed
>   is reproducible; the API models are not.
> - Self-hosting is a fixed hourly cost against a purely variable API cost, so the
>   break-even is a rate (requests/hour), not a total.
> - TODO
