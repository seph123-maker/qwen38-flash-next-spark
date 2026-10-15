# Qwen3.8-Flash-Next on one DGX Spark

The recipe for running an abliterated NVIDIA Qwen3.8-Flash-Next NVFP4 at **524,288-token
context with a 1,068,740-token KV pool** on a single GB10 (DGX Spark), with 47.7 GiB of
NVMe-streamed n-gram (PLE) memory. Based on [Blazux's work](https://github.com/blazux/qwen3.8-Flash-DGX)
and NVIDIA's public checkpoint — not a claim to have invented a new inference stack.
[Credits](CREDITS.md) · [Sources](docs/SOURCES.md).

## Current headline numbers (measured, 2026-10-15)

| | |
|---|---|
| Context / KV pool | 524,288 in · **1,068,740** pool (fp8_e4m3 KV, 2.03× concurrency) |
| Decode | 40–44 tok/s single-stream (MTP n=2; acceptance 71.7% / 53.9%) |
| Quality checks | hex-exact retrieval @ 198K tokens · cache coherence exact · swap growth 0 |
| Warmup | ~165 s |

## Start here

| Need | Guide |
|---|---|
| **What is actually running (canonical)** | [Configuration](docs/CONFIGURATION.md) · [recipe-current.json](recipe-current.json) |
| Launch it in one script | [scripts/docker-run-current.sh](scripts/docker-run-current.sh) |
| Apply/rollback tool | [scripts/qwen38-flash-v2.py](scripts/qwen38-flash-v2.py) |
| Pinned live snapshots | [active-20261015.json](config/active-20261015.json) (current) · [active-20261014.json](config/active-20261014.json) (previous) |
| The Oct-15 upgrade (changes, measurements, gates) | [UPDATE-20261015.md](docs/UPDATE-20261015.md) · [execution log](docs/EXECUTION-LOG-20261015.md) |
| Build & run from source | [Setup](docs/SETUP.md) |
| Hermes/API connection | [Usage](docs/USAGE.md) |
| Terminology / troubleshooting | [Glossary](docs/GLOSSARY.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Earlier comparisons | [Blazux-defaults](docs/BLAZUX-DEFAULTS.md) · [testing history](docs/TESTING.md) · [PLE](docs/PLE-GATHER.md) · [Drowzeys/679k](docs/DROWZEYS-679K.md) |

## Known open items
- Long-context A/B validating the YaRN factor 4.0→2.0 correction (raw NLL is not comparable
  across factors — see open items in [UPDATE-20261015.md](docs/UPDATE-20261015.md)).
- Phase C candidates (batched-tokens 4096, FlashInfer autotune, MTP n=3) unranked pending it.

## Repository layout
`config/` pinned docker-inspect snapshots · `scripts/` launch + rebuild/rollback tools ·
`docs/` guides and update records · `benchmark/`, `blazux-comparison/`, `evidence/` test
fixtures and results (apply only to their recorded configurations) · `upstream*/` pinned
Blazux source snapshots for reproducibility.

Weights are not redistributed; gated access and model-license terms apply separately from
code licensing. See [sources and licenses](docs/SOURCES.md).

## History
September previews (`production.json`, `recipe-v030.json`, the v0.29/679k experiments,
[UPDATE-20260926.md](docs/UPDATE-20260926.md), [PARSER-UPDATE.md](docs/PARSER-UPDATE.md))
and the bf16/500K profile superseded on Oct 15 remain in git history for audit; the current
configuration above supersedes all of them.
