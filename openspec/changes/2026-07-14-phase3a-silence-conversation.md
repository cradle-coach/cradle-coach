# 2026-07-14 Phase 3a: 沉默控制 + 对话流集成

## 背景

`silence_controller.py`（§10 沉默控制）和 `conversation_flow.py`（对话流管理）已独立实现，需要集成到 Gateway 层。

## 目标

通过 HarnessManager 将两个模块注册到 Gateway 生命周期。沉默控制管理对话节奏（3-5s 窗口 + barge-in），对话流管理交互轮次（追问计数 + 难度自适应 + 情绪降级）。

## In Scope

- Gateway 集成 silence_controller 和 conversation_flow
- 沉默超时后引导回训练目标
- barge-in 立即停止当前输出

## Out of Scope

- 不包含退出管理（Phase 3b / Issue #18）
- 不包含可观测性（Phase 3b / Issue #18）

## 验收标准

- [ ] 沉默 3-5s 后引导回训练目标
- [ ] barge-in 立即停止当前输出
- [ ] 追问计数 + 难度自适应生效
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 关联

- Issue: #6（拆分后）
- Spec: `openspec/specs/compliance-harness.md`
