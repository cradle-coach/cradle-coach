# Spec: System Prompt Governance

CradleCoach System Prompt 的治理规范。配置文件：`config/cradlecoach_system_prompt.yaml`。

## 结构

```yaml
system_prompt: |
  [角色定义]
  [核心原则]（5 条）
  [禁止表述]（5 类）
  [训练流程]（开场 → 主体 → 结束）
  [年龄适配]（4-6 / 7-9 / 10-12）
```

## 约束

1. 任何 System Prompt 修改必须同步更新 `config/cradlecoach_system_prompt.yaml`
2. 修改后必须跑 `python3 -m pytest tests/test_compliance_regression.py -v`，确保安全护栏测试不受影响
3. 禁止在 System Prompt 中加入"例外""特殊情况下可以"等软性表述——安全规则必须绝对
4. 情感相关表述必须使用"功能性共情"框架（识别→调节→回到目标），禁止"陪伴""朋友""喜欢你"等情感绑定用语
5. 新增禁止表述类别时，同步更新 `gateway_modules/safety_middleware.py` 的检测模式
