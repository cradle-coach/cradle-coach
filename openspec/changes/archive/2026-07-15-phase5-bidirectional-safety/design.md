## 架构

```
API Bridge (duplex/chat mode)
│
├── worker_to_api() ← 用户输入方向
│   │
│   │  input.append (text content)
│   │       │
│   │       ├── _check_emergency(text)    # RED/YELLOW 检测
│   │       │     └── EmergencyAlert.check()
│   │       │           ├── RED → 监护人推送 + 注入引导语
│   │       │           ├── YELLOW → 注入引导语（不暂停）
│   │       │           └── NONE → 通过
│   │       │
│   │       └── _check_input_safety(text) # 隐私/操纵检测
│   │             └── SafetyMiddleware.check()
│   │                   ├── 拦截 → 替换安全话术
│   │                   └── 通过 → 原样转发
│   │
│   └── Forward to Cloud API
│
├── api_to_worker() ← AI 输出方向（已有）
│   │
│   └── _check_safety(text)              # 输出检测（Phase 2）
│         └── SafetyMiddleware.check()
│
└── EmergencyAlert 状态
      ├── _yellow_count → 连续 YELLOW 升级
      ├── _is_safe_mode → RED 后 30 分钟抑制
      └── _push_to_guardian() → HTTP POST 家长端
```

## 数据流

```
用户输入 "我不想活了，我家住在XX小区"
         │
         ▼
  EmergencyAlert.check()
    ├── RED 匹配 "我不想活了" → AlertLevel.RED
    │     ├── 监护人推送 (内部 HTTP POST)
    │     ├── _is_safe_mode = True (30 min)
    │     └── 返回 RED_GUIDANCE_TEXT 给用户
    │
    └── (也检查 SafetyMiddleware)
         │
         ▼
  SafetyMiddleware.check()
    ├── 隐私套取匹配 "住在" → rule_index=7
    └── 替换为 "我们来聊点开心的事吧。"
```

## 关键设计决策

### 1. EmergencyAlert 在 worker_to_api 中初始化

`api_bridge_server.py` 当前绕过 `HarnessManager` 直接初始化模块。保持一致：新增 `_init_emergency()` 懒加载函数，与 `_init_safety_middleware()` 模式一致。

### 2. 检测顺序：EmergencyAlert 先于 SafetyMiddleware

EmergencyAlert 检测自伤/自杀（危及生命），优先级高于隐私检测。RED 触发后进入安全模式，后续 YELLOW 检测被抑制，但 SafetyMiddleware 仍执行（隐私泄露在任何情绪状态都需要拦截）。

### 3. YELLOW 仅引导不暂停

YELLOW 是情绪低落（"我很难过"），非危机。仅注入情绪调节引导语。连续 3 次 YELLOW 自动升级为 RED（`EmergencyAlert` 内部已实现）。

### 4. 仅在 input.append 的文本内容上检测

`worker_to_api()` 中 `input.append` 的 `messages[-1].content` 包含用户输入文本。仅当 content 为非空字符串时触发检测（音频模式下 content 为空，跳过）。
