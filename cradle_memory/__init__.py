"""
CradleCoach 记忆系统 (cradle_memory)

基于 LanceDB 的三层记忆架构：
  - 会话级：当前对话上下文（内存）
  - 短期级：最近 30 天摘要（LanceDB 语义检索）
  - 核心级：永久偏好（本地 JSON）

API:
  POST /memory/search    { query, top_k } → [{text, score, timestamp}]
  POST /memory/save      { session_id, turn, user_text, ai_response, emotion }
  POST /memory/summarize { session_id } → 自动生成每日摘要
  GET  /memory/core      → { user_name, preferences, key_events, patterns }

Phase 4 实现。
"""
