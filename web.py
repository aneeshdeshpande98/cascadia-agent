import json
import os
import uuid
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

from agent import Agent

HOST = "127.0.0.1"
PORT = int(os.getenv("PORT", "8000"))
STATIC_DIR = Path(__file__).parent / "web"

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")


class ChatSession:
    def __init__(self) -> None:
        self.agent = Agent()
        self.lock = Lock()


sessions: dict[str, ChatSession] = {}
sessions_lock = Lock()


class ChatHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            self._handle_chat()
            return
        if parsed.path == "/api/reset":
            self._handle_reset()
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def end_headers(self) -> None:
        path = urlparse(self.path).path
        if path.endswith((".html", ".css", ".js")) or path in {"/", "/index.html"}:
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _handle_chat(self) -> None:
        payload = self._read_json()
        message = str(payload.get("message", "")).strip()
        if not message:
            self._send_json({"error": "Message cannot be empty."}, HTTPStatus.BAD_REQUEST)
            return

        session_id, is_new = self._session_id()
        chat_session = self._get_session(session_id)

        try:
            with chat_session.lock:
                reply = chat_session.agent.chat(message)
        except Exception as exc:
            self._send_json(
                {"error": "The agent hit an error while answering.", "detail": str(exc)},
                HTTPStatus.INTERNAL_SERVER_ERROR,
                session_id=session_id if is_new else None,
            )
            return

        self._send_json({"reply": reply}, session_id=session_id if is_new else None)

    def _handle_reset(self) -> None:
        session_id, is_new = self._session_id()
        with sessions_lock:
            sessions[session_id] = ChatSession()
        self._send_json({"ok": True}, session_id=session_id if is_new else None)

    def _read_json(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length).decode("utf-8")
        if not raw_body:
            return {}
        try:
            return json.loads(raw_body)
        except json.JSONDecodeError:
            return {}

    def _session_id(self) -> tuple[str, bool]:
        cookie_header = self.headers.get("Cookie", "")
        cookie = SimpleCookie(cookie_header)
        morsel = cookie.get("cascadia_session")
        if morsel and morsel.value:
            return morsel.value, False
        return uuid.uuid4().hex, True

    def _get_session(self, session_id: str) -> ChatSession:
        with sessions_lock:
            if session_id not in sessions:
                sessions[session_id] = ChatSession()
            return sessions[session_id]

    def _send_json(
        self,
        payload: dict,
        status: HTTPStatus = HTTPStatus.OK,
        session_id: Optional[str] = None,
    ) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if session_id:
            self.send_header("Set-Cookie", f"cascadia_session={session_id}; Path=/; SameSite=Lax")
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), ChatHandler)
    print(f"Cascadia chat UI running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
