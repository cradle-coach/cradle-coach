# 2026-07-14 API Bridge Backend

## 背景

MiniCPM-o-Demo 当前仅支持 PyTorch 本地推理（`PyTorchBackend`），需要 GPU 和模型权重本地部署。OpenBMB 已发布 MiniCPM-o 4.5 官方托管 API（`api.modelbest.cn/minicpmo45/v1/`，免费），可以用云端推理替代本地模型加载，Phase 0-5 开发不再依赖昇腾 NPU 审批。

## 目标

新增 `ApiBridgeBackend`，作为 MiniCPM-o-Demo 的第三类 Backend（现有 `PyTorchBackend` 和 `llama-omni-server` C++ Backend），在 Worker 端以独立进程运行，对上暴露与 `PyTorchBackend` 相同的 WebSocket 协议，对内将推理请求转发到 `api.modelbest.cn`。

## In Scope

- 新增 `minicpmo-demo/api_bridge_server.py`：API Bridge Backend（独立 WebSocket 服务进程）
- 修改 `minicpmo-demo/config.example.json`：新增 `api_bridge` 配置节和 `backend_server_url` 选项
- 保持 Worker 层完全不变：Whisper ASR + CosyVoice2 TTS 仍本地运行

## Out of Scope

- 不改动 `gateway.py`、`worker.py`、`runtime/` 的任何代码
- 不改动现有 `PyTorchBackend`
- 不实现昇腾 NPU 适配（Phase 6）
- 不修改 `RemoteBackendSession`（它已经是通用的 WebSocket 客户端）

## 验收标准

- [ ] `ApiBridgeBackend` 独立进程可启动，连接到 `api.modelbest.cn` 成功
- [ ] Worker 通过 WebSocket 连接 `ApiBridgeBackend`，完成一轮 Chat 模式对话
- [ ] Worker 通过 WebSocket 连接 `ApiBridgeBackend`，完成一轮 Duplex 全双工对话
- [ ] `docker compose up` 启动 Gateway + Worker + ApiBridgeBackend，浏览器全双工对话可用
- [ ] 现有 `PyTorchBackend` 模式仍可运行（通过 config 切换）
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 架构

```
原（PyTorch 本地）:
  Gateway → Worker → RemoteBackendSession(WS) → PyTorchBackend(local GPU)

新（API Bridge）:
  Gateway → Worker → RemoteBackendSession(WS) → ApiBridgeBackend → api.modelbest.cn(HTTPS/WSS)
                                                      ↑
                                              ASR/TTS 仍本地
```

## 风险

- `api.modelbest.cn` 的 WebSocket 全双工协议可能与 MiniCPM-o-Demo 的内部协议不完全匹配，需要适配层做格式转换
- API 当前免费但未来可能收费或限流——Phase 6 切回本地推理时不受影响
- API 延迟 > 本地推理延迟——开发阶段可接受，Phase 6 昇腾本地推理解决
