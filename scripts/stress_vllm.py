#!/usr/bin/env python3
"""Bounded synthetic concurrency stress test for a local OpenAI-compatible endpoint."""
import concurrent.futures, json, os, statistics, time, urllib.request, uuid

BASE = os.environ.get("CB_BASE_URL", "http://127.0.0.1:10304")
MODEL = os.environ.get("CB_MODEL", "Qwen3-0.6B")
OUT = os.environ.get("CB_EVIDENCE", "/root/private_data/commonbrain-ops/evidence")
LEVELS = [int(x) for x in os.environ.get("CB_LEVELS", "1,4,8,16,32,64").split(",")]
REQUESTS_PER_LEVEL = int(os.environ.get("CB_REQUESTS_PER_LEVEL", "64"))

def one(i, level):
    paragraph = ("运维演练材料：发布前完成代码评审、数据库备份、10%灰度并观察30分钟。 " * (1 + (i % 4)))
    payload = {"model": MODEL, "messages": [{"role":"system", "content":"你是可审计的企业运维助手，只根据材料回答。"}, {"role":"user", "content": paragraph + "请用一句话列出发布前检查项。"}], "temperature": 0.0, "max_tokens": 64, "stream": False}
    req = urllib.request.Request(BASE + "/v1/chat/completions", data=json.dumps(payload, ensure_ascii=False).encode(), method="POST", headers={"Content-Type":"application/json", "X-Load-Test":"synthetic"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            body = json.loads(r.read().decode("utf-8", "replace"))
            return {"ok": r.status == 200, "status": r.status, "latency_ms": round((time.perf_counter()-t0)*1000, 1), "request_id": str(uuid.uuid4()), "usage": body.get("usage", {})}
    except Exception as e:
        return {"ok": False, "status": None, "latency_ms": round((time.perf_counter()-t0)*1000, 1), "request_id": str(uuid.uuid4()), "error": repr(e)}

def run_level(level):
    t0 = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=level) as ex:
        rows = list(ex.map(lambda i: one(i, level), range(REQUESTS_PER_LEVEL)))
    lat = [x["latency_ms"] for x in rows if x["ok"]]
    ordered = sorted(lat)
    return {"concurrency": level, "requests": len(rows), "success": sum(x["ok"] for x in rows), "duration_s": round(time.perf_counter()-t0, 2), "avg_ms": round(statistics.mean(lat), 1) if lat else None, "p50_ms": ordered[len(ordered)//2] if ordered else None, "p95_ms": ordered[max(0, int(len(ordered)*.95)-1)] if ordered else None, "max_ms": max(lat) if lat else None, "errors": [x.get("error") for x in rows if not x["ok"]][:5]}

started = time.time()
results = [run_level(level) for level in LEVELS]
summary = {"run_id": str(uuid.uuid4()), "started_epoch": started, "base_url": BASE, "model": MODEL, "levels": LEVELS, "requests_per_level": REQUESTS_PER_LEVEL, "synthetic_only": True, "results": results}
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "stress_summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
