# Superpowers — CradleCoach 使用指南

Superpowers v6.1.1 已安装到本项目 `.claude/skills/superpowers/`（14 个 skill）。以下为各 skill 在 CradleCoach 开发流程中的触发时机和使用方式。

## 开发流程中使用的 Skill

| Skill | 触发时机 | 在 CradleCoach 中的作用 |
|-------|----------|------------------------|
| `brainstorming` | Phase 开始前、方案选型 | 推演技术路径，记录设计决策到 Issue 的「方案推演」区域 |
| `writing-plans` | 方案确认后、写代码前 | 将推演结论转化为 TDD 顺序的任务清单 |
| `test-driven-development` | 每个任务执行时 | RED → GREEN → REFACTOR 循环 |
| `executing-plans` | 按计划推进时 | 跟踪执行进度，确保不偏离方案 |
| `requesting-code-review` | PR 提交前 | 代码审查，检查合规约束和测试覆盖 |
| `receiving-code-review` | 收到 review 反馈后 | 系统性地处理 review 意见 |
| `verification-before-completion` | PR 合并前 / Issue 关闭前 | 最终门禁：验收标准全部满足、无遗漏 |
| `subagent-driven-development` | 复杂任务需要并行执行时 | 多 agent 协作，独立验证 |
| `systematic-debugging` | 遇到 bug 时 | 根因追踪而非打补丁 |
| `finishing-a-development-branch` | 分支工作完成时 | 清理、最终 commit、准备合并 |
| `dispatching-parallel-agents` | 大规模探索/搜索时 | 并行 agent 分工 |
| `using-git-worktrees` | 需要同时进行多个独立任务时 | 隔离工作区 |
| `using-superpowers` | 会话开始时自动加载 | 引导使用正确的 skill |
| `writing-skills` | 需要创建项目专属 skill 时 | 按需扩展 |

## 关键触发点

```
新 Phase Issue 创建
  → /superpowers:brainstorming   (方案推演)
  → /superpowers:writing-plans   (制定计划)
  → /superpowers:test-driven-development  (TDD 循环)
  → /superpowers:executing-plans (按计划执行)
  → /superpowers:requesting-code-review   (代码审查)
  → /verification-before-completion       (最终门禁)
```

## CradleCoach 特有约束

使用 Superpowers skill 时，必须同时遵守本项目特有规范（详见 `AGENTS.md`）：

1. 合规模块 docstring 引用《暂行办法》条款号
2. 情感交互使用功能性共情框架
3. System Prompt 修改后跑 `python3 -m pytest tests/test_compliance_regression.py -v`
4. 所有 AI 生成 commit 加 `Co-Authored-By: Claude <noreply@anthropic.com>`

## 参考

- 完整流程：`docs/engineering/development-workflow.md`
- 仓库规约：`docs/engineering/repository-governance.md`
- 行为规范：`openspec/specs/`
