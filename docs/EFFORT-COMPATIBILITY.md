# Reasoning-effort compatibility

The September 15 launcher update adapts [techfury90's Blazux PR 24](https://github.com/blazux/qwen3.8-Flash-DGX/pull/24) and [Blazux's writable-template fix](https://github.com/blazux/qwen3.8-Flash-DGX/commit/4ab5fbd0c5).

| Client value | Template receives |
|---|---|
| `high`, `max` | `xhigh` |
| `minimal` | `low` |
| `low`, `medium`, `xhigh`, omitted | Original behavior |

The launcher writes a copy of the checkpoint template inside its compilation-cache directory, then mounts that file read-only at `/qwen38/chat_template.jinja`. It leaves the checkpoint files intact and fails explicitly if the expected template line cannot be uniquely identified. Choose a writable `--compile-cache` directory; the Hugging Face cache need not be writable for this operation.

The change adds API compatibility; it does not upgrade vLLM or GPU kernels and has no measured throughput benefit. The pinned image, weights, context and speculative-decoding settings remain the same.

Template rendering checks verified byte-identical prompts for the original supported settings and for each alias versus its target. Live API results are recorded in [the verification summary](../evidence/effort-alias.json). These short requests check request acceptance, not reasoning quality or speed.

Implementation: [effort_alias.py](../effort_alias.py), [serve.py](../serve.py).
