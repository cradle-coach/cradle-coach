# Issue #4: Phase 1 — 合规人格配置（System Prompt 注入）

status: completed
branch: feature/4-phase1-system-prompt
last-session: 2026-07-15
summary: |
  API Bridge 启动时加载 config/cradlecoach_system_prompt.yaml。
  在 session.init 和首条 input.append 中注入合规 System Prompt。
  10 个单元测试全部通过。PR #27 已合并。
