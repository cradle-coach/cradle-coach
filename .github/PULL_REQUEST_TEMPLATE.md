## 关联 Issue

Closes #

## 变更摘要

<!-- 简述这个 PR 做了什么变更。 -->

## Superpowers 流程确认

<!-- 勾选本次开发中使用的 Superpowers skill -->

- [ ] `/superpowers:brainstorming` — 方案推演已完成
- [ ] `/superpowers:test-driven-development` — TDD 循环已执行
- [ ] `/superpowers:executing-plans` — 按计划执行
- [ ] `/superpowers:requesting-code-review` — 代码审查已请求

## 验证清单

- [ ] `python3 -m pytest tests/ -v` 全部通过
- [ ] 新行为有测试覆盖
- [ ] `/verification-before-completion` 通过
- [ ] CCPM `.claude/issue-state/` 已更新
- [ ] 如有 OpenSpec 影响，`openspec/changes/` 提案已同步
- [ ] PR 描述不含开发环境 IP/域名
- [ ] 未串分支（本 PR 仅含本 Issue 的 commit）

## 合并后检查清单

<!-- PR 合并后需执行，完成后在对应 Issue 中确认 -->

- [ ] OpenSpec 提案 `tasks.md` 实现状态已更新
- [ ] `README.md` 已检查是否需要更新
- [ ] `.claude/epics/` 已更新
- [ ] `openspec archive <change-name>` 已执行
- [ ] Issue 已关闭

## 测试结果

<!-- 粘贴 `python3 -m pytest tests/ -v` 输出摘要 -->

```

```
