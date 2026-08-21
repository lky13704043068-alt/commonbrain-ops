#!/usr/bin/env bash
set -euo pipefail

ROOT="${COMMONBRAIN_ROOT:-/root/private_data/commonbrain-ops}"
export VLLM_TARGET_DEVICE="rocm"
export HIP_VISIBLE_DEVICES="${HIP_VISIBLE_DEVICES:-0}"
export HSA_VISIBLE_DEVICES="${HSA_VISIBLE_DEVICES:-0}"

exec "$ROOT/.venv/bin/python" -m vllm.entrypoints.openai.api_server \
  --model "$ROOT/models/Qwen3-0.6B" \
  --host 0.0.0.0 --port 10304 \
  --gpu-memory-utilization 0.70 \
  --served-model-name Qwen3-0.6B \
  --dtype bfloat16 --tensor-parallel-size 1 \
  --max-model-len 2048 --trust-remote-code --enforce-eager
