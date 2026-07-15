"""退出管理 + 可观测性集成测试."""
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
    bridge._exit_manager = None
    bridge._observability = None
    bridge._init_exit_and_observability()


class TestExitManagerIntegration:
    """Verify ExitManager keyword detection in API Bridge context."""

    def test_exit_keyword_detected(self):
        """Exit keywords MUST trigger should_exit."""
        em = bridge._exit_manager
        assert em is not None
        result = em.check_exit_keyword("再见")
        assert result.should_exit
        assert "爸爸妈妈" in result.exit_message

    def test_pause_keyword_not_exit(self):
        """Pause keywords should NOT trigger exit."""
        em = bridge._exit_manager
        result = em.check_exit_keyword("等一下")
        assert not result.should_exit

    def test_normal_text_not_exit(self):
        """Normal text should not trigger exit."""
        em = bridge._exit_manager
        result = em.check_exit_keyword("我们来玩反义词游戏吧")
        assert not result.should_exit

    def test_mark_activity_updates_timestamp(self):
        """mark_activity MUST update last_activity."""
        em = bridge._exit_manager
        em.last_activity = 0.0
        em.mark_activity()
        assert em.last_activity > 0

    def test_inactivity_detection(self):
        """30min inactivity must be detectable."""
        em = bridge._exit_manager
        em.last_activity = time.time() - em.INACTIVITY_SLEEP_TIMEOUT - 1
        assert em.is_inactivity_timeout()

    def test_post_exit_silence(self):
        """After exit, must be in silence period."""
        em = bridge._exit_manager
        em.mark_exited()
        assert em.is_in_post_exit_silence()


class TestObservabilityIntegration:
    """Verify Observability initialized in API Bridge context."""

    def test_observability_initialized(self):
        """Observability must be available after init."""
        obs = bridge._observability
        assert obs is not None

    def test_log_dirs_created(self):
        """Log directories must exist after init."""
        log_base = Path("harness_logs")
        assert log_base.exists()
        for subdir in ["safety_intercepts", "silence_control",
                       "conversation_flow", "sessions"]:
            assert (log_base / subdir).exists(), f"Missing: {subdir}"
