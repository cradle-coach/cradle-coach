---
name: Phase Development Issue
about: CradleCoach 开发 Phase（Superpowers 工作流）
title: 'Phase N: <short description>'
labels: ''
assignees: ''
---

## 背景

<!-- 这个 Phase 要解决什么问题？为什么需要做？引用 OpenSpec specs/ 或法规条款。 -->

## 方案推演

<!-- 使用 /superpowers:brainstorming 进行方案推演，在此记录关键决策：
- 技术路径选择
- 关键设计决策及理由
- 风险和边界 -->

## 任务拆解（TDD 顺序）

<!-- 每个任务以测试先行：先写失败的测试，再写实现代码。 -->

1. **<测试名称>** → 写测试：<场景>，断言 <预期行为>
2. **<实现名称>** → <实现描述>
3. ...

## 验收标准

- [ ] <!-- 可验证的完成条件 -->
- [ ] `python3 -m pytest tests/ -v` 全部通过

## 验证清单

- [ ] 所有新增行为有对应的 pytest 用例
- [ ] `/verification-before-completion` 通过
