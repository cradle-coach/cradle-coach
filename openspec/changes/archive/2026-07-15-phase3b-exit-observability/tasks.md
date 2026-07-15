## 任务拆解（TDD 顺序）

1. **ExitManager 集成测试** → 验证退出关键词检测、暂停区分、inactivity、post-exit silence
2. **Observability 集成测试** → 验证初始化和日志目录创建
3. **API Bridge 退出检测集成** → `worker_to_api()` 中检测退出关键词
4. **API Bridge 可观测性集成** → 初始化 Observability + 退出事件日志
5. **端到端验证** → 确认退出关键词触发完整退出流程

## 实现状态

- [x] ExitManager + Observability 独立模块（已有）
- [x] API Bridge 退出检测集成
- [x] API Bridge 可观测性集成
- [x] 端到端验证（44 tests pass）
