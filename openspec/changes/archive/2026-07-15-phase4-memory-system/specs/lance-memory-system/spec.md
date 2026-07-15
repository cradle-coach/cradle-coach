# Spec: LanceDB 三层记忆
MemoryService MUST 提供三层记忆，数据仅存本地。

## ADDED Requirements
### Requirement: 会话级记忆
MemoryService MUST 在内存维护会话历史。
#### Scenario: 添加轮次
- WHEN add_turn(session_id, user, ai, emotion)
- THEN get_session_history(session_id) 返回含该轮历史

### Requirement: 短期级记忆
MemoryService MUST 存入LanceDB并支持检索。
#### Scenario: DB不可用不崩溃
- WHEN db=None
- THEN search_short_term返回[]，不抛异常

### Requirement: 核心级记忆
MemoryService MUST 持久化偏好到JSON。
#### Scenario: 读写偏好
- WHEN update_core("preferences",{...})
- THEN get_core()返回更新后值
