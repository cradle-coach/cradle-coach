## 架构

```
浏览器 → Caddy（静态文件 + WS 代理）→ API Bridge → Cloud API
                                           ↓
                                    /v1/realtime* → proxy_session()
                                    /ws/half_duplex/* → proxy_half_duplex()
```

### 动态 Mode 路由

客户端连接 `wss://<host>/v1/realtime?mode=<mode>`。API Bridge 从 URL 查询字符串提取 `mode` 参数。未指定时回退到环境变量 `CRADLECOACH_API_MODE`。

Mode 映射：
- `?mode=chat` → Cloud API `?mode=chat`（turn_based）
- `?mode=audio` → Cloud API `?mode=audio`（full_duplex）
- （默认）→ Cloud API `?mode=audio`（full_duplex）

### Half-Duplex Gateway 协议适配

Half-duplex 页面使用 Gateway 专有协议，路径 `/ws/half_duplex/<sessionId>`。

翻译表：
| Gateway（浏览器发送） | Cloud API |
|---------------------|-----------|
| `prepare {system_content, config}` | 连接 → 等 queue_done → `session.init {system_prompt}` |
| ← `prepared {session_id}` | `session.created` → |
| `audio_chunk {audio_base64}` | `input.append {audio, force_listen: false}` |
| ← `chunk {text \| audio_base64}` | `response.output.delta` → |
| ← `done` | `response.done` → |
| `stop` | `session.close` |

### 静态 API 端点

全部通过 Caddy `file_server` 从预生成的 JSON 文件提供服务。`try_files {path}.json {path}` 处理无后缀 URL。

### 音频模拟测试

`AudioSession` 类管理完整 WebSocket 生命周期，无需浏览器测试：
1. `init()` — 等 queue_done → 发送 session.init → 等 session.created
2. `send_audio_chunks()` — 发送 float32 PCM chunks（base64 编码的 input.append）
3. `collect_responses()` — 收集 listen/text/audio delta 事件

## 设计决策

1. **不修改前端代码**：MiniCPM-o-Demo 静态页面原样提供。仅 CSS 和 app-nav 做必要适配。
2. **最小 Gateway 模拟**：仅实现前端实际调用的端点，不做完整 Gateway 复制。
3. **单进程 API Bridge**：通过 URL 路径分发在同一进程中处理全部模式。
4. **静态 JSON 优于动态 API**：预设元数据、应用列表、健康状态预生成，运行时数据不变。
