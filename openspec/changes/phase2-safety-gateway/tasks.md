## 任务拆解（TDD 顺序）

1. **安全检测单元测试** → 验证 SafetyMiddleware.check() 对 7 类规则的检测正确性（已有 5 个测试）
2. **API Bridge 集成测试** → 通过 API Bridge 发送违规消息，验证返回安全话术
3. **安全护栏集成** → `api_to_worker()` 中注入 SafetyMiddleware 检测
4. **拦截日志验证** → 验证日志写入 `harness_logs/safety_intercepts/`
5. **端到端验证** → 确认正常对话不被误拦截

## 实现状态

- [x] 安全检测单元测试（已有 test_compliance_regression.py）
- [ ] API Bridge 集成测试
- [ ] 安全护栏集成
- [ ] 拦截日志验证
- [ ] 端到端验证
