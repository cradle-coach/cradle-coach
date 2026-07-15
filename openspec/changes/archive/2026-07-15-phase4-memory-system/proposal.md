## 背景

`cradle_memory/` 仅有占位 `__init__.py`。需实现基于 LanceDB 的三层记忆架构：会话级（内存）、短期级（30 天 LanceDB 语义检索）、核心级（本地 JSON）。

## 变更内容

- 实现 `cradle_memory/memory_service.py`：MemoryService 类
- 支持 add_turn、get_session_history、search_short_term、get_core、update_core
- 所有数据仅存本地

## Capabilities

### 新增能力
- `lance-memory-system`：三层记忆架构，会话上下文 + 语义检索 + 持久化偏好

## 影响范围

- `cradle_memory/memory_service.py`：新增
- `requirements.txt`：lancedb 依赖

## 验收标准

- [ ] 三层记忆均可读写
- [ ] LanceDB 语义检索可用
- [ ] 核心偏好持久化到 JSON
- [ ] `python3 -m pytest tests/ -v` 全部通过
