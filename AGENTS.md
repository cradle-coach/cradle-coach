# AGENTS.md

## What is CradleCoach?

面向 ADHD 儿童的端侧 AI 认知训练设备——PC 端 Harness 原型。基于 MiniCPM-o 4.5 全模态模型（Phase 0-5 通过 OpenBMB 云端 API 推理），在 MiniCPM-o-Demo（`minicpmo-demo/`，内嵌源码）之上增加执行功能训练引擎和《暂行办法》（2026.7.15 施行）合规模块。

> 🏆 参加 MiniCPM × 昇腾挑战赛 应用创新赛道。

## Commands

```bash
python3 -m pytest tests/ -v          # 运行全部合规回归测试
python3 -m pytest tests/ -v -k NAME  # 运行指定测试
CRADLECOACH_API_KEY=sk-xxx python minicpmo-demo/api_bridge_server.py --port 22400 --api-mode chat  # API Bridge 模式
cd minicpmo-demo && docker compose up  # 本地 PyTorch 模式
python3 mock_guardian_server.py --port 8666  # 启动家长端 Mock Server
```

## Agent Operating Flow

每个 Phase 的标准流程及各阶段必须执行的 Superpowers skill：

| 阶段 | Skill | 操作 |
|------|-------|------|
| **Session Start** | — | 读 `.claude/issue-state/` 下当前活跃 Issue 的状态文件，确认上次做到哪了 |
| **方案推演** | `brainstorming` | Issue 创建后，在「方案推演」区域记录技术路径、设计决策、风险。详见 `docs/engineering/development-workflow.md` |
| **制定计划** | `writing-plans` | 将方案转化为 TDD 顺序的任务清单。如涉及行为变更，同步创建 `openspec/changes/<date>-<name>.md` 提案 |
| **开发执行** | `test-driven-development` | RED → GREEN → REFACTOR 循环。合规模块必须在 `tests/test_compliance_regression.py` 加测试。System Prompt 修改必须更新 `config/cradlecoach_system_prompt.yaml` 并跑测试 |
| **代码审查** | `requesting-code-review` | 检查合规约束、测试覆盖、Conventions 遵守情况 |
| **Before Push** | — | `python3 -m pytest tests/ -v` 全部通过。Commit 格式 `type: description` |
| **Before PR** | `verification-before-completion` | 最终门禁：验收标准 + pytest 全绿 + `.claude/issue-state/` 状态更新 |
| **After Merge** | — | 关闭 Issue，`.claude/issue-state/` 归档，更新 `.claude/epics/` Epic 状态。从最新的 `upstream/main` 开下一个分支 |

## Superpowers Integration

本项目已安装 Superpowers v6.1.1（`.claude/skills/superpowers/`，14 个 skill）。详细触发时机和 CradleCoach 特有限制见 `.claude/SUPERPOWERS_AGENTS.md`。

**关键规则**：
- 每个 Phase 必须依序经过 brainstorming → writing-plans → test-driven-development → verification-before-completion
- `/verification-before-completion` 是合并前硬门禁，不得跳过
- Issue 模板：使用 `.github/ISSUE_TEMPLATE/phase-issue.md`（Superpowers 结构预填充）
- PR 模板：使用 `.github/PULL_REQUEST_TEMPLATE.md`（Superpowers 确认项 + 验证清单）
- **PR 目标**：必须提到上游 `cradle-coach/cradle-coach`（`--repo cradle-coach/cradle-coach`），禁止提到个人 fork
- **Dual-remote**：`origin` = 个人 fork（用于 push 分支），`upstream` = 上游仓库（用于拉取 main 和创建 PR）

## Repository Areas

```text
gateway_modules/     — Harness 模块（safety/silence/exit/timer/identity/emergency/conversation/observability/harness_manager）
cradle_memory/       — LanceDB 记忆系统（Phase 4）
cradle_training/     — 训练游戏引擎（Phase 5）
config/              — System Prompt 配置
tests/               — 合规回归测试
minicpmo-demo/       — MiniCPM-o-Demo 内嵌源码（含 api_bridge_server.py）
openspec/specs/      — 行为规范（该做什么）
openspec/changes/    — 变更提案（正在改什么）
.claude/             — CCPM 项目状态（epics/tasks/issue-state）
.githooks/           — Git 质量门
.github/workflows/   — CI/CD
docs/                — 设计文档和开发规约
```

## Conventions

1. 所有合规模块必须在 docstring 中引用《暂行办法》条款号
2. 情感交互永远使用功能性共情（识别→调节→回到目标），禁止情感绑定表述
3. System Prompt 修改后必须跑 `python3 -m pytest tests/test_compliance_regression.py -v`
4. Commit 格式：`type: description`（feat/fix/chore/docs/test），所有 AI 生成的 commit 加 `Co-Authored-By: Claude <noreply@anthropic.com>`
5. 一个 Phase = 一个 Issue = 一个 branch = 一个 PR，squash merge 到 main
6. 禁止直推 main
7. **严禁串分支**：不得在 A Issue 的 branch 上 commit B Issue 的改动。每个 Issue 独占一个 branch。发现串分支立即拆分
8. Python 3.11+，类型标注，模块 docstring
9. **PR 完成时检查连带更新**：详见 `docs/engineering/repository-governance.md` 中的"PR 完成时的连带更新清单"——提案状态、PR 描述、README、Epic、OpenSpec 归档必须在合并前后更新

## Gotchas

- MiniCPM-o-Demo 的 `/competition` 页面含 WebGL 渲染，Chrome Headless 抓取时需 `--disable-gpu --disable-software-rasterizer`
- 昇腾 HiDevLab 环境审核需 1-3 工作日，申请原因备注"参加面壁昇腾大赛"
- `openspec/` 下为规划真相文件，变更提案完成后需同步 specs/
