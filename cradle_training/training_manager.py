"""
CradleCoach 训练管理器 (training_manager.py)

编排训练会话：触发判断、游戏调度、难度自适应、结束仪式。

法规依据：《暂行办法》第 10 条（不得以"替代社会交往"为服务目标）、
         第 19 条（退出管理）
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import re
import time
import random

from cradle_training.antonyms import AntonymGame
from cradle_training.reverse_memory import ReverseMemoryGame
from cradle_training.emotion_guess import EmotionGuessGame
from cradle_training.story_chain import StoryChainGame


@dataclass
class TriggerResult:
    """训练触发检查结果"""
    trigger: bool
    game_type: str = ""
    reason: str = ""


@dataclass
class TrainingSession:
    """训练会话状态"""
    active: bool = False
    start_time: float = 0.0
    total_rounds: int = 0
    correct: int = 0
    incorrect: int = 0
    recent_results: List[bool] = field(default_factory=list)  # 最近 5 轮
    last_game_type: str = ""


class TrainingManager:
    """训练管理器——编排训练会话"""

    # 会话参数
    SESSION_MAX_MINUTES = 15
    SESSION_MIN_MINUTES = 8
    MIN_TRAINING_INTERVAL = 300  # 两次训练间隔最短 5 分钟（秒）

    # 难度自适应
    DIFFICULTY_MIN = 1
    DIFFICULTY_MAX = 5
    DIFFICULTY_UP_THRESHOLD = 3     # 连续正确 N 次提升难度
    DIFFICULTY_DOWN_THRESHOLD = 2   # 连续错误 N 次降低难度

    # 需要暂停训练的情绪关键词
    NEGATIVE_EMOTIONS = [
        "sad", "angry", "frustrated", "upset", "tired",
        "难过", "生气", "沮丧", "烦恼", "疲惫",
    ]

    # 结束仪式模板
    CLOSING_MESSAGES = [
        "今天的练习到这里。{progress_summary}。你很努力！现在去找爸爸妈妈，给他们看看你今天做到的！",
        "练习完成啦！{progress_summary}。去跟爸爸妈妈分享一下你刚才的进步吧！",
        "时间到！{progress_summary}。我看到你今天很专注。去找爸爸妈妈聊聊你的练习吧。",
    ]

    # 努力导向的通用正面反馈
    EFFORT_FEEDBACK = [
        "我看到你很专注地完成了这个练习。",
        "你在认真思考，这很重要。",
        "你刚才做得很努力！",
        "每次练习都在进步，因为你很认真。",
        "你投入了很多注意力在这上面。",
    ]

    def __init__(self):
        self.session = TrainingSession()
        self.current_difficulty = 2
        self._last_training_time: float = 0.0
        self._last_prompt_word: str = ""
        self._games = {
            "antonyms": AntonymGame(),
            "reverse_memory": ReverseMemoryGame(),
            "emotion_guess": EmotionGuessGame(),
            "story_chain": StoryChainGame(),
        }

    # ── 触发判断 ─────────────────────────────────────

    def should_trigger(self, context: str, emotion: str) -> TriggerResult:
        """
        判断是否应触发训练游戏。

        Args:
            context: 对话上下文（如"开场问候完成"）
            emotion: 当前情绪状态

        Returns:
            TriggerResult: 是否触发 + 推荐游戏类型
        """
        # 情绪检查：负面情绪不触发（子串匹配）
        emotion_lower = emotion.lower()
        if any(neg.lower() in emotion_lower for neg in self.NEGATIVE_EMOTIONS):
            return TriggerResult(
                trigger=False,
                reason=f"情绪状态不适合训练: {emotion}",
            )

        # 间隔检查
        elapsed = time.monotonic() - self._last_training_time
        if elapsed < self.MIN_TRAINING_INTERVAL and self._last_training_time > 0:
            return TriggerResult(
                trigger=False,
                reason=f"距上次训练仅 {int(elapsed)}s，需至少间隔 {self.MIN_TRAINING_INTERVAL}s",
            )

        # 可选：基于上下文判断
        trigger_keywords = ["开始", "训练", "练习", "游戏", "准备好了", "玩"]
        if any(kw in context for kw in trigger_keywords):
            return TriggerResult(
                trigger=True,
                game_type=self._pick_game_type(),
                reason="用户表示准备好训练",
            )

        # 默认：可以触发（在合适的对话阶段）
        return TriggerResult(
            trigger=True,
            game_type=self._pick_game_type(),
            reason="训练间隔足够",
        )

    def _pick_game_type(self) -> str:
        """选择游戏类型（轮替策略）"""
        game_types = list(self._games.keys())
        # 避免连续两次同类型
        if self.session.last_game_type:
            others = [g for g in game_types if g != self.session.last_game_type]
            if others:
                return random.choice(others)
        return random.choice(game_types)

    # ── 游戏调度 ─────────────────────────────────────

    def start_game(self, game_type: str, difficulty: Optional[int] = None) -> Dict:
        """
        开始训练游戏。

        Args:
            game_type: 游戏类型 (antonyms/reverse_memory/emotion_guess/story_chain)
            difficulty: 难度等级，None 则使用当前难度

        Returns:
            {instructions, prompt, expected, game_type}
        """
        if game_type not in self._games:
            raise ValueError(f"未知游戏类型: {game_type}. 可用: {list(self._games.keys())}")

        diff = difficulty if difficulty is not None else self.current_difficulty
        game = self._games[game_type]

        if not self.session.active:
            self.start_session()
        elif self._session_expired():
            closing_msg = self.end_session()
            return {
                "instructions": closing_msg,
                "prompt": "",
                "expected": "",
                "game_type": game_type,
                "session_expired": True,
            }

        self.session.last_game_type = game_type

        if game_type == "antonyms":
            prompt, expected = game.generate_prompt(difficulty=diff)
            # 从 prompt 中提取题目词（最后一个「」中的词）
            _match = re.findall(r'「([^」]+)」', prompt)
            prompt_word = _match[-1] if _match else expected
            instructions = (
                f"我们来玩反义词游戏。我说一个词，你说它的反义词。"
                f"如果是水果的名字，就说这个词自己。准备好了吗？"
            )
            self._last_prompt_word = prompt_word
            return {
                "instructions": instructions,
                "prompt": prompt,
                "expected": expected,
                "prompt_word": prompt_word,
                "game_type": game_type,
            }
        elif game_type == "reverse_memory":
            seq = game.generate_sequence(difficulty=diff)
            words_str = "、".join(seq)
            prompt = f"请记住这些词：{words_str}"
            expected = seq
            instructions = (
                f"我来考考你的记忆力。我会说几个词，"
                f"听完后你要倒着说出来。准备好了吗？"
            )
        elif game_type == "emotion_guess":
            story_text, correct_emotion = game.select_story(difficulty=diff)
            prompt = story_text
            expected = correct_emotion
            instructions = (
                f"我们来猜情绪。我会讲一个小故事，"
                f"你猜猜故事里的人是什么情绪。准备好了吗？"
            )
        elif game_type == "story_chain":
            opening = game.generate_opening(difficulty=diff)
            prompt = opening
            expected = opening
            instructions = (
                f"我们来编故事。我开始讲一个故事，"
                f"你接着往下编。准备好了吗？"
            )
        else:
            raise ValueError(f"未知游戏类型: {game_type}")

        return {
            "instructions": instructions,
            "prompt": prompt,
            "expected": expected,
            "game_type": game_type,
        }

    def evaluate(self, game_type: str, response: Any, expected: Any) -> Dict:
        """
        评估训练回答。

        Args:
            game_type: 游戏类型
            response: 用户回答
            expected: 期望答案

        Returns:
            {correct, feedback, ...}
        """
        if game_type not in self._games:
            raise ValueError(f"未知游戏类型: {game_type}")

        game = self._games[game_type]

        if game_type == "antonyms":
            result = self._evaluate_antonym(response, expected)
        elif game_type == "reverse_memory":
            result = game.evaluate(response, expected)
        elif game_type == "emotion_guess":
            result = game.evaluate(response, expected)
        elif game_type == "story_chain":
            result = game.evaluate(
                response, expected, difficulty=self.current_difficulty
            )
        else:
            raise ValueError(f"未知游戏类型: {game_type}")

        # 记录结果
        is_correct = (
            result.correct
            if hasattr(result, "correct")
            else result.passed
        )
        self.record_result(correct=is_correct)

        # 构建返回字典
        output = {
            "correct": is_correct,
            "feedback": self._build_feedback(correct=is_correct, game_type=game_type),
            "game_feedback": result.feedback,
            "game_type": game_type,
        }
        if hasattr(result, "length_score"):
            output["length_score"] = result.length_score
        if hasattr(result, "coherence_score"):
            output["coherence_score"] = result.coherence_score

        return output

    def _evaluate_antonym(self, user_response: str, expected: str) -> Any:
        """评估反义词。使用存储的 _last_prompt_word。"""
        game = self._games["antonyms"]
        prompt_word = getattr(self, "_last_prompt_word", expected)
        return game.evaluate(prompt_word, expected, user_response)

    # ── 会话管理 ─────────────────────────────────────

    def start_session(self):
        """开始训练会话"""
        self.session = TrainingSession(
            active=True,
            start_time=time.monotonic(),
        )
        self._last_training_time = time.monotonic()

    def end_session(self) -> str:
        """结束训练会话，返回结束语"""
        self.session.active = False
        return self.get_closing_message()

    def record_result(self, correct: bool):
        """记录单轮结果"""
        self.session.total_rounds += 1
        if correct:
            self.session.correct += 1
        else:
            self.session.incorrect += 1

        self.session.recent_results.append(correct)
        if len(self.session.recent_results) > 5:
            self.session.recent_results = self.session.recent_results[-5:]

    def get_session_stats(self) -> Dict:
        """获取会话统计"""
        return {
            "total_rounds": self.session.total_rounds,
            "correct": self.session.correct,
            "incorrect": self.session.incorrect,
            "accuracy": (
                self.session.correct / max(1, self.session.total_rounds)
            ),
            "active": self.session.active,
        }

    # ── 难度自适应 ─────────────────────────────────────

    def adapt_difficulty(self) -> int:
        """
        基于最近表现调整难度。

        最近 N 轮全部正确 → 升难度
        最近 N 轮全部错误 → 降难度

        Returns:
            调整后的难度等级
        """
        recent = self.session.recent_results

        if len(recent) >= self.DIFFICULTY_UP_THRESHOLD:
            # 检查是否连续正确
            last_n = recent[-self.DIFFICULTY_UP_THRESHOLD:]
            if all(last_n):
                self.current_difficulty = min(
                    self.DIFFICULTY_MAX,
                    self.current_difficulty + 1
                )

        if len(recent) >= self.DIFFICULTY_DOWN_THRESHOLD:
            # 检查是否连续错误
            last_n = recent[-self.DIFFICULTY_DOWN_THRESHOLD:]
            if not any(last_n):  # 全部错误
                self.current_difficulty = max(
                    self.DIFFICULTY_MIN,
                    self.current_difficulty - 1
                )

        return self.current_difficulty

    # ── 结束仪式 ─────────────────────────────────────

    def get_closing_message(self, progress_summary: str = "") -> str:
        """
        生成训练结束语（含社交引导）。

        Args:
            progress_summary: 训练进展摘要

        Returns:
            结束仪式文本
        """
        template = random.choice(self.CLOSING_MESSAGES)
        if not progress_summary:
            stats = self.get_session_stats()
            progress_summary = (
                f"我们练习了 {stats['total_rounds']} 轮，"
                f"做对了 {stats['correct']} 个"
            )
        return template.format(progress_summary=progress_summary)

    def _build_feedback(self, correct: bool, game_type: str) -> str:
        """构建训练反馈文本"""
        if correct:
            return random.choice(self.EFFORT_FEEDBACK)
        else:
            return "没关系，每次练习都在进步。我们再试一次。"

    def _session_expired(self) -> bool:
        """检查会话是否超过最大时长"""
        if not self.session.active:
            return False
        elapsed_minutes = (time.monotonic() - self.session.start_time) / 60
        return elapsed_minutes >= self.SESSION_MAX_MINUTES

    def get_available_game_types(self) -> List[str]:
        """返回可用游戏类型列表"""
        return list(self._games.keys())
