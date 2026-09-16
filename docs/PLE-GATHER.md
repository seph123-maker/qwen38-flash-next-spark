# PLE worker-pool comparison — September 16, 2026

Following [Blazux PR 25 by techfury90](https://github.com/blazux/qwen3.8-Flash-DGX/pull/25), we tested `VLLM_PLE_MMAP_FAST_ROWS=0` against the previous default of 512. Zero sends every nonempty gather through the existing worker pool, allowing page faults to overlap. No new GPU kernel or vLLM version is involved.

| Paired comparison | Threshold 512 | Threshold 0 | Change |
|---|---:|---:|---:|
| First | 41.98 tok/s | 44.53 tok/s | +6.1% |
| Second | 42.50 tok/s | 45.61 tok/s | +7.3% |

All 24 scripted correctness checks passed. Code improved by 16.0% and 18.7%; other categories were mixed, including small declines. Full category figures are in [the results](../evidence/ple-gather.json).

## Method and decision

One independent server start, ordered A1–B1–B2–A2, using the current Gorbatjovy weights, K3, 500k configuration and existing caches. Each phase used six existing fixtures: two code tasks, two tool tasks, arithmetic and 32k retrieval. Temperature and seeds were fixed; each phase used fresh prefix-cache salts. A test-only file-read hook switched the threshold in the same process; both arms incurred that hook. Production uses the normal environment setting without the hook.

Before measurement, the rule required at least 5% pooled decode improvement in both paired comparisons, all correctness checks passing and no category dropping over 10%. It passed. Pooled rate is sum(completion tokens minus one per request) divided by the accumulated inter-token-latency counter delta. These are server-counter estimates, not GPU-kernel timings.

This small, single-start comparison does not establish gains for every workload or checkpoint. It does not test 483k preemption, and the percentages must not be added to the earlier drafting gains. Correctness means passing bounded scripted tasks, not general intelligence or proven output determinism.

## Model status

The deployed checkpoint remains Gorbatjovy. The NVIDIA-derived [Drowzeys checkpoint](https://huggingface.co/drowzeys/keys-Qwen3.8-Flash-Next-NVFP4-dual-ablit-house-qsa-L3-47) is being staged separately; no local quality, speed or memory comparison for it is reported here. Blazux's newer phase-timing counters are also not part of this change.
