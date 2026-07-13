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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
