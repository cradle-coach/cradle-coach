## 背景

CradleCoach 合规版 System Prompt 已设计完成（`config/cradlecoach_system_prompt.yaml`），定义了 AI 教练人格：5 条核心原则、5 类禁止表述、训练流程话术、年龄段分层。当前 API Bridge 转发对话时使用 Cloud API 默认人格，未注入合规 System Prompt。

## 变更内容

- 在 API Bridge 启动时加载 `config/cradlecoach_system_prompt.yaml`
- 在 `session.init` 转发到 Cloud API 时注入合规 System Prompt（如客户端未提供）
- 不修改 MiniCPM-o-Demo 前端——System Prompt 注入在后端透明完成
- 新增合规检测测试：验证 AI 输出遵守核心原则和禁止表述

## Capabilities

### 新增能力
- `compliant-system-prompt-injection`：API Bridge 自动将 CradleCoach 合规 System Prompt 注入到 Cloud API 会话中

### 修改的能力
- `api-bridge-realtime-proxy`：session.init 转发逻辑增加 System Prompt 注入

## 影响范围

- `minicpmo-demo/api_bridge_server.py`：启动时加载 YAML，session.init 注入逻辑
- `config/cradlecoach_system_prompt.yaml`：合规 System Prompt 配置
- `tests/test_compliance_system_prompt.py`：新增 10 个合规检测单元测试

## 验收标准

- [ ] AI 输出不含情感绑定表述（"我喜欢你"等）
- [ ] 情绪低落时引导调节策略，不沉溺共情
- [ ] 训练完成有退出语 + 社交引导
- [ ] 询问 AI 身份时诚实回答
- [ ] `config/cradlecoach_system_prompt.yaml` 修改后测试自动验证
- [ ] `python3 -m pytest tests/ -v` 全部通过
