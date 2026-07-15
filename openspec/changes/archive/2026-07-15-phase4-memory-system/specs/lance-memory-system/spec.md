# Spec: LanceDB 三层记忆

MemoryService MUST 提供会话、短期、核心三层记忆，数据仅存本地。

## ADDED Requirements

### Requirement: 会话级记忆

MemoryService MUST 在内存中维护当前会话的完整对话历史。

#### Scenario: 添加轮次

- **WHEN** `add_turn(session_id, user_text, ai_response, emotion)`
- **THEN** `get_session_history(session_id)` 返回含该轮的历史

#### Scenario: 多轮保持顺序

- **WHEN** 同一会话添加多轮
- **THEN** 按添加顺序返回

### Requirement: 短期级记忆

MemoryService MUST 存入 LanceDB 并支持语义检索。

#### Scenario: 语义搜索

- **WHEN** `search_short_term(query, top_k)`
- **THEN** 返回不超过 top_k 条记录

#### Scenario: DB 不可用不崩溃

- **WHEN** `db=None`
- **THEN** `search_short_term` 返回 `[]`，不抛异常

### Requirement: 核心级记忆

MemoryService MUST 持久化偏好到本地 JSON。

#### Scenario: 读写偏好

- **WHEN** `update_core("preferences", {...})`
- **THEN** `get_core()` 返回更新后值

#### Scenario: 首次返回默认值

- **WHEN** 无已有 JSON 文件
- **THEN** `get_core()` 返回 `{preferences, key_events, patterns}`
