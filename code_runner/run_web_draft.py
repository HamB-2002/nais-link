# /// script
# requires-python = ">=3.12"
# ///
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

from code_runner.sample_catalog import catalog_payload


def _draft_directory() -> Path:
    return Path(__file__).with_name("web_draft")


def _repository_root() -> Path:
    return Path(__file__).parent.parent


class DraftRequestHandler(SimpleHTTPRequestHandler):
    repository_root: ClassVar[Path]

    def do_GET(self) -> None:
        if self.path == "/api/samples":
            self._send_sample_catalog()
            return
        super().do_GET()

    def _send_sample_catalog(self) -> None:
        body = json.dumps(
            {"samples": catalog_payload(self.repository_root)}, ensure_ascii=False
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    DraftRequestHandler.repository_root = _repository_root()
    handler = partial(DraftRequestHandler, directory=str(_draft_directory()))
    server = ThreadingHTTPServer(("127.0.0.1", 8765), handler)
    print("숫자내력 웹 초안: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
