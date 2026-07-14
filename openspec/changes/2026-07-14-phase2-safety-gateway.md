# 2026-07-14 Phase 2: 安全护栏 Gateway 集成

## 背景

`gateway_modules/safety_middleware.py` 已独立实现 7 类检测规则，需要集成到 MiniCPM-o-Demo 的 Gateway 层。

## 目标

在 Gateway WebSocket 消息路径上插入 SafetyMiddleware，在模型输出进入 TTS 前执行检测。硬拦截（自伤/暴力）阻止输出，软拦截（情感绑定/操纵/社交替代/隐私套取）记录日志。

## In Scope

- 修改 Gateway 消息路径，注入 SafetyMiddleware
- 7 类规则全部在 Gateway 层生效
- 拦截日志写入 `harness_logs/safety_intercepts/`

## Out of Scope

- 不新增检测规则类别（Phase 1 System Prompt 覆盖表述层面）
- 不修改 TTS/ASR 管线

## 验收标准

- [ ] 硬拦截（自伤/暴力）100% 阻止输出
- [ ] 软拦截（情感绑定/操纵/社交替代/隐私套取）日志可查
- [ ] 正常训练对话零误拦截
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 关联

- Issue: #5
- Spec: `openspec/specs/compliance-harness.md`
