import unittest

from doc_parser.non_verification_filter import filter_obvious_non_verification_candidates
from doc_parser.numeric_candidates import extract_numeric_candidates
from doc_parser.verification_classifier import classify_candidates


def classify_text(text: str, classifier=None) -> list[dict[str, object]]:
    node = {"type": "paragraph", "text": text, "page": 13, "order": 51}
    candidates = extract_numeric_candidates(node)
    filtered = filter_obvious_non_verification_candidates(candidates)
    return classify_candidates(filtered, classifier=classifier)


class VerificationClassifierTests(unittest.TestCase):
    def assert_single_status(self, text: str, status: str) -> dict[str, object]:
        result = classify_text(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["verification_status"], status)
        self.assertEqual(result[0]["verification_method"], "rule")
        return result[0]

    def test_clear_analysis_results_are_verified(self) -> None:
        self.assert_single_status("총 1,248명을 분석하였다.", "VERIFY")
        self.assert_single_status("평균 소득은 3,241만원이었다.", "VERIFY")
        self.assert_single_status("모델 정확도는 87.3%였다.", "VERIFY")
        self.assert_single_status("p < 0.05였다.", "VERIFY")
        self.assert_single_status("95% CI는 1.2–2.4였다.", "VERIFY")

    def test_clear_metadata_is_ignored(self) -> None:
        self.assert_single_status("연구기간은 총 3년이었다.", "IGNORE")
        self.assert_single_status("Python 3.11을 사용하였다.", "IGNORE")

    def test_configuration_value_remains_uncertain(self) -> None:
        result = self.assert_single_status("임계값은 0.5로 설정하였다.", "UNCERTAIN")
        self.assertIn("configuration", result["verification_reason"])

    def test_excluded_candidate_skips_classifier(self) -> None:
        calls = []

        def fail_if_called(payload):
            calls.append(payload)
            raise AssertionError("excluded candidates must not call the classifier")

        result = classify_text("2025년", classifier=fail_if_called)[0]
        self.assertEqual(calls, [])
        self.assertEqual(result["exclude_reason"], "year")
        self.assertEqual(result["verification_status"], "IGNORE")
        self.assertEqual(result["verification_method"], "rule")

    def test_mock_classifier_receives_minimal_payload(self) -> None:
        received = []

        def mock_classifier(payload):
            received.append(payload)
            return {"status": "VERIFY", "reason": "mock: calibrated threshold output"}

        result = classify_text("임계값은 0.5로 설정하였다.", classifier=mock_classifier)[0]
        self.assertEqual(set(received[0]), {"raw", "unit", "context", "type"})
        self.assertEqual(result["verification_status"], "VERIFY")
        self.assertEqual(result["verification_reason"], "mock: calibrated threshold output")
        self.assertEqual(result["verification_method"], "llm")

    def test_invalid_classifier_response_falls_back_to_uncertain(self) -> None:
        result = classify_text("임계값은 0.5로 설정하였다.", classifier=lambda payload: {"status": "DELETE"})[0]
        self.assertEqual(result["verification_status"], "UNCERTAIN")
        self.assertEqual(result["verification_method"], "rule")
        self.assertIn("invalid classifier response", result["verification_reason"])

    def test_existing_fields_are_preserved_without_mutating_input(self) -> None:
        node = {"type": "paragraph", "text": "p < 0.05였다.", "page": 13, "order": 51}
        filtered = filter_obvious_non_verification_candidates(extract_numeric_candidates(node))
        result = classify_candidates(filtered)[0]
        self.assertEqual(result["value"], 0.05)
        self.assertEqual(result["operator"], "<")
        self.assertEqual(result["statistic"], "p")
        self.assertNotIn("verification_status", filtered[0])


if __name__ == "__main__":
    unittest.main()
