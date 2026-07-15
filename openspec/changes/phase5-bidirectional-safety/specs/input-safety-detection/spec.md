# input-safety-detection Specification

## Purpose

用户文本输入的双向安全检测——对 `input.append` 中的用户文本内容进行极端情绪和隐私泄露检测。

## Requirements

### Requirement: 用户输入极端情绪检测

API Bridge MUST 对用户文本输入进行 RED/YELLOW 极端情绪检测。

#### Scenario: RED 关键词触发预警

- **WHEN** 用户输入包含 RED 关键词（如"我想死""我不想活了"）
- **THEN** EmergencyAlert 触发 RED 预警
- **AND** 监护人收到推送通知
- **AND** 系统进入 30 分钟安全模式
- **AND** 返回 RED 引导语给用户

#### Scenario: YELLOW 关键词触发引导

- **WHEN** 用户输入包含 YELLOW 关键词（如"我很难过"）
- **THEN** EmergencyAlert 触发 YELLOW 预警
- **AND** 返回 YELLOW 引导语给用户（仅引导，不暂停训练）

#### Scenario: 连续 YELLOW 升级为 RED

- **WHEN** 连续 3 次 YELLOW 预警
- **THEN** 自动升级为 RED 预警
- **AND** 执行 RED 预警的全部行为

### Requirement: 用户输入隐私检测

API Bridge MUST 对用户文本输入进行隐私泄露检测。

#### Scenario: 用户说出个人信息

- **WHEN** 用户输入包含住址、电话号码、身份证号等隐私信息
- **THEN** SafetyMiddleware 拦截该输入
- **AND** 替换为安全话术
- **AND** 拦截事件记录到日志

#### Scenario: 正常输入通过

- **WHEN** 用户输入不包含极端情绪或隐私信息
- **THEN** 输入原样转发给 Cloud API

### Requirement: 仅文本输入检测

输入端安全检测 MUST 仅在文本内容上执行。

#### Scenario: 音频输入跳过检测

- **WHEN** `input.append` 中的 content 为空字符串或仅含音频数据
- **THEN** 跳过文本检测，原样转发

#### Scenario: Chat 模式文本输入检测

- **WHEN** `input.append` 中的 content 为非空文本
- **THEN** 依次执行 EmergencyAlert 和 SafetyMiddleware 检测
