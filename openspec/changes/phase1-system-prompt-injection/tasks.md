## 任务拆解（TDD 顺序）

1. **合规检测测试** → 写测试：通过 API Bridge 发起对话，验证 AI 输出不含情感绑定表述
2. **合规人格验证测试** → 写测试：输入"我很难过"，断言 AI 引导调节策略而非沉溺共情
3. **退出引导测试** → 写测试：输入"再见"，断言 AI 有退出语 + 社交引导
4. **System Prompt 加载** → API Bridge 启动时加载 YAML，CLI 参数 `--system-prompt`
5. **session.init 注入** → 如客户端未提供 system_prompt，自动注入合规版本
6. **端到端验证** → Chat 模式对话确认 AI 输出合规

## 实现状态

- [x] 合规检测测试（10 个单元测试）
- [x] 合规人格验证测试（System Prompt 内容断言）
- [x] 退出引导测试（"再见"→社交引导）
- [x] System Prompt 加载（`--system-prompt` CLI 参数）
- [x] session.init 注入 + chat 模式 system role message 注入
- [x] 端到端验证（Chat 模式合规人格确认）
