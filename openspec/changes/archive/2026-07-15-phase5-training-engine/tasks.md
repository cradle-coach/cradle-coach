## 任务拆解（TDD 顺序）

1. **训练引擎测试编写** → 41 个测试覆盖 4 游戏 + TrainingManager + Harness 集成（test 先行 commit: `e13b58d`）
2. **游戏引擎实现** → antonyms.py, reverse_memory.py, emotion_guess.py, story_chain.py（commit: `c43dbb1`）
3. **训练管理器实现** → training_manager.py：触发判断、难度自适应、会话管理、结束仪式
4. **HarnessManager 集成** → harness_manager.py 新增 training 模块注册
5. **合规回归测试** → test_compliance_regression.py 新增 TestTrainingCompliance（7 测试）
6. **全量回归验证** → `python3 -m pytest tests/ -v` 全部通过

## 实现状态

- [x] 训练引擎测试编写（41 tests）
- [x] 游戏引擎实现（4 个游戏模块）
- [x] 训练管理器实现（编排 + 难度自适应）
- [x] HarnessManager 集成
- [x] 合规回归测试（7 tests）
- [x] 全量回归验证（92 passed）
