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

from cradle_training.antonyms import AntonymGame, AntonymResult
from cradle_training.reverse_memory import ReverseMemoryGame, ReverseMemoryResult
from cradle_training.emotion_guess import EmotionGuessGame, EmotionGuessResult
from cradle_training.story_chain import StoryChainGame, StoryChainResult
from cradle_training.training_manager import (
    TrainingManager,
    TrainingSession,
    TriggerResult,
)

__all__ = [
    "AntonymGame",
    "AntonymResult",
    "ReverseMemoryGame",
    "ReverseMemoryResult",
    "EmotionGuessGame",
    "EmotionGuessResult",
    "StoryChainGame",
    "StoryChainResult",
    "TrainingManager",
    "TrainingSession",
    "TriggerResult",
]
