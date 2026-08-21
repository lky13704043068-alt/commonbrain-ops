#!/usr/bin/env python3
"""Synthetic CommonBrain Ops smoke evaluation for a local OpenAI-compatible endpoint."""
import json, os, time, uuid, urllib.request, statistics

BASE = os.environ.get("CB_BASE_URL", "http://127.0.0.1:10304")
MODEL = os.environ.get("CB_MODEL", "Qwen3-0.6B")
OUT = os.environ.get("CB_EVIDENCE", "/root/private_data/commonbrain-ops/evidence")
os.makedirs(OUT, exist_ok=True)

def get(path):
    t0 = time.perf_counter()
    req = urllib.request.Request(BASE + path, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode("utf-8", "replace")
            return {"status": r.status, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "body": body[:20000]}
    except Exception as e:
        return {"status": None, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "error": repr(e)}

def chat(task_id, system, user, max_tokens=128):
    payload = {"model": MODEL, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0.0, "max_tokens": max_tokens}
    req = urllib.request.Request(BASE + "/v1/chat/completions", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), method="POST", headers={"Content-Type": "application/json", "Accept": "application/json"})
    t0 = time.perf_counter()
    rec = {"request_id": str(uuid.uuid4()), "task_id": task_id, "model": MODEL, "prompt_chars": len(user)}
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            rec.update({"status": r.status, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "response": json.loads(r.read().decode("utf-8", "replace"))})
    except Exception as e:
        rec.update({"status": None, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "error": repr(e)})
    return rec

tasks = [
    ("sop_summary", "你是企业运维助手。只根据给定材料回答，不要编造。", "材料：周一发布前必须完成代码评审、备份数据库、灰度10%并观察30分钟。请用三条中文要点总结发布前检查。"),
    ("ticket_fields", "你是工单字段抽取器。请输出简短 JSON，字段为 priority、owner、deadline。", "工单：支付回调偶发超时，影响线上订单。负责人：李工。要求今天18:00前给出修复方案。"),
    ("routing", "你是任务路由器。只输出一个标签：技术、内容、运营、人工确认。", "用户反馈：模型部署时显存不足，需要调整并行策略。"),
    ("abstain", "你是审计助手。没有证据时明确说无法判断，不要猜测。", "问题：本系统上个月的真实客户满意度是多少？上下文没有提供任何统计数据。"),
    ("evidence", "你是可审计助手。回答时先给结论，再给依据；没有依据就说明缺少什么。", "上下文：本次测试只使用合成工单，不包含生产客户数据。问题：本次测试是否使用了生产客户数据？"),
]
health = {"base_url": BASE, "health": get("/health"), "models": get("/v1/models")}
records = [chat(*task) for task in tasks]
lat = [r["latency_ms"] for r in records if r.get("status") == 200]
summary = {"run_id": str(uuid.uuid4()), "model": MODEL, "base_url": BASE, "task_count": len(records), "http_success": sum(r.get("status") == 200 for r in records), "latency_ms": {"avg": round(statistics.mean(lat), 1) if lat else None, "p95": round(sorted(lat)[max(0, int(len(lat) * 0.95) - 1)], 1) if lat else None, "min": min(lat) if lat else None, "max": max(lat) if lat else None}, "health_status": health["health"].get("status"), "models_status": health["models"].get("status"), "synthetic_only": True, "notes": "smoke baseline; semantic quality requires a larger labeled set"}
with open(os.path.join(OUT, "health.json"), "w", encoding="utf-8") as f: json.dump(health, f, ensure_ascii=False, indent=2)
with open(os.path.join(OUT, "eval.jsonl"), "w", encoding="utf-8") as f:
    for r in records: f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f: json.dump(summary, f, ensure_ascii=False, indent=2)
print(json.dumps(summary, ensure_ascii=False, indent=2))
for r in records:
    text = ""
    if isinstance(r.get("response"), dict):
        choices = r["response"].get("choices", [{}])
        text = (choices[0].get("message", {}).get("content") or "") if choices else ""
    print(f"[{r['task_id']}] status={r.get('status')} latency_ms={r.get('latency_ms')} output={text[:300]!r}")
