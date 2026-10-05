import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from algorithm.frontend_scheduler import run_scheduler_for_courses


class SchedulerHandler(BaseHTTPRequestHandler):

    def _send_json(self, status_code, data):
        body = json.dumps(data, default=str).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))

        if length <= 0:
            return {}

        raw = self.rfile.read(length)

        if not raw:
            return {}

        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON request body: {exc}") from exc

    def do_POST(self):
        if self.path != "/schedule":
            self._send_json(
                404,
                {
                    "status": "ERROR",
                    "success": False,
                    "error": "Endpoint not found",
                },
            )
            return

        try:
            request = self._read_json_body()

            course_codes = request.get("course_codes")
            enrollment_overrides = request.get(
                "enrollment_overrides",
                {},
            )

            if not isinstance(course_codes, list):
                self._send_json(
                    400,
                    {
                        "status": "ERROR",
                        "success": False,
                        "error": (
                            "course_codes must be a JSON array. "
                            "The API no longer falls back to the "
                            "default full database schedule."
                        ),
                    },
                )
                return

            if not isinstance(enrollment_overrides, dict):
                self._send_json(
                    400,
                    {
                        "status": "ERROR",
                        "success": False,
                        "error": "enrollment_overrides must be a JSON object",
                    },
                )
                return

            # IMPORTANT:
            # Schedule exactly the courses supplied by Streamlit/n8n.
            # Do NOT call run_scheduler(), because that schedules the
            # entire database and can reintroduce unrelated conflicts.
            result = run_scheduler_for_courses(
                course_codes,
                enrollment_overrides,
            )

            # CONFLICT is a valid scheduler result, not an HTTP failure.
            # Always return 200 for a completed scheduling attempt so n8n
            # can inspect status/success and choose the correct IF branch.
            self._send_json(200, result)

        except ValueError as exc:
            self._send_json(
                400,
                {
                    "status": "ERROR",
                    "success": False,
                    "error": str(exc),
                },
            )

        except Exception as exc:
            self._send_json(
                500,
                {
                    "status": "ERROR",
                    "success": False,
                    "error": str(exc),
                },
            )

    def do_GET(self):
        if self.path == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "auto-scheduler",
                },
            )
            return

        self._send_json(
            404,
            {
                "status": "ERROR",
                "success": False,
                "error": "Endpoint not found",
            },
        )

    def log_message(self, format, *args):
        print(f"[api] {format % args}")


def main():
    server = ThreadingHTTPServer(
        ("0.0.0.0", 8000),
        SchedulerHandler,
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
