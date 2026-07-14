# 2026-07-14 Phase 6: 昇腾 NPU 适配 + 比赛材料提交

## 背景

Phase 0-5 使用 Cloud API 开发。Phase 6 将推理切换到昇腾 NPU 本地运行，完成 MiniCPM × 昇腾挑战赛全部提交材料。

## 目标

昇腾 NPU 替代 Cloud API Backend，保持 API Bridge 协议不变（只替换后端）。API Bridge 模式始终作为 fallback 保留。完成比赛全部材料提交。

## In Scope

- MiniCPM-o 4.5 在昇腾 NPU 推理验证
- 昇腾 Backend 与 API Bridge 协议兼容性
- Demo 视频（3-5 分钟核心交互流程）
- PPT + 项目说明书（问题→方案→架构→合规→商业模式）
- 8 月 17 日前提交

## Out of Scope

- 不修改 Gateway/Harness 层逻辑
- 不新增训练游戏

## 验收标准

- [ ] CradleCoach 在昇腾 NPU 端到端可用
- [ ] API Bridge 模式与昇腾模式切换无回归
- [ ] 所有比赛材料按时提交

## 关联

- Issue: #9
- Spec: 不涉及（部署适配，非行为变更）
