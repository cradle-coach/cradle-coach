"""
CradleCoach 反义词游戏 (antonyms.py)

训练维度：反应抑制
规则：选词 → 等待回答 → 判断反义词是否正确
水果例外规则：如果题目词是水果，正确答案 = 原词本身（抑制说反义词的冲动）

法规依据：《暂行办法》第 10 条（不得以"替代社会交往"为服务目标）
"""

from dataclasses import dataclass
from typing import List, Tuple
import random


@dataclass
class AntonymResult:
    """反义词评估结果"""
    correct: bool
    feedback: str
    expected: str = ""
    user_response: str = ""


class AntonymGame:
    """反义词游戏引擎"""

    # 反义词对（按难度分级）
    # difficulty 1-2 (easy): 具体、常用词
    # difficulty 3-4 (medium): 稍抽象词
    # difficulty 5 (hard): 更抽象或容易混淆的词
    WORD_PAIRS: List[Tuple[str, str, int]] = [
        # (词, 反义词, 难度)
        # Easy (1-2)
        ("大", "小", 1),
        ("多", "少", 1),
        ("高", "矮", 1),
        ("胖", "瘦", 1),
        ("快", "慢", 1),
        ("热", "冷", 1),
        ("上", "下", 1),
        ("左", "右", 1),
        ("前", "后", 1),
        ("开", "关", 1),
        ("来", "去", 1),
        ("进", "出", 1),
        ("白天", "黑夜", 1),
        ("笑", "哭", 1),
        # Medium (3-4)
        ("明亮", "黑暗", 3),
        ("勇敢", "胆小", 3),
        ("安静", "吵闹", 3),
        ("干净", "脏", 3),
        ("聪明", "笨", 3),
        ("善良", "凶恶", 3),
        ("勤劳", "懒惰", 3),
        ("诚实", "撒谎", 3),
        ("安全", "危险", 3),
        ("简单", "复杂", 3),
        ("开心", "难过", 3),
        ("强壮", "虚弱", 3),
        ("美丽", "丑陋", 3),
        ("富有", "贫穷", 3),
        # Hard (5)
        ("谦虚", "骄傲", 5),
        ("慷慨", "吝啬", 5),
        ("乐观", "悲观", 5),
        ("仔细", "马虎", 5),
        ("团结", "分裂", 5),
        ("民主", "专制", 5),
        ("抽象", "具体", 5),
        ("主动", "被动", 5),
        ("积极", "消极", 5),
        ("节约", "浪费", 5),
    ]

    # 水果集合——触发例外规则
    FRUIT_SET: List[str] = [
        "苹果", "香蕉", "西瓜", "葡萄", "橘子",
        "草莓", "桃子", "梨", "芒果", "樱桃",
        "菠萝", "柠檬", "猕猴桃", "火龙果", "蓝莓",
    ]

    # 努力导向的正面反馈
    POSITIVE_FEEDBACK = [
        "对啦！你反应很快！",
        "答对了，你很专注哦！",
        "很好，你做到了！",
        "没错！你刚才想得很认真。",
        "对！我看到你在努力思考。",
    ]

    # 鼓励性错误反馈
    ENCOURAGING_FEEDBACK = [
        "差一点点，再想想？",
        "没关系，下次我们试试慢一点。",
        "这个有点难，你已经很接近了！",
        "不错，继续加油！",
    ]

    def generate_prompt(self, difficulty: int = 2) -> Tuple[str, str]:
        """
        根据难度生成反义词题目。

        Returns:
            (instructions, expected_answer)
        """
        # 筛选适合当前难度的词对
        max_diff = min(difficulty + 1, 5)
        min_diff = max(1, difficulty - 1)
        candidates = [
            (w, a) for w, a, d in self.WORD_PAIRS
            if min_diff <= d <= max_diff
        ]
        if not candidates:
            candidates = [(w, a) for w, a, _ in self.WORD_PAIRS]

        # 随机选词
        word, antonym = random.choice(candidates)

        # 有一定概率选水果词（困难模式概率更高）
        if difficulty >= 3 and random.random() < 0.3:
            word = random.choice(self.FRUIT_SET)
            antonym = word  # 水果例外：正确答案是原词

        is_fruit = word in self.FRUIT_SET
        if is_fruit:
            instructions = (
                f"我们来玩反义词游戏！我说一个词，你说它的反义词。"
                f"但是——如果是水果的名字，就说这个词自己，不要想反义词哦。"
                f"准备好了吗？第一个词是：「{word}」"
            )
        else:
            instructions = (
                f"我们来玩反义词游戏！我说一个词，你说它的反义词。"
                f"准备好了吗？第一个词是：「{word}」"
            )

        return instructions, antonym

    def evaluate(
        self, prompt_word: str, expected_answer: str, user_response: str
    ) -> AntonymResult:
        """
        评估反义词回答。

        Args:
            prompt_word: 题目词
            expected_answer: 期望答案
            user_response: 用户实际回答

        Returns:
            AntonymResult: 评估结果
        """
        user_clean = user_response.strip()
        expected_clean = expected_answer.strip()

        # 水果例外规则检查
        is_fruit = prompt_word.strip() in self.FRUIT_SET

        if is_fruit:
            # 水果词：用户应该说原词
            if user_clean == expected_clean:
                feedback = (
                    f"对啦！「{prompt_word}」是水果，"
                    f"水果要说它自己，不能想反义词。你很专注！"
                )
                return AntonymResult(
                    correct=True,
                    feedback=feedback,
                    expected=expected_clean,
                    user_response=user_clean,
                )
            else:
                feedback = (
                    f"哦——「{prompt_word}」是水果的名字呀。"
                    f"水果的词不说反义词，说「{prompt_word}」自己就好。再来一次？"
                )
                return AntonymResult(
                    correct=False,
                    feedback=feedback,
                    expected=expected_clean,
                    user_response=user_clean,
                )

        # 普通反义词判断
        if user_clean == expected_clean:
            feedback = random.choice(self.POSITIVE_FEEDBACK)
            return AntonymResult(
                correct=True,
                feedback=feedback,
                expected=expected_clean,
                user_response=user_clean,
            )
        else:
            feedback = random.choice(self.ENCOURAGING_FEEDBACK)
            feedback += f"「{prompt_word}」的反义词是「{expected_clean}」哦。"
            return AntonymResult(
                correct=False,
                feedback=feedback,
                expected=expected_clean,
                user_response=user_clean,
            )
