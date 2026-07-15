# Issue #29 分析报告：双向内容安全护栏

**日期**: 2026-07-15
**状态**: 分析完成，待决策后开发

> **⚠️ 方案更新 (2026-07-15)**：第二节中的方案 A（Cloud API listen 事件）在开发前验证阶段证实不可行——Cloud API `kind: "listen"` 事件不含用户 ASR 转录文本（`is_listen: true` 时 `text` 字段为空）。实际采用**文本路径先行**方案：在 duplex/chat 模式的 `input.append` 文本内容上进行检测，语音 ASR 由 Issue #54 跟踪。第三-五节的 listen 事件架构设计保留作为未来参考，实际管线见 `openspec/changes/phase5-bidirectional-safety/design.md`。

---

## 一、现状差距分析

### 1.1 当前安全覆盖

| 方向 | 检测目标 | 当前状态 | 检测模块 |
|------|---------|:--:|------|
| AI 文本输出 | 5 类违规（自伤/暴力/情感绑定/操纵/社交替代/隐私） | ✅ | `SafetyMiddleware.check()` |
| AI 音频输出 | 无文本可检测 | N/A | 跳过 |
| **用户文本输入** | 自伤/极端情绪 | ❌ | `EmergencyAlert.check()` 已存在但从未调用 |
| **用户文本输入** | 隐私泄露（孩子说出个人信息） | ❌ | 无 |
| **用户文本输入** | Jailbreak/操纵尝试 | ❌ | 无 |

### 1.2 关键发现

**发现 1：`EmergencyAlert.check(asr_text)` 已存在但从未接入管线**

`gateway_modules/emergency_alert.py:83` — `check(asr_text: str)` 方法接受用户 ASR 文本，具备完整的 RED/YELLOW 检测 + 升级 + 安全模式逻辑。但 grep 全仓未找到任何调用点。它在 `HarnessManager` 中注册（line 48），但 API Bridge 未使用 `HarnessManager`。

**发现 2：Cloud API 的 ASR 转录被丢弃**

`api_bridge_server.py:559-561`（半双工模式）和 duplex 模式的等价位置：
```python
elif kind == "listen":
    # Listen events are status-only, not forwarded to half-duplex UI
    pass
```
Cloud API 在 `kind: "listen"` 事件中返回 ASR 转录文本，但当前代码显式丢弃。这是最可能的用户输入端文本来源。

**发现 3：API Bridge 绕过 HarnessManager 直接初始化模块**

`api_bridge_server.py:94-105` 直接 `from gateway_modules.safety_middleware import SafetyMiddleware` 并独立初始化。`HarnessManager` 中注册的 `EmergencyAlert`、`ComplianceTimer` 等模块在 API Bridge 中不可见。需要统一集成路径。

**发现 4：`SafetyMiddleware.check()` 可同时用于输入和输出**

当前 `SafetyMiddleware` 仅检查 AI 输出，但它的检测类别（特别是隐私套取 `rule_index=7`）对用户输入同样适用——孩子可能主动说出个人信息。

---

## 二、技术方案评估

### 方案 A：利用 Cloud API listen 事件中的 ASR 转录（推荐）

**原理**：Cloud API audio-duplex 模式下，每次用户说完话后会返回 `kind: "listen"` 事件，其中包含 `text` 字段（ASR 转录）。解析该事件文本 → 送入检测管线。

**优点**：
- 零额外延迟（listen 事件已在流中）
- 零资源开销（ASR 由 Cloud API 完成）
- 代码改动最小（约 50 行）

**缺点**：
- 需确认 OpenBMB Cloud API 的 listen 事件格式是否包含 text 字段
- 依赖 Cloud API 的 ASR 质量

**实现路径**：
```
Cloud API → listen event (text 字段) 
  → EmergencyAlert.check(text)   # RED/YELLOW 检测
  → SafetyMiddleware.check(text) # 隐私/操纵检测（可选）
```

### 方案 B：本地 ASR 前置

在 API Bridge 前增加 whisper.cpp/faster-whisper 做本地转写。

**优点**：
- 不依赖 Cloud API
- 低延迟离线可用

**缺点**：
- 增加 200-500ms ASR 延迟
- 需要 GPU/CPU 资源（量化模型 ~200MB）
- 维护成本高
- 对昇腾部署场景不友好

### 方案 C：Cloud API 内置内容审核

依赖 OpenBMB API 的内置审核参数。

**优点**：
- 零代码

**缺点**：
- OpenBMB API 可能不支持内容审核参数
- 不可控（审核规则不可定制）
- 无法集成 EmergencyAlert 的升级/推送逻辑

### 推荐：**方案 A**

理由：改动最小、零延迟、与现有架构兼容。唯一风险是需确认 listen 事件格式——可在开发第一步做验证。

