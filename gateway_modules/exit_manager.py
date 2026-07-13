"""
CradleCoach 退出管理器 (exit_manager.py)

法规依据：《暂行办法》第 19 条
"用户通过窗口操作、语音控制、关键词输入等方式要求退出的，
应当及时停止服务，不得采取持续互动等方式阻碍用户退出。"

职责：
  1. 训练完成主动引导退出
  2. 退出关键词检测 → 立即休眠
  3. 30 分钟无交互自动休眠
  4. 退出后 5 分钟内不主动发起对话
"""

from dataclasses import dataclass
from typing import List
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExitResult:
    should_exit: bool
    reason: str = ""
    exit_message: str = ""


class ExitManager:
    """CradleCoach 退出管理"""

    # 退出触发关键词
    EXIT_KEYWORDS: List[str] = [
        "再见", "拜拜", "不练了", "休息吧",
        "睡觉了", "关机", "停下", "别说话了",
    ]

    # 暂停关键词（非退出）
    PAUSE_KEYWORDS: List[str] = [
        "等一下", "暂停", "等等", "停一下",
    ]

    # 时间参数（秒）
    INACTIVITY_SLEEP_TIMEOUT = 1800   # 30 分钟无交互 → 休眠
    PAUSE_TIMEOUT = 600               # 暂停超 10 分钟 → 视为退出
    POST_EXIT_SILENCE = 300            # 退出后 5 分钟内不主动发起对话

    def __init__(self):
        self.is_active = True
        self.is_paused = False
        self.pause_start: float = 0.0
        self.last_exit_time: float = 0.0
        self.last_activity: float = time.time()

    def check_exit_keyword(self, asr_text: str) -> ExitResult:
        """检测用户输入中是否包含退出关键词"""
        for keyword in self.EXIT_KEYWORDS:
            if keyword in asr_text:
                return ExitResult(
                    should_exit=True,
                    reason=f"退出关键词: {keyword}",
                    exit_message=self._build_exit_message(),
                )
        return ExitResult(should_exit=False)

    def check_pause_keyword(self, asr_text: str) -> bool:
        """检测是否暂停"""
        for keyword in self.PAUSE_KEYWORDS:
            if keyword in asr_text:
                return True
        return False

    def set_paused(self, paused: bool):
        self.is_paused = paused
        if paused:
            self.pause_start = time.time()

    def is_pause_expired(self) -> bool:
        """暂停是否超时"""
        return (
            self.is_paused and
            (time.time() - self.pause_start) > self.PAUSE_TIMEOUT
        )

    def is_inactivity_timeout(self) -> bool:
        """是否无交互超时应休眠"""
        return (time.time() - self.last_activity) > self.INACTIVITY_SLEEP_TIMEOUT

    def training_complete_exit(self, progress_summary: str) -> str:
        """训练完成后主动引导退出"""
        return (
            f"今天的练习到这里。你刚才做到了{progress_summary}。"
            "现在去找爸爸妈妈，给他们看看你刚才做到的事！"
        )

    def is_in_post_exit_silence(self) -> bool:
        """是否处于退出后的静默期"""
        return (time.time() - self.last_exit_time) < self.POST_EXIT_SILENCE

    def mark_exited(self):
        """标记退出"""
        self.is_active = False
        self.last_exit_time = time.time()

    def mark_activity(self):
        """标记有活动"""
        self.last_activity = time.time()

    def _build_exit_message(self) -> str:
        """构建退出语——包含社交引导"""
        return "好的，今天的练习到这里。去喝点水，找爸爸妈妈玩一会儿吧。明天再一起练习！"
