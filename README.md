# Qwen3.8-Flash-Next on one DGX Spark

A tested **Blazux-default serving configuration with Drowzeys' NVIDIA-derived abliterated weights** on one GB10 system. The September 16 selection uses a pinned Blazux preview image, FP8 hybrid side layers, automatic KV allocation, two-token speculative drafting and a reduced draft vocabulary.

This is based on [Blazux's work](https://github.com/blazux/qwen3.8-Flash-DGX), not a claim to have invented a new inference stack. [Credits](CREDITS.md) · [Sources](docs/SOURCES.md).

## Start here

| Need | Guide |
|---|---|
| Build and run | [Setup](docs/SETUP.md) |
| Latest comparison and decision | [Blazux-default comparison](docs/BLAZUX-DEFAULTS.md) |
| Exact settings | [Configuration](docs/CONFIGURATION.md), [production.json](production.json) |
| Hermes/API connection | [Usage](docs/USAGE.md) |
| Earlier tests | [Runtime/drafting history](docs/TESTING.md), [PLE comparison](docs/PLE-GATHER.md), [Drowzeys/679k](docs/DROWZEYS-679K.md) |
| Troubleshooting and terminology | [Troubleshooting](docs/TROUBLESHOOTING.md), [Glossary](docs/GLOSSARY.md) |

## Selected configuration

| Component | Value |
|---|---|
| Serving source | Blazux `ed65cc80646e85cf6631b93d7dfcf9412183cc30`, default preview Dockerfile |
| Weights | Drowzeys `a393318fb56d9aedc56d91b6f4962d9af26d2fe7`, locally prepared FP8 hybrid |
| Maximum total context | **500,000 tokens**, YaRN factor 4 |
| KV cache | BF16; automatic sizing at utilization **0.80** |
| Drafting | **2 tokens**, reduced **65,536-token** draft vocabulary |
| PLE | Disk-backed mmap, worker-pool gathers, prewarming off |
| Attention / prefix caching | Deterministic top-k enabled; prefix caching enabled |
| Optional upstream features retained | Persistent compilation caches, Prometheus multiprocess export |

The trial boot allocated **19.21 GiB KV / 710,606 reported cache tokens**. Automatic allocation may differ after another restart; that figure is not the configured request limit. The launcher also preserves upstream-supported effort aliases. Image and weights remain separately pinned.

## Latest measured comparison

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
docker build -f upstream-blazux/Dockerfile -t qwen38-published:20260916 upstream-blazux
```

Follow [setup](docs/SETUP.md) for model access, pinned download, hybrid conversion and launch. The upstream source built and ran on the Spark; a clean end-to-end reproduction from this public checkout has not been independently repeated.

[benchmark/](benchmark/) includes synthetic fixtures and scoring/measurement scripts; [blazux-comparison/](blazux-comparison/) contains saved requests, responses, metrics and grades for both arms. Older [evidence summaries](evidence/) remain available. Historical custom build files remain under [upstream/](upstream/); current pinned upstream files are under [upstream-blazux/](upstream-blazux/).

Weights are not redistributed. Their gated access and model-license terms apply separately from code licensing. See [sources and licenses](docs/SOURCES.md).
