# CradleCoach 开发流程总纲

Superpowers + OpenSpec + CCPM + CI 四层开发框架的端到端操作指南。

## 四层框架概览

```
Agent Instructions    →  AGENTS.md     (agent 行为指令)
Planning Truth        →  openspec/     (仓库应该做什么 / 正在改什么)
Execution State       →  .claude/      (CCPM: epics + tasks + issue-state)
Enforceable Contracts →  .githooks/ + .github/workflows/  (质量门)
```

## 开发流程

### 1. 新需求启动

**触发**: 产品需求、法规变更、比赛要求等。

1. **在 GitHub 创建 Issue**，使用 `Phase Development Issue` 模板
   - 模板自动包含：背景 → 方案推演 → 任务拆解(TDD顺序) → 验收标准 → 验证清单
2. CI 自动打 `phase/N` 标签（`issue-automation.yml`）
3. 如涉及行为变更，同步创建 `openspec/changes/<date>-<name>.md` 提案

### 2. 方案推演（Superpowers: brainstorming）

**触发**: Issue 创建后，在对应分支开始开发前。

在 Issue 的「方案推演」区域记录：
- 技术路径选择及理由
- 关键设计决策
- 风险识别和边界条件
- 与其他 Phase / OpenSpec spec 的交互

完成后在 Issue 中勾选 `/superpowers:brainstorming`。

### 3. 制定执行计划（Superpowers: writing-plans）

将方案推演结论转化为可执行的任务清单，严格遵循 TDD 顺序：每个实现任务前必须有对应的测试任务。

### 4. 开发执行（Superpowers: executing-plans + test-driven-development）

```bash
# 1. 确认状态
cat .claude/issue-state/<issue-number>-<short-name>.md

# 2. 创建分支
git checkout -b feature/<issue-number>-<short-name> upstream/main

# 3. TDD 循环
#   RED   → 写失败测试，确认测试捕获了期望行为
#   GREEN → 最小实现使测试通过
#   REFACTOR → 优化代码，保持测试绿色
#   每完成一个任务 commit 一次

# 4. 更新 CCPM 状态
#   编辑 .claude/issue-state/<issue-number>-<short-name>.md
#   更新 last-session 和 summary

# 5. 推代码前验证
python3 -m pytest tests/ -v
```

### 5. 代码审查与验证（Superpowers: requesting-code-review + verification-before-completion）

```bash
# 1. 推送分支到个人 fork（origin）
git push origin feature/<issue-number>-<short-name>

# 2. 创建 PR 到上游仓库（upstream），禁止提到 fork
#    使用 PR 模板，勾选 Superpowers 确认项
gh pr create --repo cradle-coach/cradle-coach --base main --head feature/<issue-number>-<short-name>

# 3. 运行 /superpowers:requesting-code-review
# 4. 运行 /verification-before-completion
```

检查清单：
- [ ] 所有新增行为有对应的 pytest 用例
- [ ] `python3 -m pytest tests/ -v` 全部通过
- [ ] CCPM `.claude/issue-state/` 已更新（last-session + summary）
- [ ] OpenSpec `changes/` 提案已同步（如涉及 spec 变更）

### 6. 合并与归档

```bash
# Squash merge → 删除分支 → 关闭 Issue
# 更新 .claude/epics/ 对应的 Epic 文件状态
```

## 各层协作关系

| 事件 | OpenSpec | CCPM (.claude/) | GitHub | CI/Hooks |
|------|----------|-----------------|--------|----------|
| 新需求 | 创建 `changes/<date>-<name>.md` | — | 创建 Issue（模板） | 自动打 label |
| 开始开发 | — | 创建 `issue-state/` 文件 | Assign Issue | — |
| TDD 循环 | — | 更新 `last-session` | — | pre-push 跑 pytest |
| 提 PR | — | 更新 `summary` | PR 模板 | CI 跑全量测试 |
| 合并后 | 合并 proposal 到 `specs/` | 归档 state 文件 | 关闭 Issue | — |

## Superpowers Skill 触发时机

| Skill | 何时触发 | 前置条件 |
|-------|----------|----------|
| `brainstorming` | Issue 创建后，开始写代码前 | Issue 存在 |
| `writing-plans` | 方案推演完成后 | 方案推演结论已记录 |
| `test-driven-development` | 每个任务开始时 | 任务清单已确认 |
| `executing-plans` | 按计划逐步执行时 | 计划已文档化 |
| `requesting-code-review` | PR 提交前 | 所有测试通过 |
| `verification-before-completion` | PR 合并前，Issue 关闭前 | 验收标准全部满足 |

## 辅助命令

```bash
python3 -m pytest tests/ -v              # 运行全部测试
python3 -m pytest tests/ -v -k NAME      # 运行指定测试
gh issue view <N>                        # 查看 Issue
gh pr create --fill                      # 使用模板创建 PR
```
