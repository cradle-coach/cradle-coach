# Spec: 训练游戏引擎

CradleCoach 执行功能训练引擎 MUST 提供四种嵌入式对话训练游戏，纯规则引擎驱动，通过 TrainingManager 统一编排。

## ADDED Requirements

### Requirement: 反义词游戏 — 反应抑制

AntonymGame MUST 支持标准反义词判断和水果例外规则。

#### Scenario: 标准反义词正确

- **WHEN** 题目词为"大"（非水果），用户回答"小"
- **THEN** evaluate 返回 correct=True
- **AND** feedback 包含努力导向肯定词（如"专注"、"认真"、"没错"等）

#### Scenario: 标准反义词错误

- **WHEN** 题目词为"白"，用户回答"大"
- **THEN** evaluate 返回 correct=False
- **AND** feedback 包含正确答案提示

#### Scenario: 水果例外正确

- **WHEN** 题目词为"苹果"（水果），用户回答"苹果"
- **THEN** evaluate 返回 correct=True
- **AND** feedback 说明水果例外规则

#### Scenario: 水果例外错误

- **WHEN** 题目词为"苹果"（水果），用户回答非原词的任何词
- **THEN** evaluate 返回 correct=False

### Requirement: 倒序记忆游戏 — 工作记忆

ReverseMemoryGame MUST 按难度生成 2-6 个词的序列，用户复述须为原序列反转。

#### Scenario: 完全正确倒序

- **WHEN** 原序列为["猫", "狗", "鸟"]，用户回答["鸟", "狗", "猫"]
- **THEN** evaluate 返回 correct=True

#### Scenario: 顺序错误

- **WHEN** 原序列为["猫", "狗", "鸟"]，用户回答["猫", "狗", "鸟"]（正序）
- **THEN** evaluate 返回 correct=False

#### Scenario: 难度控制词数

- **WHEN** difficulty=1，generate_sequence 返回 2-4 个词
- **WHEN** difficulty=5，generate_sequence 返回 4-6 个词

### Requirement: 情绪猜谜游戏 — 情绪识别

EmotionGuessGame MUST 从故事库选段，接受完全匹配或同义词匹配。

#### Scenario: 完全匹配正确

- **WHEN** 故事情绪为"开心"，用户回答"开心"
- **THEN** evaluate 返回 correct=True

#### Scenario: 同义词匹配正确

- **WHEN** 故事情绪为"开心"，用户回答"快乐"（同义词）
- **THEN** evaluate 返回 correct=True

#### Scenario: 错误情绪

- **WHEN** 故事情绪为"开心"，用户回答"害怕"
- **THEN** evaluate 返回 correct=False

### Requirement: 故事接龙游戏 — 认知灵活性

StoryChainGame MUST 评估续写的长度和与开头的连贯性。

#### Scenario: 足够长度且连贯

- **WHEN** 续写长度 ≥ 难度最小字数，且与开头有 n-gram 重叠
- **THEN** evaluate 返回 passed=True

#### Scenario: 过短

- **WHEN** 续写仅几个字（如"然后"）
- **THEN** evaluate 返回 passed=False
- **AND** feedback 提示续写更长

#### Scenario: 不连贯

- **WHEN** 续写与开头完全无关（n-gram 重叠率为 0）
- **THEN** evaluate 返回 passed=False 或 coherence_score < 1.0

### Requirement: 训练编排 — 触发和难度

TrainingManager MUST 在合适时机触发训练，并根据表现自适应难度。

#### Scenario: 间隔足够触发

- **WHEN** 距上次训练超过 MIN_TRAINING_INTERVAL（300s）
- **THEN** should_trigger 返回 trigger=True

#### Scenario: 间隔不足不触发

- **WHEN** 刚完成训练（距上次 < 300s）
- **THEN** should_trigger 返回 trigger=False

#### Scenario: 负面情绪不触发

- **WHEN** 当前情绪为 "sad" 或 "难过" 等
- **THEN** should_trigger 返回 trigger=False

#### Scenario: 连续正确升难度

- **WHEN** 最近 3 轮全部正确
- **THEN** adapt_difficulty 返回 current_difficulty + 1（最高 5）

#### Scenario: 连续错误降难度

- **WHEN** 最近 2 轮全部错误
- **THEN** adapt_difficulty 返回 current_difficulty - 1（最低 1）

### Requirement: 合规反馈 — 努力导向

所有训练反馈 MUST 聚焦努力过程，SHALL NOT 包含情感绑定或结果导向表扬。

#### Scenario: 正面反馈聚焦努力

- **WHEN** 回答正确
- **THEN** feedback MUST 包含 effort 关键词（专注/努力/认真/思考/注意力等）
- **AND** feedback SHALL NOT 包含"你真聪明"

#### Scenario: 不含情感绑定

- **WHEN** 任意反馈文本
- **THEN** feedback SHALL NOT 包含"我喜欢你"、"你是最特别的"、"我会一直陪着你"等

### Requirement: 结束仪式 — 社交引导

TrainingManager.get_closing_message() MUST 包含社交引导，引导儿童将成就分享给真实社交圈。

#### Scenario: 结束语含社交引导

- **WHEN** 调用 get_closing_message()
- **THEN** 返回文本 MUST 包含"爸爸妈妈"或"分享"

### Requirement: HarnessManager 集成

HarnessManager MUST 注册训练模块，统一暴露给 Gateway 层。

#### Scenario: 训练模块可用

- **WHEN** 调用 HarnessManager.get_all_modules()
- **THEN** 返回字典 MUST 包含 key "training"
- **AND** training 对象 MUST 具有 should_trigger、start_game、evaluate、get_closing_message 方法
