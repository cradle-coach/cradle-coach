# api-bridge-realtime-proxy Specification

## Purpose
TBD - created by archiving change api-bridge-full-interaction. Update Purpose after archive.
## Requirements
### Requirement: 动态 mode 路由

API Bridge MUST 从客户端 WebSocket 升级请求 URL 中提取 `?mode=` 参数，并路由到对应的 Cloud API 模式。未指定 mode 时默认使用 audio（full_duplex）模式。

#### Scenario: Chat 模式路由

- **WHEN** 客户端连接 `wss://host/v1/realtime?mode=chat`
- **THEN** API Bridge 连接到 Cloud API 的 `?mode=chat` 端点
- **AND** 返回 `session.created` 的 mode 字段为 `turn_based`

#### Scenario: 默认 Audio 模式

- **WHEN** 客户端连接 `wss://host/v1/realtime`（无 mode 参数）
- **THEN** API Bridge 连接到 Cloud API 的 `?mode=audio` 端点
- **AND** 返回 `session.created` 的 mode 字段为 `full_duplex`

### Requirement: Half-Duplex 协议翻译

API Bridge MUST 将 half-duplex Gateway 协议消息翻译为 Cloud API 协议。

#### Scenario: 握手流程

- **WHEN** 客户端连接 `/ws/half_duplex/<sessionId>` 并发送 `prepare {system_content, config}`
- **THEN** API Bridge 连接到 Cloud API audio 模式
- **AND** 等待 `session.queue_done` 后发送 `session.init {system_prompt}`
- **AND** 收到 `session.created` 后向客户端返回 `prepared {session_id}`

#### Scenario: 音频数据翻译

- **WHEN** 客户端发送 `audio_chunk {audio_base64}`
- **THEN** API Bridge 翻译为 `input.append {audio, force_listen: false}` 并转发到 Cloud API

### Requirement: 消息双向转发

API Bridge MUST 双向转发所有 `input.append` 和 `session.close` 消息，并在转发 `session.init` 时注入合规 System Prompt（如客户端未提供）。

#### Scenario: session.init 注入合规 System Prompt

- **WHEN** 客户端发送 `session.init {payload: {}}`（不含 system_prompt）
- **THEN** API Bridge 在 payload 中注入 `config/cradlecoach_system_prompt.yaml` 的 System Prompt
- **AND** 转发给 Cloud API

### Requirement: 队列事件吸收

API Bridge MUST 正确处理 Cloud API 队列事件。

#### Scenario: 有队列的启动流程

- **WHEN** Cloud API 发送 `session.queued` 后发送 `session.queue_done`
- **THEN** API Bridge 吸收队列事件，在 `queue_done` 后发送 `session.init`

#### Scenario: 无队列的直接启动

- **WHEN** Cloud API 直接发送 `session.created`（跳过队列）
- **THEN** API Bridge 直接转发 `session.created` 给客户端

