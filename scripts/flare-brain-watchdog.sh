#!/bin/bash
# flare-brain-watchdog v5 (2026-11-05) — flare-only era.
#   probe :8000/v1/models; on N consecutive misses, flip BOTH the binary and the package symlink
#   back to the persistent last-good rungs, then restart flare. If already at last-good, restart in
#   place and alert. TensorFold / vLLM are NOT parachutes (John closed those lanes 2026-11-05).
#   B2: last-good lives on disk (/root/flare-releases), not /run, so it survives reboot.
#   B3: boot-in-flight guard retained — never act while a boot is in progress (~80 s).
LINK=/usr/local/bin/flare-current
PLINK=/usr/local/share/flare-package-current
REL=/root/flare-releases
LG=$REL/last-good
PKG_LG=$REL/last-good-pkg
FAILS=/run/flare-watchdog-fails
THRESHOLD=${THRESHOLD:-3}
TICK=${TICK:-60}
BOOT_GRACE_US=${BOOT_GRACE_US:-300000000}    # COUPLED: keep >= TimeoutStartSec in flare.service
                                              # (300s). Below that the watchdog fights systemd's own
                                              # patience; the n<=THRESHOLD cap is what escapes a
                                              # crash-loop, which StartLimitIntervalSec=0 allows forever.
log(){ logger -t flare-watchdog -- "$*"; echo "$(date '+%F %T') $*"; }

if curl -sf -m 10 http://127.0.0.1:8000/v1/models >/dev/null; then echo 0 > "$FAILS"; exit 0; fi

n=$(cat "$FAILS" 2>/dev/null || echo 0); n=$((n+1)); echo $n > "$FAILS"
log "probe miss ($n/$THRESHOLD)"
[ "$n" -lt "$THRESHOLD" ] && exit 0

# BEGIN-BOOT-GUARD  (extractable: the cutover script's --guard-test harness runs this block
# standalone with stubbed $systemctl/$n, because bash -n cannot evaluate arithmetic)
# B3/B7: /proc/uptime is a FLOAT. bash $(( )) is integer-only; `$((48291.73*1000000))` errors and
# leaves the variable a string, which silently makes the very next test false — i.e. the guard
# would never protect a healthy boot. Do the float->int math in awk, never in $(( )).
now_us=$(awk '{printf "%.0f\n", $1*1000000}' /proc/uptime)
start_us=$(systemctl show -p ExecMainStartTimestampMonotonic --value flare.service 2>/dev/null || echo 0)
case "$start_us" in ''|*[!0-9]*) start_us=0 ;; esac
pid=$(systemctl show -p MainPID --value flare.service 2>/dev/null || echo 0)
case "$pid" in ''|*[!0-9]*) pid=0 ;; esac
boot_age_us=$(( now_us - start_us ))
if [ "$n" -le "$THRESHOLD" ] && [ "$pid" -gt 0 ] && [ "$start_us" -gt 0 ] && [ "$boot_age_us" -lt "$BOOT_GRACE_US" ]; then
  log "flare PID $pid is $((boot_age_us/1000000))s old (booting) — standing down, letting systemd finish"
  exit 0
fi
# END-BOOT-GUARD

lb=$(cat "$LG" 2>/dev/null || true); lp=$(cat "$PKG_LG" 2>/dev/null || true)
acted=0
# B2 guard: only flip if last-good is a real file/dir. Never `ln -sfn ""`.
if [ -n "$lb" ] && [ -x "$lb" ] && [ "$(readlink -f "$LINK" 2>/dev/null)" != "$(readlink -f "$lb")" ]; then
  log "rolling binary back: $LINK -> $lb"
  ln -sfn "$lb" "$LINK"; acted=1
fi
if [ -n "$lp" ] && [ -d "$lp" ] && [ "$(readlink -f "$PLINK" 2>/dev/null)" != "$(readlink -f "$lp")" ]; then
  log "rolling package back: $PLINK -> $lp"
  ln -sfn "$lp" "$PLINK"; acted=1
fi
if systemctl restart flare.service; then log "restart issued (~80-90s)"; acted=1
else log "FATAL: systemctl restart flare.service failed"; fi
# B8: reset the counter whenever we act. Without this, n stays > THRESHOLD forever, which both
# disables the boot grace and turns the loop into a 60s restart storm that never lets a boot finish.
[ "$acted" = 1 ] && echo 0 > "$FAILS"
