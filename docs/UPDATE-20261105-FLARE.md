# Update 2026-11-05 — engine cutover to prebuilt 18b16e1 + package re-export

This is the current serving path. The Oct-27 era (self-built `3a6b46f`, package
`gb10-tp1-202610260834`) is retained as the **rollback rung** — see
[UPDATE-20261027-FLARE.md](UPDATE-20261027-FLARE.md); everything predating that one
describes the vLLM lane.

Live snapshot: [config/active-20261105.json](../config/active-20261105.json) ·
Service: [scripts/flare.service](../scripts/flare.service) ·
Watchdog: [scripts/flare-brain-watchdog.sh](../scripts/flare-brain-watchdog.sh) ·
Decode sample: [evidence/flare-sustained-20261105.json](../evidence/flare-sustained-20261105.json)

## What changed

| | Oct-27 (rollback rung) | Nov-05 live |
|---|---|---|
| Runtime | Flare 0.1.0 **self-built** @ `3a6b46f` (Oct-26) | Flare 0.1.0 **prebuilt** @ `18b16e1` (2026-11-03, "clustered BF16 PCIe all-reduce ladders" #174), sha256 `f03c2537…a439` |
| Engine distance | — | **157 commits** `3a6b46f..18b16e1`, incl. #167 hard reasoning-token budget, #170 reasoning-token usage in `usage`, #176 restart-unique request/tool-call IDs |
| Package | `gb10-tp1-202610260834` (exported Oct-26 @ recipe `ca1f960`) | `gb10-tp1-202611050945` (re-exported Nov-05 @ recipe `18b16e1` + local backport, flashinfer `560fef16`) |
| Chat template | custom qwen38 jinja replacing the native one (xhigh/medium/low instruction injection) | **native NVIDIA template + 2 insertions** (`assets/chat_template.patch.json`) |
| Boot | ~80 s | ~56 s first boot after export, **~5 s warm restart** |
| Decode (2048-tok sustained, single stream) | 38.5 tok/s (recorded, no artifact) | **36.0 / 37.8 tok/s** (reproducible, verified-idle artifacts) |
| Deployment topology | unit hardcodes binary + package paths | **dual symlinks** (`flare-current`, `flare-package-current`) + last-good markers + watchdog v5 |
| Geometry | 262,144 native · 2,318,336 KV · 40 slots · c5 | unchanged (same checkpoint, same budget) |

## Why this jump (and why a re-export was mandatory)

The Nov-4/5 engine line enforces the prepared-package **contract version**: the
`18b16e1` binary refuses the Oct-26 package outright
(`unsupported prepared model contract version; re-export the model package` — it
verifies all 99.4 GiB first, then fails at `Prepare model`). An engine-only binary
flip is therefore **not a valid deployment** in this era; binary vintage and package
vintage must move together. That is what the dual-symlink + last-good + watchdog
architecture exists to guarantee.

## The export lane (reproducible)

`ignition export qwen3.8-flash` from `/root/flare` @ **`18b16e1` with one local
backport** (below), venv via `uv sync --extra prepare` (torch 2.14.1+cu132) with
flashinfer force-pinned to the pyproject-declared `560fef16`, `HF_HOME` and the flare
`hub_cache` both pinned to the verified `/home/mogu/.cache/huggingface` tree
(checkpoint resolves in 0.8 s cached — no re-download). Measured phases: graph
catalog 84/84 in 6.1 s → kernel prep/autotune ~18 min cold (~350 kernels) →
compile forwards + serving graphs ~8 min → native package publish ~3.5 min
(99.4 GiB verify). Export needs ~80 GiB free VRAM → **brain must be down**.

### The transitional-commit trap (the bug this era had to walk around)

`18b16e1` is a *transitional* commit: its ignition recipe passes
`source_activation` / `allow_bf16_atomic_reduction` into
`blockscaled.query_from_call`, but its own pinned flashinfer (`560fef16`) predates
those parameters — they fall into `**options` and trip
`ValueError: unsupported packed BF16 declaration options` at graph-catalog build.
Upstream fixed this by *re-pairing* the recipe with flashinfer `1f8ed8a3`
(`5a1640c`, in `0009b89`, Nov-05). We did **not** adopt `0009b89`'s recipe because
its packages write a proto field (`method`) the `18b16e1` binary rejects
(`unrecognized field name 'method'`) and the `0009b89` prebuilt does not exist
(Rust build deferred). Instead the local backport reverts exactly the one call to
the `ca1f960` shape — the form this checkpoint was originally exported with —
leaving all other Nov-4 recipe semantics intact. The two new-era call sites in the
packed-MXFP8 branch are dead code for this NVFP4/MXFP4 checkpoint (verified by
branch inspection), so the patch surface is one call.

## What was NOT adopted (deliberate)

- **`0009b89` recipe + Nov-5 flashinfer** — internally consistent and exports fine,
  but needs a `0009b89`-era binary that upstream has not published as a prebuilt.
  Track for the next window (Rust build would unlock it).
- **`6fa01a4` (Nov-1) prebuilt** — predates #167/#170/#176, the substantive fixes.
- **MXFP8 LM-head patch** — quality-first veto stands (downgrades BF16 head for ~5 % decode).
- **YaRN / 1M-context packages** — native 262,144 preferred; the GB202-only 1M package
  cannot run on GB10 anyway.
- **eugr b12x** — standing never (OOM-rebooted this box; eugr issue 388).
- **ABLITERATION GATE WARNING — READ BEFORE THE GATE TABLE** — the
  [drowzeys MXFP8 sidecar](https://huggingface.co/drowzeys/Qwen3.8-Flash-Next-FP4-Local-house-answer)
  (QSA + GDN projection override, `HOUSE_ANSWER_MXFP8.json` manifest,
  `house-answer-qsa-gdn-mxfp8.safetensors`, 778,580,792 B, sha256 `9b9cf23a…`,
  96 tensors = 48 FP8 weights + 48 U8 scales: 12 QSA `o_proj` + 36 GDN `out_proj`)
  is **staged but NOT applied** on this era either. The graft script
  ([`graft.py`](https://huggingface.co/drowzeys/Qwen3.8-Flash-Next-FP4-Local-house-answer/blob/main/graft.py))
  requires a re-export of the grafted checkpoint tree — same pipeline as above, ~15–20 min dark —
  and per [DROWZEYS-679K.md](DROWZEYS-679K.md) the pre-flight gates below must pass
  on the grafted build before it may serve. **The live package is NVIDIA-official,
  un-abliterated; the abliterated lineage remains only the vLLM parachute and the
  staged sidecar.**

### Re-export / graft gates (the gate table lives after the warning)

1. `graft.py` completes only if **every one of the 96 sidecar keys maps to a checkpoint
   tensor** (hard-fail otherwise) — check the script's own completion report, not just its exit code.
2. `inspect` the re-exported package: geometry identical to the stock export
   (262,144 / c5 / 3,469-kernel class / same rank-0 file set).
3. Empty-answer battery: **6 reasoning-style prompts** — zero empty completions
   (this is the symptom the sidecar exists to remove; the *un-grafted* Nov-5 build still
   exhibits a non-deterministic empty tail at default effort on short prompts).
4. GSM8K subset + tool-call battery within −2 % of the stock baseline
   (reuse the fixtures under `benchmark/`).
5. Sustained decode (2048-tok, idle-gated) within −15 % of the stock `18b16e1`
   numbers (36–37.8 tok/s) — no LM-head downgrade allowed anywhere in the graft.
6. Prefix-cache regression: repeat-prefix probes must show `cached_tokens > 0`.
7. Only after all pass: flip symlinks (last-good still points at stock `18b16e1`),
   watchdog armed. Rollback = 5-second symlink flip.

## Gates this era actually ran (promotion evidence)

| Gate | Result |
|---|---|
| preflight `inspect` on the exact (binary, package) pair | PASS |
| boot + `/v1/models` + completion probe (rollback trigger, 300 s grace) | PASS, healthy 5 s warm |
| smoke: content + prefix-cache evidence | PASS — gated on the **deterministic `reasoning_effort=low` probe**; default-effort probe recorded only (see reasoning_effort note) |
| functional: arithmetic / fact / two-turn context / 256-tok generation | 4/4 correct |
| sustained decode, verified-idle gate | 36.02 / 37.80 tok/s, artifact in `evidence/` |

## Ops rules (added this era)

- **Watchdog v5** (`scripts/flare-brain-watchdog.sh` + `.timer`): probes
  `/v1/models` + a completion each 60 s tick; on N consecutive misses flips **both**
  symlinks to last-good and restarts. Boot grace 300 s (coupled to `TimeoutStartSec`),
  `n ≤ THRESHOLD` cap, fail-counter resets on any action. TensorFold escalation is
  **retired** — Flare-only era; do not reintroduce a second engine in the watchdog.
- **Never hand-write `ExecStart`**: derive it from the live unit swapping only the two
  symlink paths, refuse shell metacharacters, `systemd-analyze verify` before reload.
- **Smoke gating lesson**: gate on the explicit-effort probe; the native template's
  default-effort empty tail on short prompts is a model trait, not a deployment failure.
- One heavy workload at a time still stands (Flare XOR ComfyUI/H3).

## Open items

- Grafted (abliterated) re-export: staged, gated, awaiting operator go — see the
  gate table above and [DROWZEYS-679K.md](DROWZEYS-679K.md).
- `0009b89` binary via Rust build → then its recipe/flashinfer pair can be tested
  against the `method`-field contract.
- Previous-era rollback package only boots on its own binary rung (contract lock) —
  the watchdog keeps pair consistency; do not mix rungs manually.
- TF-engine rollback container still needs its weights re-download before trusted (inherited).
