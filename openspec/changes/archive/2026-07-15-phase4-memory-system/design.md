## 架构

```
MemoryService
  ├── _sessions: Dict[str, List]    # 会话级（内存 dict）
  ├── _db: LanceDB Connection       # 短期级（LanceDB 表）
  └── _core_path → core_memory.json # 核心级（本地 JSON）
```

## 三层记忆

- **会话级**：`defaultdict(list)`，每轮 `{user, ai, emotion, ts}`，会话结束可丢弃
- **短期级**：LanceDB `short_term_memory` 表，30 天摘要，支持语义检索 top-k
- **核心级**：本地 JSON，`{preferences, key_events, patterns}`，跨会话持久化

## 设计决策

1. **LanceDB 可选降级**：`db=None` 时仅使用会话级 + 核心级
2. **向量嵌入占位**：当前使用随机向量（Phase 5 实现真正嵌入）
3. **PII 不入库**：所有数据仅存本地
