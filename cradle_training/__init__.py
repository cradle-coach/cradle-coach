"""
CradleCoach 训练游戏引擎 (cradle_training)

嵌入式执行功能训练游戏：
  - 反义词（反应抑制）
  - 倒序记忆（工作记忆）
  - 情绪猜谜（情绪识别）
  - 故事接龙（认知灵活性）

纯规则引擎 + REST API 封装。

API:
  POST /training/should_trigger { context, emotion } → { trigger, game_type }
  POST /training/start          { game_type, difficulty } → { instructions, prompt }
  POST /training/evaluate       { game_type, response, expected } → { correct, feedback }

Phase 5 实现。
"""
