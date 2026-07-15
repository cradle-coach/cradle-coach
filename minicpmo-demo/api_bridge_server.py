"""
API Bridge Backend Server — MiniCPM-o 4.5 Cloud API 适配层。

替代本地 PyTorch Backend，将 Worker 的推理请求转发到
OpenBMB 官方托管 API (minicpmo45.modelbest.cn)。

用法：
  CRADLECOACH_API_KEY=sk-xxx python api_bridge_server.py --port 22400 --api-mode audio
"""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, urlparse

import websockets
from websockets.asyncio.server import serve

# Ensure project root is in path for gateway_modules imports
_PROJ_ROOT = Path(__file__).parent.parent
if str(_PROJ_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJ_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("api_bridge")

# ── API 配置 ──────────────────────────────────────────────
API_REALTIME_HOST = os.getenv(
    "CRADLECOACH_API_HOST", "minicpmo45.modelbest.cn"
)
API_REALTIME_PATH = "/v1/realtime"
API_KEY = os.getenv("CRADLECOACH_API_KEY")
API_MODE = os.getenv("CRADLECOACH_API_MODE", "audio")
API_MAX_WS_SIZE = 128 * 1024 * 1024


def _api_ws_url(mode: Optional[str] = None) -> str:
    if mode is None:
        mode = os.getenv("CRADLECOACH_API_MODE", API_MODE)
    return f"wss://{API_REALTIME_HOST}{API_REALTIME_PATH}?mode={mode}"


def _api_headers() -> dict:
    if not API_KEY:
        raise RuntimeError(
            "CRADLECOACH_API_KEY is required."
        )
    return {"Authorization": f"Bearer {API_KEY}"}


# ── System Prompt ──────────────────────────────────────────

_SYSTEM_PROMPT: Optional[str] = None


def _load_system_prompt(path: Optional[str]) -> None:
    """Load compliance System Prompt from YAML file."""
    global _SYSTEM_PROMPT
    if not path:
        return
    try:
        import yaml
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        _SYSTEM_PROMPT = config.get("system_prompt", "").strip()
        if _SYSTEM_PROMPT:
            logger.info("Loaded system prompt from %s (%d chars)",
                        path, len(_SYSTEM_PROMPT))
        else:
            logger.warning("System prompt file %s has no system_prompt field", path)
    except FileNotFoundError:
        logger.warning("System prompt file not found: %s", path)
    except Exception:
        logger.exception("Failed to load system prompt from %s", path)


def _inject_system_prompt(payload: dict) -> dict:
    """Inject compliance System Prompt if not already provided."""
    if _SYSTEM_PROMPT and "system_prompt" not in payload:
        payload = dict(payload)
        payload["system_prompt"] = _SYSTEM_PROMPT
    return payload


# ── Safety Middleware ──────────────────────────────────────

_safety_middleware = None


def _init_safety_middleware():
    """Initialize the safety middleware (lazy import)."""
    global _safety_middleware
    if _safety_middleware is None:
        from gateway_modules.safety_middleware import SafetyMiddleware
        _safety_middleware = SafetyMiddleware()
        logger.info("SafetyMiddleware initialized")


def _check_safety(text: str) -> str:
    """Check text through safety middleware. Returns filtered text if blocked."""
    if _safety_middleware is None:
        return text
    result = _safety_middleware.check(text)
    if not result.passed:
        logger.warning("Safety blocked: rule=%d reason=%s",
                       result.rule_index, result.intercept_reason)
        return result.filtered_tokens
    return text


def _decode_event(raw: str | bytes) -> dict:
    return json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode())


# ── 单会话代理 ────────────────────────────────────────────

