# exit-and-observability Specification

## Purpose
TBD - created by archiving change phase3b-exit-observability. Update Purpose after archive.
## Requirements
### Requirement: 退出关键词检测

API Bridge MUST 在用户输入中检测退出关键词并立即执行合规退出。

#### Scenario: 退出关键词触发立即退出

- **WHEN** 用户输入包含"再见""拜拜""不练了""休息吧"等退出关键词
- **THEN** API Bridge 发送合规退出语（含社交引导）
- **AND** 发送 response.done 和 session.closed 关闭会话

#### Scenario: 暂停关键词不触发退出

- **WHEN** 用户输入包含"等一下""暂停"等暂停关键词
- **THEN** 不触发退出流程

#### Scenario: 正常文本不触发退出

- **WHEN** 用户输入不含退出或暂停关键词
- **THEN** 正常转发到 Cloud API

### Requirement: 可观测性初始化

API Bridge MUST 在启动时初始化 Observability 并创建日志目录。

#### Scenario: 日志目录创建

- **WHEN** API Bridge 启动
- **THEN** `harness_logs/` 下 `safety_intercepts/`、`silence_control/`、`conversation_flow/`、`sessions/` 四个子目录被创建

