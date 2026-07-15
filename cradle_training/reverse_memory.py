"""
CradleCoach 倒序记忆游戏 (reverse_memory.py)

训练维度：工作记忆
规则：3-6 个词 → 等待倒序复述 → 规则判断
词数量 + 抽象度控制难度。

法规依据：《暂行办法》第 10 条（不得以"替代社会交往"为服务目标）
"""

from dataclasses import dataclass
from typing import List
import random


@dataclass
class ReverseMemoryResult:
    """倒序记忆评估结果"""
    correct: bool
    feedback: str
    original: List[str] = None
    expected_reversed: List[str] = None
    user_response: List[str] = None

    def __post_init__(self):
        if self.original is None:
            self.original = []
        if self.expected_reversed is None:
            self.expected_reversed = []
        if self.user_response is None:
            self.user_response = []


class ReverseMemoryGame:
    """倒序记忆游戏引擎"""

    # 词库（按难度分级）
    # difficulty 1-2: 具体名词，2-3 个词
    # difficulty 3-4: 具体+抽象混合，3-5 个词
    # difficulty 5: 抽象词为主，4-6 个词
    WORD_BANK = {
        "concrete": [
            "猫", "狗", "鸟", "鱼", "花", "树", "太阳", "月亮",
            "星星", "云朵", "大海", "高山", "河流", "房子", "桌子",
            "椅子", "书本", "铅笔", "苹果", "香蕉", "汽车", "火车",
            "飞机", "足球", "篮球", "电视", "电话", "手表", "鞋子",
            "帽子", "杯子", "窗户", "门", "桥", "马路", "花园",
            "蝴蝶", "小鸟", "大象", "老虎", "猴子", "兔子",
        ],
        "abstract": [
            "快乐", "勇敢", "智慧", "友谊", "梦想", "希望", "记忆",
            "时间", "力量", "自由", "美丽", "和平", "知识", "音乐",
            "故事", "颜色", "声音", "味道", "温暖", "寒冷", "安静",
            "光明", "黑暗", "速度", "方向", "距离", "重量", "年龄",
        ],
    }

    # 努力导向的正面反馈
    POSITIVE_FEEDBACK = [
        "完全正确！你的记忆力很棒，刚才很专注！",
        "太厉害了，全都倒着说对了，刚才很认真地在记忆！",
        "对！你做到了，一个都没漏，记忆力真棒！",
        "真棒，顺序完全正确！我看到你在认真记忆。",
    ]

    ENCOURAGING_FEEDBACK = [
        "差一点点，我们来听听正确的顺序：{expected_str}。再试一次？",
        "你记住了 {correct_count}/{total} 个，继续加油！正确的顺序是：{expected_str}。",
        "没关系，倒着说确实需要练习。正确的顺序是：{expected_str}。",
    ]

    def generate_sequence(self, difficulty: int = 2) -> List[str]:
        """
        根据难度生成词序列。

        难度映射：
          1-2 (easy): 2-3 个具体词
          3-4 (medium): 3-5 个混合词
          5 (hard): 4-6 个词，以抽象词为主
        """
        if difficulty <= 2:
            word_count = random.randint(2, 4)
            pool = self.WORD_BANK["concrete"]
        elif difficulty <= 4:
            word_count = random.randint(3, 5)
            pool = self.WORD_BANK["concrete"] + self.WORD_BANK["abstract"][:10]
        else:
            word_count = random.randint(4, 6)
            pool = self.WORD_BANK["abstract"] + self.WORD_BANK["concrete"][:10]

        # 不重复选择
        selected = random.sample(pool, min(word_count, len(pool)))
        return selected

    def evaluate(
        self, user_words: List[str], original: List[str]
    ) -> ReverseMemoryResult:
        """
        评估倒序记忆回答。

        Args:
            user_words: 用户说的词序列
            original: 原始词序列

        Returns:
            ReverseMemoryResult: 评估结果
        """
        expected = list(reversed(original))
        user_clean = [w.strip() for w in user_words]

        # 判断是否完全正确
        is_correct = (
            len(user_clean) == len(expected)
            and all(u == e for u, e in zip(user_clean, expected))
        )

        if is_correct:
            feedback = random.choice(self.POSITIVE_FEEDBACK)
            return ReverseMemoryResult(
                correct=True,
                feedback=feedback,
                original=original,
                expected_reversed=expected,
                user_response=user_clean,
            )

        # 计算部分正确数
        correct_count = 0
        for i, u in enumerate(user_clean):
            if i < len(expected) and u == expected[i]:
                correct_count += 1

        expected_str = "、".join(expected)
        feedback_template = (
            self.ENCOURAGING_FEEDBACK[1]
            if correct_count > 0
            else self.ENCOURAGING_FEEDBACK[0]
        )
        feedback = feedback_template.format(
            correct_count=correct_count,
            total=len(expected),
            expected_str=expected_str,
        )

        return ReverseMemoryResult(
            correct=False,
            feedback=feedback,
            original=original,
            expected_reversed=expected,
            user_response=user_clean,
        )
