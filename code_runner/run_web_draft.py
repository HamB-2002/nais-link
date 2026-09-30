# /// script
# requires-python = ">=3.12"
# ///
import json
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar

from code_runner.sample_catalog import catalog_payload
from code_runner.table_demo import JsonValue, demo_payload


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
        if self.path == "/api/table-reconciliation-demo":
            self._send_json(demo_payload())
            return
        super().do_GET()

    def _send_sample_catalog(self) -> None:
        samples = [dict(sample) for sample in catalog_payload(self.repository_root)]
        self._send_json({"samples": samples})

    def _send_json(self, payload: dict[str, JsonValue]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    DraftRequestHandler.repository_root = _repository_root()
    handler = partial(DraftRequestHandler, directory=str(_draft_directory()))
    port = int(os.environ.get("NAIS_WEB_DRAFT_PORT", "8765"))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"숫자내력 웹 초안: http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
