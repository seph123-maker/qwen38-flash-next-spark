[Home](../README.md) · [Setup](SETUP.md) · [Settings](CONFIGURATION.md) · [Tests](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Sources](SOURCES.md)

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

## Measurement details and evidence files

Output-generation rates above are estimates from server counters: total completion tokens minus the first token of each response, divided by accumulated inter-token latency. They exclude prompt processing and are not direct GPU-kernel timings. Total request times for retrieval include processing the input. Responses and output lengths sometimes differed even with temperature zero and a fixed seed.

The two-token baseline used an already-running server; the three-token setting used a different start. In the second arithmetic pass, first-position draft acceptance fell from 100% to 88.9%. That sample is too small to establish a general quality regression, but it exceeded the original 10-percentage-point acceptance guard. A dedicated repeated-prefix check has not been rerun with three-token drafting; the earlier check passed during the runtime comparison with two-token drafting.

These filenames retain the original experiment identifiers so the evidence stays traceable:

| Evidence file | Contents |
|---|---|
| [Runtime comparison](../evidence/block-a.json) | Previous server versus vLLM 0.29.0: correctness, latency and preemptions |
| [Two- versus three-token drafting](../evidence/block-b.json) | Generation speed, acceptance and correctness by task category and pass |
| [Long-prompt retrieval](../evidence/k3-483k.json) | The later 483,011-token test with three-token drafting |
| [Alternative server startup](../evidence/block-c-state.json) | Failed candidate startup and completed production restore |

The full experimental protocols and response files remain in the original local experiment folders. This repository includes compact evidence summaries, not the complete fixtures and scoring tools needed for an independent rerun of every benchmark. The launch instructions reproduce the serving configuration.
