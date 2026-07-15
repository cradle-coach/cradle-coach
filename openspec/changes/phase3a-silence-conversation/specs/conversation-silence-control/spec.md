# Spec: 对话沉默控制

API Bridge MUST 追踪对话时间戳并在沉默超限时执行干预。

## ADDED Requirements

### Requirement: 沉默检测

API Bridge MUST 追踪最后一条消息的时间戳，并在沉默超过阈值时执行干预。

#### Scenario: 正常对话不触发

- **WHEN** AI 和用户在 60s 内有交互
- **THEN** 不触发任何干预

#### Scenario: 长时间沉默触发退出

- **WHEN** 自最后一条消息起超过 60s 无交互
- **THEN** API Bridge 向客户端发送合规退出消息
- **AND** 关闭会话

### Requirement: 追问计数

API Bridge MUST 追踪 AI 连续疑问句数量，超过阈值时干预。

#### Scenario: 连续追问限制

- **WHEN** AI 连续输出 >= 2 条疑问句
- **THEN** 下一轮 system_prompt 追加"请使用陈述句，不要提问"
