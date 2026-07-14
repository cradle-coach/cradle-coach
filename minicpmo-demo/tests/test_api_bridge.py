"""Integration tests for API Bridge — mode routing, chat, and audio pipeline."""

import json
import os

import numpy as np
import pytest
import websockets

from tests.audio_fixtures import (
    AudioSession,
    b64_float32,
    require_api_key,
)

pytest_plugins = ["tests.audio_fixtures"]

API_BRIDGE_HOST = "127.0.0.1"


def _ws_url(port: int, mode: str = "") -> str:
    base = f"ws://{API_BRIDGE_HOST}:{port}/v1/realtime"
    return f"{base}?mode={mode}" if mode else base


class TestModeRouting:
    """Verify ?mode= parameter routing from client URL to Cloud API mode."""

    @pytest.mark.asyncio
    async def test_chat_mode_explicit(self, bridge_server):
        """?mode=chat → turn_based session."""
        require_api_key()
        async with websockets.connect(
            _ws_url(bridge_server, "chat"), max_size=128 * 1024 * 1024
        ) as ws:
            await ws.send(json.dumps({"type": "session.init", "payload": {}}))
            async for raw in ws:
                event = json.loads(raw)
                if event.get("type") == "session.created":
                    assert event.get("mode") == "turn_based"
                    return

    @pytest.mark.asyncio
    async def test_audio_mode_default(self, bridge_server):
        """No ?mode= → full_duplex (audio default)."""
        require_api_key()
        async with websockets.connect(
            _ws_url(bridge_server), max_size=128 * 1024 * 1024
        ) as ws:
            await ws.send(json.dumps({"type": "session.init", "payload": {}}))
            async for raw in ws:
                event = json.loads(raw)
                if event.get("type") == "session.created":
                    assert event.get("mode") == "full_duplex"
                    return


class TestChatConversation:
    """Complete text chat roundtrip through API Bridge."""

    @pytest.mark.asyncio
    async def test_chat_roundtrip(self, bridge_server):
        """Send text message → receive text response."""
        require_api_key()
        async with websockets.connect(
            _ws_url(bridge_server, "chat"), max_size=128 * 1024 * 1024
        ) as ws:
            await ws.send(json.dumps({"type": "session.init", "payload": {}}))

            got_created = False
            response_text = []

            async for raw in ws:
                event = json.loads(raw)
                etype = event.get("type", "")

                if etype == "session.created" and not got_created:
                    got_created = True
                    await ws.send(json.dumps({
                        "type": "input.append",
                        "input": {
                            "messages": [{"role": "user", "content": "Hello"}],
                            "streaming": True,
                            "generation": {"max_new_tokens": 32},
                        },
                    }))

                elif etype == "response.output.delta":
                    if event.get("kind") == "text":
                        response_text.append(event.get("text", ""))

                elif etype == "response.done":
                    break

            assert got_created, "session.created not received"
            assert len(response_text) > 0, "No text response"
            assert len("".join(response_text)) > 0


class TestAudioPipeline:
    """Audio pipeline: WAV → PCM chunks → Cloud API → verify processing.

    All audio WS tests share a single connection to avoid repeated API queue waits.
    """

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_audio_full_pipeline(self, bridge_server, audio_chunks):
        """Complete audio pipeline in one connection:

        1. session.init → session.created (full_duplex)
        2. Send 20 audio chunks → verify listen events
        3. Verify format validity
        """
        require_api_key()
        async with websockets.connect(
            _ws_url(bridge_server), max_size=128 * 1024 * 1024
        ) as ws:
            # Step 1: Session setup
            session = AudioSession(ws)
            sid = await session.init()
            assert sid, "No session_id"
            assert session.mode == "full_duplex", \
                f"Expected full_duplex, got {session.mode}"

            # Step 2: Send audio and verify Cloud API processing
            await session.send_audio_chunks(audio_chunks[:20])
            result = await session.collect_responses(max_events=30, timeout=12.0)

            has_response = (
                result["listen"] > 0
                or len(result["text"]) > 0
                or result["audio"] > 0
            )
            assert has_response, f"No response events: {result}"

    def test_audio_chunk_format(self, audio_chunks):
        """Verify audio chunks are correctly formatted for Cloud API."""
        assert len(audio_chunks) > 0, "No audio chunks loaded"
        for i, chunk in enumerate(audio_chunks[:3]):
            assert chunk.dtype == np.float32, \
                f"Chunk {i}: expected float32, got {chunk.dtype}"
            assert chunk.ndim == 1, \
                f"Chunk {i}: expected 1D, got {chunk.ndim}D"
            assert abs(chunk).max() <= 1.0, \
                f"Chunk {i}: values exceed [-1, 1]"

    def test_b64_encoding(self, audio_chunks):
        """Verify base64 encoding roundtrip."""
        chunk = audio_chunks[0]
        encoded = b64_float32(chunk)
        assert isinstance(encoded, str), "b64_float32 must return str"
        assert len(encoded) > 0, "Empty encoding"

        import base64
        decoded = np.frombuffer(
            base64.b64decode(encoded), dtype="<f4"
        )
        np.testing.assert_array_almost_equal(decoded, chunk, decimal=5)
