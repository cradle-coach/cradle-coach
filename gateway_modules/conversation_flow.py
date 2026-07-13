"""
CradleCoach 对话流管理器 (conversation_flow.py)

管理对话节奏和训练难度自适应。
  - 追问计数限制——连续疑问句过多时强制陈述句
  - 问题难度自适应——无回应时降级问题
  - 话题跳跃检测——不强制拉回旧话题
  - 情绪降级——检测到负面情绪时暂停追问
"""

from dataclasses import dataclass, field
from typing import List, Optional
from collections import deque


@dataclass
class ConversationState:
    """对话状态"""
    question_count: int = 0          # 连续疑问句计数
    no_response_count: int = 0       # 连续无回应计数
    current_difficulty: int = 2      # 难度等级 1-5
    last_topic: str = ""            # 上一个话题
    emotion_downgraded: bool = False  # 是否因情绪降级


class ConversationFlow:
    """对话流管理"""

    MAX_CONSECUTIVE_QUESTIONS = 2     # 最多连续疑问句
    NO_RESPONSE_DOWNGRADE = 2         # 连续 N 次无回应后降级难度

    # 中文疑问句标志
    QUESTION_MARKERS = ["吗", "呢", "吧", "？", "什么", "怎么", "哪个"]

    def __init__(self):
        self.state = ConversationState()

    def is_question(self, text: str) -> bool:
        """检测是否为疑问句"""
        return any(marker in text for marker in self.QUESTION_MARKERS)

    def should_force_statement(self) -> bool:
        """是否需要强制下一轮为陈述句"""
        return self.state.question_count >= self.MAX_CONSECUTIVE_QUESTIONS

    def get_difficulty_hint(self) -> Optional[str]:
        """获取难度调整的 Prompt hint"""
        if self.state.no_response_count >= self.NO_RESPONSE_DOWNGRADE:
            old = self.state.current_difficulty
            self.state.current_difficulty = max(1, self.state.current_difficulty - 1)
            self.state.no_response_count = 0
            return f"[DIFFICULTY: {old} → {self.state.current_difficulty}]"
        return None

    def on_user_response(self, text: str, is_valid_response: bool):
        """用户回应后更新状态"""
        if is_valid_response:
            self.state.no_response_count = 0
            self.state.question_count = (
                self.state.question_count + 1 if self.is_question(text) else 0
            )
        else:
            self.state.no_response_count += 1

    def on_emotion_downgrade(self):
        """情绪降级——暂停追问和训练"""
        self.state.emotion_downgraded = True
        self.state.question_count = 0

    def on_emotion_recovered(self):
        """情绪恢复"""
        self.state.emotion_downgraded = False
