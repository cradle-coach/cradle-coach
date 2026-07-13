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

- PR 描述引用 Issue：`Closes #N`
- PR 标题与 Issue 标题一致或概括其核心变更
- Solo 模式：自己 review 后合并

## 质量门

1. **pre-push**：`python3 -m pytest tests/ -v` 全部通过
2. **CI**：PR 触发 GitHub Actions 全量测试
3. **代码审查**：Phase 完成后使用 `/code-review` skill

## Agent 工作流

每个 Phase 的标准流程：

1. 确认 GitHub Issue 已存在
2. 创建 `.claude/issue-state/<issue-number>-<short-name>.md`
3. `git checkout -b feature/<issue-number>-<short-name> upstream/main`
4. 开发 → 测试 → commit
5. `git push origin feature/<issue-number>-<short-name>`
6. 创建 PR 到 `upstream/main`
7. Review → squash merge → 关闭 Issue
8. 更新 Epic 状态

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
