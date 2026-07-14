# 2026-07-14 Phase 1: System Prompt 注入

## 背景

CradleCoach 合规版 System Prompt 已设计完成（`config/cradlecoach_system_prompt.yaml`），需要注入到 MiniCPM-o-Demo 的推理管线中，使 API Bridge 转发的对话使用合规人格。

## 目标

修改 UnifiedProcessor 的 System Prompt 加载路径，使其读取 CradleCoach YAML 配置而非默认 System Prompt。确保 AI 输出遵守 5 条核心原则和 5 类禁止表述。

## In Scope

- 修改 `minicpmo-demo/core/processors/unified.py` 的 System Prompt 加载逻辑
- 新增合规检测测试（情感绑定、退出引导、AI 身份声明）
- 关联 `config/cradlecoach_system_prompt.yaml`

## Out of Scope

- 不修改 SafetyMiddleware（Phase 2）
- 不修改 Gateway 层（Phase 3a/3b）

## 验收标准

- [ ] AI 输出不含情感绑定表述
- [ ] 情绪低落时引导调节策略
- [ ] 训练完成有退出语 + 社交引导
- [ ] 询问 AI 身份时诚实回答
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 关联

- Issue: #4
- Spec: `openspec/specs/system-prompt.md`
