"""沉默控制 + 对话流集成测试."""
import os
import sys
import time
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
_MINICPMO = _PROJECT_ROOT / "minicpmo-demo"
if str(_MINICPMO) not in sys.path:
    sys.path.insert(0, str(_MINICPMO))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import api_bridge_server as bridge  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_state():
    """Reset conversation state before each test."""
    bridge._silence_controller = None
    bridge._conversation_flow = None
    bridge.LAST_MESSAGE_TIME = 0.0
    bridge._init_conversation_control()


class TestSilenceDetection:
    """Verify silence timeout detection."""

    def test_no_silence_when_recent_message(self):
        """No trigger when message was just now."""
        bridge.LAST_MESSAGE_TIME = time.time()
        result = bridge._check_silence()
        assert result is None, "Should not trigger for recent message"

    def test_silence_triggers_after_timeout(self):
        """Trigger exit message after SILENCE_EXIT_SECONDS."""
        bridge.LAST_MESSAGE_TIME = time.time() - bridge.SILENCE_EXIT_SECONDS - 1
        result = bridge._check_silence()
        assert result is not None, "Should trigger exit message"
        assert "爸爸妈妈" in result, "Exit should include social guidance"

    def test_silence_not_triggered_without_controller(self):
        """No trigger when controller not initialized."""
        bridge._silence_controller = None
        result = bridge._check_silence()
        assert result is None

    def test_touch_message_time_updates_timestamp(self):
        """_touch_message_time must update LAST_MESSAGE_TIME."""
        bridge.LAST_MESSAGE_TIME = 0.0
        bridge._touch_message_time()
        assert bridge.LAST_MESSAGE_TIME > 0.0
        assert abs(bridge.LAST_MESSAGE_TIME - time.time()) < 1.0


class TestConversationFlow:
    """Verify conversation flow hint generation."""

    def test_force_statement_after_consecutive_questions(self):
        """After 2 consecutive questions, hint should force statement."""
        flow = bridge._conversation_flow
        assert flow is not None
        # Simulate 2 question responses from AI
        flow.on_user_response("你好吗？", True)
        flow.on_user_response("今天开心吗？", True)
        hint = bridge._get_conversation_hint()
        assert "陈述句" in hint, f"Should force statement, got: '{hint}'"

    def test_no_hint_on_first_question(self):
        """Single question should not trigger force statement."""
        flow = bridge._conversation_flow
        flow.on_user_response("你好吗？", True)
        hint = bridge._get_conversation_hint()
        assert "陈述句" not in hint, f"Single question should not force: '{hint}'"

    def test_no_hint_without_controller(self):
        """No hint when controller not initialized."""
        bridge._conversation_flow = None
        hint = bridge._get_conversation_hint()
        assert hint == ""


class TestModuleIntegration:
    """Verify all three modules coexist without conflicts."""

    def test_all_modules_initialized_together(self):
        """SafetyMiddleware + SilenceController + ConversationFlow coexist."""
        bridge._init_conversation_control()
        bridge._init_safety_middleware()
        assert bridge._safety_middleware is not None
        assert bridge._silence_controller is not None
        assert bridge._conversation_flow is not None

    def test_safety_and_silence_independent(self):
        """Safety check and silence check work independently."""
        bridge._init_safety_middleware()
        bridge._init_conversation_control()
        # Safety on normal text
        safe = bridge._check_safety("你好")
        assert safe == "你好"
        # Silence should not trigger on recent activity
        bridge._touch_message_time()
        assert bridge._check_silence() is None
