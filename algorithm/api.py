import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from algorithm.run import run_scheduler


class SchedulerHandler(BaseHTTPRequestHandler):

    def _send_json(self, status_code, data):
        body = json.dumps(data, default=str).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()

        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/schedule":
            self._send_json(
                404,
                {"error": "Endpoint not found"}
            )
            return

        try:
            length = int(self.headers.get("Content-Length", 0))

            if length:
                self.rfile.read(length)

            result = run_scheduler()

            self._send_json(200, result)

        except Exception as e:
            self._send_json(
                500,
                {
                    "status": "ERROR",
                    "success": False,
                    "error": str(e)
                }
            )

    def do_GET(self):
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "auto-scheduler"
                }
            )
        else:
            self._send_json(
                404,
                {"error": "Endpoint not found"}
            )

    def log_message(self, format, *args):
        print(f"[api] {format % args}")


def main():
    server = ThreadingHTTPServer(
        ("0.0.0.0", 8000),
        SchedulerHandler
    )

    print("======================================")
    print(" Auto-Scheduler Python API")
    print(" http://localhost:8000")
    print(" POST /schedule")
    print(" GET  /health")
    print("======================================")

    server.serve_forever()


if __name__ == "__main__":
    main()