async def _proxy_session(
    worker_ws: websockets.ServerConnection,
) -> None:
    api_ws: Optional[websockets.ClientConnection] = None

    try:
        # 1. 从客户端请求 URL 中提取 mode 参数
        client_mode = None
        try:
            req_path = worker_ws.request.path if worker_ws.request else ""
            parsed = urlparse(req_path)
            params = parse_qs(parsed.query)
            client_mode = params.get("mode", [None])[0]
        except Exception:
            client_mode = None
        logger.info("Client requested mode: %s (env fallback: %s)",
                    client_mode, API_MODE)

        # 2. 连接 Cloud API（优先使用客户端指定的 mode）
        url = _api_ws_url(mode=client_mode)
        logger.info("Connecting to Cloud API: %s", url)
        api_ws = await websockets.connect(
            url,
            additional_headers=_api_headers(),
            max_size=API_MAX_WS_SIZE,
        )

        # 2. 等待 API 就绪信号（带超时——video 模式不发任何事件）
        got_session_created = False
        async def _absorb_queue():
            async for raw in api_ws:
                event = _decode_event(raw)
                etype = event.get("type", "")
                if etype in ("session.queued", "session.queue_update"):
                    logger.info("API queue: %s position=%s",
                                etype, event.get("position"))
                elif etype == "session.queue_done":
                    await worker_ws.send(json.dumps(event))
                    return "queue_done"
                elif etype == "session.created":
                    await worker_ws.send(json.dumps(event))
                    return "session_created"
                else:
                    logger.warning("Unexpected pre-init event: %s", etype)
            return "closed"

        try:
            result = await asyncio.wait_for(_absorb_queue(), timeout=5.0)
            if result == "session_created":
                got_session_created = True
        except asyncio.TimeoutError:
            logger.info("Cloud API silent (video mode?) — proceeding to handshake")

        # 3. 转发 Worker 的 session.init，等 session.created
        raw_init = await worker_ws.recv()
        init_msg = _decode_event(raw_init)
        if init_msg.get("type") == "session.init":
            payload = _inject_system_prompt(dict(init_msg.get("payload", {})))
            payload.pop("mode", None)
            await api_ws.send(json.dumps(
                {"type": "session.init", "payload": payload}
            ))
            if not got_session_created:
                async for raw in api_ws:
                    event = _decode_event(raw)
                    if event.get("type") == "session.created":
                        await worker_ws.send(json.dumps(event))
                        break

        # 4. 双向消息循环
        _first_input = [True]  # mutable to allow modification in closure

        async def worker_to_api():
            async for raw in worker_ws:
                msg = _decode_event(raw)
                mtype = msg.get("type", "")
                if mtype == "session.close":
                    await api_ws.send(json.dumps(msg))
                    return
                elif mtype == "input.append":
                    # Inject system prompt into first input message for chat mode
                    if _first_input[0] and _SYSTEM_PROMPT:
                        _first_input[0] = False
                        inp = dict(msg.get("input", {}))
                        msgs = list(inp.get("messages", []))
                        if msgs:
                            msgs.insert(0, {
                                "role": "system",
                                "content": _SYSTEM_PROMPT,
                            })
                        inp["messages"] = msgs
                        await api_ws.send(json.dumps({
                            "type": "input.append",
                            "input": inp,
                        }))
                    else:
                        _first_input[0] = False
                        await api_ws.send(json.dumps(msg))
                else:
                    logger.debug("Dropping unknown: %s", mtype)

        async def api_to_worker():
            async for raw in api_ws:
                event = _decode_event(raw)
                etype = event.get("type", "")
                if etype in ("session.queued", "session.queue_update",
                             "session.queue_done"):
                    continue
                # Safety check on text output
                if etype == "response.output.delta" and event.get("kind") == "text":
                    text = event.get("text", "")
                    filtered = _check_safety(text)
                    if filtered != text:
                        event = dict(event)
                        event["text"] = filtered
                try:
                    await worker_ws.send(json.dumps(event))
                except websockets.ConnectionClosed:
                    return
                if etype == "session.closed":
                    return

        worker_task = asyncio.create_task(worker_to_api())
        api_task = asyncio.create_task(api_to_worker())

        await worker_task
        try:
            await asyncio.wait_for(api_task, timeout=10.0)
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for session.closed from API")
            api_task.cancel()
            try:
                await api_task
            except asyncio.CancelledError:
                pass

    except websockets.ConnectionClosed as e:
        logger.info("Connection closed: code=%s reason=%s", e.code, e.reason)
    except Exception:
        logger.exception("Session proxy error")
    finally:
        if api_ws is not None:
            try:
                await api_ws.close()
            except Exception:
                pass
        try:
            await worker_ws.close()
        except Exception:
            pass


