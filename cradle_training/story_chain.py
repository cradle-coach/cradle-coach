"""
CradleCoach 故事接龙游戏 (story_chain.py)

训练维度：认知灵活性
规则：生成故事开头 → 等待续写 → 评估长度和连贯性

法规依据：《暂行办法》第 10 条（不得以"替代社会交往"为服务目标）
"""

from dataclasses import dataclass
from typing import List, Set
import random
import re


@dataclass
class StoryChainResult:
    """故事接龙评估结果"""
    passed: bool
    feedback: str
    length_score: float = 0.0      # 长度评分 (0-1)
    coherence_score: float = 0.0   # 连贯性评分 (0-1)


class StoryChainGame:
    """故事接龙游戏引擎"""

    # 故事开头库（按难度分级）
    OPENING_LIBRARY: List[dict] = [
        # Easy (1-2): 简单、具体情境
        {
            "text": "从前有一只小兔子，它有一对特别长的耳朵。有一天，它发现自己的耳朵能听到很远很远的声音……",
            "difficulty": 1,
            "keywords": ["小兔子", "耳朵", "声音", "森林", "动物"],
        },
        {
            "text": "一个小女孩在沙滩上捡到了一个闪闪发光的贝壳。她把贝壳放在耳边，听到了大海在说话……",
            "difficulty": 1,
            "keywords": ["沙滩", "贝壳", "大海", "女孩", "说话"],
        },
        {
            "text": "森林里有一棵会唱歌的大树。每天早晨，它都会用树枝轻轻摇摆，为小鸟们打节拍。可是今天，大树不唱歌了……",
            "difficulty": 2,
            "keywords": ["森林", "大树", "唱歌", "小鸟", "早晨"],
        },
        # Medium (3-4): 有情节冲突
        {
            "text": "小明搬到了一个新城市，他发现新家的后院有一扇被藤蔓遮住的小门。门后面是一条他没有见过的街道……",
            "difficulty": 3,
            "keywords": ["新家", "小门", "街道", "发现", "小明"],
        },
        {
            "text": "在一座高高的山上，住着一只会魔法的老猫。它有一个规矩：每个来找它帮忙的人，都要先讲一个故事……",
            "difficulty": 3,
            "keywords": ["山", "魔法", "猫", "故事", "帮忙"],
        },
        {
            "text": "小发明家阿杰造了一台能跟动物说话的机器。第一次打开的时候，他听到窗外的麻雀说了一句话，让他大吃一惊……",
            "difficulty": 4,
            "keywords": ["发明", "动物", "说话", "机器", "麻雀"],
        },
        # Hard (5): 抽象/复杂主题
        {
            "text": "在未来的地球，每个人出生时都会得到一个特殊的颜色。这个颜色不是给别人看的，而是代表了一个人内心的世界。有一天，出现了一个没有颜色的小孩……",
            "difficulty": 5,
            "keywords": ["未来", "颜色", "内心", "世界", "小孩"],
        },
        {
            "text": "村子里有一口古老的水井，老人们说，往井里说出一个愿望，井水会告诉你一个故事。但从没有人听到过同一个故事两次……",
            "difficulty": 5,
            "keywords": ["水井", "愿望", "故事", "村子", "老人"],
        },
    ]

    # 最小续写字数（按难度）
    MIN_CONTINUATION_CHARS = {1: 20, 2: 30, 3: 50, 4: 70, 5: 100}

    # 努力导向反馈
    POSITIVE_FEEDBACK = [
        "太有想象力了！你编的故事很有意思，刚才想得很投入。",
        "哇，这个发展我完全没想到。你很会编故事，思维很灵活！",
        "真棒！你续写得很精彩，我听到了你的创意。",
        "很好的故事！你在认真想每个细节，继续这样！",
    ]

    def generate_opening(self, difficulty: int = 2) -> str:
        """根据难度生成故事开头"""
        max_diff = min(difficulty + 1, 5)
        min_diff = max(1, difficulty - 1)
        candidates = [
            o for o in self.OPENING_LIBRARY
            if min_diff <= o["difficulty"] <= max_diff
        ]
        if not candidates:
            candidates = self.OPENING_LIBRARY

        opening = random.choice(candidates)
        return opening["text"]

    def evaluate(
        self, continuation: str, opening: str, difficulty: int = 2
    ) -> StoryChainResult:
        """
        评估故事续写。

        维度：
        1. 长度——续写足够长（>= 难度对应最小字数）
        2. 连贯性——与开头有关键词重叠

        Args:
            continuation: 用户的续写
            opening: 原始开头
            difficulty: 当前难度

        Returns:
            StoryChainResult: 评估结果
        """
        clean_continuation = continuation.strip()
        clean_opening = opening.strip()

        # 1. 长度评分
        min_chars = self.MIN_CONTINUATION_CHARS.get(difficulty, 50)
        char_count = len(clean_continuation)

        if char_count >= min_chars:
            length_score = 1.0
        elif char_count >= min_chars * 0.5:
            length_score = 0.5
        else:
            length_score = char_count / min_chars

        # 2. 连贯性评分——关键词重叠
        opening_words = self._extract_keywords(clean_opening)
        continuation_words = self._extract_keywords(clean_continuation)

        if opening_words:
            overlap = opening_words & continuation_words
            coherence_score = min(1.0, len(overlap) / max(1, len(opening_words) * 0.3))
        else:
            coherence_score = 0.5  # 无法评估时中性分

        # 3. 综合判断
        passed = length_score >= 0.5 and coherence_score >= 0.2

        if passed and length_score >= 1.0 and coherence_score >= 0.5:
            feedback = random.choice(self.POSITIVE_FEEDBACK)
        elif passed:
            feedback = (
                "不错！你接得很好。下次可以试着说更长的故事，"
                "加入更多细节会更有趣哦。"
            )
        elif length_score < 0.5:
            feedback = (
                f"你接得有点短哦，才{char_count}个字。"
                "再想一点点，故事接下来会发生什么？试着多说几句。"
            )
        else:
            feedback = (
                "你接的故事跟开头好像关系不大？"
                "试着想想，开头说的那些人和东西，接下来会怎么样呢？"
            )

        return StoryChainResult(
            passed=passed,
            feedback=feedback,
            length_score=length_score,
            coherence_score=coherence_score,
        )

    def _extract_keywords(self, text: str) -> Set[str]:
        """从文本中提取关键特征词（中文 2-gram）"""
        # 去掉标点
        cleaned = re.sub(r'[，。！？、；：""''「」『』（）…\s]', '', text)
        # 提取 2-gram 作为关键词特征
        keywords = set()
        for i in range(len(cleaned) - 1):
            bigram = cleaned[i:i + 2]
            keywords.add(bigram)
        # 也加入较大的 n-gram (3-4 chars)
        for i in range(len(cleaned) - 2):
            keywords.add(cleaned[i:i + 3])
        return keywords
