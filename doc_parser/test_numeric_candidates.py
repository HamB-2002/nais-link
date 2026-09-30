import unittest

from doc_parser.numeric_candidates import extract_numeric_candidates


def node(text: str) -> dict[str, object]:
    return {"type": "paragraph", "text": text, "page": 13, "order": 51}


class ExtractNumericCandidatesTests(unittest.TestCase):
    def test_required_examples_preserve_raw_and_normalize_value(self) -> None:
        examples = [
            ("정확도는 87.3%였다.", "87.3%", 87.3, "%"),
            ("총 1,248명을 분석했다.", "1,248명", 1248.0, "명"),
            ("처리 시간은 3.21초다.", "3.21초", 3.21, "초"),
            ("효과는 2.7배다.", "2.7배", 2.7, "배"),
            ("증감률은 -4.2%다.", "-4.2%", -4.2, "%"),
            ("p = 0.032", "p = 0.032", 0.032, ""),
            ("추정치는 3.14 ± 0.21이다.", "3.14 ± 0.21", 3.14, ""),
            ("농도는 1.2×10^-3이다.", "1.2×10^-3", 0.0012, ""),
            ("예산은 12억 원이다.", "12억 원", 12.0, "억 원"),
            ("비용은 3,241만원이다.", "3,241만원", 3241.0, "만원"),
        ]

        for text, raw, value, unit in examples:
            with self.subTest(text=text):
                candidate = extract_numeric_candidates(node(text))[0]
                self.assertEqual(candidate["raw"], raw)
                self.assertEqual(candidate["value"], value)
                self.assertEqual(candidate["unit"], unit)
                self.assertEqual(text[candidate["start"] : candidate["end"]], raw)

    def test_plain_decimal_and_metadata_are_preserved(self) -> None:
        text = "2025년 조사 결과 총 1,248명의 데이터를 분석했으며 정확도는 87.3%였다."
        candidates = extract_numeric_candidates(node(text))

        self.assertEqual([item["raw"] for item in candidates], ["2025년", "1,248명", "87.3%"])
        self.assertEqual([item["value"] for item in candidates], [2025.0, 1248.0, 87.3])
        self.assertTrue(all(item["context"] == text for item in candidates))
        self.assertTrue(all(item["page"] == 13 for item in candidates))
        self.assertTrue(all(item["type"] == "paragraph" for item in candidates))
        self.assertTrue(all(item["order"] == 51 for item in candidates))

    def test_dates_and_section_numbers_are_not_filtered(self) -> None:
        candidates = extract_numeric_candidates(node("제2장 표 3은 2025년 7월 1일 기준이다."))
        self.assertEqual([item["raw"] for item in candidates], ["2", "3", "2025년", "7월", "1일"])

    def test_empty_or_non_string_text_returns_no_candidates(self) -> None:
        self.assertEqual(extract_numeric_candidates({"text": ""}), [])
        self.assertEqual(extract_numeric_candidates({"text": None}), [])


if __name__ == "__main__":
    unittest.main()
