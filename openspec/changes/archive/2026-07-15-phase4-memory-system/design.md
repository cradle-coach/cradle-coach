## 架构
MemoryService: 会话级(内存dict) + 短期级(LanceDB表) + 核心级(本地JSON)

## 三层记忆
- 会话级: defaultdict(list), {user,ai,emotion,ts}, 会话结束可丢弃
- 短期级: LanceDB short_term_memory表, 30天, 语义检索top-k
- 核心级: 本地JSON, {preferences,key_events,patterns}, 跨会话持久化

## 设计决策
1. LanceDB可选降级: db=None时仅用会话+核心级
2. 向量嵌入占位: 随机向量(Phase 5实现真正嵌入)
3. PII不入库: 所有数据仅存本地
