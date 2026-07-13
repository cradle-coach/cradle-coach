"""
CradleCoach Harness 管理器 (harness_manager.py)

注册和编排所有 Harness 组件在 Gateway 层的生命周期。

使用方式（在 minicpmo45_service/gateway.py 中）:
    from gateway_modules.harness_manager import HarnessManager
    hm = HarnessManager(age_group=2)
    # 在 Gateway 消息路径上注入中间件
"""

from pathlib import Path
from typing import Optional

from gateway_modules.safety_middleware import SafetyMiddleware
from gateway_modules.silence_controller import SilenceController
from gateway_modules.exit_manager import ExitManager
from gateway_modules.compliance_timer import ComplianceTimer
from gateway_modules.identity_disclosure import IdentityDisclosure
from gateway_modules.emergency_alert import EmergencyAlert
from gateway_modules.conversation_flow import ConversationFlow
from gateway_modules.observability import Observability


class HarnessManager:
    """CradleCoach Harness 组件注册和编排"""

    def __init__(
        self,
        age_group: int = 2,
        log_base: Optional[Path] = None,
        guardian_push_url: str = "http://localhost:8666/alert",
    ):
        self.log_base = log_base or Path("harness_logs")

        # 合规模块
        self.safety = SafetyMiddleware(
            log_dir=self.log_base / "safety_intercepts"
        )
        self.timer = ComplianceTimer(
            state_dir=self.log_base / "compliance/timer_events"
        )
        self.identity = IdentityDisclosure(
            age_group=age_group,
            state_dir=self.log_base / "compliance/identity_disclosures",
        )
        self.emergency = EmergencyAlert(
            push_url=guardian_push_url,
            log_dir=self.log_base / "compliance/emergency_alerts",
        )

        # 退出管理（依赖 timer 的退出倒计时回调）
        self.exit_mgr = ExitManager()

        # 沉默控制（依赖 exit_mgr 的休眠回调）
        self.silence = SilenceController(
            exit_manager=self.exit_mgr.initiate_sleep
            if hasattr(self.exit_mgr, 'initiate_sleep') else None
        )

        # 对话流和可观测性
        self.conversation = ConversationFlow()
        self.obs = Observability(log_base=self.log_base)

    def get_all_modules(self) -> dict:
        """返回所有 Harness 模块的字典"""
        return {
            "safety": self.safety,
            "silence": self.silence,
            "exit_mgr": self.exit_mgr,
            "timer": self.timer,
            "identity": self.identity,
            "emergency": self.emergency,
            "conversation": self.conversation,
            "obs": self.obs,
        }
