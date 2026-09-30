"""Local-only Ollama adapter for numeric verification classification."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_MODEL = "qwen3:8b"
DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/chat"
_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost"})
_ALLOWED_STATUSES = frozenset({"VERIFY", "IGNORE", "UNCERTAIN"})
_PAYLOAD_FIELDS = ("raw", "unit", "context", "type")


class OllamaClassifierError(RuntimeError):
    """Raised when a local Ollama result cannot be safely used."""


Transport = Callable[[Request, float], bytes]


def _validate_local_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOCAL_HOSTS
        or parsed.username is not None
        or parsed.password is not None
    ):
        raise ValueError("Ollama endpoint must use localhost or 127.0.0.1 over HTTP")


def _default_transport(request: Request, timeout_seconds: float) -> bytes:
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise OllamaClassifierError("local Ollama request failed") from exc


class OllamaClassifier:
    """Callable adapter compatible with ``verification_classifier.Classifier``.

    It sends only the four fields already prepared by the provider-independent
    classifier interface.  No API key or external endpoint is supported.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        endpoint: str = DEFAULT_ENDPOINT,
        timeout_seconds: float = 30.0,
        transport: Transport | None = None,
    ) -> None:
        _validate_local_endpoint(endpoint)
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _default_transport

    def __call__(self, payload: dict[str, Any]) -> dict[str, str]:
        minimal_payload = {field: payload.get(field) for field in _PAYLOAD_FIELDS}
        request_body = {
            "model": self.model,
            "stream": False,
            "think": False,
            "options": {"temperature": 0},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You classify whether one numeric candidate is a re-execution "
                        "verification target for provenance tracing. "
                        "Do not calculate, create, or modify any number. "
                        "Follow this exact decision order: (1) VERIFY only with affirmative "
                        "evidence that it is an OUTPUT calculated by analysis code or data "
                        "processing, such as a mean, standard deviation, accuracy, regression "
                        "coefficient, p-value, confidence interval, analyzed sample count, or "
                        "calculated proportion; (2) IGNORE only with affirmative evidence that "
                        "it is an INPUT, SETTING, or METADATA value, such as a threshold or "
                        "cutoff, learning rate, epoch setting, hyperparameter, version, study "
                        "duration, or budget; (3) otherwise return UNCERTAIN. "
                        "Absence of output evidence is never evidence for IGNORE. A simple or "
                        "unlabeled number must be UNCERTAIN, not IGNORE. "
                        "Required examples: '값 | 12' and '수치 | 0.8' are UNCERTAIN; "
                        "'임계값 | 0.5' and '학습률 | 0.001' are IGNORE; "
                        "'정확도 | 87.3%' is VERIFY. "
                        "Return only one JSON object with exactly status and reason. "
                        "status must be VERIFY, IGNORE, or UNCERTAIN. "
                        "Do not include thinking, markdown, or any text outside the JSON."
                    ),
                },
                {"role": "user", "content": json.dumps(minimal_payload, ensure_ascii=False)},
            ],
        }
        encoded_body = json.dumps(request_body, ensure_ascii=False).encode("utf-8")
        request = Request(
            self.endpoint,
            data=encoded_body,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )

        try:
            response_bytes = self._transport(request, self.timeout_seconds)
            response = json.loads(response_bytes.decode("utf-8"))
            content = response["message"]["content"]
            if not isinstance(content, str):
                raise OllamaClassifierError("Ollama message.content is not text")
            final_json = json.loads(content.strip())
        except OllamaClassifierError:
            raise
        except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError, TimeoutError, OSError) as exc:
            raise OllamaClassifierError("Ollama response is invalid") from exc

        if not isinstance(final_json, Mapping):
            raise OllamaClassifierError("Ollama final content is not a JSON object")
        status = final_json.get("status")
        reason = final_json.get("reason")
        if status not in _ALLOWED_STATUSES or not isinstance(reason, str) or not reason.strip():
            raise OllamaClassifierError("Ollama final JSON has an invalid status or reason")
        return {"status": status, "reason": reason}