# ── Half-Duplex Gateway 协议适配 ────────────────────────────

async def _proxy_half_duplex(
    browser_ws: websockets.ServerConnection,
    session_id: str,
) -> None:
    """将 half-duplex Gateway 协议翻译为 Cloud API 协议。

    Gateway 协议（浏览器 ↔ Gateway）:
      browser → prepare {system_content, config}
      gateway → prepared
      browser → audio_chunk {audio_base64}
      gateway → chunk {audio_base64, ...}
      gateway → done

    Cloud API 协议:
      client → session.init
      server → session.created
      client → input.append {audio, ...}
      server → response.output.delta
      server → response.done
    """
    api_ws: Optional[websockets.ClientConnection] = None

    try:
        # 1. 等待 prepare 消息（含 system_content）
        raw_prepare = await asyncio.wait_for(browser_ws.recv(), timeout=15.0)
        prepare_msg = _decode_event(raw_prepare)
        if prepare_msg.get("type") != "prepare":
            logger.warning("Half-duplex: expected prepare, got %s",
                           prepare_msg.get("type"))
            return

        system_content = prepare_msg.get("system_content", [])
        config = prepare_msg.get("config", {})
        tts_enabled = config.get("tts_enabled", True)
        logger.info("Half-duplex session %s: system_content=%d items, tts=%s",
                    session_id, len(system_content), tts_enabled)

        # 2. 连接 Cloud API (audio mode)
        url = _api_ws_url(mode="audio")
        logger.info("Connecting to Cloud API: %s", url)
        api_ws = await websockets.connect(
            url,
            additional_headers=_api_headers(),
            max_size=API_MAX_WS_SIZE,
        )

        # 3. 构建 session.init payload
        prompt_parts = []
        for item in system_content:
            if isinstance(item, dict) and item.get("type") == "text":
                prompt_parts.append(item.get("text", ""))
        system_prompt = "\n".join(prompt_parts) if prompt_parts else ""

        session_init_msg = json.dumps({
            "type": "session.init",
            "payload": {"system_prompt": system_prompt} if system_prompt else {},
        })

        # 4. 等待 Cloud API 就绪信号 → 发送 session.init → 等待 session.created
        got_session_created = False
        session_init_sent = False

        async for raw in api_ws:
            event = _decode_event(raw)
            etype = event.get("type", "")

            if etype in ("session.queued", "session.queue_update"):
                logger.info("API queue: %s position=%s", etype, event.get("position"))

            elif etype == "session.queue_done":
                # Cloud API 就绪 → 发送 session.init
                if not session_init_sent:
                    await api_ws.send(session_init_msg)
                    session_init_sent = True
                    logger.info("Half-duplex: sent session.init after queue_done")

            elif etype == "session.created":
                # Cloud API 直接创建了 session（无队列）→ 仍需发 session.init
                if not session_init_sent:
                    await api_ws.send(session_init_msg)
                    session_init_sent = True
                    logger.info("Half-duplex: sent session.init after direct session.created")
                # 翻译为 prepared 发给浏览器
                await browser_ws.send(json.dumps({
                    "type": "prepared",
                    "session_id": event.get("session_id", session_id),
                }))
                got_session_created = True
                break

            elif etype == "error":
                logger.error("Half-duplex init error: %s", event.get("error", ""))
                await browser_ws.send(json.dumps({
                    "type": "error",
                    "message": event.get("error", "unknown"),
                }))
                return

            else:
                logger.debug("Half-duplex pre-init: %s", etype)

        if not got_session_created:
            logger.warning("Half-duplex: never got session.created")
            return

        # 6. 双向消息循环
        async def browser_to_api():
            async for raw in browser_ws:
                msg = _decode_event(raw)
                mtype = msg.get("type", "")

                if mtype == "audio_chunk":
                    # 翻译 audio_chunk → input.append
                    audio_b64 = msg.get("audio_base64", "")
                    await api_ws.send(json.dumps({
                        "type": "input.append",
                        "input": {
                            "audio": audio_b64,
                            "force_listen": False,
                        },
                    }))
                elif mtype == "stop":
                    await api_ws.send(json.dumps({
                        "type": "session.close",
                        "reason": "user_stop",
                    }))
                    return
                else:
                    logger.debug("Half-duplex: dropping %s", mtype)

        async def api_to_browser():
            async for raw in api_ws:
                event = _decode_event(raw)
                etype = event.get("type", "")

                if etype in ("session.queued", "session.queue_update",
                             "session.queue_done"):
                    continue
                elif etype == "response.output.delta":
                    kind = event.get("kind", "")
                    if kind == "text":
                        await browser_ws.send(json.dumps({
                            "type": "chunk",
                            "text": event.get("text", ""),
                        }))
                    elif kind == "audio":
                        await browser_ws.send(json.dumps({
                            "type": "chunk",
                            "audio_base64": event.get("audio", ""),
                        }))
                    elif kind == "listen":
                        # Listen events are status-only, not forwarded to half-duplex UI
                        pass
                elif etype == "response.done":
                    await browser_ws.send(json.dumps({"type": "done"}))
                    return
                elif etype == "session.closed":
                    return
                else:
                    # Forward any unrecognized events as-is
                    try:
                        await browser_ws.send(json.dumps(event))
                    except websockets.ConnectionClosed:
                        return

        browser_task = asyncio.create_task(browser_to_api())
        api_task = asyncio.create_task(api_to_browser())

        await browser_task
        try:
            await asyncio.wait_for(api_task, timeout=10.0)
        except asyncio.TimeoutError:
            api_task.cancel()
            try:
                await api_task
            except asyncio.CancelledError:
                pass

    except asyncio.TimeoutError:
        logger.warning("Half-duplex: timeout waiting for prepare")
    except websockets.ConnectionClosed as e:
        logger.info("Half-duplex connection closed: code=%s", e.code)
    except Exception:
        logger.exception("Half-duplex proxy error")
    finally:
        if api_ws is not None:
            try:
                await api_ws.close()
            except Exception:
                pass
        try:
            await browser_ws.close()
        except Exception:
            pass


