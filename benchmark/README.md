# Synthetic benchmark files

Run on Linux on the Spark with a model serving at localhost:8000. Python scripts use the standard library. Review `safe_code.py` before using the scorer: it executes constrained model-generated Python in a subprocess and is **not a security sandbox**. Use trusted synthetic outputs or an isolated environment, not arbitrary untrusted responses.

```bash
python3 bench.py my-arm --only code-clamp,code-dedupe,tools-read,tools-search,reason-thinking-arithmetic,long-32k
python3 bench.py my-long-arm --only long-483k
```

Each output directory is resumable: saved result files are skipped. Use a new label for a fresh run. Pause unrelated inference; the harness checks request counters for contamination. Prompts, raw responses, before/after metrics and grades are saved locally. Fixed salts differ across arm labels to prevent deliberate cross-arm prefix reuse.

Code is graded by constrained execution of supplied tests; JSON by exact parsed equality; tools by native tool names/arguments with no extra content. Long retrieval uses repetitive synthetic filler and three known keys. These are bounded correctness screens, not comprehensive intelligence or long-context reasoning benchmarks.

The historical per-request `decode_counter_tps` field divides all completion tokens by decode time. Published pooled figures subtract one token per request before aggregation. Do not average the per-request rates to reproduce the published table.
