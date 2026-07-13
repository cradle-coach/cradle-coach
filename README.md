# CradleCoach

面向 ADHD 儿童的端侧 AI 认知训练设备——PC 端 Harness 原型。

基于 [MiniCPM-o 4.5](https://huggingface.co/openbmb/MiniCPM-o-4_5) 全模态模型和昇腾 NPU，在 [MiniCPM-o-Demo](https://github.com/OpenBMB/MiniCPM-o-Demo) 之上增加面向 ADHD 儿童的执行功能训练引擎，以及《人工智能拟人化互动服务管理暂行办法》（2026.7.15 施行）合规模块。

> 🏆 本项目参加 [MiniCPM × 昇腾挑战赛](https://ascend.openbmb.cn) 应用创新赛道。

## 产品定位

CradleCoach 不是一个 AI 玩伴，而是一个 **AI 教练**。它以毛绒玩具形态，通过全双工语音对话和嵌入式训练游戏，帮助 4-12 岁 ADHD 儿童改善执行功能（工作记忆、认知灵活性、反应抑制）。所有推理在设备本地完成，数据不出设备。

核心设计原则：
- **功能性共情而非情感共情**——识别情绪 → 引导调节 → 回到训练
- **退出友好而非沉浸粘性**——训练完成后主动说"去找爸爸妈妈吧"
- **透明身份而非模糊边界**——诚实告知"我是一个训练工具"

## 架构

```
minicpmo-demo/              # MiniCPM-o-Demo 子模块（Git Submodule）
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
mock_guardian_server.py     # 家长端 Mock Server（PC 仿真）
tests/
  └── test_compliance_regression.py  # 17 个合规回归测试
resources/                  # 参考音频等资源文件
harness_logs/               # Harness 运行日志
```

## 快速开始

### 前置条件

- Python 3.11+
- GPU（用于 MiniCPM-o 4.5 推理，推荐 A100/L40S 或 RTX 4090 24GB+）
- 昇腾 NPU 开发环境（通过 [华为 HiDevLab](https://hidelab.huawei.com) 申请，备注"参加面壁昇腾大赛"，审核 1-3 工作日）

### 环境搭建

```bash
# 1. 克隆仓库（含子模块）
git clone --recursive https://github.com/cradle-coach/cradle-coach.git
cd cradle-coach

# 2. 初始化 MiniCPM-o-Demo
cd minicpmo-demo/minicpmo45_service
pip install -r requirements.txt
cp config.example.json config.json
# 编辑 config.json 设置模型路径和 GPU 分配

# 3. 安装 CradleCoach 依赖
cd ../..
pip install -r requirements.txt

# 4. 启动（Docker Compose 方式）
cd minicpmo-demo
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

## 开发阶段

| Phase | 内容 | 状态 |
|-------|------|:--:|
| Phase 0 | 环境搭建 + MiniCPM-o-Demo 跑通 | ⬜ |
| Phase 1 | 合规人格配置（System Prompt 注入） | ⬜ |
| Phase 2 | 安全护栏 Gateway 集成 | ⬜ |
| Phase 3 | 沉默控制 + 退出管理 + 对话流 + 可观测性集成 | ⬜ |
| Phase 4 | 记忆系统（LanceDB） | ⬜ |
| Phase 5 | 训练游戏引擎 | ⬜ |
| Phase 6 | 合规模块套件端到端联调 | ⬜ |

## 相关文档

- [CradleCoach 监管合规版产品方案](docs/product-plan.md)
- [CradleCoach Harness 开发方案](docs/harness-implementation.md)
- [ADHD 硬件 ×《暂行办法》监管冲击分析](docs/regulation-impact.md)
- [MiniCPM × 昇腾挑战赛 参赛策略](docs/competition-strategy.md)

## 许可证

[Apache License 2.0](LICENSE)
