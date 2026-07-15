# Spec: API Bridge Realtime 代理（修改）

## MODIFIED Requirements

### Requirement: 消息双向转发

API Bridge MUST 在转发 `response.output.delta`（kind=text）到客户端前进行安全检测，拦截违规内容。

#### Scenario: 安全审核后的文本转发

- **WHEN** Cloud API 发送 `response.output.delta {kind: "text", text: "..."}`
- **THEN** API Bridge 通过 SafetyMiddleware 检测内容
- **AND** 通过检测后原样转发给客户端
- **AND** 未通过检测时替换为安全话术后转发
