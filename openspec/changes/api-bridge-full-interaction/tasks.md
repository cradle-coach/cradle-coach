## 任务拆解（TDD 顺序）

1. **音频帧管线测试** → 写测试：`AudioSession` 类，WAV→float32 PCM→base64，验证格式正确性
2. **动态 mode 路由** → 从客户端 WebSocket URL 提取 `?mode=` 参数
3. **Chat 模式端到端** → 文字消息发送→AI 回复验证
4. **Half-Duplex 协议适配** → `prepare`/`audio_chunk`↔`session.init`/`input.append` 翻译
5. **Audio Duplex 验证** → 音频 mode session 握手 + listen 事件确认
6. **静态 API 生成** → 一键生成 presets、apps、health、ref_audio、frontend_defaults JSON
7. **前端适配** → app-nav 重定向禁用、readability CSS、index 首页更新
8. **Demo 页面** → `demo.html` 自包含 Chat + Audio Duplex 页面
9. **集成测试** → mode 路由、chat 对话、音频 pipeline 测试

## 实现状态

- [x] 动态 mode 路由
- [x] Half-Duplex 协议适配
- [x] 静态 API 生成
- [x] 音频模拟测试基础设施
- [x] 前端适配
- [x] Demo 页面
- [x] 集成测试（5 fast + 1 slow）
- [x] 服务器端验证（Python WS 脚本 + Playwright headless Chrome）

## 端到端人工验证（2026-07-14，macOS Chrome）

| 模式 | 结果 | 说明 |
|------|:--:|------|
| **Audio Duplex** | ✅ 可用 | 全双工语音交互正常 |
| **Omni** | ✅ 可用 | 全模态（语音+视频）正常 |
| Turnbased Chat 文字 | ✅ 可用 | 文字对话正常 |
| Turnbased Chat 录音 | ❌ 不可用 | Cloud API chat 模式不支持混合音频附件格式 |
| Mobile 页面 | ❌ 不可用 | mobile-bridge.js 依赖原生 App WebView API，需完整 Gateway |
| Half Duplex | — 未测 | 非目标模式 |

## 限制说明

- **Turnbased 录音不可用**：Chat 模式通过 `UserContentEditor._startRecording()` 将录音嵌入为 base64 附件，Cloud API chat 模式仅处理 `messages` 数组中的文本，不处理音频附件
- **Mobile 页面不可用**：`mobile-omni/` 依赖原生 App WebView Bridge，不在 API Bridge 代理范围内
- **仅需 Audio Duplex + Omni**：后续开发围绕全双工语音和多模态两个核心模式进行
