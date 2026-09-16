[Home](../README.md) · [Setup](SETUP.md) · [Settings](CONFIGURATION.md) · [Tests](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Sources](SOURCES.md)

## Exact settings for reproduction

The table below keeps the software's actual option names, with a plain-language description of what each controls.

| Component | Production value | What it controls / why it is here |
|---|---|---|
| Runtime | Blazux pinned preview image | Updated serving software; pinned Blazux recipe |
| Checkpoint | [drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47](https://huggingface.co/drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47), revision `a393318fb56d9aedc56d91b6f4962d9af26d2fe7` | NVIDIA-derived model, plus local FP8 side-layer conversion |
| Weight layout | NVFP4 experts; blockwise FP8 side layers; FP8 PLE; NVIDIA blockwise FP8 MTP experts | Existing hybrid layout retained |
| MTP | 2 speculative tokens, 65,536-token draft vocabulary | Draft two tokens ahead; main-model vocabulary remains full |
| Context | 500,000 tokens; YaRN 4; original 262,144 | Retained |
| RoPE | theta 10,000,000; partial factor 0.25; interleaved mRoPE [11,11,10] | Retained |
| KV cache | `auto` resolves to BF16; automatic sizing at utilization 0.80 (trial: 19.21 GiB) | Memory reserved for attention history |
| Scheduler | 8 sequences; 8,192 batched tokens; chunked prefill | Limits concurrent work and processes long inputs in chunks |
| Prefix caching | Enabled | Reuses processing of shared prompt beginnings; tested during the runtime upgrade |
| Graphs | PIECEWISE with explicit splitting operators | CPU PLE lookup must run outside capture |
| Attention | jschmied deterministic QSA top-k, `e0ef69d4`; exact Torch fallback off | Consistent sparse-attention selection; installed before these comparisons |
| PLE | mmap; 32 workers; prewarm off; MADV_RANDOM | Existing PLE upgrade retained |
| PLE gather threshold | `VLLM_PLE_MMAP_FAST_ROWS=0` | All nonempty gathers use the worker pool; measured against the former threshold of 512 |
| PLE metrics | Prometheus multiprocess export on; fresh 256 MiB tmpfs | Retained |
| Compilation caches | Persistent vLLM and FlashInfer bind mounts | Keeps compiled artifacts when the server container is recreated |
| GDN | Upstream preview GB10 FLA compatibility patches | Compatibility update for this GPU family |
| Sampling | FlashInfer sampler on; FlashInfer autotuning off; DeepGemm off | Retained |
| Tools / reasoning | `qwen3_coder`, `qwen3`; auto tool choice on | Retained |
| Reasoning-effort compatibility | `high` / `max` → `xhigh`; `minimal` → `low` | Launcher generates a template copy under the writable compilation-cache directory and mounts it read-only; original checkpoint template stays intact |
| API | OpenAI-compatible `/v1`; served name `qwen3.8-flash-next` | Port 8000 by default |

[`production.json`](../production.json) contains the full exported argument list, graph splitting operators, environment variables and container settings. [`serve.py`](../serve.py) uses that export to launch the server. Private hostnames, credentials and original user filesystem paths are excluded.
