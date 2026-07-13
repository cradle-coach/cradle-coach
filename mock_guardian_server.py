"""
CradleCoach Mock Guardian Server (mock_guardian_server.py)

PC 仿真阶段模拟家长 App 后端。
接收 emergency_alert.py 推送的预警，打印到控制台。

使用方式:
    python mock_guardian_server.py --port 8666
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import argparse
from datetime import datetime


class GuardianHandler(BaseHTTPRequestHandler):
    """家长端 Mock 请求处理器"""

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            self._print_alert(data)
        except json.JSONDecodeError:
            data = {"raw": body.decode()}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received"}).encode())

    def _print_alert(self, data: dict):
        severity = data.get("severity", "UNKNOWN")
        timestamp = data.get("timestamp", datetime.now().isoformat())

        if severity == "RED":
            prefix = "\n🔴🔴🔴 RED ALERT — 需立即关注 🔴🔴🔴"
        elif severity == "YELLOW":
            prefix = "\n🟡 YELLOW ALERT"
        else:
            prefix = "\n📢 ALERT"

        print(f"{prefix}")
        print(f"  时间: {timestamp}")
        print(f"  级别: {severity}")
        print(f"  事件: {data.get('event', 'N/A')}")
        print(f"  注意: 设备已进入安全模式，请家长关注\n")

    def log_message(self, format, *args):
        """抑制默认 HTTP 日志"""
        pass


def main():
    parser = argparse.ArgumentParser(description="CradleCoach Mock Guardian Server")
    parser.add_argument("--port", type=int, default=8666, help="监听端口")
    parser.add_argument("--host", type=str, default="localhost", help="监听地址")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), GuardianHandler)
    print(f"Mock Guardian Server 启动: http://{args.host}:{args.port}")
    print("等待接收预警推送...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
