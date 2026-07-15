## 背景

当前 Phase 2 安全护栏仅检测 AI 文本输出。用户输入（孩子文本/语音）未经安全检测。`EmergencyAlert` 模块已实现但从未接入管线——`check(asr_text)` 在整个代码库中零调用点。`SafetyMiddleware` 的隐私套取检测（rule_index=7）也未在输入端启用。

法规依据：《暂行办法》第 13 条（极端情境联络监护人）、第 8 条第（七）项（隐私保护）。

关联 Issue：#29。关联 Spec：`openspec/specs/safety-gateway-filter/spec.md`。

## 变更内容

- 更新 `api_bridge_server.py`：在 `worker_to_api()` 的用户文本输入路径增加安全检测
- 新增加 `_check_emergency()` 函数：调用 `EmergencyAlert.check()` 进行 RED/YELLOW 检测
- 新增加 `_check_input_safety()` 函数：调用 `SafetyMiddleware.check()` 进行隐私检测
- RED 级别 → EmergencyAlert 内部推送监护人 + 注入 `RED_GUIDANCE_TEXT` 到下一轮输出
- YELLOW 级别 → 仅注入 `YELLOW_GUIDANCE_TEXT`，不暂停训练
- 新增 `tests/test_input_safety.py`：用户输入端安全检测测试
- 更新 `tests/test_compliance_regression.py`：新增输入端 RED/YELLOW 合规测试

## Capabilities

### 新增能力

- `input-safety-detection`：用户文本输入的双层安全检测（EmergencyAlert + SafetyMiddleware）

### 修改的能力

- `safety-gateway-filter`：SafetyMiddleware 同时应用于输入和输出方向
- `api-bridge-realtime-proxy`：API Bridge 增加输入端安全检测管线

## 影响范围

- `minicpmo-demo/api_bridge_server.py`：新增 ~60 行检测逻辑
- `tests/test_input_safety.py`：新文件，~10 测试
- `tests/test_compliance_regression.py`：新增 ~3 测试

## 不在本次范围

- 语音 ASR 转录：Cloud API 不暴露 ASR 文本，由 Issue #54 跟踪
- 半双工音频模式：仅在 duplex/chat 模式覆盖
