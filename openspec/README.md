# OpenSpec

CradleCoach 的规范驱动开发层。规划真相，不是执行状态。

## 目录

- `specs/` — 稳定的行为规范（"这个仓库应该做什么"）。长期不变
- `changes/` — 进行中的变更提案（"正在改什么"）。完成后合并回 `specs/`

## 使用方式

需要提案时手动创建 `openspec/changes/<date>-<name>.md`。Claude Code 读取 `specs/` 下的文件即自动对齐行为预期。

轻量路径不依赖 OpenSpec CLI——Spec 文件本身就是 Claude Code 会话之间的共享真相来源。
