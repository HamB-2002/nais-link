# /// script
# requires-python = ">=3.12"
# ///
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _draft_directory() -> Path:
    return Path(__file__).with_name("web_draft")


def main() -> None:
    handler = partial(SimpleHTTPRequestHandler, directory=str(_draft_directory()))
    server = ThreadingHTTPServer(("127.0.0.1", 8765), handler)
    print("숫자내력 웹 초안: http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
