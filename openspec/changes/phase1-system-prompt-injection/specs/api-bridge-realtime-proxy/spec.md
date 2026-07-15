# Spec: API Bridge Realtime 代理（修改）

## MODIFIED Requirements

### Requirement: 消息双向转发

API Bridge MUST 双向转发所有 `input.append` 和 `session.close` 消息，并在转发 `session.init` 时注入合规 System Prompt（如客户端未提供）。

#### Scenario: session.init 注入合规 System Prompt

- **WHEN** 客户端发送 `session.init {payload: {}}`（不含 system_prompt）
- **THEN** API Bridge 在 payload 中注入 `config/cradlecoach_system_prompt.yaml` 的 System Prompt
- **AND** 转发给 Cloud API
