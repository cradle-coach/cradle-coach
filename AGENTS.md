# AGENTS.md

## What is CradleCoach?

面向 ADHD 儿童的端侧 AI 认知训练设备——PC 端 Harness 原型。基于 MiniCPM-o 4.5 全模态模型和昇腾 NPU，在 MiniCPM-o-Demo（子模块 `minicpmo-demo/`）之上增加执行功能训练引擎和《暂行办法》（2026.7.15 施行）合规模块。

> 🏆 参加 MiniCPM × 昇腾挑战赛 应用创新赛道。

## Commands

```bash
python3 -m pytest tests/ -v          # 运行全部合规回归测试
python3 -m pytest tests/ -v -k NAME  # 运行指定测试
cd minicpmo-demo && docker compose up  # 启动 Demo
python3 mock_guardian_server.py --port 8666  # 启动家长端 Mock Server
```

## Agent Operating Flow

- **Session Start**: 读 `.claude/issue-state/` 下当前活跃 Issue 的状态文件，确认上次做到哪了。
- **Before Work**: 确认当前 Issue 已存在 → 创建或确认匹配的 `.claude/tasks/` 文件 → 初始化 `.claude/issue-state/` 文件。
- **Implementing**: 每个 Phase 开一个 `feature/#N-phase-name` branch。合规模块必须在 `tests/test_compliance_regression.py` 加测试。System Prompt 修改必须更新 `config/cradlecoach_system_prompt.yaml` 并跑测试。
- **Before Push**: `python3 -m pytest tests/ -v` 全部通过。Commit 格式 `type: description`。
- **Before PR**: 刷新 `.claude/issue-state/` 文件，确保 `last-session` 和 `summary` 是最新的。
- **After Merge**: 关闭 Issue，`.claude/issue-state/` 归档。从最新的 `upstream/main` 开下一个分支。

## Repository Areas

```text
gateway_modules/     — Harness 模块（safety/silence/exit/timer/identity/emergency/conversation/observability/harness_manager）
cradle_memory/       — LanceDB 记忆系统（Phase 4）
cradle_training/     — 训练游戏引擎（Phase 5）
config/              — System Prompt 配置
tests/               — 合规回归测试
minicpmo-demo/       — MiniCPM-o-Demo 子模块
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
7. Python 3.11+，类型标注，模块 docstring

## Gotchas

- MiniCPM-o-Demo 的 `/competition` 页面含 WebGL 渲染，Chrome Headless 抓取时需 `--disable-gpu --disable-software-rasterizer`
- 昇腾 HiDevLab 环境审核需 1-3 工作日，申请原因备注"参加面壁昇腾大赛"
- `minicpmo-demo/` 是 git submodule，clone 时需 `--recursive`
