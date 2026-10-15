# EXECUTION REPORT — qwen38-flash v2 staged config upgrade
Host: DGX Spark 192.168.1.11 · Executed: 2026-10-15 (Asia/Bangkok, +07) · All times local.

## Step 1 — pre-flight (11:51, all clean)
- `:8188/system_stats` → `000` (ComfyUI not resident)
- `docker ps` → `qwen38-flash Up 14 hours`
- `free -g | awk NR==2` → `Mem: 121 105 2 0 15 15` (Mem line; the awk target)
- Explicit swap check: `Swap: 15Gi total, 148Mi used` (< 1 GiB ✓)

## Step 2 — apply (11:51:31 → 11:57:34, 360 s)
- `python3 /root/qwen38-flash-v2.py apply`
- Output (verbatim):
  ```
  a78ff6b88a0695172da620b4791b39859f4d6be9a0dc8baa95ec12a720c7f9eb
  new container starting; warming up…
  TIMEOUT: not healthy in 360s — run: python3 /root/qwen38-flash-v2.py rollback
  ```
- No `HEALTHY` line; warmup window = full 360 s. Per the stated fallback, rollback was run.
- Rollback (11:57:40 → 11:57:41), output (verbatim):
  ```
  ABORT: --hf-overrides pattern '"factor":\s*4\.0' matched 0x — live config drifted from audit assumptions
  ```
  Per the script's own ABORT semantics (before any docker run), the rollback changed nothing: the new v2 container stayed live (crash-looping, see Noticed) and `qwen38-flash-ROLLBACK-1015` stayed Exited.
- Manual restore (12:07:04 → 12:10:11): executed the script's own rollback block's four docker operations verbatim (`stop` v2 → `rename` v2 → `qwen38-flash-FAILED-1015` → `rename` ROLLBACK-1015 → `qwen38-flash` → `start`). Restored container: **HEALTHY after 135 s**, single clean start (RestartCount=0, StartedAt 12:07:16).

## Step 3 — /v1/models (12:10:21)
```
qwen3.8-flash-next 500000
```
→ 500000 shown → per the stated fallback: v2 not in effect, stop and report. (The v2 container's non-default-args dump did show the intended values — max_model_len 524288, kv_cache_dtype fp8_e4m3, max_num_seqs 4, hf-overrides factor 2.0 / original_max_position_embeddings 262144, speculative max_model_len 524288, VLLM_PLE_MMAP_WORKERS=16 — but the serving brain is on the prior config.)

## Step 4 — gates (12:10:37 → 12:13:01, exit 1)
No ssh timeouts inside; no rerun needed. Full JSON (verbatim):
```json
{
 "gate2": {
  "kv_pool_tokens": 0,
  "pool_logged_at": "",
  "swap_used_bytes": 155471872,
  "mem_available_kib": 18224072,
  "verdict": "ABORT"
 },
 "gate1": {
  "tok_per_s": 42.85,
  "baseline_tok_per_s": 43.56,
  "gather_ms_per_op": null,
  "major_faults_1024tok": 13084,
  "verdict": "REVIEW"
 },
 "gate3a": {
  "nll": 2.99899,
  "baseline": 2.99899,
  "delta": -0.0,
  "verdict": "PASS"
 },
 "gate3b": {
  "context_tokens": 198817,
  "blocks": 12,
  "exact_match": true,
  "verdict": "PASS"
 },
 "gate4": {
  "first_token_logprob_delta": 0.0,
  "greedy32_identical": true,
  "verdict": "PASS"
 }
}
```

## 3-line factual summary
1. gate3a, gate3b, gate4 = PASS.
2. gate2 = ABORT: `kv_pool_tokens` parsed as 0 from the current container log (script's own log-parse regex found no "GPU KV cache size" line in this container's log file).
3. gate1 = REVIEW: 42.85 tok/s vs baseline 43.56 (98.4%, above the 0.95 bar) but `gather_ms_per_op` = null (script's `docker logs --since 3m | grep "mmap stats"` found no parseable "gather <x.xx> ms" sample), so it stays at the initial REVIEW.

## Noticed (facts, no verdicts)
- The v2 container (now `qwen38-flash-FAILED-1015`, preserved) was in a deterministic ~2.5-min crash loop: every incarnation died in the APIServer process with `FileNotFoundError: [Errno 2] No such file or directory: '/tmp/vllm-prometheus/counter_1.db'` (prometheus_client MmapedDict, PrometheusStatLogger/spec-decode init), then clean exit 0 (no OOM), auto-restarted by its restart policy. `PROMETHEUS_MULTIPROC_DIR=/tmp/vllm-prometheus` is set in the container env (inherited verbatim from the old container) and that dir does not exist in the fresh container's /tmp; vLLM's own prometheus.py logs "Found PROMETHEUS_MULTIPROC_DIR was set by user" and does not makedirs in that case. The old container has been running with the same env var without issue.
- The script's `rollback` mode calls `derive()` (which expects the old `"factor": 4.0` / `"max_model_len": 500000` values) for all modes, so after a successful apply it can ABORT on its own pre-check.
- Container state at report time: `qwen38-flash` = prior config (500000 / kv auto / seqs 8 / factor 4.0), Up and healthy; `qwen38-flash-FAILED-1015` = v2 config container, Exited; `qwen38-flash-next-tf` = Exited (pre-existing); `:8188` = 000 (ComfyUI not resident).
