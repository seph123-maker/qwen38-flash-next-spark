# Drowzeys and 679k context — September 16, 2026

Production now uses Drowzeys' NVIDIA-derived checkpoint at revision `a393318fb56d9aedc56d91b6f4962d9af26d2fe7`, prepared with the bundled Saren-Arterius FP8 side-layer converter. The original download is preserved. The converter reported a worst per-tensor maximum relative round-trip error of 0.0354; this is a numerical conversion check, not a quality score.

## Model comparison at 500k configured context

| Measurement | Previous Gorbatjovy | Drowzeys |
|---|---:|---:|
| Scripted checks, two passes of six tasks | 12/12 | 12/12 |
| Pooled decode estimate, pass 1 | 42.40 tok/s | 41.83 tok/s |
| Pooled decode estimate, pass 2 | 45.09 tok/s | 42.87 tok/s |
| Model-loading memory report | 77.23 GiB | 74.90 GiB |

Fixtures covered code, tool-call JSON, arithmetic and 32k retrieval. Both models used the selected worker-pool PLE setting, K3 and a fixed 17.38 GiB KV budget. Each model's two passes shared one start; this is not an interleaved independent-start benchmark or evidence of general quality parity. Drowzeys was kept by user choice after successful operation, not because it won on speed.

## Cache capacity versus usable request length

Blazux's reported 679k KV pool is not a validated single-request context limit. Our separate test raised the actual request limit to 679,000 tokens, including output.

| Drowzeys test | KV budget | Input tokens | Correct | Elapsed | Preemptions |
|---|---:|---:|---|---:|---:|
| Initial long retrieval | 17.38 GiB | 483,011 | Yes | 305.91 s | 1 |
| Larger cache, same input | 19.38 GiB | 483,011 | Yes | 302.27 s | 1 |
| Extended context | 19.38 GiB | 678,477 | Yes | 502.66 s | 3 |

The larger-cache 483k test missed its zero-preemption goal and was initially reverted. A subsequent, separately authorized 679k capacity test allowed preemptions and passed, so 19.38 GiB and 679k are now selected. vLLM reported 708,083 cache-token capacity at the larger budget. This does not guarantee all that capacity can be used by one request.

The extended fixture placed three exact keys around 10%, 50% and 90% of a repetitive maintenance-record archive. Temperature was zero; seed 42; thinking disabled; output budget 256 tokens. It returned the expected JSON in 46 output tokens and passed a subsequent short smoke check. See [679k evidence](../evidence/context679.json) and [initial Drowzeys 483k evidence](../evidence/drowzeys-483k.json).

## Limits

One synthetic retrieval success does not establish reasoning, code, agent-loop or realistic-document quality at this length. YaRN remains factor 4 with original context 262,144; no new YaRN comparison was performed. Three preemptions remain a performance limitation. Reserve output room within 679,000 total tokens. Neither the context increase nor checkpoint swap upgrades the pinned vLLM image or attention kernel. A clean rebuild from the published bundle remains unverified.
