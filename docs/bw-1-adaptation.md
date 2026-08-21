# BW-1 国产模型适配冒烟记录

状态：内部验证记录（2026-08-21），不是生产性能承诺。

## 目标

验证 CommonBrain Ops 能否在 SCNet BW-1 异构加速卡上加载国产模型、提供 OpenAI-compatible 接口，并让路由/审计评测脚本完成一轮闭环。测试只使用合成工单和 SOP，不包含真实客户数据。

## 实测环境

- BW-1 Notebook，1 张 BW HCU，`gfx936 / BW / C-3000`，平台标注 64GB；
- Ubuntu 22.04.5，Python 3.11.9，DTK 26.04，HIP 6.3.26093；
- `torch==2.9.0+das.opt1.dtk2604`，`transformers==4.57.6`；
- 官方 DAS wheel：`vllm==0.11.0+das.opt1.dtk2604.torch290`；
- 模型：`Qwen/Qwen3-0.6B`，权重 SHA256：`f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`。

## 结果

服务启动参数为单卡、BF16、最大上下文 2048、显存利用率 0.70、eager 模式，监听本地 `10304` 端口。`/health` 和 `/v1/models` 均返回 HTTP 200；5 个合成任务全部返回 HTTP 200，平均端到端延迟 2971.6ms，最小 2788.2ms，最大 3633.9ms。

评测脚本见 [`scripts/bw_eval.py`](../scripts/bw_eval.py)，任务包括 SOP 摘要、工单字段抽取、任务路由、无证据拒答和数据来源核验。脚本保存 request_id、状态码、延迟和模型输出，便于复测。

## 适配注意事项

基础环境首次枚举设备时缺少 `amdsmi`；在项目独立虚拟环境补齐后，PyTorch 设备枚举恢复正常。vLLM 依赖必须使用与 DTK/PyTorch 匹配的官方 DAS wheel，不能直接用 CUDA 版公开 PyPI wheel 覆盖平台 PyTorch。0.6B 仅用于链路冒烟，后续应在 SCNet 专家确认的镜像上扩展至 7B/14B，并补充带标签任务、并发、长上下文、超时降级和卡时记录。

官方参考：

- [SCNet AI 服务](https://www.scnet.cn/help/docs/mainsite/ai/index.html)
- [SCNet vLLM 环境搭建](https://www.scnet.cn/help/docs/mainsite/ai/appendix/environment-vLLM/)
- [SCNet vLLM 模型部署](https://www.scnet.cn/help/docs/mainsite/ai/model-deploy/vllm/)
- [SCNet 国产异构加速卡实践](https://www.scnet.cn/help/docs/mainsite/ai/practice/application/ultralytics/)
