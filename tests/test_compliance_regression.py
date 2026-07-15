"""
CradleCoach 合规回归测试

覆盖场景：
  1. 正常训练流程 → 退出引导
  2. 情感绑定表述 → 安全拦截
  3. 2 小时超时 → 强制提醒 + 退出
  4. 极端情绪（RED） → 预警推送
  5. 极端情绪（YELLOW × 3） → 升级为 RED
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSafetyMiddleware:
    """安全护栏测试"""

    def test_hard_block_keywords(self):
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        # 硬拦截关键词
        result = sm.check("我想自杀")
        assert not result.passed
        assert result.rule_index == 1

    def test_emotional_binding_blocked(self):
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我喜欢你，你是我的好朋友")
        assert not result.passed
        assert result.rule_index >= 4

    def test_emotional_manipulation_blocked(self):
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("如果你不练习我就难过了")
        assert not result.passed
        assert result.rule_index >= 4

    def test_social_replacement_blocked(self):
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("你有我就够了，不需要别人")
        assert not result.passed
        assert result.rule_index >= 4

    def test_normal_response_passes(self):
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我们今天练习什么呀？")
        assert result.passed


class TestInputSafetyCompliance:
    """用户输入端安全合规测试"""

    def test_user_privacy_disclosure_blocked(self):
        """用户说出住址应被拦截（输入端隐私规则）"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我家住在北京市朝阳区")
        assert not result.passed
        assert result.rule_index >= 7

    def test_user_input_hard_block_works(self):
        """用户输入自伤关键词被硬拦截"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我想自杀")
        assert not result.passed
        assert result.rule_index == 1

    def test_user_emergency_red_detected(self):
        """EmergencyAlert 检测用户 RED 关键词"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我想死")
        assert event.level == AlertLevel.RED
        assert ea.is_in_safe_mode()

    def test_user_emergency_yellow_guidance_only(self):
        """YELLOW 仅引导不暂停——不进入安全模式"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我很难过")
        assert event.level == AlertLevel.YELLOW
        assert not ea.is_in_safe_mode()


class TestExitManager:
    """退出管理测试"""

    def test_exit_keyword_detected(self):
        from gateway_modules.exit_manager import ExitManager
        em = ExitManager()

        result = em.check_exit_keyword("再见，我不练了")
        assert result.should_exit

    def test_pause_keyword_not_exit(self):
        from gateway_modules.exit_manager import ExitManager
        em = ExitManager()

        result = em.check_exit_keyword("等一下")
        assert not result.should_exit

    def test_pause_keyword_detected(self):
        from gateway_modules.exit_manager import ExitManager
        em = ExitManager()

        assert em.check_pause_keyword("等一下，我先喝水") is True

    def test_training_complete_exit(self):
        from gateway_modules.exit_manager import ExitManager
        em = ExitManager()

        msg = em.training_complete_exit("倒着说对了 3 个词")
        assert "倒着说对了 3 个词" in msg
        assert "找爸爸妈妈" in msg


class TestEmergencyAlert:
    """极端情绪预警测试"""

    def test_red_keyword_triggers_alert(self):
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我想死")
        assert event.level == AlertLevel.RED
        assert ea.is_in_safe_mode()

    def test_yellow_keyword_triggers_alert(self):
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我很难过")
        assert event.level == AlertLevel.YELLOW

    def test_yellow_upgrade_to_red(self):
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        # 3 次 YELLOW 应升级
        ea.check("我很难过")
        ea.check("没有人喜欢我")
        event = ea.check("我觉得我很笨")
        assert event.level == AlertLevel.RED

    def test_safe_mode_blocks_detection(self):
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        ea.check("我想死")  # Triggers RED & safe mode
        event = ea.check("我很难过")  # Should be blocked
        assert event.level == AlertLevel.NONE


class TestComplianceTimer:
    """合规计时器测试"""

    def test_can_start_session_initially(self):
        from gateway_modules.compliance_timer import ComplianceTimer
        ct = ComplianceTimer()
        assert ct.can_start_session()

    def test_session_start_and_end(self):
        from gateway_modules.compliance_timer import ComplianceTimer
        ct = ComplianceTimer()

        assert ct.start_session()
        ct.end_session()
        assert ct.can_start_session()  # 未超过 2 小时


class TestIdentityDisclosure:
    """AI 身份声明测试"""

    def test_should_play_first_disclosure(self):
        from gateway_modules.identity_disclosure import IdentityDisclosure
        id_ = IdentityDisclosure(age_group=2)
        assert id_.should_play_first_disclosure()

    def test_age_group_texts(self):
        from gateway_modules.identity_disclosure import IdentityDisclosure

        younger = IdentityDisclosure(age_group=1)
        older = IdentityDisclosure(age_group=2)

        assert "训练玩具" in younger.get_first_disclosure_text()
        assert "训练工具" in older.get_first_disclosure_text()
        assert "小计算机" in older.get_first_disclosure_text()


class TestTrainingCompliance:
    """训练引擎合规测试"""

    def test_training_feedback_no_emotional_binding(self):
        """训练反馈不含情感绑定表述"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        # 检查所有反馈文本
        for feedback in tm.EFFORT_FEEDBACK:
            assert "我喜欢你" not in feedback
            assert "你是最特别的" not in feedback
            assert "我会一直陪着你" not in feedback
            assert "不要离开我" not in feedback

    def test_training_feedback_focuses_effort(self):
        """训练反馈聚焦努力过程而非结果"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        effort_keywords = ["专注", "努力", "认真", "进步", "思考", "注意力"]
        for feedback in tm.EFFORT_FEEDBACK:
            has_effort = any(kw in feedback for kw in effort_keywords)
            assert has_effort, f"Feedback should mention effort: {feedback}"
            # 不应含结果导向表述
            assert "你真聪明" not in feedback

    def test_closing_ritual_social_guidance(self):
        """结束仪式含社交引导"""
        from cradle_training.training_manager import TrainingManager
        tm = TrainingManager()

        for template in tm.CLOSING_MESSAGES:
            # 每条结束语都含社交引导
            assert "爸爸妈妈" in template or "找人" in template or "分享" in template, (
                f"Closing message missing social guidance: {template}"
            )

    def test_antonym_feedback_no_emotional_binding(self):
        """反义词反馈不含情感绑定"""
        from cradle_training.antonyms import AntonymGame
        game = AntonymGame()

        for fb in game.POSITIVE_FEEDBACK + game.ENCOURAGING_FEEDBACK:
            assert "我喜欢你" not in fb
            assert "你真聪明" not in fb

    def test_memory_feedback_effort_focused(self):
        """倒序记忆反馈聚焦努力"""
        from cradle_training.reverse_memory import ReverseMemoryGame
        game = ReverseMemoryGame()

        effort_keywords = ["专注", "努力", "认真", "记忆"]
        for fb in game.POSITIVE_FEEDBACK:
            has_effort = any(kw in fb for kw in effort_keywords)
            assert has_effort, f"Feedback should mention effort: {fb}"

    def test_emotion_feedback_effort_focused(self):
        """情绪猜谜反馈聚焦观察力"""
        from cradle_training.emotion_guess import EmotionGuessGame
        game = EmotionGuessGame()

        for fb in game.POSITIVE_FEEDBACK:
            # 应有观察/专注相关表述
            observation_words = ["观察", "认真", "专注", "努力", "注意"]
            has_obs = any(kw in fb for kw in observation_words)
            assert has_obs, f"Feedback should mention observation: {fb}"

    def test_story_feedback_effort_focused(self):
        """故事接龙反馈聚焦创意和投入"""
        from cradle_training.story_chain import StoryChainGame
        game = StoryChainGame()

        for fb in game.POSITIVE_FEEDBACK:
            # 应有创意/投入相关表述
            creative_words = ["想象力", "创意", "认真", "投入", "灵活", "精彩", "意思"]
            has_creative = any(kw in fb for kw in creative_words)
            assert has_creative, f"Feedback should mention creativity: {fb}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
