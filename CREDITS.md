# Credits tied to deployed artifacts

| Contribution | Source |
|---|---|
| Serving foundation, PLE mmap, ModelOpt hybrid dispatch, prefix-cache fix, v0.29 port | [Blazux pinned recipe](https://github.com/blazux/qwen3.8-Flash-DGX/tree/d542745cd41045bcd71b9d7dbe659bca014202bf) |
| Deterministic QSA top-k CUDA source | [jschmied kernel-det, e0ef69d4](https://github.com/jschmied/qwen38-flash-next-gb10/tree/e0ef69d4f5575dad00d34e05479eaf4c6547bace/patches/kernel-det), [upstream PR 55122](https://github.com/vllm-project/vllm/pull/55122) |
| FP8 side-layer converter, GB10 FLA fixes, faster PLE gather and state-copy guard | [Saren-Arterius fork](https://github.com/Saren-Arterius/qwen3.8-Flash-DGX-AutoRound), incorporated by Blazux |
| PLE metrics and explicit KV-budget serving option | [techfury90, Blazux PR 19](https://github.com/blazux/qwen3.8-Flash-DGX/pull/19) |
| Enable worker-pool gathering for all PLE requests | [techfury90, Blazux PR 25](https://github.com/blazux/qwen3.8-Flash-DGX/pull/25); tested locally using the existing implementation's environment setting |
| Persistent compilation cache option | [AronRubin, Blazux PR 21](https://github.com/blazux/qwen3.8-Flash-DGX/pull/21) |
| Reasoning-effort aliases, adapted into the Python launcher with a writable template copy and read-only mount | [techfury90, Blazux PR 24](https://github.com/blazux/qwen3.8-Flash-DGX/pull/24), [Blazux writable-cache fix](https://github.com/blazux/qwen3.8-Flash-DGX/commit/4ab5fbd0c5) |
| MADV_RANDOM advice idea, reimplemented by Blazux | [MiaAI-Lab recipe](https://github.com/MiaAI-Lab/Qwen3.8-Flash-Next-Single-DGX-Spark) |
| Sparse top-k problem diagnosis | [k3dani, Blazux issue 3](https://github.com/blazux/qwen3.8-Flash-DGX/issues/3) |
| Mamba state-copy race fix already included in v0.29 | [AndreasKaratzas, vLLM PR 50729](https://github.com/vllm-project/vllm/pull/50729) |
| GDN SM12x compatibility change ported locally | [vLLM PR 55715](https://github.com/vllm-project/vllm/pull/55715) |
| Optional NVIDIA block-FP8 MTP loader backport in image | [techfury90, vLLM PR 55513](https://github.com/vllm-project/vllm/pull/55513); not the current BF16 drafter's format |
| Base model | [Qwen](https://huggingface.co/Qwen) |
| Abliteration and NVFP4 checkpoint lineage | [windowsxp811203/Qwen3.8-Flash-Next-Abliterated-NVFP4](https://huggingface.co/windowsxp811203/Qwen3.8-Flash-Next-Abliterated-NVFP4), named as the parent in the [pinned Gorbatjovy card](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8/blob/2065365912e46b205c64a70ac5b85b4869674d31/README.md) |
| FP8 PLE repack | [gorbatjovy checkpoint](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8) |
| Inference runtime and underlying kernels | [vLLM](https://github.com/vllm-project/vllm), [FlashInfer](https://github.com/flashinfer-ai/flashinfer), [PyTorch](https://github.com/pytorch/pytorch), NVIDIA CUDA |

Local contributions: assembling pinned sources, the GDN selector adaptation, logging-only allocation diagnostics, persistent-cache deployment, the comparison of drafting two versus three tokens ahead, and publication helpers. The underlying kernel and recipe authors retain credit.

Related but not deployed: [Eugr](https://github.com/eugr/spark-vllm-docker) and [B12X](https://github.com/local-inference-lab/b12x) supplied the alternative serving stack we tried; that candidate failed startup before any inference benchmark. Nanetnounou's optional FP8-KV work is credited by upstream but is not enabled in this BF16-KV recipe. The reduced-vocabulary patch exists in the image and is disabled.

License notices in `upstream/LICENSE` and source headers are preserved. No MiaAI source is newly copied into this bundle; the deployed mmap implementation is the Blazux implementation. Checkpoint redistribution remains subject to the checkpoint/base-model licenses rather than the serving-code license.
