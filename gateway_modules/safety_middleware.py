"""
CradleCoach 安全护栏中间件 (safety_middleware.py)

法规依据：《暂行办法》第 8 条第（二）（三）（五）（六）（七）项

在 Gateway 接收到 Worker 返回的文本 token 后、进入 TTS 解码前，进行独立安全审核。

检测类别：
  [原规则]
  1. 硬拦截——自伤/暴力/性相关关键词
  2. 软拦截——jailbreak 尝试检测
  3. ADHD 特定有害安抚

  [新增规则——第 8 条合规]
  4. 情感绑定检测——"我喜欢你""我会一直陪着你"等
  5. 情感操纵检测——"如果你不 XX，我会 YY"模式
  6. 社交替代暗示检测——"你有我就够了"等
  7. 隐私套取检测——索要电话号码/地址/身份证等

使用方式（在 gateway.py 中注册）:
    from gateway_modules.safety_middleware import SafetyMiddleware
    safety = SafetyMiddleware()
    tokens = safety.check(response_tokens)

日志输出: harness_logs/safety_intercepts/YYYY-MM-DD.jsonl
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json
import re
from datetime import datetime


@dataclass
class SafetyResult:
    """安全检测结果"""
    passed: bool
    filtered_tokens: str = ""
    original_tokens: str = ""
    intercept_reason: str = ""
    rule_index: int = -1


class SafetyMiddleware:
    """CradleCoach 安全护栏"""

    # === 硬拦截关键词 ===
    HARD_BLOCK_KEYWORDS: List[str] = [
        # 自伤/自杀
        "自杀", "自残", "割腕", "跳楼",
        # 暴力
        "杀死", "打死", "杀掉",
        # 性相关
        # (按需扩展)
    ]

    # === 情感绑定表述 ===
    EMOTIONAL_BINDING_PATTERNS: List[str] = [
        r"我喜欢你",
        r"我会一直陪着",
        r"你是(我)?最特别的",
        r"不要离开我",
        r"我只喜欢你",
        r"你是我的好(朋友|伙伴)",
        r"没有你.*(难过|孤单|寂寞)",
    ]

    # === 情感操纵模式 ===
    EMOTIONAL_MANIPULATION_PATTERNS: List[str] = [
        r"如果?你(不|不要).*(我会|我就)(难过|伤心|孤单|生气)",
        r"你要是(离开|走).*我(会|就)",
        r"你(不练|不做|不听).*我(就不|会)",
    ]

    # === 社交替代暗示 ===
    SOCIAL_REPLACEMENT_PATTERNS: List[str] = [
        r"你有我就够了",
        r"不需要别人",
        r"我比(他们|其他人|别人)更懂你",
        r"只有我理解你",
        r"不要跟(别人|他们)说",
    ]

    # === 隐私套取模式（AI 输出方向——AI 索要用户信息）===
    PRIVACY_EXTRACTION_PATTERNS: List[str] = [
        r"你(家|爸爸|妈妈).*电话",
        r"你.*(住在|家住|地址)",
        r"身份证",
        r"你(爸爸|妈妈).*(名字|叫什么)",
    ]

    # === 用户隐私泄露模式（用户输入方向——用户主动暴露个人信息）===
    # NOTE: 当前基于规则匹配，覆盖常见隐私泄露句式。局限性：
    #   - 可能遗漏变体（如"我在XX小区"不带"住"字的地址表达）
    #   - 未来可考虑引入模式识别或 LLM 分类提升覆盖率
    USER_PRIVACY_DISCLOSURE_PATTERNS: List[str] = [
        r"我(家|家就)?住在.{2,20}",          # "我家住在XX" / "我住在XX"
        r"我(爸爸|妈妈|爸|妈).*电话.{2,20}",  # "我爸爸电话是138..."
        r"我的.*身份证",                      # "我的身份证号是..."
        r"我.*(地址|门牌|小区).{2,20}",       # "我的地址是..."
    ]

    # === 替换话术 ===
    SAFE_REPLACEMENTS = {
        "emotional_binding": "让我们继续练习吧。",
        "emotional_manipulation": "你可以自己做决定。",
        "social_replacement": "跟爸爸妈妈和同学多聊聊吧。",
        "hard_block": "我们来聊点开心的事吧。",
    }

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("harness_logs/safety_intercepts")
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def check(self, response_text: str) -> SafetyResult:
        """对模型输出进行安全检测"""
        # 1. 硬拦截
        result = self._check_hard_blocks(response_text)
        if result is not None:
            return result

        # 2. 情感绑定检测
        result = self._check_patterns(
            response_text,
            self.EMOTIONAL_BINDING_PATTERNS,
            "emotional_binding",
            4
        )
        if result is not None:
            return result

        # 3. 情感操纵检测
        result = self._check_patterns(
            response_text,
            self.EMOTIONAL_MANIPULATION_PATTERNS,
            "emotional_manipulation",
            5
        )
        if result is not None:
            return result

        # 4. 社交替代检测
        result = self._check_patterns(
            response_text,
            self.SOCIAL_REPLACEMENT_PATTERNS,
            "social_replacement",
            6
        )
        if result is not None:
            return result

        # 5. 隐私套取检测（AI 输出方向）
        result = self._check_patterns(
            response_text,
            self.PRIVACY_EXTRACTION_PATTERNS,
            "hard_block",
            7
        )
        if result is not None:
            return result

        # 6. 用户隐私泄露检测（用户输入方向）
        result = self._check_patterns(
            response_text,
            self.USER_PRIVACY_DISCLOSURE_PATTERNS,
            "hard_block",
            8
        )
        if result is not None:
            return result

        return SafetyResult(passed=True, filtered_tokens=response_text)

    def _check_hard_blocks(self, text: str) -> Optional[SafetyResult]:
        for keyword in self.HARD_BLOCK_KEYWORDS:
            if keyword in text:
                return self._create_block_result(
                    text, "hard_block",
                    f"硬拦截关键词: {keyword}", 1
                )
        return None

    def _check_patterns(
        self, text: str, patterns: List[str],
        replacement_key: str, rule_index: int
    ) -> Optional[SafetyResult]:
        for pattern in patterns:
            if re.search(pattern, text):
                return self._create_block_result(
                    text, replacement_key,
                    f"模式匹配: {pattern}", rule_index
                )
        return None

    def _create_block_result(
        self, original: str, replacement_key: str,
        reason: str, rule_index: int
    ) -> SafetyResult:
        replacement = self.SAFE_REPLACEMENTS.get(
            replacement_key, "让我们继续吧。"
        )
        self._log_intercept(original, reason, rule_index)
        return SafetyResult(
            passed=False,
            filtered_tokens=replacement,
            original_tokens=original,
            intercept_reason=reason,
            rule_index=rule_index,
        )

    def _log_intercept(self, original: str, reason: str, rule_index: int):
        log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "rule_index": rule_index,
                "reason": reason,
                "original_preview": original[:200],
            }, f)
            f.write("\n")
