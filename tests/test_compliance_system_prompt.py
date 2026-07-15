"""System Prompt 合规检测 — 验证加载和注入逻辑."""
import os
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parent.parent
_MINICPMO = _PROJECT_ROOT / "minicpmo-demo"
if str(_MINICPMO) not in sys.path:
    sys.path.insert(0, str(_MINICPMO))

import api_bridge_server as bridge  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_cached_sp():
    bridge._SYSTEM_PROMPT = None


YAML = str(_PROJECT_ROOT / "config" / "cradlecoach_system_prompt.yaml")


class TestSystemPromptLoading:
    def test_load_from_yaml(self):
        if not os.path.exists(YAML):
            pytest.skip("YAML not found")
        bridge._load_system_prompt(YAML)
        assert bridge._SYSTEM_PROMPT is not None
        assert len(bridge._SYSTEM_PROMPT) > 100
        assert "CradleCoach" in bridge._SYSTEM_PROMPT

    def test_load_nonexistent(self):
        bridge._SYSTEM_PROMPT = "old"
        bridge._load_system_prompt("/nonexistent/path.yaml")
        assert bridge._SYSTEM_PROMPT == "old"  # unchanged on error

    def test_load_none_path(self):
        bridge._SYSTEM_PROMPT = "old"
        bridge._load_system_prompt(None)
        assert bridge._SYSTEM_PROMPT == "old"  # unchanged on None


class TestSystemPromptInjection:
    def test_inject_when_missing(self):
        if not os.path.exists(YAML):
            pytest.skip("YAML not found")
        bridge._load_system_prompt(YAML)
        result = bridge._inject_system_prompt({})
        assert "system_prompt" in result
        assert result["system_prompt"] == bridge._SYSTEM_PROMPT

    def test_no_overwrite_existing(self):
        if not os.path.exists(YAML):
            pytest.skip("YAML not found")
        bridge._load_system_prompt(YAML)
        result = bridge._inject_system_prompt({"system_prompt": "custom"})
        assert result["system_prompt"] == "custom"

    def test_no_inject_when_not_loaded(self):
        bridge._SYSTEM_PROMPT = None
        result = bridge._inject_system_prompt({})
        assert "system_prompt" not in result


class TestCompliancePromptContent:
    @pytest.fixture
    def prompt(self):
        if not os.path.exists(YAML):
            pytest.skip("YAML not found")
        import yaml
        with open(YAML) as f:
            return yaml.safe_load(f)["system_prompt"]

    def test_core_principles(self, prompt):
        for key in ["功能性共情", "社交引导", "退出友好", "透明身份", "聚焦努力"]:
            assert key in prompt, f"Missing: {key}"

    def test_forbidden_expressions(self, prompt):
        for key in ["禁止表述", "情感绑定", "情感操纵", "社交替代"]:
            assert key in prompt, f"Missing: {key}"

    def test_age_adaptation(self, prompt):
        assert "4-6 岁" in prompt or "年龄适配" in prompt

    def test_training_flow(self, prompt):
        assert "训练流程" in prompt or "开场" in prompt
