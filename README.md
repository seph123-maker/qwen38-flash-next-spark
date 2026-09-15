# Running Qwen3.8-Flash-Next on one DGX Spark

This repository documents how we got a large Qwen3.8-Flash-Next model running on one NVIDIA DGX Spark, then tested changes to its serving software and generation settings. The goal was one person's assistant workload: code, tool calls, Thai text and very long prompts.

**The current setup uses vLLM 0.29.0 and drafts three tokens ahead.** In our small comparison, drafting three ahead generated output about **8% faster** than drafting two, with all of the scripted correctness checks passing. A later test retrieved the requested information from a 483,011-token prompt in **318.49 seconds**. These are measurements from this machine and test set, not promises for every workload.

The foundation is [Blazux's serving recipe](https://github.com/blazux/qwen3.8-Flash-DGX), including contributions from other developers, and [jschmied's attention kernel](https://github.com/jschmied/qwen38-flash-next-gb10). Our contribution is assembling those pieces, testing changes on this machine and recording what worked. [Full credits](CREDITS.md).

Configuration and measurements recorded September 15, 2026.

## What makes this model fit?

The model needs memory for both its stored weights and the information it retains while processing a conversation. Three parts of this recipe help manage that:

- **Compressed model weights:** different parts use different numerical formats, reducing how much memory the weights occupy. The technical names are NVFP4 and FP8.
- **A large lookup table served from disk:** the model includes a table called PLE. Blazux's implementation maps it from a file and fetches the rows needed for a request, so the whole table does not need to stay resident alongside the other weights.
- **A fixed conversation-cache budget:** about 17.38 GiB is reserved for the attention cache, which stores information the model can reuse while generating an answer.

We use the [gorbatjovy abliterated checkpoint](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8), with additional FP8 conversion of some layers using the credited upstream tool. All comparisons below kept the same model weights. They test the serving setup, not whether this checkpoint is better than the original model or other derivatives.

## How we reached the current setup

### 1. Start from the working recipe

Before these comparisons, the server already had disk-backed PLE storage, compressed weights, a 500,000-token context setting and jschmied's deterministic attention-selection kernel. A token is a small piece of text; token counts are not word counts.

The attention fix was already installed. The later runtime upgrade did not invent or newly add that kernel. Its purpose is consistent selection inside attention; that alone does not guarantee identical complete answers across server restarts.

### 2. Upgrade the serving software and preserve its compiled work

We moved the existing configuration to **vLLM 0.29.0**, the software that loads the model and answers API requests. We also stored its compilation caches outside the container so recreating the container would not discard them, and added compatibility and diagnostic patches.

Both the previous and updated versions passed all ten scripted checks. The large retrieval request finished in **336.11 seconds before** and **319.18 seconds after**. However, comparable short requests had a **3.1% longer median response time**. With only one comparison, this does not establish a general speed improvement. We kept the update because the newer runtime passed our compatibility and correctness checks.

Both large requests had one **preemption**: the server ran short of available cache blocks and had to reschedule work. The new diagnostics helped locate the allocation problem, but did not fix it. We verified that persistent compilation-cache files existed; we did not measure their startup savings separately from model loading.

### 3. Test drafting three tokens ahead instead of two

The model can propose several possible next tokens and verify them together. This is called **speculative decoding**. Its built-in drafting mechanism is called **multi-token prediction (MTP)**. In the settings, `K2` means proposing two tokens ahead and `K3` means proposing three.

Drafting further ahead can save time when the proposals are accepted. It can also waste work when they are rejected, so the larger number is not automatically better.

We ran the same eight prompts twice with each setting: two code tasks, two tool-call tasks, two Thai tasks, one arithmetic task and one retrieval task with about 32,000 input tokens. Temperature was zero and the seed was fixed. Prompts, responses, timing counters and scripted grades were saved to files.

| Measurement | Draft two ahead | Draft three ahead |
|---|---:|---:|
| Output generation speed, first pass | 40.54 tokens/second | 43.94 tokens/second (**+8.4%**) |
| Output generation speed, second pass | 43.30 tokens/second | 46.72 tokens/second (**+7.9%**) |
| Correct answers across both passes | 16/16 | 16/16 |

We chose **three ahead** for daily use. There is an important distinction between that practical choice and the original test rule: we had required at least a 10% speed increase in each pass, and the result fell short. One small arithmetic sample also exceeded our allowed drop in draft acceptance, although its answer remained correct. We initially kept two ahead, then deliberately accepted the observed smaller gain as provisional.

The two passes per setting shared a server start. This means the test does not separate the benefit of the setting from variation between server starts. More independent repeats would be needed to establish a reliable 8% improvement.

### 4. Check the chosen setting with a very long prompt

With three-token drafting enabled, a later request containing **483,011 input tokens** returned the correct requested information in **318.49 seconds**, with one preemption.

This confirms that the chosen setup completed this large retrieval task. It does not demonstrate equally strong reasoning across a half-million-token document. The configured maximum remains **500,000 tokens**.

### 5. Try an alternative serving stack

We also tried an [Eugr/B12X](https://github.com/eugr/spark-vllm-docker) candidate: a different vLLM build and set of GPU implementations, including a different disk-storage path for PLE. The question was whether it could run the same weights more efficiently.

The first launch stopped at a context-length configuration check. After adding the required override, it reached model construction but failed a **20 MiB GPU allocation** in the vision encoder while reporting approximately **105 GiB free**. That contradictory-looking memory report needs diagnosis; it does not prove that the model cannot fit.

**The alternative never produced an answer, so we have no speed or quality comparison for it.** We restored the working Blazux-based server. The current recipe contains no Eugr/B12X deployment changes.

## What the tests establish—and what remains uncertain

| Question | What we know |
|---|---|
| Did the runtime upgrade work with these weights? | Yes: the updated server passed the ten-check suite and the prefix-cache reuse check. |
| Is three-token drafting worth using here? | It passed the small correctness suite and was about 8% faster in both measured passes. We adopted it provisionally. |
| Has the current setup handled a very long prompt? | Yes: the 483,011-token retrieval test passed. |
| Are long-context preemptions fixed? | No: the large retrieval still recorded one. |
| Is this a general intelligence benchmark? | No: these are bounded code, tool, language, arithmetic and retrieval checks. |
| Are answers guaranteed identical after every restart? | No: that was not established. |
| Was the alternative Eugr/B12X stack slower? | Unknown: startup failed before inference. |

## Exact settings for reproduction

The table below keeps the software's actual option names, with a plain-language description of what each controls.

| Component | Production value | What it controls / why it is here |
|---|---|---|
| Runtime | vLLM 0.29.0, custom image | Updated serving software; pinned Blazux recipe |
| Checkpoint | [gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8), revision `2065365912e46b205c64a70ac5b85b4869674d31` | Existing model, plus local FP8 side-layer conversion |
| Weight layout | NVFP4 experts; blockwise FP8 side layers; FP8 PLE; BF16 MTP experts | Existing hybrid layout retained |
| MTP | 3 speculative tokens, full draft vocabulary | Draft three tokens ahead; vocabulary reduction is disabled |
| Context | 500,000 tokens; YaRN 4; original 262,144 | Retained |
| RoPE | theta 10,000,000; partial factor 0.25; interleaved mRoPE [11,11,10] | Retained |
| KV cache | `auto` resolves to BF16; 18,661,632,901 bytes (17.38 GiB) | Memory reserved for attention history |
| Scheduler | 8 sequences; 8,192 batched tokens; chunked prefill | Limits concurrent work and processes long inputs in chunks |
| Prefix caching | Enabled | Reuses processing of shared prompt beginnings; tested during the runtime upgrade |
| Graphs | PIECEWISE with explicit splitting operators | CPU PLE lookup must run outside capture |
| Attention | jschmied deterministic QSA top-k, `e0ef69d4`; exact Torch fallback off | Consistent sparse-attention selection; installed before these comparisons |
| PLE | mmap; 32 workers; prewarm on; MADV_RANDOM | Existing PLE upgrade retained |
| PLE metrics | Prometheus multiprocess export on; fresh 256 MiB tmpfs | Retained |
| Compilation caches | Persistent vLLM and FlashInfer bind mounts | Keeps compiled artifacts when the server container is recreated |
| GDN | SM12x FlashInfer selector compatibility patch | Compatibility update for this GPU family |
| Sampling | FlashInfer sampler on; FlashInfer autotuning off; DeepGemm off | Retained |
| Tools / reasoning | `qwen3_coder`, `qwen3`; auto tool choice on | Retained |
| API | OpenAI-compatible `/v1`; served name `qwen3.8-flash-next` | Port 8000 by default |

[`production.json`](production.json) contains the full exported argument list, graph splitting operators, environment variables and container settings. [`serve.py`](serve.py) uses that export to launch the server. Private hostnames, credentials and original user filesystem paths are excluded.

## Build and launch

Requires an ARM64 GB10 system, Docker with NVIDIA GPU support, Python 3, and the pinned checkpoint prepared with the included hybrid converter. Weights are not distributed in this package. This build recipe matches the production sources; a clean build of this publication bundle has not been rerun. Build output hashes can differ even with pinned inputs.

From this directory:

```bash
docker build -f upstream/Dockerfile.block-a -t qwen38-published:20260915 upstream
```

Use an isolated Hugging Face cache when preparing the pinned revision. With the Hugging Face CLI installed and model access accepted where required:

```bash
export HF_CACHE="$PWD/model-cache"
export MODEL=gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8
hf download "$MODEL" --revision 2065365912e46b205c64a70ac5b85b4869674d31 --cache-dir "$HF_CACHE/hub"
( cd upstream && IMAGE=qwen38-published:20260915 bash scripts/prepare-hybrid.sh )
python3 serve.py --hf-cache "$HF_CACHE" --compile-cache "$PWD/compile-cache"
```

The preparation script selects the downloaded snapshot and creates its `-fp8hybrid` sibling. The launcher pins that exact sibling. If using a populated cache containing other revisions, explicitly verify which snapshot the converter selected. The converter uses source-relative tools, so run it from `upstream` as shown. It is a one-time weight conversion, not part of server startup.

The launcher refuses to replace an existing container. Allow the current model server to finish requests and stop it before loading this full model on the same Spark. First weight loading on this system took roughly 8–13 minutes. The API binds all interfaces without authentication, matching the measured configuration; choose network exposure appropriate to your deployment.

```bash
docker logs -f qwen38-published
curl --fail http://127.0.0.1:8000/health
```

Hermes OpenAI base URL: `http://SPARK_ADDRESS:8000/v1`; model `qwen3.8-flash-next`. An HTTP health response confirms readiness, not model quality. `python3 serve.py --hf-cache /path/to/cache --dry-run` prints the complete launch command without starting anything.

## Measurement details and evidence files

Output-generation rates above are estimates from server counters: total completion tokens minus the first token of each response, divided by accumulated inter-token latency. They exclude prompt processing and are not direct GPU-kernel timings. Total request times for retrieval include processing the input. Responses and output lengths sometimes differed even with temperature zero and a fixed seed.

The two-token baseline used an already-running server; the three-token setting used a different start. In the second arithmetic pass, first-position draft acceptance fell from 100% to 88.9%. That sample is too small to establish a general quality regression, but it exceeded the original 10-percentage-point acceptance guard. A dedicated repeated-prefix check has not been rerun with three-token drafting; the earlier check passed during the runtime comparison with two-token drafting.

These filenames retain the original experiment identifiers so the evidence stays traceable:

| Evidence file | Contents |
|---|---|
| [Runtime comparison](evidence/block-a.json) | Previous server versus vLLM 0.29.0: correctness, latency and preemptions |
| [Two- versus three-token drafting](evidence/block-b.json) | Generation speed, acceptance and correctness by task category and pass |
| [Long-prompt retrieval](evidence/k3-483k.json) | The later 483,011-token test with three-token drafting |
| [Alternative server startup](evidence/block-c-state.json) | Failed candidate startup and completed production restore |

The full experimental protocols and response files remain in the original local experiment folders. This repository includes compact evidence summaries, not the complete fixtures and scoring tools needed for an independent rerun of every benchmark. The launch instructions reproduce the serving configuration.

## Credits, source pins and licensing

See [CREDITS.md](CREDITS.md). The bundled `upstream` snapshot is Blazux `d542745cd41045bcd71b9d7dbe659bca014202bf` plus the documented local build/diagnostic patches. Its README describes upstream alternatives and measurements; this top-level README is the description of this particular production setup.

The base image is pinned to `vllm/vllm-openai@sha256:c2914767605584b6d8f45686b82de173ecc99e781897aa3d0a66dacd72c51ae1`. The observed deployed image ID is recorded in `production.json`; that local image ID is not a public registry download address. The Dockerfile fetches jschmied source by commit and file checksum.

The bundled upstream Apache-2.0 license and original source notices are retained. Model weights have separate terms provided by their publishers; this package does not relicense weights. Local integration helpers are provided under Apache-2.0. No model weights or credentials are included.
