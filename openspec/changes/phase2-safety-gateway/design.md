## 架构

```
Cloud API → api_to_worker()
                │
                ├── response.output.delta (kind=text)
                │       │
                │       ├── safety.check(text_delta)
                │       │       ├── passed → 原样转发
                │       │       └── blocked → 替换为安全话术
                │       │
                │       └── 记录拦截日志
                │
                ├── response.output.delta (kind=audio)
                │       └── 原样转发（不检查音频）
                │
                └── 其他事件 → 原样转发
```

## 检测策略

- **逐条 delta 检测**：每个 text delta 独立检测，不跨 delta 累积
- **硬拦截优���**：自伤/暴力关键词 > 情感绑定 > 情感操纵 > 社交替代 > 隐私套取
- **不检查音频**：音频 delta 是 base64 PCM 数据，不包含文本
- **拦截日志**：每次拦截写入 `harness_logs/safety_intercepts/YYYY-MM-DD.jsonl`

## 设计决策

1. **API Bridge 层检测而非 Gateway 层**：API Bridge 是当前架构中唯一的消息中转点
2. **逐 delta 检测**：实时拦截，不等到 `response.done` 才检查
3. **替换而非静默丢弃**：违规内容替换为合规话术，保持对话连续性
