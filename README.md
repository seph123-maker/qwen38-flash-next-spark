# Qwen3.8-Flash-Next on one DGX Spark

A community serving recipe for running an **abliterated Qwen3.8-Flash-Next model on one GB10 system**, with tests covering code, tool calling, Unicode text and long-document retrieval.

The launcher also adapts Blazux's reasoning-effort compatibility fix: clients can send `high` or `max` (mapped to `xhigh`) and `minimal` (mapped to `low`). This is an API compatibility change, with no claimed speed improvement. See [credits](CREDITS.md).

This combines **[Blazux's serving recipe](https://github.com/blazux/qwen3.8-Flash-DGX)** with **[gorbatjovy's abliterated checkpoint](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8)**, additional FP8 conversion and our selected settings. Blazux supplies the serving foundation; the abliterated weights come from a separate model lineage. [Authors and credits](CREDITS.md) · [Exact sources and lineage](docs/SOURCES.md).

**Recorded configuration: September 16, 2026.** This is a dated, pinned recipe, not a promise to track the newest upstream defaults.

## Start here

| You want to… | Read |
|---|---|
| Recreate the server | [Setup guide](docs/SETUP.md) |
| Understand what we changed and tested | [Tests and decisions](docs/TESTING.md) |
| See every important setting | [Configuration reference](docs/CONFIGURATION.md) |
| Connect Hermes or check the API | [Using the server](docs/USAGE.md) |
| Investigate slow startup, cache pressure or a failed launch | [Troubleshooting](docs/TROUBLESHOOTING.md) |
| Trace code, weights, licenses and limitations | [Sources and reproducibility](docs/SOURCES.md) |
| Decode unfamiliar terms | [Short glossary](docs/GLOSSARY.md) |

## What is running?

| Part | Current choice | Plain-language meaning |
|---|---|---|
| Serving software | Blazux-based vLLM 0.29.0 | Loads the model and serves requests |
| Model | Gorbatjovy's abliterated NVFP4/FP8-PLE checkpoint, with FP8 side-layer conversion | The selected model weights, compressed to fit |
| Drafting | Three tokens ahead; full draft vocabulary | Proposes several next tokens and verifies them together |
| Maximum context | 500,000 tokens, YaRN factor 4 | Configured input-and-output window; quality at every depth is not established |
| Attention cache | BF16, 17.38 GiB | Memory reserved for attention history |
| PLE table | File-backed lookup through Blazux's mmap implementation | Fetches required table rows without keeping the entire table resident |
| Attention-selection fix | jschmied's deterministic top-k kernel | Addresses a specific attention-selection problem |
| Compiled artifacts | Persistent vLLM and FlashInfer caches | Keeps compiled work when the container is recreated |

The complete machine-readable launch configuration is [production.json](production.json). [serve.py](serve.py) uses it directly. Technical terms are explained in the [glossary](docs/GLOSSARY.md).

## What did testing show?

| Experiment | Observed result | Decision |
|---|---|---|
| Upgrade to vLLM 0.29 and preserve compilation caches | Both versions passed 10 checks. Long retrieval: 336.11 → 319.18 seconds; comparable short median latency was 3.1% longer. | Adopted the compatible runtime update; no general speed claim |
| Draft three tokens ahead instead of two | About 8% faster output generation in two passes; all 32 requests across both settings passed their checks | Adopted provisionally; independent-start repeatability is unproven |
| Retrieve information from a 483,011-token prompt with the chosen setting | Correct answer in 318.49 seconds, with one cache-related preemption | Kept the setting; this does not prove long-document reasoning quality |
| Try Eugr/B12X with the same weights | Failed during startup, before producing an answer | Restored the working server; no speed comparison was possible |
| Send all PLE gathers through the worker pool | +6.1% and +7.3% pooled decode rate in two paired comparisons; all 24 checks passed | `VLLM_PLE_MMAP_FAST_ROWS=0`; see [method and limitations](docs/PLE-GATHER.md) |

The drafting change missed our original 10% speed threshold and one small-sample acceptance guard. We deliberately accepted the smaller observed benefit; the [test history](docs/TESTING.md) preserves that distinction.

These results do **not** establish that this is the best recipe, the best abliterated checkpoint, or an 8% improvement on every workload. The long retrieval still needed one preemption, and a dedicated prefix-reuse check has not been repeated after changing to three-token drafting.

## Recreating it

Use the [setup guide](docs/SETUP.md) for the three stages: build the pinned image, download/prepare the pinned model, and launch. If that exact prepared model already exists, skip its preparation.

From the repository root, the image build is:

```bash
docker build -f upstream/Dockerfile.block-a -t qwen38-published:20260915 upstream
```

The historical Dockerfile name is retained for traceability; the guide explains what it builds. The package's launcher was checked with a Linux dry run. A clean build and complete setup from this published checkout have **not** been repeated, so this remains a documented reproduction recipe rather than an independently verified installer.

## Repository map

| Path | Purpose |
|---|---|
| `docs/` | Setup, usage, settings, tests, troubleshooting and sources |
| `production.json` | Exact exported settings, excluding credentials |
| `serve.py` | Launcher that refuses to replace an existing container |
| `evidence/` | Compact measured results and trial state |
| `upstream/` | Preserved pinned Blazux source plus documented local patches |
| `CREDITS.md` / `LICENSE` | Attribution and code license notice |
| `SHA256SUMS` | Checksums for this package's files |

The bundled upstream documentation includes other profiles and upstream measurements; it does not describe our selected settings in every case. Start with the guides above.

## Share a result or report a problem

Use [the issue tracker](https://github.com/seph123-maker/qwen38-flash-next-spark/issues) and include the model revision, image/runtime version, settings, prompt/output lengths and relevant error excerpt. See [how to contribute](CONTRIBUTING.md) for the details that make comparisons useful.

Code notices are preserved under Apache-2.0. Model weights use their separate publisher terms; the selected checkpoint declares Qwen Community License 1.0. No weights or credentials are included. See [sources and licensing](docs/SOURCES.md).
