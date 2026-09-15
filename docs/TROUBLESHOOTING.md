[Home](../README.md) · [Setup](SETUP.md) · [Using the server](USAGE.md) · [Tests](TESTING.md)

# Troubleshooting from this deployment

Start with the container's first specific error. The final message “engine initialization failed” usually wraps an earlier cause.

```bash
docker ps -a --filter name=qwen38-published
docker logs --tail 120 qwen38-published
free -h
df -h
```

| Symptom | What it can mean | Next check |
|---|---|---|
| API unavailable immediately after launch | Weights are still loading | Follow logs. Roughly 8–13 minutes was normal on this machine; that is not a guaranteed deadline. |
| Launcher says container already exists | It intentionally refuses replacement | Start the existing container, or choose another name for a changed configuration. |
| Prepared pinned model missing | Downloaded base weights lack the expected `-fp8hybrid` sibling, or a different revision was prepared | Compare the path in `production.json` with the cache. Use the isolated-cache setup instructions. |
| Missing tokenizer/config/shard | Incomplete download or stale converted directory | Verify the pinned source download and the conversion's selected source. Do not assume installing a tokenizer package repairs missing model files. |
| Context limit says 262,144 instead of 500,000 | A long-context override was omitted or the runtime interprets it differently | Compare the full environment and RoPE arguments in `production.json`. The published launcher includes both. |
| Long prompt reports preemption | Not enough cache blocks were available at an allocation point | Record counts and request sizes. One occurred in our successful 483k tests; it is an unresolved performance limitation. |
| Reload is slow despite persistent caches | Compiled graphs and model weights are different things | Check cache mounts, then distinguish compilation time from weight-loading time in logs. |
| Client can chat but tools fail | Client definitions, parser or application behavior may differ | Check the actual tool-call response and parser settings. A successful text reply does not validate an agent loop. |
| Responses differ at temperature zero | Numerical/execution differences can persist despite deterministic attention selection | Record image, server start and request settings. Do not claim whole-model determinism from the kernel flag alone. |

## The alternative runtime's allocation failure

The Eugr/B12X trial failed a **20 MiB** allocation while the runtime reported **about 105 GiB free**. It occurred during vision-encoder construction, before loading the complete model or running an inference benchmark.

That result is insufficient to blame the checkpoint size, the vision component's total memory cost, or the alternative recipe's performance. Memory reporting, allocation behavior and that image's configuration need investigation. No root cause was established. Removing vision or changing weights would change the treatment and should be documented as a separate experiment.

## Reading the cache diagnostics

The local diagnostic patch only logs allocation information; it does not change scheduling. One recorded allocation required nine blocks when eight were available around 360k processed tokens. Increasing a cache budget might help some allocations, but it also competes with model and file-cache memory. We have not validated a new budget as a fix.

## Information to include in an issue

Provide the first meaningful error and nearby stack frames, the exact model/image revisions, context and cache settings, and whether another workload was running. Review logs before sharing: diagnostic excerpts are usually enough, and complete prompts or Docker environment dumps may contain private information.
