## 任务拆解（TDD 顺序）

1. **SilenceController 单元测试** → 验证沉默检测和状态转换（已有模块测试）
2. **ConversationFlow 单元测试** → 验证追问检测和难度调整（已有模块测试）
3. **API Bridge 沉默检测集成** → 在消息循环中嵌入时间戳追踪和超时检测
4. **API Bridge 对话流集成** → 注入追问限制和难度提示
5. **端到端验证** → 模拟沉默超时和连续追问场景

## 实现状态

- [x] SilenceController + ConversationFlow 独立模块（已有）
- [ ] API Bridge 沉默检测集成
- [ ] API Bridge 对话流集成
- [ ] 端到端验证
