## 架构

```
cradle_training/
├── __init__.py           # Public API exports
├── antonyms.py           # AntonymGame — 反应抑制
├── reverse_memory.py     # ReverseMemoryGame — 工作记忆
├── emotion_guess.py      # EmotionGuessGame — 情绪识别
├── story_chain.py        # StoryChainGame — 认知灵活性
└── training_manager.py   # TrainingManager — 编排层

gateway_modules/
└── harness_manager.py    # 注册 self.training = TrainingManager()
```

```
对话流 → should_trigger(context, emotion)
              │
              ├── trigger=False → 不触发（间隔不足/情绪不佳）
              │
              └── trigger=True
                      │
                      ▼
                start_game(game_type, difficulty)
                      │
                      ▼
                生成 prompt → 等待用户回答
                      │
                      ▼
                evaluate(game_type, response, expected)
                      │
                      ├── 反馈（努力导向）
                      ├── record_result(correct)
                      └── adapt_difficulty()
                              │
                              ▼
                        get_closing_message()
                        → 社交引导："找爸爸妈妈分享"
```

## 游戏引擎设计

### 1. 反义词 (AntonymGame)

- **词库**：35 对反义词，按难度 1-5 分级
- **水果例外规则**：15 种水果词汇触发例外——说原词算对，说反义词算错
- **评估**：`evaluate(prompt_word, expected_answer, user_response) → AntonymResult`
- **难度**：easy 选常见词 + 低水果概率，hard 选抽象词 + 30% 水果概率

### 2. 倒序记忆 (ReverseMemoryGame)

- **词库**：42 个具体词 + 27 个抽象词
- **词数映射**：easy(2-4) → medium(3-5) → hard(4-6)
- **评估**：逐位置比较反转序列，支持部分正确计数
- **难度**：easy 仅具体词，hard 以抽象词为主

### 3. 情绪猜谜 (EmotionGuessGame)

- **情绪**：6 种基本情绪（开心/难过/生气/害怕/惊讶/讨厌），各含 5-6 个同义词
- **故事库**：13 个场景故事，按 emotional subtlety 分 3 级
- **评估**：完全匹配 + 同义词匹配均视为正确

### 4. 故事接龙 (StoryChainGame)

- **开头库**：8 个故事开头，按主题复杂度分级
- **评估维度**：
  - 长度评分：续写字数 vs 难度最小字数(20-100 字)
  - 连贯性评分：基于中文 2-gram + 3-gram 的 n-gram 重叠率
- **综合判断**：length_score ≥ 0.5 且 coherence_score ≥ 0.2 为通过

## 设计决策

1. **纯规则引擎，非 LLM**：所有判断基于字符串匹配和规则，不依赖模型推理。训练目标是对话中嵌入的行为干预，游戏逻辑本身应确定、一致
2. **难度对接 ConversationFlow**：TrainingManager.current_difficulty 与 ConversationFlow.current_difficulty 使用同一标度(1-5)
3. **反馈设计**：所有正面反馈聚焦过程（专注/努力/认真），禁止"你真聪明"等结果导向表扬，顺应 ADHD 儿童成长型思维培养
4. **社交引导硬编码**：每条结束语必须提及"爸爸妈妈"或"分享"，不可配置
5. **无外部依赖**：仅使用 Python 标准库（random, re, dataclasses），无需新增 pip 包
