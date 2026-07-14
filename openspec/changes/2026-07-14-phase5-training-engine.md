# 2026-07-14 Phase 5: 训练游戏引擎

## 背景

执行功能训练（反义词/倒序记忆/情绪猜谜/故事接龙）通过纯规则引擎 + REST API 封装，嵌入对话流中。

## 目标

实现 Training Service API（should_trigger / start / evaluate），Gateway 在对话中触发训练游戏。难度基于正确率和响应时间自适应。每次训练结束有明确结束仪式 + 社交引导。

## In Scope

- 四个训练游戏的规则引擎
- Training Service REST API
- 难度自适应算法
- Gateway 对话中嵌入训练触发

## Out of Scope

- 不包含训练数据长期存储（Phase 4 记忆系统可复用）
- 不包含游戏 UI（以语音对话形式交互）

## 验收标准

- [ ] 4 个训练游戏全部可交互
- [ ] 难度自适应生效
- [ ] 训练完成主动退出引导
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 关联

- Issue: #8
- Spec: `openspec/specs/training-engine.md`
