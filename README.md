# Qwen3.8-Flash-Next on one DGX Spark

The recipe for running Qwen3.8-Flash-Next on a single GB10 (DGX Spark). **Since
2026-10-27 the live serving path is [NVIDIA Flare](https://github.com/NVIDIA/flare-local-inference)**
serving NVIDIA's prepared FP4-Local package at native **262,144-token context with a
2,318,336-token KV pool**, text+image in. The earlier abliterated-vLLM recipe (524K via
YaRN, 1.07M-token pool) is retained as the **parachute** and historical record.
[Credits](CREDITS.md) · [Sources](docs/SOURCES.md).

## Current headline numbers

| | |
|---|---|
| Runtime | Flare 0.1.0, self-built @ `3a6b46f`, systemd, `--verify-weights` every boot |
| Context / KV pool | 262,144 native (no YaRN) · **2,318,336** pool · 40 snapshot slots · c5 |
| Decode | **38.5 tok/s** sustained (2048-token single stream, recorded 2026-10-27 idle; shared-endpoint samples under one co-resident request measured 21.4 — see evidence) |
| Modalities | text + image in (≤4,096 tok/image), text out |
| Boot | ~80 s incl. 45 s full-package weight verification (99.4 GiB) |
| Sampling | server-clamped: temp ∈ [0.7, 1.0], top_p ∈ [0.80, 0.95], top_k 20 |

## Start here

| Need | Guide |
|---|---|
| **What is actually running (canonical)** | [UPDATE-20261027-FLARE.md](docs/UPDATE-20261027-FLARE.md) · [active-20261027.json](config/active-20261027.json) |
| Launch it in one script | [scripts/flare-install.sh](scripts/flare-install.sh) · [scripts/flare.service](scripts/flare.service) |
| Latest decode sample | [evidence/flare-sustained-20261028.json](evidence/flare-sustained-20261028.json) |
| **vLLM parachute** (abliterated checkpoint, 524K/YaRN) | [Configuration](docs/CONFIGURATION.md) · [recipe-current.json](recipe-current.json) · [docker-run-current.sh](scripts/docker-run-current.sh) · [apply/rollback tool](scripts/qwen38-flash-v2.py) |
| Oct-15 vLLM upgrade record | [UPDATE-20261015.md](docs/UPDATE-20261015.md) · [execution log](docs/EXECUTION-LOG-20261015.md) |
| Build & run from source (vLLM lane) | [Setup](docs/SETUP.md) |
| Hermes/API connection | [Usage](docs/USAGE.md) |
| Terminology / troubleshooting | [Glossary](docs/GLOSSARY.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Earlier comparisons | [Blazux-defaults](docs/BLAZUX-DEFAULTS.md) · [testing history](docs/TESTING.md) · [PLE](docs/PLE-GATHER.md) · [Drowzeys/679k](docs/DROWZEYS-679K.md) |

## Known open items
- Re-measure sustained Flare decode in a verified-idle window (`flare_active_requests 0`,
  `flare_free_request_slots 5`); the 38.5 figure is recorded, not yet a dated public artifact.
- QAD thinkiness at ≤16k-token budgets (empty completions on reasoning-style prompts);
  32k budgets behave — upstream behavior, watch [NVIDIA/flare-local-inference](https://github.com/NVIDIA/flare-local-inference).
- Two local ignition-preparation patches pending upstream PRs (listed in
  [UPDATE-20261027-FLARE.md](docs/UPDATE-20261027-FLARE.md)).
- The TF-engine rollback container needs a weights re-download before it can be trusted again.
- (vLLM lane, dormant) Long-context A/B for the YaRN factor 4.0→2.0 correction; Phase C
  candidates — see [UPDATE-20261015.md](docs/UPDATE-20261015.md).

## Operational rules
- **One heavy workload at a time:** the brain (Flare or a rollback engine) and
  ComfyUI/H3 video never coexist on the 121 GiB unified pool. Probe ports, never assume.
- **Never run eugr b12x** on this box (OOM-rebooted it; eugr issue 388).
- Benchmark only in verified-idle windows — the endpoint is shared with a second user.
  `benchmark/bench.py` targets the vLLM lane only (`vllm:*` counters).

## Repository layout
`config/` pinned live snapshots · `scripts/` launch + rebuild/rollback tools ·
`docs/` guides and update records · `benchmark/`, `blazux-comparison/`, `evidence/` test
fixtures and results (apply only to their recorded configurations) · `upstream*/` pinned
Blazux source snapshots for reproducibility.

Weights are not redistributed; gated access and model-license terms apply separately from
code licensing. See [sources and licenses](docs/SOURCES.md).

## History
September previews (`production.json`, `recipe-v030.json`, the v0.29/679k experiments,
[UPDATE-20260926.md](docs/UPDATE-20260926.md), [PARSER-UPDATE.md](docs/PARSER-UPDATE.md)),
the bf16/500K profile superseded on Oct 15, and the Oct-15 vLLM default superseded on
Oct 27 remain in git history for audit; the current configuration above supersedes them.
