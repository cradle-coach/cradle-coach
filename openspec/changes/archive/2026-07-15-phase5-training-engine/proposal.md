## 背景

CradleCoach 产品设计中定义了四种执行功能训练游戏（反义词、倒序记忆、情绪猜谜、故事接龙），以对话嵌入形式运行，非独立课程。`cradle_training/` 目录仅含占位 `__init__.py`（API 签名定义），无实际实现。Phase 5 需实现完整训练游戏引擎，与已有 HarnessManager 集成。

关联 Issue：#8。关联 Spec：`openspec/specs/training-engine.md`。

## 变更内容

- 新增 4 个游戏引擎模块：`antonyms.py`、`reverse_memory.py`、`emotion_guess.py`、`story_chain.py`
- 新增 `training_manager.py`：训练会话编排、触发判断、难度自适应(1-5)、结束仪式
- 更新 `gateway_modules/harness_manager.py`：注册 `TrainingManager`
- 新增 `tests/test_training_engine.py`：41 个单元测试
- 更新 `tests/test_compliance_regression.py`：新增 `TestTrainingCompliance`（7 个测试）
- 所有反馈语言聚焦努力过程（"你很专注"），禁止情感绑定和结果导向表扬

## Capabilities

### 新增能力

- `training-engine`：纯规则引擎驱动的执行功能训练游戏

### 修改的能力

- `compliance-harness`：HarnessManager 新增 training 模块注册

## 影响范围

- `cradle_training/`：5 个新文件（antonyms, reverse_memory, emotion_guess, story_chain, training_manager）
- `gateway_modules/harness_manager.py`：新增 training 模块注册
- `tests/test_training_engine.py`：41 个测试
- `tests/test_compliance_regression.py`：7 个训练合规测试

## 验收标准

- [x] 4 种游戏引擎各可独立 evaluate（规则判断）
- [x] TrainingManager.should_trigger() 正确处理间隔和情绪状态
- [x] 难度自适应：连续正确升难度，连续错误降难度
- [x] 结束仪式含社交引导（"找爸爸妈妈分享"）
- [x] 所有反馈聚焦努力过程，不含情感绑定表述
- [x] HarnessManager.get_all_modules() 返回 training 模块
- [x] `python3 -m pytest tests/ -v` 92 passed
