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
from typing import Optional

import websockets
from websockets.asyncio.server import serve

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


def _api_ws_url() -> str:
    mode = os.getenv("CRADLECOACH_API_MODE", API_MODE)
    return f"wss://{API_REALTIME_HOST}{API_REALTIME_PATH}?mode={mode}"


def _api_headers() -> dict:
    if not API_KEY:
        raise RuntimeError(
            "CRADLECOACH_API_KEY is required."
        )
    return {"Authorization": f"Bearer {API_KEY}"}


def _decode_event(raw: str | bytes) -> dict:
    return json.loads(raw) if isinstance(raw, str) else json.loads(raw.decode())


# ── 单会话代理 ────────────────────────────────────────────

async def _proxy_session(
    worker_ws: websockets.ServerConnection,
) -> None:
    api_ws: Optional[websockets.ClientConnection] = None

    try:
        # 1. 连接 Cloud API
        url = _api_ws_url()
        logger.info("Connecting to Cloud API: %s", url)
        api_ws = await websockets.connect(
            url,
            additional_headers=_api_headers(),
            max_size=API_MAX_WS_SIZE,
        )

        # 2. 等待 API 就绪 + Worker 握手（两阶段管线）
        got_session_created = False
        async for raw in api_ws:
            event = _decode_event(raw)
            etype = event.get("type", "")
            if etype in ("session.queued", "session.queue_update"):
                logger.info("API queue: %s position=%s",
                            etype, event.get("position"))
            elif etype == "session.queue_done":
                break
            elif etype == "session.created":
                await worker_ws.send(json.dumps(event))
                got_session_created = True
                break
            else:
                logger.warning("Unexpected pre-init event: %s", etype)

        # 3. 转发 Worker 的 session.init，等 session.created
        raw_init = await worker_ws.recv()
        init_msg = _decode_event(raw_init)
        if init_msg.get("type") == "session.init":
            payload = dict(init_msg.get("payload", {}))
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
        async def worker_to_api():
            async for raw in worker_ws:
                msg = _decode_event(raw)
                mtype = msg.get("type", "")
                if mtype == "session.close":
                    await api_ws.send(json.dumps(msg))
                    return
                elif mtype == "input.append":
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


# ── 服务器入口 ────────────────────────────────────────────

async def main(host: str = "0.0.0.0", port: int = 22400):
    async def handler(ws: websockets.ServerConnection):
        logger.info("Worker connected")
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
    args = parser.parse_args()

    if args.api_mode:
        os.environ["CRADLECOACH_API_MODE"] = args.api_mode

    asyncio.run(main(host=args.host, port=args.port))
