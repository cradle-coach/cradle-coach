## 架构

```
API Bridge 消息管线
     │
     ├── worker_to_api() —— 用户输入方向
     │       │
     │       ├── ExitManager.check_exit_keyword() — 检测退出关键词
     │       │       └── 匹配 → 发送退出语 + response.done + session.closed
     │       ├── ExitManager.mark_activity() — 更新活动时间戳
     │       └── ConversationFlow.on_user_response() — 更新对话状态
     │
     └── api_to_worker() —— AI 输出方向
             │
             ├── ExitManager.mark_activity() — 更新活动时间戳
             └── 安全检测 + 对话流提示注入
```

## 退出检测策略

- **关键词匹配**：用户输入包含退出关键词 → 立即退出
- **暂停关键词**：不会触发退出，区别于退出关键词
- **退出语含社交引导**：退出时引导孩子"找爸爸妈妈"
- **退出后静默**：退出后 5 分钟内不主动发起对话（由 `_exit_manager.mark_exited()` 标记）

## 可观测性策略

- **初始化时创建日志目录**：`harness_logs/safety_intercepts/`、`silence_control/`、`conversation_flow/`、`sessions/`
- **退出事件日志**：检测到退出关键词时写入 `sessions/` 日志

## 设计决策

1. **退出检测在用户输入方向**：用户说"再见"时立即响应，不等 AI 回复
2. **不覆盖 System Prompt 实现的退出引导**：退出关键词检测是硬拦截，System Prompt 提供的退出引导是软引导——两者互补
