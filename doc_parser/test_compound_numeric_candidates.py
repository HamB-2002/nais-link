import unittest

from doc_parser.numeric_candidates import extract_numeric_candidates


def extract_one(text: str) -> dict[str, object]:
    candidates = extract_numeric_candidates({"type": "paragraph", "text": text, "page": 13, "order": 51})
    assert len(candidates) == 1, candidates
    return candidates[0]


class CompoundNumericCandidateTests(unittest.TestCase):
    def test_p_value_inequalities_preserve_operator_and_statistic(self) -> None:
        for text, operator, value in [
            ("p < 0.05", "<", 0.05),
            ("p ≤ 0.01", "≤", 0.01),
            ("p > 0.10", ">", 0.10),
            ("p ≥ 0.001", "≥", 0.001),
        ]:
            with self.subTest(text=text):
                candidate = extract_one(text)
                self.assertEqual(candidate["raw"], text)
                self.assertEqual(candidate["value"], value)
                self.assertEqual(candidate["operator"], operator)
                self.assertEqual(candidate["statistic"], "p")

    def test_plus_minus_preserves_error_and_outer_unit(self) -> None:
        for text, value, error, unit in [
            ("3.14 ± 0.21", 3.14, 0.21, ""),
            ("87.3 ± 2.1%", 87.3, 2.1, "%"),
        ]:
            with self.subTest(text=text):
                candidate = extract_one(text)
                self.assertEqual(candidate["raw"], text)
                self.assertEqual(candidate["value"], value)
                self.assertEqual(candidate["error"], error)
                self.assertEqual(candidate["unit"], unit)

    def test_ranges_preserve_both_endpoints_and_unit(self) -> None:
        for text, start, end, unit in [
            ("10~20", 10.0, 20.0, ""),
            ("10–20", 10.0, 20.0, ""),
            ("10-20", 10.0, 20.0, ""),
            ("3.2~4.7%", 3.2, 4.7, "%"),
            ("20명~30명", 20.0, 30.0, "명"),
        ]:
            with self.subTest(text=text):
                candidate = extract_one(text)
                self.assertEqual(candidate["raw"], text)
                self.assertEqual(candidate["value"], start)
                self.assertEqual(candidate["range_end"], end)
                self.assertEqual(candidate["unit"], unit)

    def test_confidence_intervals_keep_level_and_bounds(self) -> None:
        for text in ["95% CI: 1.2–2.4", "95% CI [1.2, 2.4]", "95% CI = 1.2–2.4"]:
            with self.subTest(text=text):
                candidate = extract_one(text)
                self.assertEqual(candidate["raw"], text)
                self.assertEqual(candidate["value"], 1.2)
                self.assertEqual(candidate["confidence_level"], 95.0)
                self.assertEqual(candidate["range_start"], 1.2)
                self.assertEqual(candidate["range_end"], 2.4)

    def test_unicode_scientific_notation(self) -> None:
        for text, value in [("1.2 × 10⁻³", 0.0012), ("10⁻³", 0.001)]:
            with self.subTest(text=text):
                candidate = extract_one(text)
                self.assertEqual(candidate["raw"], text)
                self.assertEqual(candidate["value"], value)
                self.assertEqual(candidate["unit"], "")


if __name__ == "__main__":
    unittest.main()
