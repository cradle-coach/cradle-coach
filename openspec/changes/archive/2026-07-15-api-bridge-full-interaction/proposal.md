## 背景

MiniCPM-o-Demo 提供 5 种交互模式（turnbased、realtime、half-duplex、audio-duplex、omni），但 Phase 0 的 API Bridge 仅支持 Chat 模式。完整 Demo 需要本地 GPU 和 PyTorch Backend。本次变更通过 WebSocket 代理将全部 5 种模式接入 OpenBMB Cloud API，无需本地 GPU。

## 变更内容

- **动态 mode 路由**：从客户端 WebSocket URL 提取 `?mode=` 参数，路由到正确的 Cloud API 模式（chat→turn_based，默认→full_duplex）
- **Half-Duplex Gateway 协议适配**：将 Gateway 协议（`prepare`/`audio_chunk`/`chunk`/`done`）翻译为 Cloud API 协议（`session.init`/`input.append`/`response.output.delta`/`response.done`），路由路径 `/ws/half_duplex/*`
- **静态 API 端点**：以静态 JSON 提供 `/health`、`/api/presets`、`/api/apps`、`/api/default_ref_audio`、`/api/frontend_defaults`
- **音频模拟测试基础设施**：`AudioSession` 类、WAV→float32 PCM 转换、base64 编码工具，支持服务器端音频管线测试
- **集成测试**：5 个快速测试（mode 路由、chat 对话、音频格式）+ 1 个慢速测试（实时音频管线）
- **Demo 页面**：自包含的 `demo.html`，支持 Chat 和 Audio Duplex 模式
- **前端适配**：禁用 app-nav 重定向、可读性 CSS、首页展示全部 5 种模式

## Capabilities

### 新增能力
- `api-bridge-realtime-proxy`：WebSocket 代理，将 MiniCPM-o-Demo 全部 5 种交互模式路由到 OpenBMB Cloud API，无需本地 GPU。包含 half-duplex 模式的 Gateway 协议翻译

### 修改的能力

无。本次为新增能力，不修改已有行为规范。

## 影响范围

- `minicpmo-demo/api_bridge_server.py`：动态 mode 路由、half-duplex 适配器、URL 路径分发
- `minicpmo-demo/static/`：HTML 页面、API JSON 文件、demo.html
- `minicpmo-demo/tests/`：audio_fixtures.py、test_api_bridge.py、pytest.ini
- `minicpmo-demo/scripts/generate_static_api.py`：静态 API 生成器
- `minicpmo-demo/static/shared/app-nav.js`：禁用重定向、移除 i18n 覆盖
- 运行时：Caddy 反向代理配置、API Bridge 服务进程

## 验收标准

- [ ] `turnbased.html` 可输入文字并收到 AI 回复
- [ ] `realtime/realtime.html` 实时文字对话可用
- [ ] `half-duplex/half_duplex.html` 录音并获取语音回复
- [ ] `audio-duplex/audio_duplex.html` 全双工语音交互可用
- [ ] `omni/omni.html` 全模态交互可用
- [ ] 所有模式通过 API Bridge 代理，无需本地 GPU
- [ ] `python3 -m pytest tests/ -v` 全部通过
