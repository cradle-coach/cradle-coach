# Spec: Compliance Harness

CradleCoach Gateway 层合规模块的行为规范。法规依据：《人工智能拟人化互动服务管理暂行办法》（2026.7.15 施行）。

## 模块清单

| 模块 | 法规条款 | 核心行为 |
|------|----------|----------|
| `safety_middleware.py` | §8(二)(三)(五)(六)(七) | 7 类输出过滤：硬拦截、情感绑定、情感操纵、社交替代、隐私套取 |
| `silence_controller.py` | §10 | 沉默窗口 + barge-in + 短回应过滤；超时后引导回训练目标 |
| `exit_manager.py` | §19 | 退出关键词立即休眠 + 30 分钟无交互自动休眠；退出后 5 分钟不主动发起对话 |
| `compliance_timer.py` | §18 | 2 小时累计提醒 + 5 分钟倒计时强制休眠；每日零点重置 |
| `identity_disclosure.py` | §18 | 首次启动 AI 身份声明 + 每月定期提醒；按年龄段分层文本 |
| `emergency_alert.py` | §13 | RED/YELLOW 两级极端情绪检测；RED 触发语音引导 + 家长推送 + 30 分钟安全模式 |

## 约束

1. 所有模块必须在 docstring 首行引用法规条款号
2. 新增检测规则必须在 `tests/test_compliance_regression.py` 加对应测试
3. 安全护栏的检测逻辑不得包含"例外"——宁可误拦截不能漏拦截
4. 退出管理不得在退出后 5 分钟内主动发起对话（第 19 条机械执行）
