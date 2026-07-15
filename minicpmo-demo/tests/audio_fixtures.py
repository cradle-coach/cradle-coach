"""Audio simulation fixtures for API Bridge integration testing.

Provides reusable helpers for testing the full audio pipeline without a browser:
- WAV → float32 PCM chunk conversion (Cloud API format)
- AudioSession: manages queue → session.init → audio send → response collect
- pytest fixtures: test_wav_path, audio_chunks, bridge_server, api_bridge_ws

Usage:
    from tests.audio_fixtures import AudioSession, wav_to_float32_chunks

    async def test_audio(api_bridge_ws, audio_chunks):
        session = AudioSession(api_bridge_ws)
        await session.init()
        await session.send_audio_chunks(audio_chunks[:10])
        result = await session.collect_responses()
        assert result["listen"] > 0  # Cloud API is processing audio
"""

import asyncio
import base64
import json
import os
import subprocess
import time
import wave
from typing import List, Optional

import numpy as np
import pytest
import websockets

# ── Constants ────────────────────────────────────────────────

DEFAULT_API_BRIDGE_PORT = 22413
API_BRIDGE_HOST = "127.0.0.1"
INPUT_SAMPLE_RATE = 16000
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
API_KEY = os.getenv("CRADLECOACH_API_KEY", "")

_TEST_WAVS = [
    "tests/cases/common/user_audio/000_user_audio0.wav",
    "tests/cases/common/user_audio/当出现植物大战僵尸的时候提醒我.wav",
]


# ── Audio helpers ────────────────────────────────────────────

def require_api_key():
    if not API_KEY:
        pytest.skip("CRADLECOACH_API_KEY not set")


def wav_to_float32_chunks(
    wav_path: str,
    chunk_ms: int = 60,
    max_chunks: Optional[int] = None,
) -> List[np.ndarray]:
    """Load WAV → 16kHz mono float32 chunks (Cloud API input format).

    Each chunk is a numpy float32 array, chunk_ms milliseconds long.
    """
    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if sample_width == 1:
        data = (np.frombuffer(frames, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif sample_width == 2:
        data = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32768.0
    elif sample_width == 4:
        data = np.frombuffer(frames, dtype="<i4").astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported sample width: {sample_width}")

    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)

    if sample_rate != INPUT_SAMPLE_RATE:
        old_x = np.linspace(0.0, 1.0, num=len(data), endpoint=False)
        new_len = int(round(len(data) * INPUT_SAMPLE_RATE / sample_rate))
        new_x = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
        data = np.interp(new_x, old_x, data).astype(np.float32)

    data = np.clip(data, -1.0, 1.0).astype(np.float32)

    chunk_len = int(INPUT_SAMPLE_RATE * chunk_ms / 1000)
    chunks = []
    for start in range(0, len(data), chunk_len):
        chunk = data[start : start + chunk_len]
        if len(chunk) > 0:
            chunks.append(chunk.astype(np.float32, copy=False))

    if max_chunks is not None:
        chunks = chunks[:max_chunks]
    return chunks


def b64_float32(samples: np.ndarray) -> str:
    """Encode float32 array as base64 (Cloud API audio wire format)."""
    return base64.b64encode(
        samples.astype("<f4", copy=False).tobytes()
    ).decode("ascii")


# ── AudioSession ─────────────────────────────────────────────

class AudioSession:
    """Manage an audio-duplex WebSocket session for integration testing.

    Lifecycle: queue_done → session.init → session.created → audio send → collect.

    Usage::

        session = AudioSession(ws)
        sid = await session.init()
        await session.send_audio_chunks(chunks)
        result = await session.collect_responses()
        assert result["listen"] > 0  # server is processing audio
    """

    def __init__(self, ws: websockets.ClientConnection):
        self.ws = ws
        self.session_id: str = ""
        self.mode: str = ""
        self.errors: List[dict] = []

    async def init(self, system_prompt: str = "") -> str:
        """Wait for queue_done, send session.init, return session_id."""
        async for raw in self.ws:
            event = json.loads(raw)
            etype = event.get("type", "")

            if etype == "session.queue_done":
                payload = {}
                if system_prompt:
                    payload["system_prompt"] = system_prompt
                await self.ws.send(json.dumps({
                    "type": "session.init",
                    "payload": payload,
                }))

            elif etype == "session.created":
                self.session_id = event.get("session_id", "")
                self.mode = event.get("mode", "")
                return self.session_id

            elif etype == "error":
                self.errors.append(event)
                raise RuntimeError(f"init error: {event}")

    async def send_audio_chunks(
        self, chunks: List[np.ndarray], cadence_ms: int = 60
    ) -> None:
        """Send audio chunks with real-time cadence."""
        for chunk in chunks:
            await self.ws.send(json.dumps({
                "type": "input.append",
                "input": {"audio": b64_float32(chunk), "force_listen": False},
            }))
            await asyncio.sleep(cadence_ms / 1000.0)

    async def collect_responses(
        self, max_events: int = 50, timeout: float = 15.0
    ) -> dict:
        """Collect response events from server.

        Returns:
            {"text": [...], "audio": N, "listen": N, "done": bool}
        """
        result = {"text": [], "audio": 0, "listen": 0, "done": False}

        for _ in range(max_events):
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            except asyncio.TimeoutError:
                break

            event = json.loads(raw)
            etype = event.get("type", "")

            if etype == "response.output.delta":
                kind = event.get("kind", "")
                if kind == "text":
                    result["text"].append(event.get("text", ""))
                elif kind == "audio":
                    result["audio"] += 1
                elif kind == "listen":
                    result["listen"] += 1

            elif etype == "response.done":
                result["done"] = True
                break

            elif etype == "error":
                self.errors.append(event)
                break

        return result


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture
def test_wav_path() -> str:
    """First available test WAV file."""
    for rel in _TEST_WAVS:
        full = os.path.join(PROJECT_ROOT, rel)
        if os.path.exists(full):
            return full
    pytest.skip("No test WAV files available")


@pytest.fixture
def audio_chunks(test_wav_path: str) -> List[np.ndarray]:
    """Pre-loaded audio chunks from test WAV (first 30)."""
    return wav_to_float32_chunks(test_wav_path, max_chunks=30)


@pytest.fixture(scope="session")
def bridge_server():
    """Start API Bridge on test port, yield port, teardown. Session-scoped."""
    proc = subprocess.Popen(
        [
            "python3",
            os.path.join(PROJECT_ROOT, "api_bridge_server.py"),
            "--port", str(DEFAULT_API_BRIDGE_PORT),
            "--api-mode", "audio",
        ],
        cwd=PROJECT_ROOT,
        env={**os.environ, "CRADLECOACH_API_KEY": API_KEY},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)
    yield DEFAULT_API_BRIDGE_PORT
    proc.kill()
    proc.wait(timeout=5)
