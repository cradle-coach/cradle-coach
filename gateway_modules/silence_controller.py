"""
CradleCoach 沉默控制模块 (silence_controller.py)

法规依据：《暂行办法》第 10 条（不得以"替代社会交往"为服务目标）

管理对话中的节奏——沉默窗口、barge-in、短回应过滤。
与 exit_manager.py 协作：长时间沉默后触发退出流程。

保留原 Demo 的沉默控制逻辑（沉默窗口 + barge-in + 短回应过滤）。
合规适配变更：
  - 超时引导从"陪伴型轻量问候"改为"功能型状态检查"
  - 不再使用"我在这呢"等陪伴用语
  - 长时间无响应时调用 exit_manager 触发休眠
"""

from dataclasses import dataclass
import time
from typing import Optional, Callable


@dataclass
class SilenceState:
    """沉默控制状态机"""
    SILENT = "SILENT"       # AI 说完，等待孩子回应
    LISTENING = "LISTENING"  # 检测到孩子说话
    SPEAKING = "SPEAKING"    # AI 正在说话
    HOLDING = "HOLDING"      # 强制沉默窗口


class SilenceController:
    """CradleCoach 沉默控制"""

    # 沉默窗口（秒）
    MIN_SILENCE_WINDOW = 3.0     # AI 说完后的最小沉默时间
    MAX_SILENCE_WINDOW = 5.0     # 最大沉默时间
    LONG_SILENCE_THRESHOLD = 30.0  # 长时间沉默阈值
    EXIT_SILENCE_THRESHOLD = 60.0  # 触发退出的沉默阈值

    # 短回应过滤
    SHORT_RESPONSE_PATTERNS = [
        "嗯", "哦", "好的", "好的呀", "这样啊", "嗯嗯", "喔",
    ]
    MIN_RESPONSE_LENGTH = 5  # 少于此长度的 token 视为短回应

    def __init__(self, exit_manager: Optional[Callable] = None):
        """
        Args:
            exit_manager: exit_manager.initiate_sleep() 回调。
                          当沉默超过 60s 时调用。
        """
        self.exit_manager = exit_manager
        self.state = SilenceState.SILENT
        self.silence_start: float = time.time()
        self.last_response_time: float = time.time()

    def is_short_response(self, response_text: str) -> bool:
        """检测是否为无意义短回应"""
        text = response_text.strip()
        return (
            len(text) < self.MIN_RESPONSE_LENGTH or
            text in self.SHORT_RESPONSE_PATTERNS
        )

    def should_hold_silence(self) -> bool:
        """是否应保持沉默（不主动说话）"""
        elapsed = time.time() - self.last_response_time
        return elapsed < self.MIN_SILENCE_WINDOW

    def get_status_check_message(self) -> Optional[str]:
        """
        长时间沉默后的状态检查消息。
        合规版：不是"陪伴型问候"，而是"功能型状态检查"。
        """
        elapsed = time.time() - self.last_response_time
        if elapsed > self.EXIT_SILENCE_THRESHOLD:
            if self.exit_manager:
                self.exit_manager()
            return None
        if elapsed > self.LONG_SILENCE_THRESHOLD:
            return "你还在吗？我们要继续练习还是休息一下？"
        return None

    def on_user_speech_detected(self):
        """VAD 检测到孩子说话"""
        self.state = SilenceState.LISTENING
        self.silence_start = time.time()

    def on_ai_speech_started(self):
        """AI 开始说话"""
        self.state = SilenceState.SPEAKING

    def on_ai_speech_ended(self):
        """AI 结束说话"""
        self.state = SilenceState.SILENT
        self.last_response_time = time.time()

    def on_barge_in(self):
        """孩子打断 AI"""
        self.state = SilenceState.LISTENING
        # barge-in 逻辑——在 Gateway 层停止 TTS 输出
