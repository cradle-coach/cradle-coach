# CradleCoach

面向 ADHD 儿童的端侧 AI 认知训练设备——PC 端 Harness 原型。

CradleCoach 是基于 [MiniCPM-o-Demo](https://github.com/OpenBMB/MiniCPM-o-Demo) 的上层应用，增加面向 ADHD 儿童的执行功能训练引擎和《人工智能拟人化互动服务管理暂行办法》（2026.7.15 施行）合规模块。

## 架构

```
minicpmo-demo/              # MiniCPM-o-Demo 子模块（Git Submodule）
gateway_modules/            # Harness 合规模块和训练中间件
cradle_memory/              # 记忆系统（LanceDB）
cradle_training/            # 训练游戏引擎
mock_guardian_server.py     # 家长端 Mock Server（PC 仿真）
tests/                      # 合规回归测试
resources/                  # 参考音频等资源文件
harness_logs/               # Harness 运行日志
```

## 快速开始

### 前置条件

- Python 3.11+
- GPU（用于 MiniCPM-o 4.5 推理，推荐 A100/L40S 或 RTX 4090 24GB+）
- 昇腾 NPU 开发环境（通过 [华为 HiDevLab](https://hidelab.huawei.com) 申请，备注"参加面壁昇腾大赛"）

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

## Harness 模块

| 模块 | 文件 | 法规依据 | 功能 |
|------|------|----------|------|
| 安全护栏 | `gateway_modules/safety_middleware.py` | §8(二)(三)(五)(六)(七) | 输出层安全过滤 |
| 沉默控制 | `gateway_modules/silence_controller.py` | §10 | 对话节奏管理 |
| 退出管理 | `gateway_modules/exit_manager.py` | §19 | 退出关键词 + 无交互休眠 |
| 对话流管理 | `gateway_modules/conversation_flow.py` | — | 追问计数 + 难度自适应 |
| 合规计时器 | `gateway_modules/compliance_timer.py` | §18 | 2 小时提醒 + 强制休眠 |
| 身份声明 | `gateway_modules/identity_disclosure.py` | §18 | AI 身份声明（首次 + 月度） |
| 极端情绪预警 | `gateway_modules/emergency_alert.py` | §13 | RED/YELLOW 两级检测 + 家长推送 |
| 可观测性 | `gateway_modules/observability.py` | — | 日志记录 |

## 开发阶段

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 0 | 环境搭建 + Demo 跑通 | ⬜ |
| Phase 1 | 合规人格配置（System Prompt 重写） | ⬜ |
| Phase 2 | 安全护栏合规升级 | ⬜ |
| Phase 3 | 沉默控制 + 退出管理 + 对话流 + 可观测性 | ⬜ |
| Phase 4 | 记忆系统 | ⬜ |
| Phase 5 | 训练游戏引擎 | ⬜ |
| Phase 6 | 合规模块套件 | ⬜ |

## 许可证

待定
