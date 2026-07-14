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
- [ ] 浏览器端验证（需真实 Mic/Camera）
