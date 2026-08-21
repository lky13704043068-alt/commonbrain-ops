# BW-1 CommonBrain Ops 复测 Runbook

## 启动

```bash
cd /root/private_data/commonbrain-ops
nohup ./launch_vllm.sh > vllm.log 2>&1 & echo $! > vllm.pid
curl -f http://127.0.0.1:10304/health
curl -f http://127.0.0.1:10304/v1/models
```

## 合成评测

```bash
/root/private_data/commonbrain-ops/.venv/bin/python scripts/bw_eval.py
```

结果写入 `evidence/health.json`、`evidence/eval.jsonl` 和 `evidence/summary.json`。

## 停止

```bash
kill "$(cat vllm.pid)"
```

本轮使用 Qwen3-0.6B 作为链路冒烟基线，输入全部为合成数据；不要将生产客户数据或 API Key 放入该目录或日志。
