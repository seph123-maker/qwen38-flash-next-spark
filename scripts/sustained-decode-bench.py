#!/usr/bin/env python3
"""Idle-gated sustained-decode bench for the Spark brain (Flare lane).

Publishable metric ONLY: 2048-token single-stream sustained decode.
Burst probes misreport this box badly. Each sample runs only if the box is
verified idle at start (flare_active_requests==0, flare_free_request_slots==5);
mid-run metric snapshots document contention. decode_tps = completion_tokens/(wall-ttft).

Run ON the Spark:  python3 sustained-decode-bench.py [out.json]
Requires: no deps beyond stdlib + curl. Never run while chat traffic flows;
if a sample's end metrics show active>0, quarantine it (caveat field) -- do not
promote to a README headline.
"""
import json, subprocess, sys, time, urllib.request

BASE = "http://127.0.0.1:8000"
MODEL = "qwen3.8-flash-next"
PROMPT = ("Write a long, detailed, original essay about the history of lighthouse "
          "keeping: cover antiquity, the 18th and 19th century golden age, notable "
          "lighthouse engineers, daily life of keepers, the mechanization of lighting, "
          "and the eventual automation. Do not stop early; continue in detail as long "
          "as you can.")

def metrics():
    try:
        out = subprocess.run(["curl", "-s", "--max-time", "5", BASE + "/metrics"],
                             capture_output=True, text=True).stdout
        d = {}
        for line in out.splitlines():
            if line.startswith("flare_active_requests ") or line.startswith("flare_free_request_slots "):
                k, v = line.split()
                d[k] = float(v)
        return d
    except Exception as e:
        return {"err": str(e)}

def _max_slots():
    # derive from live engine; was hard-coded 5 (c5 era), engine now reports max_concurrency 32
    try:
        out = subprocess.run(["curl", "-s", "--max-time", "5", BASE + "/v1/models"],
                             capture_output=True, text=True, timeout=8).stdout
        import json as _json
        return _json.loads(out)["data"][0]["flare"]["max_concurrency"]
    except Exception:
        return 5

def idle(m, _mx=[None]):
    if _mx[0] is None:
        _mx[0] = _max_slots()
    return m.get("flare_active_requests", -1) == 0 and m.get("flare_free_request_slots", -1) == _mx[0]

def run(n):
    m0 = metrics()
    if not idle(m0):
        print(f"run {n}: SKIPPED - not idle {m0}")
        return None
    body = {"model": MODEL, "stream": True, "stream_options": {"include_usage": True},
            "max_tokens": 2048, "temperature": 0.8, "top_p": 0.9,
            "messages": [{"role": "user", "content": PROMPT}]}
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    t0, ttft, usage, mid = time.time(), None, {}, []
    for raw in urllib.request.urlopen(req, timeout=300):
        line = raw.decode().strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if payload == "[DONE]":
            break
        try:
            d = json.loads(payload)
        except Exception:
            continue
        if d.get("usage"):
            usage = d["usage"]
        ch = d.get("choices") or [{}]
        if ttft is None and (ch[0].get("delta") or {}).get("content") is not None:
            ttft = time.time() - t0
        if ttft is None:
            continue  # still prefilling/thinking-before-first-token
        now = time.time()
        if not mid or now - mid[-1][0] > 10:
            mid.append((round(now - t0, 1), metrics()))
    wall = time.time() - t0
    ct, pt = usage.get("completion_tokens", 0), usage.get("prompt_tokens", 0)
    dec = ct / max(wall - ttft, 1e-6) if ttft else 0
    end = metrics()
    r = {"run": n, "prompt_tokens": pt, "completion_tokens": ct,
         "ttft_s": round(ttft, 2) if ttft else None,
         "wall_s": round(wall, 2), "decode_tps": round(dec, 2),
         "overall_tps": round(ct / wall, 2),
         "active_at_start": m0.get("flare_active_requests"),
         "midrun_metrics": mid, "end_metrics": end,
         "caveat": None if idle(end) else "contention observed -- quarantine"}
    print(f"run {n}: completion={ct} ttft={r['ttft_s']}s wall={r['wall_s']}s decode={r['decode_tps']} t/s")
    return r

out = {"date": time.strftime("%Y-%m-%d"),
       "method": "POST /v1/chat/completions, stream=true, stream_options.include_usage, "
                 "max_tokens=2048, temperature=0.8, top_p=0.9, single stream; "
                 "decode_tps = completion_tokens / (wall - ttft)",
       "idle_gate": "flare_active_requests==0 and flare_free_request_slots==5 at start; "
                    "mid-run snapshots recorded; non-idle samples get a quarantine caveat",
       "samples": [s for s in (run(i) for i in (1, 2)) if s]}
path = sys.argv[1] if len(sys.argv) > 1 else f"flare-sustained-{time.strftime('%Y%m%d')}.json"
open(path, "w").write(json.dumps(out, indent=2) + "\n")
print("saved", path)
