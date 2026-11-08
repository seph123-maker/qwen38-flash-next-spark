# Update 2026-11-08 — package re-export gb10-tp1-202611051744 (geometry move)

## What changed vs the 2026-11-05 era
| Field | Nov-05 snapshot (0945 pkg) | Live now (1744 pkg) |
|---|---|---|
| Package | `gb10-tp1-202611050945` | `gb10-tp1-202611051744` (re-exported Nov-06 00:48 +0700; 0945 removed from disk) |
| Max concurrency | 5 | **32** |
| KV pool | 2,318,336 tok / 31.2 GiB | **~1.86M tok / 28.2 GiB, boot-variable ("limited by memory")** — observed 1,921,024 and 1,855,488 on two boots |
| Shared snapshot slots | 40 | **~202** |
| Sustained decode | 36.0–37.8 tok/s | **37.6–40.8 tok/s** (2026-11-08, verified-idle, [artifact](../evidence/flare-sustained-20261108.json)) |
| Binary | prebuilt `18b16e1` | unchanged |
| ExecStart flags | full list in config | unchanged, byte-for-byte |

## Why the package moved
The 0945 export was replaced by a fresh same-vintage re-export (recipe `18b16e1` +
the local `ignition/components/linear.py` 2-kwarg backport, flashinfer pinned
`560fef16`). The binary+package contract stays locked: `18b16e1` binary + `1744`
package only.

## Verified 2026-11-08 (not inherited)
- `readlink -f` both symlinks: binary → `/root/flare-staging-18b16e1/flare`, package → `.../house/gb10-tp1-202611051744`
- `/v1/models` engine block: max_model_len 262,144; max_concurrency 32; prefill chunk 4,096; vocab 248,320
- Boot trace: `Allocate cache 28.2 GiB · 1855488 KV tokens · 202 shared snapshot slots · limited by memory`
- `flare inspect` rc=0 on BOTH rungs: live pair AND the cross-vintage last-good pair (`oct27-3a6b46f` binary + `1744` package)
- Watchdog v5 active (60 s tick, 300 s boot grace, n<=THRESHOLD cap, counter reset on every action)
- Two verified-idle decode samples, gate = active==0 and free_slots==max_concurrency (gate now self-derives max from /v1/models; it was hard-coded to the c5-era value 5)

## Deliberate non-adoptions (unchanged)
- `0009b89` recipe lane: writes proto field `method` the `18b16e1` binary rejects; needs its own binary (no prebuilt; Rust build).

## Ops rules that still hold
- One heavy workload on the box at a time (Flare OR ComfyUI/H3).
- Rollback = two `ln -sfn` flips (binary + package together), never a unit rewrite.
- Gate promotion smokes on explicit `reasoning_effort: "low"`; default effort has a non-deterministic empty tail.

## Open items
- drowzeys graft re-export staged, awaiting operator go.
- 0009b89 binary via Rust build to test the next-era contract.

## Graft cutover (later 2026-11-08)

The drowzeys QSA/GDN sidecar — staged since Nov-05, awaiting operator go — was
baked and promoted on 2026-11-08 after John's go-ahead.

- **Why the re-export was needed:** `flare` rejects any tensor name present in two
  files, and the index must agree with the file that physically holds each tensor.
  The sidecar's 96 keys still existed as stock copies inside
  `model-00001-of-00021.safetensors`, so the snapshot had to be re-cut: the 96
  stale copies were stripped from that one shard (all 96 lived in it), byte-verified
  8644/8644 against stock, then prepared with the same `/root/flare` tree that
  built 1744 (local `linear.py` patch, flashinfer `560fef16`).
- **Result:** package `gb10-tp1-202611080129`, geometry identical to stock
  (262,144 / c32 / 4,096 / 248,320 / MTP 1-6), gate battery passed (see
  `config/active-20261108.json: model.graft`). Promoted via two-symlink flip;
  last-good updated to the verified pair (18b16e1 + stock 1744).
- **Effect:** default-effort short prompts no longer burn the budget on thinking —
  8/8 clean post-boot probes vs the stock build's non-deterministic empty tail.
- **Source of record:** `/root/grafted-tree-1108` kept on the Spark; the Nov-05
  attempt tree (`grafted-tree-1105`) was removed.
