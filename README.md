# Single-Spark Qwen3.8-Flash-Next: tested Blazux-based recipe

Production snapshot: September 15, 2026. One GB10 system, abliterated Qwen3.8-Flash-Next, vLLM 0.29.0, disk-backed PLE and MTP K3. This is a locally integrated and tested configuration of credited upstream work. It is not a claim of an original kernel or a universally optimal recipe.

## Configuration

| Component | Production value | Provenance / change |
|---|---|---|
| Runtime | vLLM 0.29.0, custom image | Block A; pinned Blazux recipe |
| Checkpoint | [gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8), revision `2065365912e46b205c64a70ac5b85b4869674d31` | Existing model, plus local FP8 side-layer conversion |
| Weight layout | NVFP4 experts; blockwise FP8 side layers; FP8 PLE; BF16 MTP experts | Existing hybrid layout retained |
| MTP | 3 speculative tokens, full draft vocabulary | Block B: K2 to K3 |
| Context | 500,000 tokens; YaRN 4; original 262,144 | Retained |
| RoPE | theta 10,000,000; partial factor 0.25; interleaved mRoPE [11,11,10] | Retained |
| KV cache | `auto` resolves to BF16; 18,661,632,901 bytes (17.38 GiB) | Retained |
| Scheduler | 8 sequences; 8,192 batched tokens; chunked prefill | Retained |
| Prefix caching | Enabled | Correctness and reuse checked in Block A |
| Graphs | PIECEWISE with explicit splitting operators | CPU PLE lookup must run outside capture |
| Attention | jschmied deterministic QSA top-k, `e0ef69d4`; exact Torch fallback off | Already installed before A/B |
| PLE | mmap; 32 workers; prewarm on; MADV_RANDOM | Existing PLE upgrade retained |
| PLE metrics | Prometheus multiprocess export on; fresh 256 MiB tmpfs | Retained |
| Compilation caches | Persistent vLLM and FlashInfer bind mounts | Block A |
| GDN | SM12x FlashInfer selector compatibility patch | Block A |
| Sampling | FlashInfer sampler on; FlashInfer autotuning off; DeepGemm off | Retained |
| Tools / reasoning | `qwen3_coder`, `qwen3`; auto tool choice on | Retained |
| API | OpenAI-compatible `/v1`; served name `qwen3.8-flash-next` | Port 8000 by default |

`production.json` is the allowlisted export of the actual running container: full argument list, graph splitting operators, environment variables and container settings. `serve.py` uses that export, including the previously omitted graph and mmap settings. No private hostnames, credentials or original user filesystem paths are needed.

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

## Measured results and limits

| Test | Baseline | Candidate / current | Interpretation |
|---|---|---|---|
| Block A correctness | 10/10 | 10/10 | Small frozen suite, not a general intelligence evaluation |
| Block A 483k retrieval | 336.11 s, 1 preemption | 319.18 s, 1 preemption | Single pair; preemption not fixed |
| Block A comparable short median | Reference | 3.1% longer latency | Runtime migration did not establish a general speed gain |
| Block B pooled decode, pass 1 | K2 40.54 tok/s | K3 43.94 tok/s | +8.4% |
| Block B pooled decode, pass 2 | K2 43.30 tok/s | K3 46.72 tok/s | +7.9% |
| Block B correctness | 16/16 K2 requests | 16/16 K3 requests | All 32 passed |
| Subsequent K3 483,011-token retrieval | — | 318.49 s, correct, 1 preemption | Closes the previously unrun K3 retrieval check |
| Block C Eugr/B12X | Current K3 retained | Startup failed, no inference benchmark | See failure note below |

Decode values are pooled proxies computed from completion tokens minus first tokens and inter-token latency counters. Both B passes used one start per arm; the first K2 start was already running. They do not establish repeatability across independent boots. Outputs/lengths sometimes differed. A small arithmetic sample also exceeded the acceptance guard: first-position acceptance 100% to 88.9% in pass 2. The original >=10% speed promotion rule was not met. K3 was adopted by explicit operator choice as a provisional improvement; that decision does not rewrite the test rule.

The later 483k result tests extractive retrieval, not long-context reasoning quality. The K3-specific prefix-repeat gate remains unrun. Persistent cache mounts/files were verified; startup savings have not been isolated in a paired recreate test. Kernel selection is deterministic by design; whole-model cross-start determinism is not established.

Block C: the first candidate hit the MTP context-limit validator. With the long-context environment override added, it reached model construction and failed a 20 MiB CUDA allocation in the vision encoder while reporting approximately 105 GiB free. That is an unresolved allocation failure, not proof that the full checkpoint cannot fit or that Eugr is slower. No candidate responses were produced. The working Blazux/K3 container was restored and its health endpoint returned HTTP 200. No further experiment or recurring automation is running.

Evidence: `evidence/block-a.json`, `evidence/block-b.json`, `evidence/k3-483k.json`, and `evidence/block-c-state.json`. Full experimental protocols remain in the original local experiment folders; this package contains compact summaries, not a complete independent benchmark reproduction kit.

## Credits, source pins and licensing

See [CREDITS.md](CREDITS.md). The bundled `upstream` snapshot is Blazux `d542745cd41045bcd71b9d7dbe659bca014202bf` plus the documented local build/diagnostic patches. Its README describes upstream alternatives and measurements; this top-level README is the description of this particular production setup.

The base image is pinned to `vllm/vllm-openai@sha256:c2914767605584b6d8f45686b82de173ecc99e781897aa3d0a66dacd72c51ae1`. The observed deployed image ID is recorded in `production.json`; that local image ID is not a public registry download address. The Dockerfile fetches jschmied source by commit and file checksum.

The bundled upstream Apache-2.0 license and original source notices are retained. Model weights have separate terms provided by their publishers; this package does not relicense weights. Local integration helpers are provided under Apache-2.0. No model weights or credentials are included.
