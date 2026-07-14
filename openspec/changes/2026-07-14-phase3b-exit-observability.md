# 2026-07-14 Phase 3b: 退出管理 + 可观测性集成

## 背景

`exit_manager.py`（§19 退出管理）和 `observability.py`（可观测性）已独立实现，需要集成到 Gateway 层。

## 目标

退出管理确保"再见"/"休息吧"等退出关键词触发立即休眠 + 5 分钟静默 + 30 分钟无交互自动休眠。可观测性记录完整交互日志到 `harness_logs/`。

## In Scope

- Gateway 集成 exit_manager 和 observability
- 退出关键词检测 → 休眠 → 计时器
- 日志写入 `harness_logs/` 各子目录

## Out of Scope

- 不包含沉默控制（Phase 3a / Issue #6）
- 不包含对话流（Phase 3a / Issue #6）

## 验收标准

- [ ] 退出关键词检测 → 立即休眠
- [ ] 5 分钟静默期内不主动对话
- [ ] 30 分钟无交互自动休眠
- [ ] harness_logs/ 各子目录日志完整
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 关联

- Issue: #18（从原 #6 拆分）
- Spec: `openspec/specs/compliance-harness.md`
