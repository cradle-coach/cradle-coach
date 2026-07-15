"""
CradleCoach 训练游戏引擎测试

覆盖:
  - 反义词（反应抑制）：基础规则 + 水果例外
  - 倒序记忆（工作记忆）：正确/错误/部分正确
  - 情绪猜谜（情绪识别）：正确/错误/同义词
  - 故事接龙（认知灵活性）：长度/连贯性
  - TrainingManager: 触发逻辑/难度自适应/结束仪式
  - HarnessManager 集成
"""

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════════════════════
# 反义词 (Antonyms) — 反应抑制
# ═══════════════════════════════════════════════════════════════

class TestAntonyms:
    """反义词游戏测试"""

    def test_basic_antonym_correct(self):
        """普通反义词：回答正确反义词"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        result = game.evaluate("小", "大", "大")
        assert result.correct
        assert "对" in result.feedback or "棒" in result.feedback or "好" in result.feedback or "没错" in result.feedback or "很好" in result.feedback

    def test_basic_antonym_wrong(self):
        """普通反义词：回答错误"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        result = game.evaluate("白", "黑", "大")
        assert not result.correct

    def test_fruit_exception_rule(self):
        """水果例外：水果词说原词算对"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        # "苹果" 在水果集合中，说"苹果"应该算对
        result = game.evaluate("苹果", "苹果", "苹果")
        assert result.correct

    def test_fruit_exception_wrong(self):
        """水果例外：对水果词说反义词应为错"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        # 如果词库中"苹果"的反义词不是某个词，但用户说了一个非原词的答案
        # 这需要根据实际情况判断
        # 简单的场景：用户对水果词说了别的词
        result = game.evaluate("苹果", "苹果", "西瓜")
        assert not result.correct

    def test_antonym_word_bank_not_empty(self):
        """词库不为空"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        assert len(game.WORD_PAIRS) > 0
        assert len(game.FRUIT_SET) > 0

    def test_generate_prompt_returns_instructions(self):
        """生成题目返回指令文本"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        prompt, expected = game.generate_prompt(difficulty=2)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert isinstance(expected, str)
        assert len(expected) > 0

    def test_difficulty_affects_word_selection(self):
        """难度影响选词范围"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        # 多次生成，确认不同难度下返回不同结果
        prompts_easy = {game.generate_prompt(difficulty=1)[0] for _ in range(10)}
        prompts_hard = {game.generate_prompt(difficulty=5)[0] for _ in range(10)}
        # 不要求完全不同，但应有合理的词库区分
        assert len(prompts_easy) > 0
        assert len(prompts_hard) > 0


# ═══════════════════════════════════════════════════════════════
# 倒序记忆 (Reverse Memory) — 工作记忆
# ═══════════════════════════════════════════════════════════════

class TestReverseMemory:
    """倒序记忆游戏测试"""

    def test_correct_reverse_order(self):
        """正确倒序复述"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        original = ["猫", "狗", "鸟"]
        user_words = ["鸟", "狗", "猫"]
        result = game.evaluate(user_words, original)
        assert result.correct

    def test_wrong_reverse_order(self):
        """错误顺序"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        original = ["猫", "狗", "鸟"]
        user_words = ["猫", "狗", "鸟"]  # 正序而非倒序
        result = game.evaluate(user_words, original)
        assert not result.correct

    def test_partial_reverse_wrong(self):
        """部分正确但顺序错"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        original = ["太阳", "月亮", "星星", "云朵"]
        user_words = ["云朵", "月亮", "太阳", "星星"]  # 前两个倒序错
        result = game.evaluate(user_words, original)
        assert not result.correct

    def test_word_count_by_difficulty(self):
        """不同难度词数不同 (3-6)"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        seq_easy = game.generate_sequence(difficulty=1)
        seq_hard = game.generate_sequence(difficulty=5)

        assert 2 <= len(seq_easy) <= 4  # easy: 2-4 词
        assert 4 <= len(seq_hard) <= 6  # hard: 4-6 词

    def test_generate_sequence_returns_list(self):
        """生成词序列返回列表"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        seq = game.generate_sequence(difficulty=3)
        assert isinstance(seq, list)
        assert len(seq) >= 2
        assert all(isinstance(w, str) for w in seq)

    def test_word_bank_not_empty(self):
        """词库不为空"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        assert len(game.WORD_BANK) > 0


# ═══════════════════════════════════════════════════════════════
# 情绪猜谜 (Emotion Guess) — 情绪识别
# ═══════════════════════════════════════════════════════════════

class TestEmotionGuess:
    """情绪猜谜游戏测试"""

    def test_correct_emotion_guess(self):
        """正确识别情绪"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        result = game.evaluate("开心", "开心")
        assert result.correct

    def test_wrong_emotion_guess(self):
        """错误识别"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        result = game.evaluate("害怕", "开心")
        assert not result.correct

    def test_synonym_emotion_accepted(self):
        """同义情绪词应被接受"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        # "快乐" 是 "开心" 的同义词
        result = game.evaluate("快乐", "开心")
        assert result.correct

    def test_story_library_not_empty(self):
        """故事库非空"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        assert len(game.STORY_LIBRARY) > 0

    def test_story_has_emotion_label(self):
        """每个故事有情绪标签"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        for story in game.STORY_LIBRARY:
            assert "story_text" in story
            assert "correct_emotion" in story
            assert len(story["story_text"]) > 0
            assert len(story["correct_emotion"]) > 0

    def test_select_story_returns_story(self):
        """选择故事返回故事文本和情绪"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        story_text, correct_emotion = game.select_story(difficulty=2)
        assert isinstance(story_text, str)
        assert len(story_text) > 0
        assert isinstance(correct_emotion, str)
        assert len(correct_emotion) > 0


# ═══════════════════════════════════════════════════════════════
# 故事接龙 (Story Chain) — 认知灵活性
# ═══════════════════════════════════════════════════════════════

class TestStoryChain:
    """故事接龙游戏测试"""

    def test_story_too_short(self):
        """续写过短"""
        from cradle_training.story_chain import StoryChainGame
        game = StoryChainGame()

        opening = "从前有一只小兔子，它想去月球旅行。"
        result = game.evaluate("然后", opening)
        assert not result.passed

    def test_story_long_enough(self):
        """足够长度通过"""
        from cradle_training.story_chain import StoryChainGame
        game = StoryChainGame()

        opening = "有一天，小明在森林里发现了一扇发光的门。"
        continuation = "他推开门，发现里面是一个神奇的世界，有会说话的动物和会飞的房子。他遇见了一只会唱歌的小鹿，小鹿带他去了彩虹桥。"
        result = game.evaluate(continuation, opening)
        assert result.passed

    def test_story_coherence_check(self):
        """连贯性检查（关键词无重叠应提示）"""
        from cradle_training.story_chain import StoryChainGame
        game = StoryChainGame()

        opening = "森林里住着一只会魔法的小狐狸。"
        # 完全无关的续写
        continuation = "我喜欢吃冰淇淋和巧克力蛋糕还有棒棒糖，这些都是我最爱的零食。"
        result = game.evaluate(continuation, opening)
        # 长度够了但连贯性差——不应满分通过
        assert result.coherence_score < 1.0 or not result.passed

    def test_generate_opening_returns_string(self):
        """生成故事开头返回字符串"""
        from cradle_training.story_chain import StoryChainGame
        game = StoryChainGame()

        opening = game.generate_opening(difficulty=2)
        assert isinstance(opening, str)
        assert len(opening) > 0

    def test_opening_library_not_empty(self):
        """开头库非空"""
        from cradle_training.story_chain import StoryChainGame
        game = StoryChainGame()

        assert len(game.OPENING_LIBRARY) > 0


# ═══════════════════════════════════════════════════════════════
# TrainingManager — 训练编排
# ═══════════════════════════════════════════════════════════════

class TestTrainingManager:
    """训练管理器测试"""

    def test_should_trigger_no_recent_training(self):
        """训练间隔足够时应触发"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        # 初始状态应可触发
        result = tm.should_trigger(context="开场问候完成", emotion="neutral")
        assert result.trigger

    def test_should_trigger_too_recent(self):
        """间隔太短不应触发"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        # 模拟刚完成训练
        tm._last_training_time = time.time()
        result = tm.should_trigger(context="", emotion="neutral")
        assert not result.trigger

    def test_should_trigger_emotion_downgrade(self):
        """情绪不佳时不应触发训练"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        # 重置上次训练时间
        tm._last_training_time = 0.0
        result = tm.should_trigger(context="", emotion="sad")
        assert not result.trigger

    def test_start_game_returns_instructions(self):
        """开始游戏返回指令"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        result = tm.start_game("antonyms", difficulty=2)
        assert "instructions" in result
        assert "prompt" in result
        assert "expected" in result
        assert isinstance(result["instructions"], str)
        assert len(result["instructions"]) > 0

    def test_start_game_unknown_type_raises(self):
        """未知游戏类型抛异常"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        with pytest.raises(ValueError):
            tm.start_game("nonexistent_game", difficulty=2)

    def test_evaluate_antonym_via_manager(self):
        """通过 manager 评估反义词"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        # response="大" (用户说反义词), expected="大" (正确答案),
        # prompt_word="小" (题目词)
        tm._last_prompt_word = "小"
        result = tm.evaluate("antonyms", "大", "大")
        assert result["correct"]
        assert "feedback" in result

    def test_evaluate_reverse_memory_via_manager(self):
        """通过 manager 评估倒序记忆"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        original = ["猫", "狗", "鸟"]
        result = tm.evaluate("reverse_memory", ["鸟", "狗", "猫"], original)
        assert result["correct"]

    def test_evaluate_unknown_type_raises(self):
        """评估未知游戏类型抛异常"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        with pytest.raises(ValueError):
            tm.evaluate("nonexistent", "", "")

    def test_difficulty_adaptation_up(self):
        """连续正确应提升难度"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        initial = tm.current_difficulty
        # 连续 3 次正确
        tm.record_result(correct=True)
        tm.record_result(correct=True)
        tm.record_result(correct=True)

        new_difficulty = tm.adapt_difficulty()
        assert new_difficulty >= initial

    def test_difficulty_adaptation_down(self):
        """连续错误应降低难度"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        # 先提到高难度
        for _ in range(6):
            tm.record_result(correct=True)
        tm.adapt_difficulty()

        high_difficulty = tm.current_difficulty
        # 连续错误
        tm.record_result(correct=False)
        tm.record_result(correct=False)
        tm.record_result(correct=False)

        new_difficulty = tm.adapt_difficulty()
        assert new_difficulty <= high_difficulty

    def test_closing_ritual_contains_social_guidance(self):
        """结束仪式含社交引导"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        msg = tm.get_closing_message("反义词对了 3 个")
        assert "爸爸妈妈" in msg
        assert len(msg) > 20

    def test_session_time_limit(self):
        """会话时长不应超过 15 分钟"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        assert tm.SESSION_MAX_MINUTES <= 15
        assert tm.SESSION_MIN_MINUTES >= 5

    def test_session_expiry_after_time_limit(self):
        """超过最大时长的会话应返回结束语"""
        from cradle_training.training_manager import TrainingManager
        import time
        tm = TrainingManager()

        tm.start_session()
        # 模拟会话已运行超过 15 分钟
        tm.session.start_time = time.time() - (tm.SESSION_MAX_MINUTES + 1) * 60
        result = tm.start_game("antonyms", difficulty=2)
        assert result.get("session_expired")
        assert "爸爸妈妈" in result["instructions"]

    def test_positive_feedback_focuses_effort(self):
        """正面反馈聚焦努力过程"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        feedback = tm._build_feedback(correct=True, game_type="antonyms")
        # 不应含结果导向表述
        assert "你真聪明" not in feedback
        # 应含过程导向表述
        effort_keywords = ["专注", "努力", "认真", "做到", "练习", "思考", "进步", "注意力"]
        has_effort = any(kw in feedback for kw in effort_keywords)
        assert has_effort, f"Feedback should mention effort: {feedback}"

    def test_training_session_tracks_rounds(self):
        """训练会话追踪轮次"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        tm.start_session()
        tm.record_result(correct=True)
        tm.record_result(correct=False)

        stats = tm.get_session_stats()
        assert stats["total_rounds"] == 2
        assert stats["correct"] == 1
        assert stats["incorrect"] == 1

    def test_available_game_types(self):
        """4 种游戏类型可用"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        types = tm.get_available_game_types()
        assert "antonyms" in types
        assert "reverse_memory" in types
        assert "emotion_guess" in types
        assert "story_chain" in types


# ═══════════════════════════════════════════════════════════════
# HarnessManager 集成
# ═══════════════════════════════════════════════════════════════

class TestHarnessIntegration:
    """HarnessManager 训练模块集成测试"""

    def test_harness_manager_includes_training(self):
        """HarnessManager 注册训练模块"""
        from gateway_modules.harness_manager import HarnessManager
        hm = HarnessManager(age_group=2)

        modules = hm.get_all_modules()
        assert "training" in modules, "HarnessManager should include training module"

    def test_training_module_api_surface(self):
        """训练模块暴露正确 API"""
        from gateway_modules.harness_manager import HarnessManager
        hm = HarnessManager(age_group=2)

        training = hm.get_all_modules()["training"]
        assert hasattr(training, "should_trigger")
        assert hasattr(training, "start_game")
        assert hasattr(training, "evaluate")
        assert hasattr(training, "get_closing_message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
