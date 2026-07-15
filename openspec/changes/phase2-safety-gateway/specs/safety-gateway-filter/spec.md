# Spec: API Bridge 安全审核

API Bridge MUST 在转发 Cloud API 文本输出到客户端前进行安全检测，拦截违规内容并替换为合规话术。

## ADDED Requirements

### Requirement: 文本输出安全检测

API Bridge MUST 对每条 `response.output.delta`（kind=text）进行安全检测。

#### Scenario: 硬拦截检测

- **WHEN** AI 输出包含自伤/暴力关键词（如"自杀""杀死"）
- **THEN** 该 delta 被替换为安全话术
- **AND** 拦截事件记录到日志

#### Scenario: 情感绑定检测

- **WHEN** AI 输出包含情感绑定表述（如"我喜欢你"）
- **THEN** 该 delta 被替换为合规话术
- **AND** 拦截事件记录到日志

#### Scenario: 正常内容通过

- **WHEN** AI 输出不包含任何违规模式
- **THEN** delta 原样转发给客户端

#### Scenario: 音频不检查

- **WHEN** AI 输出 `response.output.delta` kind=audio
- **THEN** delta 原样转发，不进行文本检测
