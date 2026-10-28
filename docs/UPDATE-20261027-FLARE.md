# Update 2026-10-27 — serving moved from vLLM to NVIDIA Flare

This is the current serving path. The Oct-15 vLLM configuration
([recipe-current.json](../recipe-current.json), [UPDATE-20261015.md](UPDATE-20261015.md))
is retained as the **parachute** and historical record; every document predating this one
describes that stack, not what is live.

Live snapshot: [config/active-20261027.json](../config/active-20261027.json) ·
Service file: [scripts/flare.service](../scripts/flare.service) ·
Install: [scripts/flare-install.sh](../scripts/flare-install.sh) ·
Latest decode sample: [evidence/flare-sustained-20261028.json](../evidence/flare-sustained-20261028.json)

## What changed

| | Oct-15 (vLLM) | Oct-27 live (Flare) |
|---|---|---|
| Runtime | Blazux `qwen38-published:20261004-v031` (vLLM 0.31) | [NVIDIA Flare](https://github.com/NVIDIA/flare-local-inference) 0.1.0, self-built |
| Checkpoint | NVFP4 snapshot `fc694b54…-fp8hybrid` (abliterated lineage) | `nvidia/Qwen3.8-Flash-Next-FP4-Local`, prepared pkg `gb10-tp1-202610260834` |
| Context | 524,288 via YaRN factor 2.0 | **262,144 native — no YaRN, no rope overrides** |
| KV pool | 1,068,740 tok | **2,318,336 tok** (31.2 GiB, 40 shared snapshot slots) |
| Decode (sustained 2048 tok, single stream) | 40–44 tok/s at 524K ctx | **38.5 tok/s** (vs Transformer-Engine engine 32.1 the same day) |
| Input modalities | text | **text + image** (≤4,096 tokens/image; ≤32 MiB, ≤8192²px per image) |
| Boot | ~165 s warmup | **~80 s** incl. 45 s `--verify-weights` |
| Concurrency | max-num-seqs 4 | max_concurrency 5 |

Note on comparability: the 524K vLLM figure ran 2× the context window and the abliterated
checkpoint; the Flare 38.5 tok/s is native-262K on NVIDIA's official prepared package.
Sustained means 2,048-token single-stream decode — 512-token burst probes mislead badly on
this box (same binary measured 49.1 and 12.7 tok/s in burst conditions during gate runs).

## Why Flare

- Single Rust binary + verified package replaces the vLLM/FlashInfer/patch-matrix stack;
  boot went 165 s → 80 s and the `zig` segfault / sticky CUDA-700 crash modes of the
  TF-engine container are gone from the serving path.
- The prepared package does a cryptographic weight verification on every boot (99.4 GiB
  in ~44 s), so a silently corrupt weight set can no longer serve.
- Native 262,144 context: the YaRN factor correction and its long-context open item from
  [UPDATE-20261015.md](UPDATE-20261015.md) no longer apply to the live path.
- Text+image input comes for free from the FP4-Local prepared package (the old vLLM path
  was text-only; vision was served by a separate model).

## What was NOT adopted (deliberate)

- **eugr b12x** — never run it on this box: OOM-rebooted the Spark in testing (eugr issue 388).
- **RAM embedding tables** — `--embedding-table-storage ram` is what the package was
  originally tuned for (~49 tok/s burst), but it steals the ~7.6 GiB of host headroom the
  KV pool and host cache need. The disk-table default (1,024 MiB row cache, NVMe-streamed
  n-gram tables) is the live, safe configuration.
- **YaRN / rope overrides** — Flare serves the native window; nothing to override.
- **The abliterated checkpoint on this path** — Flare runs NVIDIA's official prepared
  FP4-Local package. The abliterated NVFP4 lineage stays available in the vLLM parachute.

## Local modifications

Serving binary: built from `NVIDIA/flare-local-inference` @ `3a6b46f` ("Return undeclared
MiniMax tool calls under automatic tool choice", #49) — tree otherwise clean; `target-x/`
is the untracked release output at `/root/flare-x-build`.

The separate work tree `/root/flare` @ `ca1f960` carries **two staged local patches**
(backup of the pre-pull tree at `/root/flare-3267` @ `3267c05`), both in the ignition
preparation tooling, both awaiting upstream PRs:

1. `ignition/cli/preparation.py` — the pinned b12x `AutotuneEffort` enum
   (`off/low/medium/high/max`) has no `default` name; map `default` → `medium` (the enum
   default policy) and `audit` → `high`.
2. `ignition/preparation/tuning.py` — same mapping at `RecordedPreparationSession` init.

These affect package preparation/tuning CLI ergonomics, not the live serve path.

## Gate results recorded during the migration (2026-10-27, Stage-A, 07:54–08:15)

| Gate | TF baseline | Flare Oct-26 | Flare Stage-A | Notes |
|---|---|---|---|---|
| Decode (burst probe) | 42.1 | 49.1 | **12.7** | mislead by design — burst probes rejected after this; use sustained 2048 |
| 118k @4k budget | 3/3 | 0/3 | 0/3 | upstream #94 did **not** fix the QAD thinkiness at small budgets |
| 118k @16k budget | 3/3 | 0/3 | 0/3 | same |
| Tools | 3/3 | 3/3 | 3/3 | |
| 30×16k empty | 0/30 | 0/30 | 0/30 | pass |
| 100× short prompts empty | 87/100 | — | 78/100 | model property (QAD thinking), non-discriminating |
| MemAvailable | 33.9 GiB | 7.6–8.1 | 7.5 | KV grew 2.04M → 2.32M tok, reusing the freed table RAM |
| 244k prefill @16k budget | 3/3 (159 s) | 3/3 (315 s) | 3/3 (**219 s**) | |
| Boot | 64 s | ~2 min | 66 s + 45 s verify | |

Accepted state: thinkiness only bites at budgets ≤16k tokens; 32k budgets behave.
Callers that pass tiny `max_tokens` on reasoning-style prompts may see empty completions.

## Live service state as shipped

- systemd unit [scripts/flare.service](../scripts/flare.service) (installed as
  `/etc/systemd/system/flare.service`, enabled; `Restart=always`, `RestartSec=10`,
  `StartLimitIntervalSec=0` so CUDA-700 crash loops cannot wedge into `failed`,
  `TimeoutStartSec=300` so systemd never SIGTERMs a mid-boot flare).
- ExecStart: `flare run /root/.cache/flare/packages/models/nvidia_2FQwen3.8-Flash-Next-FP4-Local/gb10-tp1-202610260834 --host 0.0.0.0 --port 8000 --served-model-name qwen3.8-flash-next --verify-weights`
- Boot trace (from `/root/flare-live.log`): signatures 0.1 s · verify 99.4 GiB 44.3 s ·
  allocate 75.1 GiB GPU 2.7 s · load weights 72.5 GiB 8.7 s · embedding tables **disk** ·
  1024 MiB row cache 0.2 s · plan 78.88 GiB loaded / 31.27 GiB cache budget · allocate
  31.2 GiB · **2,318,336 KV tokens** · 40 shared snapshot slots · server up 1.0 s.
- Sampling is server-clamped: temperature ∈ [0.7, 1.0] (default 1.0), top_p ∈ [0.80, 0.95]
  (default 0.95), top_k 20, seed 0, presence_penalty ∈ [0, 2]. Requests outside the range
  are clamped, not rejected.
- Host: DGX Spark (GB10, aarch64, 121 GiB unified), driver 580.178.04. With the engine up,
  `MemAvailable` sits near ~7 GiB — that is the designed steady state, not a leak.

## Rollback layers (kept warm)

1. **TF engine container** `qwen38-flash-next-tf` (64 s boot) — container exists but its
   weight dir was emptied by the 2026-10-27 orphan-blob sweep (symlinked snapshots made
   the blobs the only copy). Revive = re-download `nvidia/Qwen3.8-Flash-Next-FP4-Local`
   before relying on it. Known crash modes: zig segfault (exit 133), sticky CUDA-700.
2. **vLLM parachute** container `qwen38-vllm-8000` + image pinned in
   [recipe-current.json](../recipe-current.json); NVFP4 `fp8hybrid` weights verified intact
   on disk. This is the only path that serves the abliterated checkpoint.
3. Watchdog auto-rollback crons were **deleted 2026-10-27** by owner decision (Flare-only);
   the escalation script remains for manual runs.

## Operational rules (Spark-specific)

- **One heavy workload at a time.** Flare (or the rollback engines) and ComfyUI/H3 video
  cannot coexist on the 121 GiB unified pool — stop the serving container/service before
  switching to video mode and vice versa. Probe the ports; never assume.
- The endpoint is shared with a second Hermes user. The old bench harness aborted on
  foreign traffic via vLLM Prometheus counters; Flare's equivalents are
  `flare_active_requests` and `flare_free_request_slots` (idle ⇔ `active==0`, `slots==5`).
  Never publish a decode number sampled outside an idle window — on 2026-10-28 a
  single-stream run co-resident with one other request measured 21.4 tok/s vs the 38.5
  recorded idle on Oct-27; see [evidence/flare-sustained-20261028.json](../evidence/flare-sustained-20261028.json).
- Health probes: `GET /health` → `{"status":"ok"}`; `GET /v1/models` exposes the full
  geometry (vocab 248,320, clamps, image limits); `GET /metrics` is Flare-native
  Prometheus, **not** `vllm:*` — do not run `benchmark/bench.py` against Flare, its
  foreign-traffic guard and decode counters will not resolve.
- Logs: `/root/flare-live.log` (stdout+stderr appended by the unit).

## Open items

- Re-measure sustained decode in a verified-idle window and replace the 38.5 figure or
  this caveat with a dated artifact.
- QAD thinkiness at ≤16k budgets: upstream behavior, watch NVIDIA/flare-local-inference.
- Two local ignition patches pending upstream PRs (see Local modifications).
- TF rollback weights need a re-download to be trustworthy again.
