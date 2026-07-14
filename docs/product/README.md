# CradleCoach 产品文档

## 文档索引

| 文档 | 回答的问题 |
|------|-----------|
| [market-landscape.md](./market-landscape.md) | 为什么选这个方向？市场竞品格局是什么？ |
| [adhd-product-design.md](./adhd-product-design.md) | 产品是什么？怎么设计？目标用户是谁？ |
| [regulatory-compliance.md](./regulatory-compliance.md) | 法律怎么合规？每个法规条款怎么应对？ |
| [architecture-decisions.md](./architecture-decisions.md) | 技术为什么这样做？每个关键决策的理由是什么？ |
| [system-prompt-design.md](./system-prompt-design.md) | AI 人格怎么设计？什么能说什么不能说？ |

## 文档关系图

```
market-landscape.md        adhd-product-design.md
(为什么做)                  (做什么)
      |                          |
      v                          v
regulatory-compliance.md  system-prompt-design.md
(法律怎么合规)              (AI 怎么说)
      |                          |
      +------------+-------------+
                   |
                   v
         architecture-decisions.md
         (技术上怎么实现)
```

## 相关文档

- 工程流程：`docs/engineering/development-workflow.md`
- 仓库规约：`docs/engineering/repository-governance.md`
- 行为规范：`openspec/specs/`
- 变更提案：`openspec/changes/`
- 项目 README：`../README.md`
