import unittest

from doc_parser.non_verification_filter import filter_obvious_non_verification_candidates
from doc_parser.numeric_candidates import extract_numeric_candidates


def extract_and_filter(text: str) -> list[dict[str, object]]:
    node = {"type": "paragraph", "text": text, "page": 13, "order": 51}
    return filter_obvious_non_verification_candidates(extract_numeric_candidates(node))


class NonVerificationFilterTests(unittest.TestCase):
    def assert_decisions(self, text: str, expected: list[tuple[str, bool, str | None]]) -> None:
        actual = extract_and_filter(text)
        self.assertEqual(
            [(item["raw"], item["exclude"], item["exclude_reason"]) for item in actual],
            expected,
        )

    def test_year_does_not_remove_other_results(self) -> None:
        self.assert_decisions(
            "2025년 조사 결과 총 1,248명을 분석했으며 정확도는 87.3%였다.",
            [("2025년", True, "year"), ("1,248명", False, None), ("87.3%", False, None)],
        )

    def test_table_number_does_not_remove_mean(self) -> None:
        self.assert_decisions(
            "표 3에서 실험군의 평균은 12.7이었다.",
            [("3", True, "table_number"), ("12.7", False, None)],
        )

    def test_figure_number_does_not_remove_accuracy(self) -> None:
        self.assert_decisions(
            "그림 2는 모델 정확도 91.4%를 보여준다.",
            [("2", True, "figure_number"), ("91.4%", False, None)],
        )

    def test_named_section_does_not_remove_count(self) -> None:
        self.assert_decisions(
            "제2장에서는 350명의 조사 결과를 분석한다.",
            [("2", True, "section_number"), ("350명", False, None)],
        )

    def test_outline_section_number_only_at_line_start(self) -> None:
        self.assert_decisions("2.1 연구방법", [("2.1", True, "section_number")])

    def test_complete_date_labels_each_component_as_date(self) -> None:
        self.assert_decisions(
            "2026년 9월 30일 기준 응답률은 73.2%였다.",
            [
                ("2026년", True, "date"),
                ("9월", True, "date"),
                ("30일", True, "date"),
                ("73.2%", False, None),
            ],
        )

    def test_page_number_does_not_remove_coefficient(self) -> None:
        self.assert_decisions(
            "p. 15의 분석 결과 회귀계수는 0.382였다.",
            [("15", True, "page_number"), ("0.382", False, None)],
        )

    def test_explicit_structural_forms_are_excluded(self) -> None:
        self.assert_decisions(
            "<표 2-1> [그림 4] Figure 3 Fig. 2 제3절 2.1 연구방법 15쪽 페이지 23 [12] [3, 5] [7-9]",
            [
                ("2", True, "table_number"),
                ("1", True, "table_number"),
                ("4", True, "figure_number"),
                ("3", True, "figure_number"),
                ("2", True, "figure_number"),
                ("3", True, "section_number"),
                ("2.1", False, None),
                ("15쪽", True, "page_number"),
                ("23", True, "page_number"),
                ("12", True, "reference_number"),
                ("3", True, "reference_number"),
                ("5", True, "reference_number"),
                ("7", True, "reference_number"),
                ("9", True, "reference_number"),
            ],
        )

    def test_ambiguous_prose_decimal_and_bracketed_result_remain(self) -> None:
        self.assert_decisions(
            "모델의 평균은 2.1이고 신뢰구간은 [12.7%]였다.",
            [("2.1", False, None), ("12.7%", False, None)],
        )

    def test_input_candidates_are_not_mutated_or_deleted(self) -> None:
        candidates = extract_numeric_candidates({"text": "2025년 평균 12.7"})
        result = filter_obvious_non_verification_candidates(candidates)
        self.assertEqual(len(result), len(candidates))
        self.assertNotIn("exclude", candidates[0])
        self.assertEqual(result[0]["exclude_reason"], "year")


if __name__ == "__main__":
    unittest.main()
