## 背景

`gateway_modules/safety_middleware.py` 已独立实现 7 类检测规则（硬拦截、情感绑定、情感操纵、社交替代、隐私套取），但未集成到 API Bridge 消息管线中。当前 API Bridge 直接转发 Cloud API 输出，无安全审核。

## 变更内容

- 在 API Bridge 启动时初始化 `SafetyMiddleware` 实例
- 在 `api_to_worker()` 中对每条 `response.output.delta`（kind=text）进行安全检测
- 检测到违规内容时替换为安全话术，记录拦截日志
- 不影响 audio delta（音频帧不检查）

## Capabilities

### 新增能力
- `safety-gateway-filter`：API Bridge 在模型输出转发前进行实时安全审核

### 修改的能力
- `api-bridge-realtime-proxy`：`api_to_worker()` 增加安全检测节点

## 影响范围

- `minicpmo-demo/api_bridge_server.py`：初始化 SafetyMiddleware，注入检测逻辑
- `gateway_modules/safety_middleware.py`：现有模块（不变）
- `tests/test_compliance_regression.py`：已有 5 个 SafetyMiddleware 测试
- `harness_logs/safety_intercepts/`：拦截日志

## 验收标准

- [ ] 7 类检测规则在 API Bridge 消息管线中全部生效
- [ ] 拦截内容记录到 `harness_logs/safety_intercepts/`
- [ ] 正常训练对话零误拦截
- [ ] `python3 -m pytest tests/ -v` 全部通过
