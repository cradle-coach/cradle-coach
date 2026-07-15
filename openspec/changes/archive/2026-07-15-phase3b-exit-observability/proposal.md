## 背景

`exit_manager.py`（§19 退出管理）和 `observability.py`（可观测性）已独立实现，需集成到 API Bridge 消息管线。沉默控制 + 对话流由 #6 处理。

## 变更内容

- 在 API Bridge 启动时初始化 `ExitManager` 和 `Observability` 实例
- 在 `worker_to_api()` 中检测用户输入是否包含退出关键词
- 在 `api_to_worker()` 中检测 inactivity timeout
- 可观测性记录会话日志到 `harness_logs/`

## Capabilities

### 新增能力
- `exit-and-observability`：API Bridge 层的退出管理和可观测性

## 影响范围

- `minicpmo-demo/api_bridge_server.py`
- `gateway_modules/exit_manager.py`（不变）
- `gateway_modules/observability.py`（不变）

## 验收标准

- [ ] 退出关键词检测 → 立即退出 + 合规退出语
- [ ] 30 分钟无交互自动休眠
- [ ] 可观测性初始化并创建日志目录
- [ ] `python3 -m pytest tests/ -v` 全部通过
