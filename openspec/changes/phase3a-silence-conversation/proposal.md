## 背景

`silence_controller.py`（§10 沉默控制）和 `conversation_flow.py`（对话流管理）已独立实现，需集成到 API Bridge 消息管线。退出管理 + 可观测性由 #18 单独处理。

## 变更内容

- 在 API Bridge 中初始化 `SilenceController` 和 `ConversationFlow` 实例
- 在 `api_to_worker()` 中追踪消息时间戳，检测沉默超时
- 沉默超过 60s 时触发退出流程（通过 exit_manager 回调）
- 在 `api_to_worker()` 中注入对话流状态（难度提示、追问计数）

## Capabilities

### 新增能力
- `conversation-silence-control`：API Bridge 层的对话节奏管理和沉默检测

### 修改的能力
- `api-bridge-realtime-proxy`：消息管线增加沉默检测和对话流状态注入

## 影响范围

- `minicpmo-demo/api_bridge_server.py`：初始化 SilenceController + ConversationFlow，注入检测逻辑
- `gateway_modules/silence_controller.py`：现有模块（不变）
- `gateway_modules/conversation_flow.py`：现有模块（不变）

## 验收标准

- [ ] 沉默超过 60s 触发退出流程
- [ ] AI 连续追问超过 2 次后强制陈述句
- [ ] `python3 -m pytest tests/ -v` 全部通过
