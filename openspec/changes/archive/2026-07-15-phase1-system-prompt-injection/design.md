## 架构

```
API Bridge 启动
     │
     ├── 加载 config/cradlecoach_system_prompt.yaml
     │
     v
客户端连接 → session.init {payload}
     │
     ├── payload 已有 system_prompt? → 使用客户端提供的
     │
     └── payload 无 system_prompt? → 注入 YAML 中的合规 System Prompt
              │
              v
         Cloud API（使用 CradleCoach 合规人格）
```

## 注入策略

- **启动加载**：API Bridge 启动时通过 `--system-prompt` CLI 参数或环境变量指定 YAML 路径，加载后缓存在内存
- **不覆盖**：仅当客户端 session.init 未提供 `system_prompt` 时才注入。Demo 页面和 preset 选择器可以覆盖
- **不影响模式路由**：所有模式（chat、audio、video）均注入合规 System Prompt

## Chat 模式适配

Cloud API chat 模式不支持 `session.init` 中的 `system_prompt` 字段（仅 audio/duplex 模式支持）。Chat 模式采用替代方案：在首条 `input.append` 消息的 `messages` 数组中插入 `{"role": "system", "content": "<合规 System Prompt>"}` 作为第一条消息。

```
input.append → API Bridge 拦截首条消息 → 注入 system role message → 转发 Cloud API
```

## 设计决策

1. **后端注入优于前端修改**：不修改 MiniCPM-o-Demo 页面，所有用户在 API Bridge 后自动获得合规人格
2. **双路径注入**：session.init 注入覆盖 audio/duplex 模式，首条消息注入覆盖 chat 模式
3. **YAML 配置优于硬编码**：合规团队可直接修改 YAML 文件，无需改动 Python 代码
4. **可覆盖**：前端 preset 选择器的 system_prompt 优先于默认值，方便测试不同人格
