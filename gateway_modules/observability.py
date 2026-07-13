"""
CradleCoach 可观测性模块 (observability.py)

日志记录：
  - 对话日志（会话级别）
  - 安全拦截日志
  - 沉默控制日志
  - 对话流管理日志

全部写入本地 JSONL 文件。
"""

from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional
import json


class Observability:
    """可观测性——日志记录"""

    def __init__(self, log_base: Optional[Path] = None):
        self.log_base = log_base or Path("harness_logs")
        self._ensure_dirs()

    def _ensure_dirs(self):
        for subdir in [
            "safety_intercepts",
            "silence_control",
            "conversation_flow",
            "sessions",
        ]:
            (self.log_base / subdir).mkdir(parents=True, exist_ok=True)

    def _write_log(self, subdir: str, entry: Dict[str, Any]):
        log_file = (
            self.log_base / subdir /
            f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        )
        entry["timestamp"] = datetime.now().isoformat()
        with open(log_file, "a") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

    def log_session(self, session_id: str, event: str, data: Dict[str, Any] = None):
        """记录会话事件"""
        self._write_log("sessions", {
            "session_id": session_id,
            "event": event,
            "data": data or {},
        })

    def log_safety_intercept(self, rule: int, reason: str, preview: str):
        """记录安全拦截"""
        self._write_log("safety_intercepts", {
            "rule": rule,
            "reason": reason,
            "preview": preview[:200],
        })

    def log_silence_event(self, event: str, duration_seconds: float):
        """记录沉默控制事件"""
        self._write_log("silence_control", {
            "event": event,
            "duration": duration_seconds,
        })

    def log_conversation_flow(self, event: str, data: Dict[str, Any]):
        """记录对话流事件"""
        self._write_log("conversation_flow", {
            "event": event,
            **data,
        })
