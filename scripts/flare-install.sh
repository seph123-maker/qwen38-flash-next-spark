#!/usr/bin/env bash
# Reproduce the live Flare serving path on a DGX Spark (GB10, aarch64).
# See docs/UPDATE-20261027-FLARE.md for context and rollback layers.
# Idempotent where possible; run as root on the Spark.
set -euo pipefail

FLARE_REPO="https://github.com/NVIDIA/flare-local-inference"
FLARE_COMMIT="${FLARE_COMMIT:-3a6b46f}"          # live serving commit
PKG="nvidia/Qwen3.8-Flash-Next-FP4-Local"
PKG_REV="${PKG_REV:-gb10-tp1-202610260834}"
PKG_DIR="/root/.cache/flare/packages/models/nvidia_2FQwen3.8-Flash-Next-FP4-Local/${PKG_REV}"
BUILD_DIR="${BUILD_DIR:-/root/flare-x-build}"

# 0. One-heavy-workload guard: refuse to start the brain next to ComfyUI/H3.
if curl -sf -m 2 http://127.0.0.1:8188/api/system_stats >/dev/null 2>&1; then
  echo "ERROR: ComfyUI/H3 is live on :8188 — stop it first (121 GiB unified pool)." >&2
  exit 1
fi

# 1. Build the release binary from the pinned commit.
if [ ! -x "$BUILD_DIR/target-x/release/flare" ]; then
  git clone "$FLARE_REPO" "$BUILD_DIR"
  git -C "$BUILD_DIR" checkout "$FLARE_COMMIT"
  (cd "$BUILD_DIR" && cargo build --release --target-dir target-x)   # long; ~30-60 min on GB10
fi
"$BUILD_DIR/target-x/release/flare" --version

# 2. Fetch the prepared package (99.4 GiB) unless already resident.
#    flare verifies signatures + a full hash pass on every boot with --verify-weights.
if [ ! -d "$PKG_DIR" ]; then
  "$BUILD_DIR/target-x/release/flare" download "$PKG" --revision "$PKG_REV"
fi

# 3. Install the unit and start it.
install -m 0644 "$(dirname "$0")/flare.service" /etc/systemd/system/flare.service
systemctl daemon-reload
systemctl enable --now flare.service

# 4. Verify. Boot is ~80 s (45 s weight verification included); poll, don't assume.
for _ in $(seq 1 60); do
  curl -sf -m 3 http://127.0.0.1:8000/health >/dev/null && break
  sleep 5
done
curl -sf http://127.0.0.1:8000/health
echo
curl -sf http://127.0.0.1:8000/v1/models | head -c 400
echo
echo "OK — served as qwen3.8-flash-next on :8000 (native 262144 ctx, 2.32M KV pool, c5)."
echo "Decode numbers: benchmark only when /metrics shows flare_active_requests 0 and"
echo "flare_free_request_slots 5 — the endpoint is shared with a second Hermes user."
