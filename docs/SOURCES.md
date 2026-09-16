[Home](../README.md) · [Credits](../CREDITS.md) · [Tests](TESTING.md)

# Sources, model lineage and reproducibility

## Current serving inputs

Current source: [Blazux ed65cc8](https://github.com/blazux/qwen3.8-Flash-DGX/tree/ed65cc80646e85cf6631b93d7dfcf9412183cc30), bundled under [upstream-blazux](../upstream-blazux/). Base: `vllm/vllm-openai:qwen38-flash-next@sha256:fc120ece0a388cc0aa1caad4a9f1cd92113484ab7ec2fd0efadd62585be05bf8`. Built image ID: `sha256:11e907b55b7489d3ccec7f4d9cede4791ad1d7fd0a95252ee9ab6d8fb618dc59`. Current exact launch: [production.json](../production.json). Our selection uses the upstream preview recipe, plus supported model/cache/metrics options.

## Two separate things: serving code and model weights

Blazux's repository provides the serving foundation. It is not the publisher of the abliterated weights used here. We selected a separate checkpoint and applied the compatible side-layer conversion tool.

| Stage | Source | What the attribution means |
|---|---|---|
| Original model | [Qwen](https://huggingface.co/Qwen) | Base model developer |
| Abliteration and NVFP4 derivative | [windowsxp811203/Qwen3.8-Flash-Next-Abliterated-NVFP4](https://huggingface.co/windowsxp811203/Qwen3.8-Flash-Next-Abliterated-NVFP4) | Parent explicitly named by the selected checkpoint's card |
| FP8 PLE repack | [Gorbatjovy card at the selected revision](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8/blob/2065365912e46b205c64a70ac5b85b4869674d31/README.md) | Published checkpoint we downloaded |
| Additional FP8 side-layer conversion | [Bundled converter](../upstream/tools/fp8_convert.py), credited to Saren-Arterius | Creates the local `-fp8hybrid` directory |

The pinned Gorbatjovy card declares `base_model: windowsxp811203/Qwen3.8-Flash-Next-Abliterated-NVFP4` and `license_name: qwen-community-license-1.0`. Those are model-card provenance statements; our serving tests do not independently measure the effect of abliteration or prove quality parity with the base model. References to RadixArk's work in upstream credits do not by themselves establish that its tensor files are part of this checkpoint's lineage.

## Current checkpoint

The table above describes our **former** WindowsXP/Gorbatjovy checkpoint. Current lineage: Qwen → [NVIDIA NVFP4](https://huggingface.co/nvidia/Qwen3.8-Flash-Next-NVFP4) → [Drowzeys house projection](https://huggingface.co/drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47/blob/a393318fb56d9aedc56d91b6f4962d9af26d2fe7/README.md) → local Saren-Arterius FP8 side-layer conversion. Drowzeys credits Dealign as the projection-axis source. Our earlier checkpoint authors are not part of this new lineage.

## Historical custom v0.29 inputs

These pins describe the previous image, preserved for comparison. Current source and base are listed above.

| Input | Pin / reference |
|---|---|
| Blazux serving source | [`d542745cd41045bcd71b9d7dbe659bca014202bf`](https://github.com/blazux/qwen3.8-Flash-DGX/tree/d542745cd41045bcd71b9d7dbe659bca014202bf) |
| Base container | `vllm/vllm-openai@sha256:c2914767605584b6d8f45686b82de173ecc99e781897aa3d0a66dacd72c51ae1` |
| Attention kernel | [jschmied `e0ef69d4f5575dad00d34e05479eaf4c6547bace`](https://github.com/jschmied/qwen38-flash-next-gb10/tree/e0ef69d4f5575dad00d34e05479eaf4c6547bace/patches/kernel-det) |
| Downloaded checkpoint revision | `a393318fb56d9aedc56d91b6f4962d9af26d2fe7` |
| Observed deployed image ID | `sha256:256342813adc473736bf153e83b050a8e408da8c5ac7544bfbeeff397041853a` |
| Build instructions | [Dockerfile](../upstream/Dockerfile.block-a) |
| Previous launch settings | [previous-679k-config.json](../evidence/previous-679k-config.json) |

The observed image ID is a local Docker content identifier, not an image we have published to a registry. Build the image from the included Dockerfile. It fetches the kernel files by commit and validates their file checksums. A rebuild need not produce the same image ID.

## Historical custom additions (previous image)

| Local addition / selection | File or evidence |
|---|---|
| Pinned base image, limited build parallelism and local patch application | [Dockerfile.block-a](../upstream/Dockerfile.block-a) |
| GDN SM12x selector adaptation from upstream PR 55715 | [patch_gdn_sm12.py](../upstream/patch_gdn_sm12.py), [upstream PR](https://github.com/vllm-project/vllm/pull/55715) |
| Allocation/preemption logging, without scheduler behavior changes | [patch_diagnostics.py](../upstream/patch_diagnostics.py) |
| Former three-token/full-vocabulary configuration | [previous configuration](../evidence/previous-679k-config.json) |
| Launcher and measured comparison summaries | [serve.py](../serve.py), [evidence directory](../evidence) |

The current checkpoint differs from upstream stock weights; reduced draft vocabulary now follows upstream. Do not substitute current upstream defaults and describe the result as this exact configuration.

## Reproducibility status

| Claim | Status |
|---|---|
| Running configuration exported | Yes, using an explicit allowlist excluding credentials |
| Build source and base pinned | Yes |
| Public launcher checked on Linux | Dry-run command generation checked; the new launcher itself was not used to replace production |
| Entire published setup rerun from a clean machine | No |
| Full benchmark fixtures, responses and scorer published | No; only compact result files are included |
| Whole-model repeatability across independent starts established | No |
| Byte-for-byte reproducible image or local converted weights established | No |

These limits matter when interpreting a reported percentage. The included results support the bounded claims in [Tests and decisions](TESTING.md), not a universal ranking against other recipes. Upstream headline results and other checkpoint authors' quality evaluations are not substituted for our own measurements.

## Code and model licenses

The bundled Blazux license notice and original file headers are retained in [LICENSE](../LICENSE) and [upstream/LICENSE](../upstream/LICENSE). They identify Apache-2.0; the [full Apache-2.0 text](https://www.apache.org/licenses/LICENSE-2.0.txt) defines those code-license terms. Local integration helpers use Apache-2.0.

The current [Drowzeys card](https://huggingface.co/drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47/blob/a393318fb56d9aedc56d91b6f4962d9af26d2fe7/README.md) declares NVIDIA Open Model License and Qwen Community License 1.0 terms. The former Gorbatjovy checkpoint declares Qwen Community License 1.0. See its [license at the pinned revision](https://huggingface.co/gorbatjovy/qwen3.8-flash-next-abliterated-NVFP4-plefp8/blob/2065365912e46b205c64a70ac5b85b4869674d31/LICENSE). Code licensing does not replace the model terms. No model weights are distributed here.

Per-contribution author links are in [CREDITS.md](../CREDITS.md). The preserved upstream README covers additional options that are not deployed here; crediting those projects does not imply every optional patch is enabled.
