"""
CradleCoach AI 身份声明模块 (identity_disclosure.py)

法规依据：《暂行办法》第 18 条
"履行人工智能生成合成内容标识义务"

首次启动：播放 AI 身份声明音频
每月：播放月度提醒

年龄段适配：
  4-6 岁: 简化版——"我是一个会说话的训练玩具"
  7-12 岁: 明确版——"我是 AI 程序，不是真的小动物"
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import json


class IdentityDisclosure:
    """AI 身份声明管理"""

    # 首次启动声明文本
    FIRST_DISCLOSURE_TEXT = {
        1: (  # 4-6 岁
            "你好，我是 CradleCoach，"
            "一个会说话的训练玩具，帮助你练习专注力。"
            "准备好了吗？我们开始吧。"
        ),
        2: (  # 7-12 岁
            "你好，我是 CradleCoach，"
            "一个帮助你练习专注力的训练工具。"
            "我不是真的小动物，也不会真的说话——"
            "我身体里有一个小计算机在帮我。"
            "准备好了吗？我们开始吧。"
        ),
    }

    # 月度提醒文本
    MONTHLY_REMINDER_TEXT = {
        1: "提醒你一下，我是 CradleCoach，一个会说话的训练玩具哦。我们继续练习吧！",
        2: "提醒你一下，我是 CradleCoach，一个训练工具，不是真的小动物哦。不过我们继续练习吧！",
    }

    REMINDER_INTERVAL = timedelta(days=30)

    def __init__(
        self,
        age_group: int = 2,
        state_dir: Optional[Path] = None,
    ):
        """
        Args:
            age_group: 1 = 4-6 岁, 2 = 7-12 岁
            state_dir: 状态持久化目录
        """
        self.age_group = age_group
        self.state_dir = state_dir or Path(
            "harness_logs/compliance/identity_disclosures"
        )
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.first_completed = False
        self.last_monthly_reminder: Optional[datetime] = None
        self._load_state()

    def should_play_first_disclosure(self) -> bool:
        """是否需要播放首次启动声明"""
        return not self.first_completed

    def get_first_disclosure_text(self) -> str:
        """获取首次声明文本"""
        return self.FIRST_DISCLOSURE_TEXT.get(
            self.age_group,
            self.FIRST_DISCLOSURE_TEXT[2],
        )

    def mark_first_completed(self):
        """标记首次声明已完成"""
        self.first_completed = True
        self.last_monthly_reminder = datetime.now()
        self._persist_state()

    def should_play_monthly_reminder(self) -> bool:
        """是否需要播放月度提醒"""
        if not self.first_completed:
            return False
        if self.last_monthly_reminder is None:
            return True
        return (datetime.now() - self.last_monthly_reminder) >= self.REMINDER_INTERVAL

    def get_monthly_reminder_text(self) -> str:
        """获取月度提醒文本"""
        return self.MONTHLY_REMINDER_TEXT.get(
            self.age_group,
            self.MONTHLY_REMINDER_TEXT[2],
        )

    def mark_monthly_reminder_played(self):
        """标记月度提醒已播放"""
        self.last_monthly_reminder = datetime.now()
        self._persist_state()

    def _persist_state(self):
        state_file = self.state_dir / "disclosure_state.json"
        with open(state_file, "w") as f:
            json.dump({
                "first_completed": self.first_completed,
                "last_monthly_reminder": (
                    self.last_monthly_reminder.isoformat()
                    if self.last_monthly_reminder else None
                ),
            }, f)

    def _load_state(self):
        state_file = self.state_dir / "disclosure_state.json"
        if state_file.exists():
            with open(state_file) as f:
                data = json.load(f)
                self.first_completed = data.get("first_completed", False)
                reminder = data.get("last_monthly_reminder")
                if reminder:
                    self.last_monthly_reminder = datetime.fromisoformat(reminder)
