# Issue #52: fix — 修复 Phase 5 代码审查发现的 10 个问题

status: done
branch: fix/52-phase5-review-fixes
last-session: 2026-07-15
summary: |
  Phase 5 max-effort 代码审查（10 角度并行）发现 10 个问题：
  3 正确性 bug + 4 死代码/耦合问题 + 3 测试/文档质量。
  25 个候选发现已反驳（见 issue body）。

  Bugs to fix:
  - Session 过期后永久卡死 (training_manager.py:162)
  - 复合情绪词绕过负面检测 (training_manager.py:103)
  - time.time() → time.monotonic() (training_manager.py:110)
  - _build_feedback 死代码 (training_manager.py:378)
  - _last_prompt_word 未初始化 (training_manager.py:184)
  - regex 耦合提示词格式 (training_manager.py:178)
  - Docstring 词数不符 (reverse_memory.py:82)
  - 弱断言 SESSION_MIN_MINUTES (test_training_engine.py:408)
  - test_session_expiry 不测恢复路径 (test_training_engine.py:417)
  - evaluate/start_game 重复 dispatch (training_manager.py:244)

  Refuted (no code change):
  - Class-level mutable 常量（只读，Python 标准模式）
  - sys.path.insert 副作用（项目既有模式）
  - random 无 seed（行为测试不需要）
  - 同义词自引用（有意设计）
  - Fruit rule 重复（有意设计）
  - Difficulty range 重复（设计取舍）
  - Dispatch 重复（各有不同逻辑）
