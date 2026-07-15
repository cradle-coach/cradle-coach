"""Phase 4: LanceDB 记忆系统测试."""
import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_db():
    """Temporary LanceDB for testing."""
    import lancedb
    tmp = tempfile.mkdtemp()
    db = lancedb.connect(tmp)
    yield db
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


class TestMemoryServiceCore:
    """Core memory service operations."""

    def test_session_memory_store_and_retrieve(self):
        """Session-level memory must store and retrieve turns."""
        from cradle_memory.memory_service import MemoryService
        svc = MemoryService(":memory:")
        svc.add_turn("sess1", "你好", "你好！我是教练", "neutral")
        history = svc.get_session_history("sess1")
        assert len(history) == 1
        assert history[0]["user"] == "你好"

    def test_session_memory_multi_turn(self):
        """Multiple turns must be retrievable in order."""
        from cradle_memory.memory_service import MemoryService
        svc = MemoryService(":memory:")
        svc.add_turn("s2", "Q1", "A1", "happy")
        svc.add_turn("s2", "Q2", "A2", "neutral")
        svc.add_turn("s2", "Q3", "A3", "tired")
        history = svc.get_session_history("s2")
        assert len(history) == 3
        assert history[-1]["user"] == "Q3"


class TestShortTermMemory:
    """LanceDB-based short-term memory (30-day)."""

    def test_short_term_save_and_search(self, temp_db):
        """Short-term entries must be retrievable by search."""
        from cradle_memory.memory_service import MemoryService
        svc = MemoryService(temp_db)
        svc.add_turn("s_x", "我们来玩反义词游戏", "好的！", "excited")
        svc.add_turn("s_x", "我今天不想训练", "没关系，深呼吸", "tired")
        results = svc.search_short_term("反义词游戏", top_k=3)
        assert len(results) > 0

    def test_short_term_respects_top_k(self, temp_db):
        """Search must respect top_k limit."""
        from cradle_memory.memory_service import MemoryService
        svc = MemoryService(temp_db)
        for i in range(5):
            svc.add_turn("s_t", f"消息{i}", f"回复{i}", "neutral")
        results = svc.search_short_term("消息", top_k=3)
        assert len(results) <= 3


class TestCoreMemory:
    """Permanent core memory (local JSON)."""

    def test_core_memory_read_write(self):
        """Core preferences must persist to JSON."""
        import tempfile
        from cradle_memory.memory_service import MemoryService
        tmp = tempfile.mkdtemp()
        core_path = Path(tmp) / "core_memory.json"
        svc = MemoryService(":memory:", core_path=core_path)
        svc.update_core("preferences", {"difficulty": 3})
        loaded = svc.get_core()
        assert loaded["preferences"]["difficulty"] == 3

    def test_core_memory_defaults(self):
        """Uninitialized core must return defaults."""
        from cradle_memory.memory_service import MemoryService
        svc = MemoryService(":memory:")
        core = svc.get_core()
        assert "preferences" in core
        assert "key_events" in core


class TestMemoryIntegration:
    """Integration: all three layers work together."""

    def test_add_turn_updates_all_layers(self, temp_db):
        """add_turn must update session + short-term."""
        import tempfile
        from cradle_memory.memory_service import MemoryService
        tmp = tempfile.mkdtemp()
        core_path = Path(tmp) / "core.json"
        svc = MemoryService(temp_db, core_path=core_path)
        svc.add_turn("int1", "你好", "你好！", "happy")
        # Session
        assert len(svc.get_session_history("int1")) == 1
        # Short-term
        results = svc.search_short_term("你好", top_k=1)
        assert len(results) > 0
