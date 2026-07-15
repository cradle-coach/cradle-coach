# Issue #29: feat — 完整内容安全检测（双向安全护栏）

status: done
branch: feature/29-bidirectional-safety
last-session: 2026-07-15
summary: |
  当前 Phase 2 仅检测 AI 文本输出。需要增加用户输入端安全检测。

  决策 (2026-07-15):
  - 方案: 文本路径先行（chat 模式 input.append 文本检测）
  - 用户输入端启用 SafetyMiddleware 隐私套取检测
  - YELLOW 级别: 仅引导，不暂停训练
  - 方案 A (Cloud API listen 事件) 验证不可行—listen 不含 ASR 文本
  - 语音 ASR 跟踪: Issue #54

  Implementation:
  - api_bridge_server.py: 在 worker_to_api() 的 input.append 路径增加安全检测
  - _check_emergency(): 调用 EmergencyAlert.check() 进行 RED/YELLOW 检测
  - _check_input_safety(): 调用 SafetyMiddleware.check() 进行隐私检测
  - RED → 监护人推送 + 注入引导语
  - YELLOW → 仅引导，不暂停训练
