## 任务拆解（TDD 顺序）

1. **编写输入端安全检测测试** → `test_input_safety.py`：RED 检测、YELLOW 引导、隐私拦截、正常通过、音频跳过（test 先行 commit）
2. **EmergencyAlert 集成** → `api_bridge_server.py`：新增 `_check_emergency()` + 懒加载初始化
3. **SafetyMiddleware 输入端集成** → `api_bridge_server.py`：新增 `_check_input_safety()`
4. **RED/YELLOW 引导语注入** → 检测结果影响后续 AI 输出
5. **合规回归测试** → `test_compliance_regression.py` 新增输入端合规测试
6. **全量回归验证** → `python3 -m pytest tests/ -v` 全部通过

## 实现状态

- [x] 输入端安全检测测试编写（15 tests + 4 compliance）
- [x] EmergencyAlert 集成（_check_emergency + _init_emergency_alert）
- [x] SafetyMiddleware 输入端集成（USER_PRIVACY_DISCLOSURE_PATTERNS + _check_input_safety）
- [x] RED/YELLOW 引导语注入（_pending_emergency_guidance → api_to_worker）
- [x] 合规回归测试（TestInputSafetyCompliance: 4 tests）
- [x] 全量回归验证（122 passed）
