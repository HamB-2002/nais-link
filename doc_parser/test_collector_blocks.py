import unittest

from doc_parser.non_verification_filter import filter_obvious_non_verification_candidates
from doc_parser.numeric_candidates import (
    extract_numeric_candidates,
    extract_numeric_candidates_from_blocks,
)
from doc_parser.verification_classifier import classify_candidates


class CollectorBlockNumericCandidateTests(unittest.TestCase):
    def test_paragraph_remains_text_driven(self) -> None:
        candidates = extract_numeric_candidates(
            {"type": "paragraph", "text": "평균은 15였다.", "page": 4, "order": 18}
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["raw"], "15")
        self.assertEqual(candidates[0]["context"], "평균은 15였다.")
        self.assertEqual(candidates[0]["page"], 4)
        self.assertEqual(candidates[0]["order"], 18)

    def test_caption_and_none_page_are_preserved(self) -> None:
        candidates = extract_numeric_candidates(
            {"type": "caption", "text": "그림의 정확도는 87.3%", "page": None, "order": 22}
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["raw"], "87.3%")
        self.assertEqual(candidates[0]["type"], "caption")
        self.assertIsNone(candidates[0]["page"])
        self.assertEqual(candidates[0]["order"], 22)

    def test_table_rows_extract_cells_with_row_context_and_coordinates(self) -> None:
        block = {
            "type": "table",
            "text": "항목\t수치\n평균\t15\n표준편차\t20",
            "page": 10,
            "order": 2,
            "rows": [["항목", "수치"], ["평균", "15"], ["표준편차", "20"]],
        }

        candidates = extract_numeric_candidates(block)

        self.assertEqual(
            [(item["raw"], item["row"], item["column"], item["context"]) for item in candidates],
            [("15", 1, 1, "평균 | 15"), ("20", 2, 1, "표준편차 | 20")],
        )
        self.assertTrue(all(item["type"] == "table" for item in candidates))
        self.assertTrue(all(item["page"] == 10 for item in candidates))
        self.assertTrue(all(item["order"] == 2 for item in candidates))
        self.assertEqual((candidates[0]["start"], candidates[0]["end"]), (0, 2))

    def test_table_rows_do_not_also_extract_rendered_text(self) -> None:
        block = {
            "type": "table",
            "text": "평균 15 평균 15",
            "page": 10,
            "order": 2,
            "rows": [["평균", "15"]],
        }

        candidates = extract_numeric_candidates(block)

        self.assertEqual([item["raw"] for item in candidates], ["15"])
        self.assertEqual((candidates[0]["row"], candidates[0]["column"]), (0, 1))

    def test_table_with_none_rows_falls_back_to_text_without_coordinates(self) -> None:
        candidates = extract_numeric_candidates(
            {
                "type": "table",
                "text": "평균 15",
                "page": 10,
                "order": 2,
                "rows": None,
            }
        )

        self.assertEqual([item["raw"] for item in candidates], ["15"])
        self.assertNotIn("row", candidates[0])
        self.assertNotIn("column", candidates[0])

    def test_table_with_empty_rows_does_not_fall_back_to_text(self) -> None:
        candidates = extract_numeric_candidates(
            {
                "type": "table",
                "text": "평균 15",
                "page": 10,
                "order": 2,
                "rows": [],
            }
        )

        self.assertEqual(candidates, [])

    def test_batch_extraction_preserves_block_order_values(self) -> None:
        blocks = [
            {"type": "paragraph", "text": "표본은 10명", "page": 1, "order": 90},
            {"type": "caption", "text": "정확도 87.3%", "page": None, "order": 4},
            {
                "type": "table",
                "text": "평균 15",
                "page": 3,
                "order": 500,
                "rows": [["평균", "15"]],
            },
        ]

        candidates = extract_numeric_candidates_from_blocks(blocks)

        self.assertEqual([item["raw"] for item in candidates], ["10명", "87.3%", "15"])
        self.assertEqual([item["order"] for item in candidates], [90, 4, 500])
        self.assertEqual((candidates[2]["row"], candidates[2]["column"]), (0, 1))

    def test_filter_and_classifier_preserve_table_coordinates(self) -> None:
        candidates = extract_numeric_candidates(
            {
                "type": "table",
                "text": "정확도 87.3%",
                "page": 10,
                "order": 2,
                "rows": [["정확도", "87.3%"]],
            }
        )

        filtered = filter_obvious_non_verification_candidates(candidates)
        classified = classify_candidates(filtered)

        self.assertEqual((classified[0]["row"], classified[0]["column"]), (0, 1))
        self.assertEqual(classified[0]["context"], "정확도 | 87.3%")
        self.assertEqual(classified[0]["verification_status"], "VERIFY")


if __name__ == "__main__":
    unittest.main()
