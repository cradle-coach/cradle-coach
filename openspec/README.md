# OpenSpec

CradleCoach 的规范驱动开发层。使用 OpenSpec CLI 管理提案→执行→归档闭环。

## 目录

- `config.yaml` — OpenSpec 配置（schema: spec-driven）
- `specs/` — 稳定的行为规范，长期不变
- `changes/` — 进行中的变更提案（目录格式，含 `proposal.md`）
- `changes/archive/` — 已完成的提案归档

## 使用方式

### CLI 命令

```bash
openspec list                    # 列出活跃提案
openspec list --specs            # 列出行为规范
openspec show <name>             # 查看提案详情
openspec validate <name>         # 验证提案格式
openspec archive <name>          # 归档已完成提案
```

### Claude Code 命令

```
/opsx:propose <description>     # 创建新提案
/opsx:apply <change-name>       # 按提案执行开发
/opsx:archive <change-name>     # 归档已完成提案
/opsx:explore                   # 浏览 specs 和 changes
```

### 开发流程

1. **创建 Issue** → GitHub Issue 模板
2. **创建提案** → `/opsx:propose` 生成 `openspec/changes/<name>/proposal.md`
3. **执行开发** → `/opsx:apply` 按提案 TDD 实现
4. **归档** → `/opsx:archive` 将提案移入 `archive/`，涉及的行为变更合并到 `specs/`

### 语言规范

所有 OpenSpec 工件（proposal、design、specs、tasks）必须使用中文撰写。配置见 `config.yaml`。
