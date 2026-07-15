"""
CradleCoach 情绪猜谜游戏 (emotion_guess.py)

训练维度：情绪识别
规则：内置故事库选段 → 等待识别情绪 → 规则判断
支持同义词匹配。

法规依据：《暂行办法》第 10 条（不得以"替代社会交往"为服务目标）
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import random


@dataclass
class EmotionGuessResult:
    """情绪猜谜评估结果"""
    correct: bool
    feedback: str
    correct_emotion: str = ""
    user_emotion: str = ""


class EmotionGuessGame:
    """情绪猜谜游戏引擎"""

    # 6 种基本情绪的同义词映射
    EMOTION_SYNONYMS: Dict[str, List[str]] = {
        "开心": ["高兴", "快乐", "愉快", "欢喜", "兴奋", "喜悦"],
        "难过": ["伤心", "悲伤", "哀伤", "忧伤", "悲痛", "不开心"],
        "生气": ["愤怒", "恼怒", "气愤", "发怒", "不爽", "恼火"],
        "害怕": ["恐惧", "惊恐", "畏惧", "害怕", "胆怯", "受惊"],
        "惊讶": ["吃惊", "惊奇", "诧异", "震惊", "意外", "愕然"],
        "讨厌": ["厌恶", "反感", "不喜欢", "厌烦", "嫌弃", "恶心"],
    }

    # 故事库 (story_text, correct_emotion, difficulty)
    STORY_LIBRARY: List[Dict] = [
        # Easy (1-2): 明显情绪线索
        {
            "story_text": "小明等了很久的生日到了，妈妈给他准备了一个大蛋糕，上面还有他最喜欢的玩具恐龙。小明跳了起来。",
            "correct_emotion": "开心",
            "difficulty": 1,
        },
        {
            "story_text": "小花养的小金鱼不动了，浮在水面上。小花蹲在鱼缸旁边，眼泪一直往下掉。",
            "correct_emotion": "难过",
            "difficulty": 1,
        },
        {
            "story_text": "小刚搭了一下午的积木塔，弟弟跑过来一下子推倒了。小刚的脸涨得通红，拳头握得紧紧的。",
            "correct_emotion": "生气",
            "difficulty": 1,
        },
        {
            "story_text": "晚上一个人在家，听到窗外传来奇怪的声音。小红缩在被子里，一动都不敢动。",
            "correct_emotion": "害怕",
            "difficulty": 1,
        },
        {
            "story_text": "小李打开书包，发现里面多了一个他没见过的礼物盒，上面写着他的名字。他瞪大了眼睛。",
            "correct_emotion": "惊讶",
            "difficulty": 2,
        },
        {
            "story_text": "每次吃青菜的时候，小美都会皱着眉头把菜推到盘子边上，说不想吃。",
            "correct_emotion": "讨厌",
            "difficulty": 2,
        },
        # Medium (3-4): 需要稍加推断
        {
            "story_text": "比赛结果公布了，小强是第二名。他看着第一名的奖杯，嘴角微微动了一下，然后用力鼓掌。",
            "correct_emotion": "难过",
            "difficulty": 3,
        },
        {
            "story_text": "老师说今天要换座位。小文的新同桌是班上最调皮的同学。小文慢慢地收拾书包，一句话也没说。",
            "correct_emotion": "讨厌",
            "difficulty": 3,
        },
        {
            "story_text": '妈妈答应周末去游乐园，可是周五晚上妈妈说临时要加班。小宇说"没关系"，但声音很小。',
            "correct_emotion": "难过",
            "difficulty": 3,
        },
        {
            "story_text": "小亮在操场上被一个高年级同学推倒了。他站起来，拍了拍身上的土，大声说要去找老师。",
            "correct_emotion": "生气",
            "difficulty": 4,
        },
        {
            "story_text": "第一次上台演讲，台下坐满了人。小芳站在台上，手心里全是汗，嘴巴有点干。",
            "correct_emotion": "害怕",
            "difficulty": 4,
        },
        # Hard (5): 复杂/混合情绪线索
        {
            "story_text": "毕业典礼上，小杰拿到了优秀学生奖。他站在台上笑着，可是眼眶有点红。",
            "correct_emotion": "开心",
            "difficulty": 5,
        },
        {
            "story_text": "搬家去新城市的那天，小童坐在车里回头看老房子。她没有哭，只是一直回头看，直到看不见为止。",
            "correct_emotion": "难过",
            "difficulty": 5,
        },
    ]

    # 努力导向的正面反馈
    POSITIVE_FEEDBACK = [
        "对！你判断得很准，刚才听得很认真！",
        "没错，就是这个情绪。你很会观察别人的感受哦。",
        "答对了！你注意到了故事里的细节。",
        "很好，你说得对。你在努力理解别人的情绪。",
    ]

    ENCOURAGING_FEEDBACK = [
        "差一点点，这个故事里的情绪是「{correct}」。你注意到哪些地方不对了吗？",
        "不完全是。故事里的人感觉是「{correct}」。我们再听一个？",
    ]

    def select_story(self, difficulty: int = 2) -> Tuple[str, str]:
        """
        根据难度选择故事。

        Returns:
            (story_text, correct_emotion)
        """
        max_diff = min(difficulty + 1, 5)
        min_diff = max(1, difficulty - 1)
        candidates = [
            s for s in self.STORY_LIBRARY
            if min_diff <= s["difficulty"] <= max_diff
        ]
        if not candidates:
            candidates = self.STORY_LIBRARY

        story = random.choice(candidates)
        return story["story_text"], story["correct_emotion"]

    def evaluate(
        self, user_emotion: str, correct_emotion: str
    ) -> EmotionGuessResult:
        """
        评估情绪猜谜回答。

        Args:
            user_emotion: 用户说的情绪词
            correct_emotion: 故事对应的正确答案

        Returns:
            EmotionGuessResult: 评估结果
        """
        user_clean = user_emotion.strip()
        correct_clean = correct_emotion.strip()

        # 完全匹配
        if user_clean == correct_clean:
            feedback = random.choice(self.POSITIVE_FEEDBACK)
            return EmotionGuessResult(
                correct=True,
                feedback=feedback,
                correct_emotion=correct_clean,
                user_emotion=user_clean,
            )

        # 同义词匹配
        synonyms = self.EMOTION_SYNONYMS.get(correct_clean, [])
        if user_clean in synonyms:
            feedback = (
                f"对！你说「{user_clean}」，和「{correct_clean}」是一个意思。"
                f"你很会表达情绪！"
            )
            return EmotionGuessResult(
                correct=True,
                feedback=feedback,
                correct_emotion=correct_clean,
                user_emotion=user_clean,
            )

        # 错误
        feedback_template = random.choice(self.ENCOURAGING_FEEDBACK)
        feedback = feedback_template.format(correct=correct_clean)
        return EmotionGuessResult(
            correct=False,
            feedback=feedback,
            correct_emotion=correct_clean,
            user_emotion=user_clean,
        )
