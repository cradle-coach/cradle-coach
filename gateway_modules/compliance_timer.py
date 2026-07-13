"""
CradleCoach 2 小时合规计时器 (compliance_timer.py)

法规依据：《暂行办法》第 18 条
"连续使用每超过 2 个小时，以对话或者弹窗等显著方式提醒注意使用时长"

追踪今日累计使用时长。
累计达 120 分钟时：
  1. 注入提醒消息到对话流
  2. 启动 5 分钟退出倒计时
  3. 倒计时完成后强制休眠
每日零点重置。
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json


@dataclass
class TimerState:
    """计时器状态"""
    session_start: Optional[datetime] = None
    accumulated_today: timedelta = timedelta(0)
    last_reminder_at: Optional[datetime] = None
    exit_countdown_start: Optional[datetime] = None
    is_blocked: bool = False


class ComplianceTimer:
    """2 小时合规计时器"""

    MAX_DAILY_USAGE = timedelta(minutes=120)  # 2 小时
    EXIT_COUNTDOWN = timedelta(minutes=5)     # 提醒后 5 分钟强制退出
    REMINDER_MESSAGE = (
        "[TIMER] 你已经练习了 2 小时，该休息了。"
        "去喝点水，找爸爸妈妈玩一会儿。"
    )

    def __init__(self, state_dir: Optional[Path] = None):
        self.state = TimerState()
        self.state_dir = state_dir or Path("harness_logs/compliance/timer_events")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def can_start_session(self) -> bool:
        """检查是否可以开始新会话"""
        if self.state.accumulated_today >= self.MAX_DAILY_USAGE:
            return False
        return True

    def start_session(self) -> bool:
        """开始会话"""
        if not self.can_start_session():
            self.state.is_blocked = True
            return False
        self.state.session_start = datetime.now()
        self.state.is_blocked = False
        return True

    def end_session(self):
        """结束会话，累计使用时长"""
        if self.state.session_start:
            duration = datetime.now() - self.state.session_start
            self.state.accumulated_today += duration
            self.state.session_start = None
            self._persist_state()

    def check_and_get_message(self) -> Optional[str]:
        """检查是否需要提醒或强制退出"""
        now = datetime.now()
        if not self.state.session_start:
            return None

        session_duration = now - self.state.session_start
        total = self.state.accumulated_today + session_duration

        # 检查强制退出倒计时
        if self.state.exit_countdown_start:
            if now - self.state.exit_countdown_start >= self.EXIT_COUNTDOWN:
                return "EXIT_NOW"
            return None

        # 检查 2 小时提醒
        if total >= self.MAX_DAILY_USAGE and not self.state.last_reminder_at:
            self.state.last_reminder_at = now
            self.state.exit_countdown_start = now
            return self.REMINDER_MESSAGE

        return None

    def reset_daily(self):
        """每日零点重置"""
        now = datetime.now()
        if now.hour == 0 and self.state.last_reminder_at:
            if self.state.last_reminder_at.date() < now.date():
                self.state = TimerState()
                self._persist_state()

    def _persist_state(self):
        state_file = self.state_dir / "timer_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "accumulated_seconds": self.state.accumulated_today.total_seconds(),
                "date": datetime.now().strftime("%Y-%m-%d"),
            }, f)

    def _load_state(self):
        state_file = self.state_dir / "timer_state.json"
        if state_file.exists():
            with open(state_file) as f:
                data = json.load(f)
                if data.get("date") == datetime.now().strftime("%Y-%m-%d"):
                    self.state.accumulated_today = timedelta(
                        seconds=data.get("accumulated_seconds", 0)
                    )
