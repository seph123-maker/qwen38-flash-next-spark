[Home](../README.md) · [Sources](SOURCES.md)

# September 19: tool-parser correctness update

When a model explains tool syntax, quoted XML-like tool markers can resemble real tool calls. These upstream fixes preserve that text and the following answer instead of emitting an unintended tool call or losing output.

## Credits and source

- Patch 12, malformed tool preambles: [JordiPosthumus, PR 20](https://github.com/blazux/qwen3.8-Flash-DGX/pull/20).
- Patch 13, quoted markers and code fences: [techfury90, PR 29](https://github.com/blazux/qwen3.8-Flash-DGX/pull/29), including Blazux review follow-ups for CommonMark fence lengths and channel changes.
- Integration: [Blazux revision 5be6637](https://github.com/blazux/qwen3.8-Flash-DGX/tree/5be66376e8beaf96655f2d5682c82d538a970e66). Bundled source preserves upstream authorship and license notices.

## Deployed change

The existing ed65cc8 preview image received only patches 12 and 13, applied in order with zero patch fuzz. Model weights, vision support, 500,000 context, YaRN factor 4, automatic BF16 KV allocation at 0.80 utilization, two-token MTP, reduced vocabulary and cache settings stayed unchanged. This was not a vLLM-version migration.

The public build uses the complete upstream 5be6637 Dockerfile. Its only executable Dockerfile additions over the preceding snapshot are these two patches. A clean build from this public checkout has not been independently repeated; Docker image IDs need not match the deployed layered image.

## Verification

| Check | Result |
|---|---|
| Upstream standalone quoted-marker regression suite | 30/30 passed |
| Code generation | 2/2 passed |
| Native tool-call formatting | 2/2 passed |
| Arithmetic | 1/1 passed |
| Approximately 32k retrieval | 1/1 passed |
| Live health endpoint after promotion | HTTP 200 |

[Machine-readable results](../evidence/parser-upgrade-20260919.json). The standalone suite is `upstream-blazux/src/patches/qwen-tool-marker-guard-tests.patch`; it exercises the combined parser with both fixes applied. This is not a claim that every upstream vLLM test ran.

The initial launch was blocked by a separate image-generation workload occupying GPU memory. After that workload was stopped, the same configuration loaded and passed. No memory setting was reduced to obtain a pass.

## Limits

These are correctness and startup checks, not a performance A/B. Historical 483k and 679k measurements predate this parser update and were not repeated. Vision inference was not tested in this upgrade. Upstream still documents limitations around illustrative unfenced tool XML in reasoning and unclosed code fences; these patches do not eliminate every tool-parsing ambiguity.