# ── 服务器入口 ────────────────────────────────────────────

async def main(host: str = "0.0.0.0", port: int = 22400):
    async def handler(ws: websockets.ServerConnection):
        path = ws.request.path if ws.request else "/"
        logger.info("Connection: %s", path)

        if path.startswith("/ws/half_duplex/"):
            session_id = path.rsplit("/", 1)[-1] if "/" in path else "unknown"
            await _proxy_half_duplex(ws, session_id)
        else:
            await _proxy_session(ws)

    stop = asyncio.get_running_loop().create_future()
    for sig in (signal.SIGINT, signal.SIGTERM):
        asyncio.get_running_loop().add_signal_handler(
            sig, lambda s=stop: (s.done() or s.set_result(None))
        )

    logger.info("API Bridge Backend starting on %s:%s → %s",
                host, port, _api_ws_url())
    async with serve(handler, host, port) as server:
        await stop
        logger.info("Shutting down...")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CradleCoach API Bridge Backend")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=22400)
    parser.add_argument(
        "--api-mode", default=API_MODE, choices=["chat", "audio", "video"],
    )
    parser.add_argument(
        "--system-prompt", default=None,
        help="Path to YAML file with CradleCoach compliance system prompt",
    )
    args = parser.parse_args()

    if args.api_mode:
        os.environ["CRADLECOACH_API_MODE"] = args.api_mode
    if args.system_prompt:
        _load_system_prompt(args.system_prompt)
    _init_safety_middleware()

    asyncio.run(main(host=args.host, port=args.port))
