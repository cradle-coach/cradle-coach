# Issue #7: Phase 4 — 记忆系统（LanceDB）

status: pending
branch: feature/7-phase4-memory
last-session: 2026-07-14
summary: |
  基于 LanceDB 的三层记忆架构：会话级（内存）、短期级（30 天摘要语义检索）、核心级（永久偏好 JSON）。
  Memory Service API（FastAPI 四个端点）→ Gateway 推理前注入记忆上下文。
  关联 OpenSpec: openspec/specs/training-engine.md
