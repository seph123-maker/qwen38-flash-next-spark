# Qwen3.8-Flash-Next on one DGX Spark

A **Blazux-based recipe with Drowzeys' NVIDIA-derived abliterated weights** on one GB10 system. The September 26 update adds a pinned vLLM 0.30 source recipe with faster loading and optional FP8 KV support. **This new build has not yet been built or run locally.** The September-tested preview recipe and its results remain available separately. This repository does not describe the maintainer's current live Hasso/SGLang deployment.

This is based on [Blazux's work](https://github.com/blazux/qwen3.8-Flash-DGX), not a claim to have invented a new inference stack. [Credits](CREDITS.md) · [Sources](docs/SOURCES.md).

## September 26 source update

The default launcher now selects the v0.30 candidate. It keeps the same checkpoint revision, API name/port, 500k context, YaRN factor 4, BF16 cache and two-token drafting. [Changes, upstream measurements, validation status and rollback](docs/UPDATE-20260926.md). No new local speed or quality claim is made.

## September 19 historical update

Installed upstream tool-parser fixes. **30/30 parser regression cases and 6/6 serving checks passed.** Model, context, KV sizing and drafting settings are unchanged. This is a correctness update; no speed gain is claimed. [Details, credits and limitations](docs/PARSER-UPDATE.md).

## Start here

| Need | Guide |
|---|---|
| Build and run | [Setup](docs/SETUP.md) |
| Latest comparison and decision | [Blazux-default comparison](docs/BLAZUX-DEFAULTS.md) |
| Exact settings | [Configuration](docs/CONFIGURATION.md), [recipe-v030.json](recipe-v030.json) |
| Hermes/API connection | [Usage](docs/USAGE.md) |
| Earlier tests | [Runtime/drafting history](docs/TESTING.md), [PLE comparison](docs/PLE-GATHER.md), [Drowzeys/679k](docs/DROWZEYS-679K.md) |
| Troubleshooting and terminology | [Troubleshooting](docs/TROUBLESHOOTING.md), [Glossary](docs/GLOSSARY.md) |

## September 26 candidate configuration

| Component | Value |
|---|---|
| Serving source | Blazux `5108d90dedf15a31aa20432319f151b2fdda17a3`, `Dockerfile.v0.30` |
| Weights | Drowzeys `a393318fb56d9aedc56d91b6f4962d9af26d2fe7`, locally prepared FP8 hybrid |
| Maximum total context | **500,000 tokens**, YaRN factor 4 |
| KV cache | BF16; automatic sizing at utilization **0.80** |
| Drafting | **2 tokens**, reduced **65,536-token** draft vocabulary |
| PLE | Disk-backed mmap, worker-pool gathers, prewarming off |
| Attention / prefix caching | Deterministic top-k enabled; prefix caching enabled |
| Optional upstream features retained | Persistent compilation caches, Prometheus multiprocess export |

The **historical preview** trial boot reported **19.21 GiB KV / 710,606 cache tokens**. This is not a v0.30 capacity promise; upstream now explains that slow-load swap can inflate automatic sizing. Automatic allocation may differ after another restart; that figure is not the configured request limit. The launcher also preserves upstream-supported effort aliases. Image and weights remain separately pinned.

## Historical measured comparison (preview, not v0.30)

| Measurement | Previous custom v0.29 / K3 / 679k | Blazux defaults / K2 / 500k |
|---|---:|---:|
| Short scripted checks | 12/12 | 12/12 |
| Pooled decode, first pass | 42.29 tok/s | 44.79 tok/s (+5.9%) |
| Pooled decode, second pass | 43.70 tok/s | 46.66 tok/s (+6.8%) |
| Total short-request time, first pass | 45.58 s | 50.18 s |
| Total short-request time, second pass | 43.98 s | 43.98 s |
| 483,011-token retrieval | Correct, 325.74 s, 1 preemption | Correct, 312.89 s, 1 preemption |

Selected by user preference after successful testing. Generation was faster in these samples; complete request latency was mixed. This is a small whole-recipe comparison, not proof of general intelligence parity, a universal speed gain or the benefit of any one setting. Each arm had one start and two short passes. Earlier successful 679k retrieval remains documented, but **679k is not the current limit**.

## Reproduce and audit

```bash
docker build -f upstream-blazux-v030/Dockerfile.v0.30 -t qwen38-published:20260926-v030 upstream-blazux-v030
```

Follow [setup](docs/SETUP.md) for model access, pinned download, hybrid conversion and launch. The v0.30 source is published for reproduction; its ARM64 image build and execution with these weights are still pending. Existing benchmark results apply only to their recorded older configurations.

[benchmark/](benchmark/) includes synthetic fixtures and scoring/measurement scripts; [blazux-comparison/](blazux-comparison/) contains saved requests, responses, metrics and grades for both arms. Older [evidence summaries](evidence/) remain available. Historical custom build files remain under [upstream/](upstream/); September 19 source is under [upstream-blazux/](upstream-blazux/); the new unmodified snapshot is under [upstream-blazux-v030/](upstream-blazux-v030/).

Weights are not redistributed. Their gated access and model-license terms apply separately from code licensing. See [sources and licenses](docs/SOURCES.md).
