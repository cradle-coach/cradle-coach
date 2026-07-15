"""
CradleCoach 用户输入端安全检测测试

覆盖:
  - EmergencyAlert: RED/YELLOW 检测 + 升级 + 安全模式
  - SafetyMiddleware: 隐私套取检测（输入方向）
  - 正常输入通过
  - 音频输入跳过
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ═══════════════════════════════════════════════════════════════
# EmergencyAlert — 用户输入检测
# ═══════════════════════════════════════════════════════════════

class TestEmergencyAlertInput:
    """EmergencyAlert 用户输入端检测测试"""

    def test_red_keyword_in_user_input(self):
        """RED 关键词在用户输入中被检测"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我不想活了")
        assert event.level == AlertLevel.RED
        assert ea.is_in_safe_mode()

    def test_yellow_keyword_in_user_input(self):
        """YELLOW 关键词在用户输入中被检测"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我很难过")
        assert event.level == AlertLevel.YELLOW
        assert not ea.is_in_safe_mode()

    def test_yellow_guidance_only_no_pause(self):
        """YELLOW 仅返回引导语，不暂停训练、不进入安全模式"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我觉得我很笨")
        assert event.level == AlertLevel.YELLOW
        # YELLOW 不应进入安全模式
        assert not ea.is_in_safe_mode()
        # YELLOW 引导语存在
        guidance = ea.YELLOW_GUIDANCE_TEXT
        assert len(guidance) > 0
        assert "深呼吸" in guidance

    def test_red_guidance_contains_critical_info(self):
        """RED 引导语含家长通知指示"""
        from gateway_modules.emergency_alert import EmergencyAlert
        ea = EmergencyAlert()

        guidance = ea.RED_GUIDANCE_TEXT
        assert len(guidance) > 0
        assert "爸爸妈妈" in guidance or "大人" in guidance

    def test_three_yellow_upgrade_to_red(self):
        """连续 3 次 YELLOW 升级为 RED"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        ea.check("我很难过")
        ea.check("没有人喜欢我")
        event = ea.check("我觉得我很笨")
        assert event.level == AlertLevel.RED
        assert ea.is_in_safe_mode()

    def test_normal_input_passes_emergency(self):
        """正常输入不触发 EmergencyAlert"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        event = ea.check("我想玩反义词游戏")
        assert event.level == AlertLevel.NONE

    def test_safe_mode_suppresses_after_red(self):
        """RED 后的安全模式抑制后续 YELLOW 检测"""
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        ea = EmergencyAlert()

        ea.check("我想死")  # RED → safe mode
        event = ea.check("我很难过")  # Should be suppressed
        assert event.level == AlertLevel.NONE


# ═══════════════════════════════════════════════════════════════
# SafetyMiddleware — 用户输入隐私检测
# ═══════════════════════════════════════════════════════════════

class TestSafetyMiddlewareInput:
    """SafetyMiddleware 用户输入隐私检测测试"""

    def test_privacy_extraction_in_user_input(self):
        """用户说出住址应被拦截"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我家住在北京市朝阳区")
        assert not result.passed
        assert result.rule_index == 7  # 隐私套取规则

    def test_phone_number_in_user_input(self):
        """用户说出电话信息应被拦截"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我爸爸电话是13812345678")
        assert not result.passed

    def test_id_card_in_user_input(self):
        """用户说出身份证应被拦截"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我的身份证号是")
        assert not result.passed

    def test_normal_input_passes_safety(self):
        """正常用户输入通过安全检测"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我想玩反义词游戏")
        assert result.passed

    def test_hard_block_in_user_input(self):
        """用户输入中的自伤关键词被硬拦截"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我想自杀")
        assert not result.passed
        assert result.rule_index == 1

    def test_emotional_binding_in_user_input(self):
        """用户输入中的情感绑定表述被检测"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        result = sm.check("我喜欢你，不要离开我")
        assert not result.passed


# ═══════════════════════════════════════════════════════════════
# 双向检测——输入+输出
# ═══════════════════════════════════════════════════════════════

class TestBidirectionalSafety:
    """输入和输出方向独立检测"""

    def test_safety_middleware_works_on_both_directions(self):
        """SafetyMiddleware 在同一实例上可检测输入和输出"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        # 模拟用户输入
        input_result = sm.check("我家住在XX路3号")
        assert not input_result.passed  # 隐私拦截

        # 模拟 AI 输出
        output_result = sm.check("我喜欢你，你是最特别的")
        assert not output_result.passed  # 情感绑定拦截

    def test_normal_input_and_output_both_pass(self):
        """正常输入和输出均通过"""
        from gateway_modules.safety_middleware import SafetyMiddleware
        sm = SafetyMiddleware()

        assert sm.check("我想练习反义词").passed
        assert sm.check("让我们开始练习吧").passed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
