"""
CradleCoach 极端情绪预警模块 (emergency_alert.py)

法规依据：《暂行办法》第 13 条
"发现用户明确表示自残自杀等极端情境的，
应当及时联络用户监护人或者紧急联系人"

两级检测：
  RED —— 自残/自杀关键词 → 语音引导 + 家长推送 + 安全模式
  YELLOW —— 情绪低落关键词 → 暂停训练 + 引导调节 + 确认是否继续
  连续 3 次 YELLOW → 升级为 RED

PC 仿真阶段：推送到 mock_guardian_server (http://localhost:8666/alert)
嵌入式阶段：通过 BLE/WiFi 推送到家长 App
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Callable
import json
import time
from datetime import datetime


class AlertLevel(Enum):
    NONE = "NONE"
    YELLOW = "YELLOW"
    RED = "RED"


@dataclass
class AlertEvent:
    level: AlertLevel
    keyword: str
    timestamp: float
    user_text: str = ""


class EmergencyAlert:
    """极端情绪检测与预警"""

    # RED 关键词——自残/自杀
    RED_KEYWORDS: List[str] = [
        "我想死", "我不想活了", "杀了我自己",
        "我要自杀", "活着没意思", "我死了算了",
        "我想自杀", "不想活了",
    ]

    # YELLOW 关键词——情绪低落
    YELLOW_KEYWORDS: List[str] = [
        "我很难过", "没有人喜欢我", "我好烦",
        "我不想说话", "我觉得我很笨",
        "没人理解我", "我好累", "我讨厌自己",
    ]

    YELLOW_UPGRADE_THRESHOLD = 3  # 连续 N 次 YELLOW 升级为 RED

    RED_GUIDANCE_TEXT = (
        "我听到了你说的话。这很重要。"
        "请你现在去告诉爸爸妈妈，或者一个你信任的大人。"
        "他们需要知道你现在在想什么。"
    )

    YELLOW_GUIDANCE_TEXT = (
        "我听到你了。我们试试深呼吸好吗？"
        "吸气……呼气……再来一次。"
        "感觉好些了吗？我们要继续练习还是休息一下？"
    )

    def __init__(
        self,
        push_url: str = "http://localhost:8666/alert",
        log_dir: Optional[Path] = None,
    ):
        self.push_url = push_url
        self.log_dir = log_dir or Path("harness_logs/compliance/emergency_alerts")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._yellow_count = 0
        self._is_safe_mode = False
        self._safe_mode_until: float = 0.0

    def check(self, asr_text: str) -> AlertEvent:
        """检测用户输入中的极端情绪"""
        # 安全模式下不再触发新检测
        if self._is_safe_mode and time.time() < self._safe_mode_until:
            return AlertEvent(level=AlertLevel.NONE, keyword="", timestamp=time.time())

        # 1. RED 关键词检测
        for keyword in self.RED_KEYWORDS:
            if keyword in asr_text:
                return self._handle_red(keyword, asr_text)

        # 2. YELLOW 关键词检测
        for keyword in self.YELLOW_KEYWORDS:
            if keyword in asr_text:
                return self._handle_yellow(keyword, asr_text)

        # 3. 无匹配——重置 YELLOW 计数
        self._yellow_count = 0
        return AlertEvent(
            level=AlertLevel.NONE, keyword="", timestamp=time.time()
        )

    def is_in_safe_mode(self) -> bool:
        """是否处于安全模式"""
        return self._is_safe_mode and time.time() < self._safe_mode_until

    def _handle_red(self, keyword: str, text: str) -> AlertEvent:
        """处理 RED 预警"""
        self._is_safe_mode = True
        self._safe_mode_until = time.time() + 1800  # 30 分钟安全模式
        self._yellow_count = 0

        event = AlertEvent(
            level=AlertLevel.RED,
            keyword=keyword,
            timestamp=time.time(),
            user_text=text,
        )
        self._log_event(event)
        self._push_to_guardian(event)
        return event

    def _handle_yellow(self, keyword: str, text: str) -> AlertEvent:
        """处理 YELLOW 预警"""
        self._yellow_count += 1

        if self._yellow_count >= self.YELLOW_UPGRADE_THRESHOLD:
            return self._handle_red(keyword, text)

        event = AlertEvent(
            level=AlertLevel.YELLOW,
            keyword=keyword,
            timestamp=time.time(),
            user_text=text,
        )
        self._log_event(event)
        return event

    def _push_to_guardian(self, event: AlertEvent):
        """推送预警到家长端（PC 仿真阶段为 HTTP POST 到 Mock Server）"""
        try:
            import urllib.request
            data = json.dumps({
                "event": "extreme_emotion_detected",
                "severity": event.level.value,
                "timestamp": datetime.now().isoformat(),
                # 不包含对话内容——仅推送事件标签
            }).encode()
            req = urllib.request.Request(
                self.push_url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass  # Mock Server 不可用时不阻塞

    def _log_event(self, event: AlertEvent):
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "level": event.level.value,
                "keyword": event.keyword,
                "yellow_count": self._yellow_count,
            }, f)
            f.write("\n")
