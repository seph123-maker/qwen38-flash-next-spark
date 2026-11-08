# Qwen3.8-Flash-Next on one DGX Spark

The recipe for running Qwen3.8-Flash-Next on a single GB10 (DGX Spark). **Since
2026-11-05 the live serving path is [NVIDIA Flare](https://github.com/local-inference-lab/flare-local-inference)
prebuilt @ `18b16e1`** serving the **`91cfb369`-vintage (2026-11-08) grafted re-export** of
NVIDIA's FP4-Local package — drowzeys QSA/GDN sidecar baked in (the empty-answer fix)
plus the Nov-05→08 upstream prep-layer fixes (streamed-response liveness,
`ignore_eos` at the output limit, SM103 prefill determinism, draft-page preservation,
upstream flashinfer pin) — at native **262,144-token context with a ~1.86M-token
boot-variable KV pool**, text+image in, dual-symlink last-good deployment with a
watchdog. The `1108` grafted package is the **rollback rung** (same `18b16e1` binary);
the Oct-27 era (self-built `3a6b46f`) and the earlier abliterated-vLLM recipe
(524K via YaRN, 1.07M-token pool) remain the **parachute** and historical record.
[Credits](CREDITS.md) · [Sources](docs/SOURCES.md).

## Current headline numbers

| | |
|---|---|
| Runtime | Flare 0.1.0, **prebuilt** @ `18b16e1` (2026-11-03), systemd, `--verify-weights` every boot, sha256-pinned staging |
| Context / KV pool | 262,144 native (no YaRN) · **~1.86M** pool (boot-variable) · ~202 snapshot slots · **c32** |
| Decode | **37.6 tok/s** sustained on the live 91cfb369 package (2048-token single stream, verified-idle 2026-11-08, [artifact](evidence/flare-sustained-20261108-0426.json)); same-day history: stock `1744` 37.6/40.8, grafted `1108` 36.2/39.0 — one band |
| Modalities | text + image in (≤4,096 tok/image), text out |
| Boot | ~56 s first boot after export, **~5 s warm restart** |
| Sampling | server-clamped: temp ∈ [0.7, 1.0], top_p ∈ [0.80, 0.95], top_k 20 |
| Reasoning | native template, no effort injection. The grafted build removed the non-deterministic empty-answer tail (18/18 clean at default effort; `max_tokens=32` 6/6 clean). Only sub-16-token budgets can still come back empty — the model's thinking preamble needs more headroom than that. `reasoning_effort: "low"` stays the pick for tight budgets ([detail](docs/UPDATE-20261105-FLARE.md)) |

## Start here

| Need | Guide |
|---|---|
| **What is actually running (canonical)** | [UPDATE-20261108-FLARE.md](docs/UPDATE-20261108-FLARE.md) · [active-20261108.json](config/active-20261108.json) |
| Launch it in one script | [scripts/flare-install.sh](scripts/flare-install.sh) · [scripts/flare.service](scripts/flare.service) |
| Supervisor (watchdog) | [scripts/flare-brain-watchdog.sh](scripts/flare-brain-watchdog.sh) · [.service](scripts/flare-brain-watchdog.service) · [.timer](scripts/flare-brain-watchdog.timer) |
| Latest decode sample | [evidence/flare-sustained-20261108-0426.json](evidence/flare-sustained-20261108-0426.json) (0426 live package) · [1744 stock](evidence/flare-sustained-20261108.json) |
| Previous era (rollback rung) | [UPDATE-20261027-FLARE.md](docs/UPDATE-20261027-FLARE.md) · [active-20261027.json](config/active-20261027.json) |
| **vLLM parachute** (abliterated checkpoint, 524K/YaRN) | [Configuration](docs/CONFIGURATION.md) · [recipe-current.json](recipe-current.json) · [docker-run-current.sh](scripts/docker-run-current.sh) · [apply/rollback tool](scripts/qwen38-flash-v2.py) |
| Oct-15 vLLM upgrade record | [UPDATE-20261015.md](docs/UPDATE-20261015.md) · [execution log](docs/EXECUTION-LOG-20261015.md) |
| Build & run from source (vLLM lane) | [Setup](docs/SETUP.md) |
| Hermes/API connection | [Usage](docs/USAGE.md) |
| Terminology / troubleshooting | [Glossary](docs/GLOSSARY.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Earlier comparisons | [Blazux-defaults](docs/BLAZUX-DEFAULTS.md) · [testing history](docs/TESTING.md) · [PLE](docs/PLE-GATHER.md) · [Drowzeys/679k](docs/DROWZEYS-679K.md) |

## Known open items
- Engine/package **contract lock**: the `18b16e1` binary rejects the Oct-26 package
  (`unsupported prepared model contract version`); the Nov-08 `91cfb369`-vintage
  package is readable by it (contract version stays 3 — verified by boot). Rungs still
  move as binary+package pairs via the dual-symlink + last-good design; never mix manually.
- The **local `linear.py` 2-kwarg backport is retired** by this era: the `91cfb369` prep
  tree pins upstream flashinfer `6b867fdb` with a redesigned `linear.py` and no local
  patch. The `18b16e1` staging tree (`/root/flare`) keeps its patch for that lane's
  exports (see [UPDATE-20261108-FLARE.md](docs/UPDATE-20261108-FLARE.md)).
- The `91cfb369` **binary** is byte-identical to the Oct-27 `3a6b46f` build (the Rust
  runtime is frozen: the `18b16e1→91cfb369` delta touches only `cli.rs`/`hardware.rs` in
  the old direction and the prep layer in the new) — so the Nov-05→08 fixes land at the
  **package level only**; a binary swap is a no-op. Staged copy kept at
  `/root/flare-releases/91cfb369/` as evidence.
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
the bf16/500K profile superseded on Oct 15, the Oct-15 vLLM default superseded on
Oct 27, and the Oct-27 Flare era (`3a6b46f` self-built, `gb10-tp1-202610260834`)
superseded on **Nov 05** (prebuilt `18b16e1` + re-exported package) remain in git
history for audit; the current configuration above supersedes them, and the Oct-27
pair is kept as a rollback rung (contract-locked to its own binary — move rungs only
as a pair).
