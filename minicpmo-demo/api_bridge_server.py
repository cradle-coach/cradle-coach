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
import time
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


# ── Emergency Alert ────────────────────────────────────────

_emergency_alert = None
_pending_emergency_guidance: str = ""


def _init_emergency_alert():
    """Initialize the emergency alert module (lazy import)."""
    global _emergency_alert
    if _emergency_alert is None:
        from gateway_modules.emergency_alert import EmergencyAlert, AlertLevel
        _emergency_alert = EmergencyAlert()
        logger.info("EmergencyAlert initialized")


def _check_emergency(text: str) -> None:
    """Check user input for extreme emotion keywords. Sets guidance if triggered."""
    global _pending_emergency_guidance
    if _emergency_alert is None:
        return
    event = _emergency_alert.check(text)
    from gateway_modules.emergency_alert import AlertLevel
    if event.level == AlertLevel.RED:
        logger.warning("Emergency RED: keyword=%s", event.keyword)
        _pending_emergency_guidance = _emergency_alert.RED_GUIDANCE_TEXT
    elif event.level == AlertLevel.YELLOW:
        logger.info("Emergency YELLOW: keyword=%s count=%d",
                    event.keyword, _emergency_alert._yellow_count)
        _pending_emergency_guidance = _emergency_alert.YELLOW_GUIDANCE_TEXT


def _check_input_safety(text: str) -> str:
    """Check user input through safety middleware. Returns filtered text."""
    if _safety_middleware is None:
        return text
    result = _safety_middleware.check(text)
    if not result.passed:
        logger.warning("Input safety blocked: rule=%d reason=%s",
                       result.rule_index, result.intercept_reason)
        return result.filtered_tokens
    return text


# ── Silence & Conversation Control ─────────────────────────

_silence_controller = None
_conversation_flow = None
LAST_MESSAGE_TIME: float = 0.0
SILENCE_EXIT_SECONDS = 60


def _init_conversation_control():
    """Initialize silence controller and conversation flow."""
    global _silence_controller, _conversation_flow, LAST_MESSAGE_TIME
    from gateway_modules.silence_controller import SilenceController
    from gateway_modules.conversation_flow import ConversationFlow

    def _on_exit_callback():
        logger.info("SilenceController triggered exit after %ds",
                    SILENCE_EXIT_SECONDS)

    _silence_controller = SilenceController(exit_manager=_on_exit_callback)
    _conversation_flow = ConversationFlow()
    LAST_MESSAGE_TIME = time.time()
    logger.info("SilenceController + ConversationFlow initialized")


def _touch_message_time():
    """Update last message timestamp."""
    global LAST_MESSAGE_TIME
    LAST_MESSAGE_TIME = time.time()


def _check_silence() -> Optional[str]:
    """Check if conversation has been silent too long. Returns exit message if so."""
    if _silence_controller is None:
        return None
    elapsed = time.time() - LAST_MESSAGE_TIME
    if elapsed >= SILENCE_EXIT_SECONDS:
        logger.info("Silence timeout: %.0fs — triggering exit", elapsed)
        return "今天的练习到这里。你刚才很努力！现在去找爸爸妈妈，给他们看看你做到的事。下次见！"
    return None


# ── Exit Manager & Observability ────────────────────────────

_exit_manager = None
_observability = None


def _init_exit_and_observability():
    """Initialize exit manager and observability."""
    global _exit_manager, _observability
    from gateway_modules.exit_manager import ExitManager
    from gateway_modules.observability import Observability
    _exit_manager = ExitManager()
    _observability = Observability()
    logger.info("ExitManager + Observability initialized")


def _check_exit_keyword(text: str) -> Optional[str]:
    """Check if text contains exit keyword. Returns exit message if so."""
    if _exit_manager is None:
        return None
    result = _exit_manager.check_exit_keyword(text)
    if result.should_exit:
        _exit_manager.mark_exited()
        if _observability:
            _observability._write_log("sessions", {
                "event": "exit_keyword",
                "reason": result.reason,
            })
        return result.exit_message
    return None


def _get_conversation_hint() -> str:
    """Get conversation flow hint for system prompt injection."""
    if _conversation_flow is None:
        return ""
    if _conversation_flow.should_force_statement():
        return " [下一轮请使用陈述句，不要提问]"
    hint = _conversation_flow.get_difficulty_hint()
    return f" {hint}" if hint else ""


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
            nonlocal _first_input
            async for raw in worker_ws:
                msg = _decode_event(raw)
                mtype = msg.get("type", "")
                _touch_message_time()  # user activity prevents silence timeout
                # Mark activity for exit manager
                if _exit_manager:
                    _exit_manager.mark_activity()
                # Check for exit keywords + update conversation flow
                if mtype == "input.append":
                    inp = msg.get("input", {})
                    msgs = inp.get("messages", [])
                    if msgs:
                        last_content = msgs[-1].get("content", "")
                        if isinstance(last_content, str):
                            # Check exit keywords first
                            exit_msg = _check_exit_keyword(last_content)
                            if exit_msg:
                                await worker_ws.send(json.dumps({
                                    "type": "response.output.delta",
                                    "kind": "text", "text": exit_msg,
                                }))
                                await worker_ws.send(json.dumps(
                                    {"type": "response.done"}))
                                await worker_ws.send(json.dumps(
                                    {"type": "session.closed"}))
                                return
                            # Check emergency alert on user input
                            _maybe_emergency_guidance = _check_emergency(last_content)
                            # Check input safety (privacy, hard blocks)
                            last_content = _check_input_safety(last_content)
                            # Update conversation flow
                            conv_flow = _conversation_flow
                            if conv_flow:
                                conv_flow.on_user_response(last_content, True)
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
                # Silence check — if silent too long, replace AI output with exit msg
                if etype == "response.output.delta" and event.get("kind") == "text":
                    exit_msg = _check_silence()
                    if exit_msg:
                        event = {"type": "response.output.delta",
                                 "kind": "text", "text": exit_msg}
                        await worker_ws.send(json.dumps(event))
                        await worker_ws.send(json.dumps(
                            {"type": "response.done"}))
                        await worker_ws.send(json.dumps(
                            {"type": "session.closed"}))
                        return
                    # Safety check + conversation hint injection
                    text = event.get("text", "")
                    filtered = _check_safety(text)
                    hint = _get_conversation_hint()
                    if hint:
                        filtered = filtered.rstrip() + hint
                    # Inject emergency guidance if pending (RED/YELLOW)
                    global _pending_emergency_guidance
                    if _pending_emergency_guidance:
                        filtered = _pending_emergency_guidance + "\n\n" + filtered
                        _pending_emergency_guidance = ""
                    if filtered != text:
                        event = dict(event)
                        event["text"] = filtered
                    _touch_message_time()
                    # Mark activity for exit manager
                    if _exit_manager:
                        _exit_manager.mark_activity()
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
    _init_emergency_alert()
    _init_conversation_control()
    _init_exit_and_observability()

    asyncio.run(main(host=args.host, port=args.port))
