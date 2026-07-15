## 任务拆解（TDD 顺序）

1. **会话级记忆测试** → add_turn + get_session_history 验证
2. **短期级记忆测试** → LanceDB save + search 验证
3. **核心级记忆测试** → JSON 读写 + 默认值验证
4. **集成测试** → 三层联调验证
5. **MemoryService 实现** → 所有方法实现

## 实现状态

- [x] 会话级记忆（2 tests）
- [x] 短期级记忆（2 tests）
- [x] 核心级记忆（2 tests）
- [x] 集成测试（1 test）
- [x] 7 个测试全部通过
