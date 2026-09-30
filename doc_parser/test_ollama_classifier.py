import json
import unittest
from urllib.error import URLError

from doc_parser.non_verification_filter import filter_obvious_non_verification_candidates
from doc_parser.numeric_candidates import extract_numeric_candidates
from doc_parser.ollama_classifier import DEFAULT_ENDPOINT, DEFAULT_MODEL, OllamaClassifier
from doc_parser.verification_classifier import classify_candidates


class RecordingTransport:
    def __init__(self, response: bytes | Exception) -> None:
        self.response = response
        self.calls: list[tuple[dict[str, object], float, list[tuple[str, str]]]] = []

    def __call__(self, request, timeout_seconds: float) -> bytes:
        body = json.loads(request.data.decode("utf-8"))
        self.calls.append((body, timeout_seconds, request.header_items()))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def ollama_response(content: str, thinking: str | None = None) -> bytes:
    message = {"content": content}
    if thinking is not None:
        message["thinking"] = thinking
    return json.dumps({"message": message}).encode("utf-8")


def run_pipeline(text: str, classifier) -> list[dict[str, object]]:
    node = {"type": "paragraph", "text": text, "page": 13, "order": 51}
    candidates = extract_numeric_candidates(node)
    filtered = filter_obvious_non_verification_candidates(candidates)
    return classify_candidates(filtered, classifier=classifier)


class OllamaClassifierTests(unittest.TestCase):
    def test_default_request_uses_only_minimal_payload_and_local_settings(self) -> None:
        transport = RecordingTransport(ollama_response('{"status":"VERIFY","reason":"analysis result"}'))
        classifier = OllamaClassifier(transport=transport)
        payload = {"raw": "0.5", "unit": "", "context": "임계값은 0.5다.", "type": "paragraph", "page": 13}

        result = classifier(payload)

        self.assertEqual(result, {"status": "VERIFY", "reason": "analysis result"})
        self.assertEqual(classifier.model, DEFAULT_MODEL)
        self.assertEqual(classifier.endpoint, DEFAULT_ENDPOINT)
        request_body, _, headers = transport.calls[0]
        self.assertEqual(request_body["model"], "qwen3:8b")
        self.assertFalse(request_body["stream"])
        self.assertFalse(request_body["think"])
        self.assertEqual(request_body["options"], {"temperature": 0})
        self.assertEqual(json.loads(request_body["messages"][1]["content"]), {"raw": "0.5", "unit": "", "context": "임계값은 0.5다.", "type": "paragraph"})
        self.assertNotIn("Authorization", dict(headers))

    def test_thinking_field_is_ignored(self) -> None:
        transport = RecordingTransport(
            ollama_response('{"status":"IGNORE","reason":"metadata"}', thinking="hidden chain of thought")
        )
        result = OllamaClassifier(transport=transport)({"raw": "3", "unit": "", "context": "기간은 3년", "type": "paragraph"})
        self.assertEqual(result, {"status": "IGNORE", "reason": "metadata"})

    def test_failure_modes_fall_back_to_uncertain_in_pipeline(self) -> None:
        failure_responses = [
            TimeoutError("timed out"),
            URLError("connection refused"),
            ollama_response("not json"),
            ollama_response('{"status":"DELETE","reason":"invalid"}'),
            json.dumps({"error": "model unavailable"}).encode("utf-8"),
        ]
        for response in failure_responses:
            with self.subTest(response=response):
                transport = RecordingTransport(response)
                result = run_pipeline("임계값은 0.5로 설정하였다.", OllamaClassifier(transport=transport))[0]
                self.assertEqual(result["verification_status"], "UNCERTAIN")
                self.assertEqual(result["verification_method"], "rule")

    def test_excluded_and_rule_decided_candidates_skip_ollama(self) -> None:
        transport = RecordingTransport(ollama_response('{"status":"VERIFY","reason":"should not be used"}'))
        classifier = OllamaClassifier(transport=transport)

        excluded = run_pipeline("2025년", classifier)[0]
        verified = run_pipeline("총 1,248명을 분석하였다.", classifier)[0]
        ignored = run_pipeline("연구기간은 총 3년이었다.", classifier)[0]

        self.assertEqual(excluded["verification_status"], "IGNORE")
        self.assertEqual(verified["verification_status"], "VERIFY")
        self.assertEqual(ignored["verification_status"], "IGNORE")
        self.assertEqual(transport.calls, [])

    def test_only_rule_uncertain_candidate_calls_ollama(self) -> None:
        transport = RecordingTransport(ollama_response('{"status":"UNCERTAIN","reason":"needs review"}'))
        result = run_pipeline("임계값은 0.5로 설정하였다.", OllamaClassifier(transport=transport))[0]

        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(result["verification_status"], "UNCERTAIN")
        self.assertEqual(result["verification_reason"], "needs review")
        self.assertEqual(result["verification_method"], "llm")

    def test_external_endpoint_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            OllamaClassifier(endpoint="https://example.com/api/chat")


if __name__ == "__main__":
    unittest.main()
