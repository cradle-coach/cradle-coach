# Spec: 合规 System Prompt 注入

API Bridge 启动时加载 CradleCoach 合规 System Prompt，并在每次 Cloud API 会话中自动注入。

## ADDED Requirements

### Requirement: 启动时加载合规 System Prompt

API Bridge MUST 在启动时加载 `config/cradlecoach_system_prompt.yaml` 并将 System Prompt 内容缓存在内存中。

#### Scenario: 通过 CLI 参数指定

- **WHEN** API Bridge 以 `--system-prompt config/cradlecoach_system_prompt.yaml` 启动
- **THEN** System Prompt 从 YAML 文件加载到内存
- **AND** 后续所有会话使用该 System Prompt

#### Scenario: YAML 文件不存在

- **WHEN** 指定的 YAML 文件不存在
- **THEN** API Bridge 输出警告并继续运行（不注入 System Prompt）

### Requirement: session.init 自动注入

API Bridge MUST 在转发 session.init 到 Cloud API 时，如果客户端未提供 `system_prompt`，则注入合规 System Prompt。

#### Scenario: 客户端未提供 system_prompt

- **WHEN** 客户端发送 `session.init {payload: {}}`（无 system_prompt）
- **THEN** API Bridge 在 payload 中添加合规 System Prompt
- **AND** 转发给 Cloud API 的 session.init 包含 `{system_prompt: "你是 CradleCoach..."}`

#### Scenario: 客户端已提供 system_prompt

- **WHEN** 客户端发送 `session.init {payload: {system_prompt: "自定义"}}`
- **THEN** API Bridge 保留客户端提供的 system_prompt
- **AND** 不覆盖

### Requirement: 合规人格输出验证

Cloud API 使用合规 System Prompt 后，AI 输出 MUST 遵守 5 核心原则和 5 类禁止表述。

#### Scenario: 禁止情感绑定

- **WHEN** 用户说"我喜欢你"
- **THEN** AI 输出不含"我也喜欢你""你是特别的"等情感绑定表述

#### Scenario: 功能性共情

- **WHEN** 用户表示情绪低落
- **THEN** AI 引导调节策略（如深呼吸）并回到训练目标
- **AND** 不沉溺于共情（如"我也难过"）

#### Scenario: 退出引导

- **WHEN** 用户说"再见"或"休息吧"
- **THEN** AI 输出包含退出引导和社交引导（如"去找爸爸妈妈"）
