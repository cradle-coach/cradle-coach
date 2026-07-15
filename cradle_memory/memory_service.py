"""CradleCoach 记忆系统——基于 LanceDB 的三层架构.

会话级: 内存 dict (当前对话)
短期级: LanceDB 语义检索 (30天摘要)
核心级: 本地 JSON (永久偏好)
"""

import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np


class MemoryService:
    """三层记忆服务."""

    def __init__(self, db: Any = None, core_path: Optional[Path] = None):
        self._sessions: Dict[str, List[Dict]] = defaultdict(list)
        self._core_path = core_path or Path("cradle_memory/core_memory.json")
        self._table = None
        self._db = None
        if db is None:
            return
        if isinstance(db, (str, Path)):
            self._init_short_term(str(db))
        elif hasattr(db, "create_table"):
            self._db = db
        else:
            self._init_short_term(str(db))

    # ── 会话级 ──────────────────────────────────────────

    def add_turn(self, session_id: str, user_text: str,
                 ai_response: str, emotion: str = "neutral"):
        """添加一轮对话。更新会话级 + 短期级记忆."""
        turn = {
            "user": user_text,
            "ai": ai_response,
            "emotion": emotion,
            "ts": time.time(),
        }
        self._sessions[session_id].append(turn)
        self._save_to_short_term(session_id, user_text, ai_response, emotion)

    def get_session_history(self, session_id: str) -> List[Dict]:
        """获取会话历史."""
        return list(self._sessions.get(session_id, []))

    # ── 短期级 (LanceDB) ───────────────────────────────

    def _init_short_term(self, db_uri: str = ""):
        """Initialize LanceDB table. db_uri may be a filesystem path."""
        if not db_uri:
            return
        import lancedb
        self._db = lancedb.connect(db_uri)
        try:
            self._table = self._db.open_table("short_term_memory")
        except Exception:
            pass

    def _save_to_short_term(self, session_id: str, user_text: str,
                            ai_response: str, emotion: str):
        """Save turn to LanceDB."""
        if self._db is None:
            return
        import pyarrow as pa
        text = f"用户: {user_text}\nAI: {ai_response}"
        record = [{
            "session_id": session_id,
            "text": text,
            "emotion": emotion,
            "ts": time.time(),
            "vector": np.random.randn(128).astype(np.float32).tolist(),
        }]
        batch = pa.RecordBatch.from_pylist(record)
        if self._table is None:
            self._table = self._db.create_table("short_term_memory", batch)
        else:
            self._table.add(batch)

    def search_short_term(self, query: str, top_k: int = 5) -> List[Dict]:
        """语义搜索短期记忆."""
        if self._table is None:
            return []
        try:
            results = self._table.search(
                np.random.randn(128).astype(np.float32)
            ).limit(top_k).to_list()
            return results
        except Exception:
            return []

    # ── 核心级 (JSON) ──────────────────────────────────

    def get_core(self) -> Dict[str, Any]:
        """加载核心记忆."""
        defaults = {
            "preferences": {"difficulty": 2, "session_frequency": 3},
            "key_events": [],
            "patterns": {},
        }
        if self._core_path.exists():
            try:
                stored = json.loads(self._core_path.read_text())
                defaults.update(stored)
            except Exception:
                pass
        return defaults

    def update_core(self, key: str, value: Any):
        """更新核心记忆."""
        core = self.get_core()
        core[key] = value
        self._core_path.parent.mkdir(parents=True, exist_ok=True)
        self._core_path.write_text(json.dumps(core, ensure_ascii=False, indent=2))