---

## 三、集成架构设计

### 3.1 当前管线 vs 目标管线

```
当前（仅输出检测）:
  用户音频 → Cloud API → AI 文本 → SafetyMiddleware.check() → TTS/显示
                          ↑ listen 事件被丢弃

目标（双向检测）:
  用户音频 → Cloud API → listen 事件(ASR文本) → EmergencyAlert.check()
                          ↓                            ↓
                       AI 文本 → SafetyMiddleware.check() → TTS/显示
                                   ↓
                              ConversationFlow hint
```

### 3.2 具体改动点

| 文件 | 改动 | 行数估计 |
|------|------|---------|
| `api_bridge_server.py` | 解析 `kind: "listen"` 事件中的 text 字段，调用 `_check_emergency(text)` | ~30 行 |
| `api_bridge_server.py` | 新增 `_check_emergency()` 函数 → EmergencyAlert.check()，RED 时触发监护人推送 + 注入引导语 | ~40 行 |
| `api_bridge_server.py` | （可选）用户输入端也调用 SafetyMiddleware.check() 检测隐私泄露 | ~15 行 |
| `tests/test_api_bridge.py` | 新增 `TestInputSafetyIntegration` 类 | ~50 行 |
| `tests/test_compliance_regression.py` | 新增隐私套取检测测试 + RED 预警后行为测试 | ~30 行 |

### 3.3 EmergencyAlert 集成逻辑

```python
def _check_emergency(asr_text: str):
    event = _emergency_alert.check(asr_text)
    
    if event.level == AlertLevel.RED:
        # 1. 监护人推送（EmergencyAlert 内部已处理）
        # 2. 注入引导语到下一轮 AI 输出
        _pending_guidance = EmergencyAlert.RED_GUIDANCE_TEXT
        logger.warning("Emergency RED: keyword=%s", event.keyword)
        
    elif event.level == AlertLevel.YELLOW:
        # 暂停训练 + 注入情绪调节引导
        _pending_guidance = EmergencyAlert.YELLOW_GUIDANCE_TEXT
        logger.info("Emergency YELLOW: keyword=%s, count=%d", 
                    event.keyword, _emergency_alert._yellow_count)
```

---

## 四、风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|:---:|------|------|
| Cloud API listen 事件不含 text 字段 | 中 | 需切换方案 B | 第一步先验证事件格式 |
| ASR 转录错误导致误报/漏报 | 中 | 用户体验差 | YELLOW 级别用引导语而非中断，给用户纠正机会 |
| 增加管线延迟 | 低 | 实时性下降 | listen 事件本就在流中，检测耗时 <1ms |
| 与现有 SilenceController 交互 | 低 | 冲突 | YELLOW 引导语期间暂停静默计时器 |

---

## 五、任务拆解（预估）

1. **调研 Cloud API listen 事件格式** → 验证 `kind: "listen"` 的 `text` 字段是否存在，格式如何（~1h）
2. **写测试** → TDD：输入检测不工作 → 修复后通过（~6 tests）
3. **实现 listen 事件解析** → 提取 ASR 文本
4. **实现 EmergencyAlert 集成** → `_check_emergency()` + RED/YELLOW 行为
5. **（可选）用户输入端 SafetyMiddleware** → 隐私套取检测
6. **集成测试** → 模拟音频输入验证全管线
7. **回归测试** → 确认现有 103 测试不受影响

---

## 六、前置依赖检查

| 依赖 | 状态 |
|------|:--:|
| Phase 2 安全护栏（SafetyMiddleware） | ✅ 已完成 |
| API Bridge audio-duplex 模式 | ✅ Phase 0/14 已完成 |
| EmergencyAlert 模块 | ✅ 已实现（但从未调用） |
| 监护人推送 Mock Server | ✅ `mock_guardian_server.py` 已存在 |
| Phase 6 昇腾适配 | ⬜ 未开始 — **建议 #29 先于 #9**，因为 #9 依赖昇腾环境 |

---

## 七、结论

**建议立即开发 Issue #29**，理由：

1. **紧急度**：当前系统对用户输入中的自伤/自杀表述完全无感知——这是 §13 合规缺口
2. **实施成本低**：核心模块（EmergencyAlert）已存在，只需接入管线，~100 行代码
3. **架构铺垫**：listen 事件 ASR 文本提取也为后续功能（如记忆系统基于用户输入的检索、训练引擎的情绪触发）提供基础
4. **零外部依赖**：方案 A 不需要新库、新模型、新服务

**决策已确认**：
- [x] 方案：A（Cloud API listen 事件），第一步先验证 listen 事件格式
- [x] 用户输入端启用 SafetyMiddleware（隐私套取检测）
- [x] YELLOW 级别行为：仅引导，不暂停训练
