# Share a useful result

This repository records one tested configuration. Improvements and independent reproductions are welcome through [issues](https://github.com/seph123-maker/qwen38-flash-next-spark/issues) and pull requests.

For a startup problem, include the hardware, driver, image and checkpoint revisions, launch settings, and the first relevant error. Redact credentials and private prompts. A final “engine failed” line alone rarely identifies the cause.

For a performance comparison, report:

- Exact weights and any conversion, with revisions.
- The setting changed, plus everything else that differs.
- Prompt and output token counts, task category, thinking setting, temperature and seed.
- Whether each measurement used the same server start, a fresh start, warm caches or reused prefixes.
- Both correctness and timings; distinguish prompt processing from answer generation.
- Repeats, failed requests, preemptions and concurrent traffic.

Compare against the current configuration on the same workload. A faster answer caused by fewer output tokens, a warmer prefix cache or a different checkpoint is useful information, but it is not an isolated serving-speed improvement.

When changing source files, preserve author notices and explain the difference from the pinned upstream version. Avoid including downloaded weights, local caches, tokens, complete Docker environment dumps or unrelated machine configuration.

Documentation updates should link claims to a source or included measurement. Label proposed improvements as proposals until tested. Refresh `SHA256SUMS` whenever tracked package files change.
