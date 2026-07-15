# CradleCoach

面向 ADHD 儿童的端侧 AI 认知训练设备——PC 端 Harness 原型。

基于 [MiniCPM-o 4.5](https://huggingface.co/openbmb/MiniCPM-o-4_5) 全模态模型，在 [MiniCPM-o-Demo](https://github.com/OpenBMB/MiniCPM-o-Demo) 之上增加面向 ADHD 儿童的执行功能训练引擎，以及《人工智能拟人化互动服务管理暂行办法》（2026.7.15 施行）合规模块。Phase 0-5 通过 OpenBMB 官方云端 API 进行推理，Phase 6 适配昇腾 NPU 本地推理。

> 🏆 本项目参加 [MiniCPM × 昇腾挑战赛](https://ascend.openbmb.cn) 应用创新赛道。

## 产品定位

CradleCoach 不是一个 AI 玩伴，而是一个 **AI 教练**。它以毛绒玩具形态，通过全双工语音对话和嵌入式训练游戏，帮助 4-12 岁 ADHD 儿童改善执行功能（工作记忆、认知灵活性、反应抑制）。所有推理在设备本地完成，数据不出设备。

核心设计原则：
- **功能性共情而非情感共情**——识别情绪 → 引导调节 → 回到训练
- **退出友好而非沉浸粘性**——训练完成后主动说"去找爸爸妈妈吧"
- **透明身份而非模糊边界**——诚实告知"我是一个训练工具"

## 架构

```
minicpmo-demo/              # MiniCPM-o-Demo 内嵌源码
gateway_modules/            # Harness 合规模块和训练中间件
  ├── safety_middleware.py   # §8  安全护栏（7 类检测规则）
  ├── silence_controller.py  # §10 沉默控制（合规适配）
  ├── exit_manager.py        # §19 退出管理
  ├── compliance_timer.py    # §18 2 小时计时器
  ├── identity_disclosure.py # §18 AI 身份声明
  ├── emergency_alert.py     # §13 极端情绪预警
  ├── conversation_flow.py   #      对话流管理
  ├── observability.py       #      可观测性
  └── harness_manager.py     #      组件注册与编排
config/
  └── cradlecoach_system_prompt.yaml  # 合规 System Prompt
cradle_memory/              # 记忆系统——LanceDB（Phase 4）
cradle_training/            # 训练游戏引擎（Phase 5）
  ├── antonyms.py            #   反义词——反应抑制（水果例外规则）
  ├── reverse_memory.py      #   倒序记忆——工作记忆（3-6 词序列）
  ├── emotion_guess.py       #   情绪猜谜——情绪识别（故事库 + 同义词）
  ├── story_chain.py         #   故事接龙——认知灵活性（长度 + 连贯性）
  └── training_manager.py    #   训练编排——触发判断、难度自适应、结束仪式
mock_guardian_server.py     # 家长端 Mock Server（PC 仿真）
tests/
  ├── test_compliance_regression.py  # 合规回归测试
  └── test_training_engine.py       # 训练引擎测试（42 个）
resources/                  # 参考音频等资源文件
harness_logs/               # Harness 运行日志
```

## 快速开始

### 前置条件

- Python 3.11+
- OpenBMB API Key（[免费获取](https://api.modelbest.cn/minicpmo45/docs)）
- （可选）昇腾 NPU 开发环境 — [华为 HiDevLab](https://hidelab.huawei.com)，备注"参加面壁昇腾大赛"

### 环境搭建

```bash
git clone https://github.com/cradle-coach/cradle-coach.git
cd cradle-coach

# API Bridge 模式（Phase 0-5，无需 GPU）
cd minicpmo-demo
pip install -r requirements.txt
CRADLECOACH_API_KEY=<your_key> python api_bridge_server.py --port 22400 --api-mode audio

# 本地 PyTorch 模式（需要 GPU）
cp config.example.json config.json
docker compose up
# 浏览器打开 https://localhost:8006
```

### 运行测试

```bash
python3 -m pytest tests/ -v
```

## 法规合规对照

| 法规条款 | 模块 | 实现 |
|----------|------|------|
| §8(二)(三)(五)(六)(七) — 禁止内容 | `safety_middleware.py` | 7 类检测规则：硬拦截、情感绑定、情感操纵、社交替代、隐私套取 |
| §10 — 不得替代社会交往 | `silence_controller.py` | 沉默控制合规适配，沉默后引导回训练目标 |
| §13 — 极端情境干预 | `emergency_alert.py` | RED/YELLOW 两级检测，语音引导 + 家长推送 + 安全模式 |
| §18 — AI 标识与防沉迷 | `compliance_timer.py` / `identity_disclosure.py` | 2 小时提醒 + 5 分钟强制退出；AI 身份首次声明 + 月度提醒 |
| §19 — 便捷退出 | `exit_manager.py` | 退出关键词立即休眠 + 30 分钟无交互自动休眠 |

## Roadmap

| 时间 | 目标 | 跟踪 |
|------|------|------|
| **近期** | 昇腾 NPU 本地推理适配 + 比赛材料提交 | [#9](https://github.com/cradle-coach/cradle-coach/issues/9) |
| **短期** | 语音输入端 ASR 安全检测 | [#54](https://github.com/cradle-coach/cradle-coach/issues/54) |
| **短期** | 训练游戏库扩展（新增游戏类型） | — |
| **中期** | 家长端 App（BLE/WiFi 推送） | — |
| **中期** | 多模态情绪识别（语音语调 + 面部表情） | — |
| **持续** | 合规审计 + 测试覆盖率提升 | — |

## 功能特性

### 基础通信

| 特性 | 说明 | 状态 |
|------|------|:--:|
| 全双工语音对话 | audio / chat / video 三模式 API Bridge 代理 | ✅ |
| 云端 API 推理 | OpenBMB MiniCPM-o 4.5 云端推理（Phase 0-5） | ✅ |

### 合规安全

| 特性 | 说明 | 法规 | 状态 |
|------|------|------|:--:|
| 内容安全护栏 | AI 输出 + 用户输入双向检测，7 类规则（硬拦截/情感绑定/操纵/社交替代/隐私套取/用户隐私泄露） | §8 | ✅ |
| 极端情绪预警 | RED/YELLOW 两级检测 + 监护人推送 + 30 分钟安全模式 | §13 | ✅ |
| 合规退出管理 | 关键词退出 + 沉默超时退出 + 2 小时强制提醒 | §19 | ✅ |
| AI 身份声明 | 首次对话 + 月度周期性声明「我是一个训练工具」 | §18 | ✅ |
| 防沉迷计时 | 单次会话 2 小时上限 + 5 分钟冷却 | §18 | ✅ |

### 训练引擎

| 特性 | 说明 | 训练维度 | 状态 |
|------|------|------|:--:|
| 反义词游戏 | 35 对反义词，水果例外规则（抑制说反义词冲动） | 反应抑制 | ✅ |
| 倒序记忆游戏 | 3-6 词序列倒序复述，具体/抽象词分级 | 工作记忆 | ✅ |
| 情绪猜谜游戏 | 13 个故事情境，6 种基本情绪 + 同义词匹配 | 情绪识别 | ✅ |
| 故事接龙游戏 | 8 个故事开头，长度 + 连贯性（中文 n-gram）评估 | 认知灵活性 | ✅ |
| 训练编排 | 触发判断 + 难度自适应（1-5 级）+ 努力导向反馈 + 社交引导结束仪式 | — | ✅ |

### 记忆系统

| 特性 | 说明 | 状态 |
|------|------|:--:|
| 用户画像存储 | LanceDB 向量数据库，存储对话历史与训练记录 | ✅ |

### 端侧部署

| 特性 | 说明 | 状态 |
|------|------|:--:|
| 昇腾 NPU 推理 | MiniCPM-o 本地推理适配，数据不出设备 | 🚧 |
| 语音输入 ASR 安全 | 用户语音内容实时安全检测 | 📋 |

> 状态说明：✅ 已完成 &nbsp; 🚧 进行中 &nbsp; 📋 计划中

## 产品文档

完整的产品设计文档见 [`docs/product/`](./docs/product/)：

- [市场全景](./docs/product/market-landscape.md) — 为什么选这个方向
- [产品方案](./docs/product/adhd-product-design.md) — 产品是什么
- [法规合规](./docs/product/regulatory-compliance.md) — 法律怎么合规
- [架构决策](./docs/product/architecture-decisions.md) — 技术为什么这样做
- [System Prompt 设计](./docs/product/system-prompt-design.md) — AI 人格设计

## 许可证

[Apache License 2.0](LICENSE)
