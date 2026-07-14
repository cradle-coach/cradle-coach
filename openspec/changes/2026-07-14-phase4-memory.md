# 2026-07-14 Phase 4: 记忆系统（LanceDB）

## 背景

CradleCoach 需要跨会话记忆能力以个性化训练体验。

## 目标

基于 LanceDB 建立三层记忆架构：会话级（内存）、短期级（30 天摘要 + 语义检索 top-5）、核心级（永久偏好 JSON）。Memory Service 通过 FastAPI 暴露四个端点，Gateway 在推理前调用检索上下文。

## In Scope

- LanceDB 表结构设计与 CRUD
- Memory Service API（/search /save /summarize /core）
- Gateway 推理前注入记忆上下文
- 所有记忆数据仅存本地

## Out of Scope

- PII 不入库（设计约束）
- 不外传数据到云端
- 不包含训练游戏数据持久化（Phase 5）

## 验收标准

- [ ] 四个 API 端点可运行
- [ ] LanceDB 语义检索 top-5 可用
- [ ] 核心级偏好持久化到 JSON
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 关联

- Issue: #7
- Spec: `openspec/specs/training-engine.md`
