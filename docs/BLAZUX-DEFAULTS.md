# Blazux-default comparison — September 16, 2026

## What changed

Same prepared Drowzeys weights, temperature, seeds and synthetic fixtures. Candidate uses the unmodified pinned [Blazux source](https://github.com/blazux/qwen3.8-Flash-DGX/tree/ed65cc80646e85cf6631b93d7dfcf9412183cc30) and its preview Dockerfile. Model override, persistent compilation caches and multiprocess metric export are upstream-supported options.

| Setting | Previous | Candidate / selected |
|---|---|---|
| Image | Custom vLLM 0.29 | Blazux pinned preview |
| Context | 679,000 | 500,000 |
| KV | Fixed 19.38 GiB | Automatic 0.80; trial boot 19.21 GiB |
| Draft depth | 3 | 2 |
| Draft vocabulary | Full | 65,536 selected IDs |
| PLE prewarm | On | Off |
| Graph splitting / compatibility patches | Custom v0.29 set | Upstream preview set |
| Phase timing counters | Older module | Current upstream PLE module |
| Weights, YaRN factor 4, BF16 KV, prefix cache, deterministic top-k, worker-pool PLE | Enabled | Retained |

This changes several variables together. It cannot attribute a difference to vocabulary reduction, drafting depth, automatic allocation or the image alone. Upstream default changes are not all upgrades relative to a later vLLM release.

## Measurements and selection

Two short passes per arm, six fixtures each: code clamp/deduplication, two native tool-call tasks, arithmetic and 32k retrieval. Then one 483k retrieval per arm. All **26 requests** passed their scripted grades. Prefix-cache salts were unique per phase and fixture; temperature and seed were fixed. Current arm ran first, candidate second, one start per arm. Independent-start repeatability and broad agent quality were not established.

| Metric | Previous pass 1 / pass 2 | Candidate pass 1 / pass 2 |
|---|---:|---:|
| Pooled decode estimate | 42.29 / 43.70 tok/s | 44.79 / 46.66 tok/s |
| Sum of short-request elapsed times | 45.58 / 43.98 s | 50.18 / 43.98 s |

Pooled decode = sum(completion tokens minus one per request) / sum(inter-token-latency counter deltas). It excludes prompt processing. Output lengths may differ. Longer retrieval passed in 325.74 s before and 312.89 s after, with one preemption in each. No zero-preemption claim is made.

The user selected the candidate after seeing the results, accepting the 500k limit. No pre-registered statistical superiority gate was used for this whole-recipe trial. The prior 679k configuration is preserved in [previous-679k-config.json](../evidence/previous-679k-config.json).

## Re-running and inspecting

See [benchmark instructions](../benchmark/README.md). Saved [requests, responses, grades and counters](../blazux-comparison/) cover all requests in this comparison. They are synthetic benchmark data, not user conversations. Earlier experiments retain their separately described evidence limitations. Re-running changes the server's cache state and consumes inference time.
