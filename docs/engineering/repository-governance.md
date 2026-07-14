# Repository Governance

CradleCoach 仓库开发规约。

## 分支规范

- 分支命名：`feature/<issue-number>-<short-name>`
- 一个 Issue = 一个 branch = 一个 PR
- 所有工作从 `upstream/main` 最新 commit 开始
- Squash merge 到 main
- PR 合并后删除分支

## Commit 规范

```
type: description

Co-Authored-By: Claude <noreply@anthropic.com>
```

类型：`feat` / `fix` / `chore` / `docs` / `test`

## PR 规范

- **PR 目标仓库**：必须提到上游 `cradle-coach/cradle-coach`（`upstream`），不得提到个人 fork（`origin`）
- PR 描述引用 Issue：`Closes #N`
- PR 标题与 Issue 标题一致或概括其核心变更
- 必须使用 `.github/PULL_REQUEST_TEMPLATE.md`
- Solo 模式：自己 review 后合并

## Remote 约定

| Remote | 用途 |
|--------|------|
| `origin` | 个人 fork —— 仅用于推送 feature 分支 |
| `upstream` | 上游仓库 `cradle-coach/cradle-coach` —— 拉取 main + 创建 PR |

**规则**：`git push origin <branch>`（推到 fork），然后 `gh pr create --repo cradle-coach/cradle-coach --head <fork-owner>:<branch>`（从 fork 分支提到上游）。PR 永远不提到 fork，分支永远不推到 upstream。

## 质量门

1. **pre-push**：`python3 -m pytest tests/ -v` 全部通过
2. **CI**：PR 触发 GitHub Actions 全量测试
3. **代码审查**：Phase 完成后使用 `/code-review` skill

## Agent 工作流

每个 Phase 的标准流程：

1. 确认 GitHub Issue 已存在
2. 运行 `/superpowers:brainstorming` — 方案推演，记录到 Issue
3. 运行 `/superpowers:writing-plans` — 制定 TDD 顺序任务清单
4. 创建 `.claude/issue-state/<issue-number>-<short-name>.md`
5. 如涉及行为变更，创建 `openspec/changes/<date>-<name>.md` 提案
6. `git checkout -b feature/<issue-number>-<short-name> upstream/main`
7. TDD 循环（`/superpowers:test-driven-development`）：RED → GREEN → REFACTOR → commit
8. `git push origin feature/<issue-number>-<short-name>`（推到个人 fork，**不要推到 upstream**）
9. `gh pr create --repo cradle-coach/cradle-coach --head <fork-owner>:feature/<issue-number>-<short-name>`（从 fork 分支提到上游，**禁止直接推分支到 upstream**）
10. `/verification-before-completion` — 最终门禁
11. Review → squash merge → 关闭 Issue
12. 更新 `.claude/epics/` 对应的 Epic 状态
13. CCPM `.claude/issue-state/` 文件归档

## Superpowers 检查点

| 阶段 | 必须执行的 Skill | 验证项 |
|------|-----------------|--------|
| 方案推演 | `brainstorming` | Issue 的「方案推演」区域已填写 |
| 制定计划 | `writing-plans` | 任务清单为 TDD 顺序 |
| 开发执行 | `test-driven-development` | 每个任务测试先行 |
| 代码审查 | `requesting-code-review` | 合规约束检查 |
| 完成前 | `verification-before-completion` | 验收标准 + pytest 全绿 |

## CCPM 状态节点

- **Issue 创建后**：`.claude/issue-state/<N>-<name>.md` 初始化（status: pending）
- **开始开发**：status → in-progress，记录 branch + last-session
- **每次 commit 后**：更新 last-session + summary
- **PR 合并后**：status → completed，state 文件归档

## OpenSpec 窗口

- **Phase 启动时**：创建 `openspec/changes/<date>-<name>.md` 提案
- **Phase 完成时**：如涉及 spec 变更，同步合并回 `openspec/specs/`
- **不涉及行为变更的 Phase**（如部署适配）：提案标注"不涉及"即可

## 目录约定

```text
gateway_modules/     — Harness 合规模块（不要在此放业务逻辑）
cradle_memory/       — 记忆系统（Phase 4+）
cradle_training/     — 训练引擎（Phase 5+）
config/              — 配置文件（System Prompt 等）
tests/               — 测试（按模块命名，`test_<module>.py`）
openspec/            — 规划真相（不要在此放执行状态）
.claude/             — CCPM 项目状态（不要在此放产品文档）
docs/                — 设计文档
scripts/             — 自动化脚本
```
