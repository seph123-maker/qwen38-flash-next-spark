[Home](../README.md) · [Setup](SETUP.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Sources](SOURCES.md)

# Current configuration (live since 2026-10-15)

Canonical spec of what is actually running, byte-verified against `docker inspect` of the
live container (2026-10-15). Machine-readable truth: [recipe-current.json](../recipe-current.json);
one-shot launch: [scripts/docker-run-current.sh](../scripts/docker-run-current.sh).
The September settings formerly documented here are superseded history (bottom).

## Target hardware
DGX Spark (GB10): 121 GiB LPDDR5x unified (~273 GB/s), 20 cores (10 Cortex-X925 +
10 Cortex-A725), local NVMe. Driver 580.178.04, CUDA 13.0.2. One heavy workload at a time.

## Exact settings for reproduction

| Component | Current value | What it controls / why it is here |
|---|---|---|
| Runtime | `qwen38-published:20261004-v031` (base `vllm/vllm-openai:v0.31.0`, commit `db9527a4`) | Blazux-lineage vLLM 0.31 image |
| Checkpoint | [nvidia/Qwen3.8-Flash-Next-NVFP4](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4), snapshot `fc694b54…-fp8hybrid` | Official NVIDIA NVFP4 weights with FP8 side-layer hybrid layout (supersedes the September drowzeys-derived snapshot) |
| Weight layout | NVFP4 backbone (E2M1 + FP8 micro-scales); FP8 dense/attention layers; FP8 PLE; FP8 MTP experts | 0.5625 B/weight backbone |
| Context | **524,288** tokens | single-session ceiling; exact 2.000× native |
| RoPE / YaRN | **factor 2.0**; theta 10,000,000; partial 0.25; interleaved mRoPE [11,11,10]; original 262,144 | factor = target/native (HF convention); previous factor 4.0 was calibrated for 1,048,576 and over-interpolated |
| KV cache | **fp8_e4m3**, automatic sizing at GMU 0.80 | storage-fp8 — QSA Triton kernel dequantizes in-kernel, indexer side-cache stays bf16 (verified in build source; AMD branch differs). Pool: **1,068,740 tokens**, 2.03× concurrency @524,288 |
| Scheduler | **4 sequences**; 8,192 batched tokens; chunked prefill | single user; idle slots were costing ~0.28 GiB each of GDN state |
| Prefix caching | enabled (GDN align-mode, auto-configured) | 33–61% hit rates measured; cold==warm replay verified exact |
| Graphs | PIECEWISE with 19 explicit splitting ops | CPU PLE gather + dynamic QSA indexing cannot be CUDA-graph captured |
| Attention | deterministic QSA top-k (`VLLM_QSA_DET_TOPK=1`, `_C_det.so`); exact-torch off | reproducible sparse block selection |
| PLE | mmap from NVMe, MADV_RANDOM, **16 workers, FAST_ROWS=256**, prewarm off | 47.7 GiB table streamed; dispatch measured faster than inline for 384-row decode batches (4.4–6.3 vs 7.4 ms/op) |
| PLE metrics | Prometheus multiproc export on fresh **256 MiB tmpfs** | LOAD-BEARING: missing tmpfs = API-server crash loop (`counter_1.db` FileNotFoundError) |
| MTP | 2 speculative tokens, 65,536-token draft vocab (`/opt/llm/…`, absolute path) | live acceptance 71.7% / 53.9% per position → 2.26 tok/pass |
| Compilation caches | persistent vLLM/CUDA/Triton/FlashInfer bind mounts | survive container recreation |
| Sampling | FlashInfer sampler on; autotuning off; DeepGEMM off (Hopper/SM100-only) | unchanged |
| Tools / reasoning | `qwen3_coder`, `qwen3`, auto tool choice | unchanged |
| Reasoning-effort compatibility | `high`/`max` → `xhigh`; `minimal` → `low` via `effort-alias.jinja` bind (still live) | unchanged from September |
| API | OpenAI-compatible `/v1`, served name `qwen3.8-flash-next`, port 8000, no auth | LAN-only exposure |

Host config (binds, `--ipc host`, shm 16 GiB, `label=disable`, `unless-stopped`, `--gpus all`)
is in `recipe-current.json`; [UPDATE-20261015.md](UPDATE-20261015.md) documents the transition.

## Measured behavior (this exact config, 2026-10-15)
Decode 40–44 tok/s single-stream · warmup ~165 s · swap growth 0 · 64-hex SHA-256
reconstruction exact at 198,819 tokens · trace NLL 3.109 nats/tok — **not comparable** to the
pre-upgrade 2.999 (attention temperature differs across YaRN factors; long-context A/B pending).

## Superseded September settings (history — do not run as-is)
drowzeys `a393318f…` checkpoint, 500,000/YaRN-4, BF16 KV, 8 sequences, FAST_ROWS=0/32
workers: preserved in [config/active-20261014.json](../config/active-20261014.json) (the
immediate pre-upgrade state) and in `production.json` / `recipe-v030.json` /
[UPDATE-20260926.md](UPDATE-20260926.md) / [PARSER-UPDATE.md](PARSER-UPDATE.md) for audit.
The September preview's 19.21 GiB/710,606-token boot figure and the v0.29-vs-blazux
comparison table belong to those historical arms.
