# 高端模型适配路线（SCNet）

## 主线：DeepSeek-V4-Flash-0731

CommonBrain Ops 的主线高端模型定为 `DeepSeek-V4-Flash-0731`，不再使用预览版。SCNet AI 社区已有同名正式模型条目，页面说明其适用于本地和 vLLM 部署，并提供国产卡适配的快速开发入口：

- 模型页：[SCNet AI 社区 / DeepSeek-V4-Flash-0731](https://www.scnet.cn/ui/aihub/models/sugon_scnet/DeepSeek-V4-Flash-0731)
- 官方模型说明：[DeepSeek-V4-Flash-0731 模型详情](https://www.scnet.cn/ui/aihub/models/sugon_scnet/DeepSeek-V4-Flash-0731)
- 官方 SCNet 新闻：[DeepSeek-V4 上线超算互联网](https://www.scnet.cn/home/news/133249.html)

页面明确给出了 `reasoning_effort=low/high/max`、DSpark 推测解码以及 OpenAI 兼容编码路径。该模型属于 284B 总参数、13B 激活参数的 MoE，不能把“激活参数较小”误解成“一张 64GB 卡即可承载完整权重”。

### 一键部署配置

1. 在 SCNet AI 社区克隆/选择 `DeepSeek-V4-Flash-0731` 的国产卡镜像。
2. 进入“模型部署/推理服务”，资源规格选择 `异构加速卡 BW 64GB × 8`（平台当前公开的 BW 核心节点规格）。
3. 使用镜像自带启动命令和服务端口，不手工重新下载权重；先以短上下文、`reasoning_effort=low` 做健康检查。
4. 再做 `low/high/max` 三档合成任务评测，记录首 token 延迟、总延迟、成功率、显存和并发吞吐。
5. 通过服务详情获取平台生成的私有 API 地址；不要把 SSH 密码或任何平台密钥写入仓库。

当前已确认模型页和正式版本条目存在；当前 SSH Notebook 是单卡实例，因此尚未把 8 卡模型服务冒充为已创建。创建 8 卡服务需要在已登录的 SCNet 控制台完成资源提交。

## 第二基准：Qwen3.8-27B-FP8

为满足“至少 27B”的基准要求，已从 ModelScope 下载并逐文件 SHA-256 校验 `Qwen/Qwen3.8-27B-FP8`，权重目录约 29GiB。官方模型卡将其定义为 27B 的视觉语言模型，支持 vLLM/OpenAI 兼容接口。

在当前 BW-1 Notebook 上的边界结果：

- Transformers 5.15.1 能够完成 1,520 个权重分片加载，证明权重和新架构可被识别；
- 当前 SCNet DAS vLLM 0.11.0 不识别 `qwen3_5` 架构；
- 独立 Transformers + fine-grained FP8 kernel 在生成阶段触发 ROCm/DAS Triton 编译崩溃，尚未形成可对外 API；
- 该结果记录为“27B 适配边界”，不作为生产可用性声明。优先使用 SCNet 官方镜像完成正式部署。

远端证据位于 `/root/private_data/commonbrain-ops/evidence/qwen38_27b_probe6.log` 与 `qwen38_27b_probe7.log`，其中不含用户业务数据。

## 证据口径

- `Qwen3-0.6B`：已完成 BW-1 vLLM 冒烟和 384 请求有界并发压测，是当前链路基线。
- `Qwen3.8-27B-FP8`：完成权重下载、校验和模型加载边界测试；生成 kernel 仍需匹配平台镜像。
- `DeepSeek-V4-Flash-0731`：已确认 SCNet 正式模型条目和一键开发入口；待 8 卡 BW 服务实例实际启动后再发布吞吐与 API 结果。

