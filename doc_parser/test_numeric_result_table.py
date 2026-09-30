import unittest

from doc_parser.numeric_result_table import (
    format_numeric_results,
    select_results_by_status,
    select_verify_results,
    to_markdown_table,
)


class NumericResultTableTests(unittest.TestCase):
    def test_paragraph_and_caption_display_locations(self) -> None:
        results = format_numeric_results(
            [
                {"raw": "15", "value": 15.0, "type": "paragraph", "page": None, "order": 12},
                {"raw": "87.3%", "value": 87.3, "type": "paragraph", "page": 10, "order": 12},
                {"raw": "3", "value": 3.0, "type": "caption", "page": 4, "order": 8},
            ]
        )

        self.assertEqual(results[0]["display_location"], "문단 #12")
        self.assertEqual(results[1]["display_location"], "p.10 · 문단 #12")
        self.assertEqual(results[2]["display_location"], "p.4 · 캡션 #8")
        self.assertIsNone(results[0]["row"])
        self.assertIsNone(results[0]["column"])

    def test_table_coordinates_are_preserved_and_displayed_one_based(self) -> None:
        candidate = {
            "raw": "26.5%",
            "value": 26.5,
            "unit": "%",
            "type": "table",
            "page": 10,
            "order": 23,
            "row": 1,
            "column": 2,
        }

        result = format_numeric_results([candidate])[0]

        self.assertEqual((result["row"], result["column"]), (1, 2))
        self.assertEqual(result["display_location"], "p.10 · 표 block #23 · 2행 3열")

    def test_table_without_coordinates_and_missing_contract_fields_are_safe(self) -> None:
        results = format_numeric_results(
            [
                {"raw": "15", "type": "table", "page": None, "order": 23},
                {"raw": "?"},
            ]
        )

        self.assertEqual(results[0]["display_location"], "표 block #23")
        self.assertIsNone(results[0]["row"])
        self.assertIsNone(results[0]["column"])
        self.assertEqual(results[1]["display_location"], "block #?")

    def test_statuses_and_selectors_preserve_all_result_types(self) -> None:
        source = [
            {"raw": "1", "verification_status": "VERIFY"},
            {"raw": "2", "verification_status": "IGNORE"},
            {"raw": "3", "verification_status": "UNCERTAIN"},
        ]
        results = format_numeric_results(source)

        self.assertEqual([row["verification_status"] for row in results], ["VERIFY", "IGNORE", "UNCERTAIN"])
        self.assertEqual([row["raw"] for row in select_results_by_status(results, "IGNORE")], ["2"])
        self.assertEqual([row["raw"] for row in select_verify_results(results)], ["1"])

    def test_invalid_status_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            select_results_by_status([], "DELETE")

    def test_compound_and_unknown_fields_are_preserved(self) -> None:
        candidate = {
            "raw": "95% CI: 1.2–2.4",
            "value": 1.2,
            "operator": "<",
            "statistic": "p",
            "error": 0.21,
            "range_start": 1.2,
            "range_end": 2.4,
            "confidence_level": 95.0,
            "future_field": {"origin": "extension"},
        }

        result = format_numeric_results([candidate])[0]

        for field in (
            "operator",
            "statistic",
            "error",
            "range_start",
            "range_end",
            "confidence_level",
            "future_field",
        ):
            self.assertEqual(result[field], candidate[field])

    def test_formatter_and_selector_do_not_mutate_inputs(self) -> None:
        candidate = {"raw": "15", "type": "paragraph", "page": None, "order": 1, "verification_status": "VERIFY"}
        candidates = [candidate]

        results = format_numeric_results(candidates)
        selected = select_verify_results(results)
        selected[0]["raw"] = "changed"

        self.assertNotIn("display_location", candidate)
        self.assertNotIn("row", candidate)
        self.assertEqual(results[0]["raw"], "15")
        self.assertEqual(candidate["raw"], "15")

    def test_markdown_escapes_pipe_newline_and_none(self) -> None:
        markdown = to_markdown_table(
            [
                {
                    "display_location": "문단 #1",
                    "raw": "26.5%",
                    "value": 26.5,
                    "unit": "%",
                    "context": "해외 | 일반\n26.5%",
                    "verification_status": "VERIFY",
                    "verification_method": None,
                }
            ]
        )

        self.assertIn("해외 \\| 일반<br>26.5%", markdown)
        self.assertIn("| — |", markdown)


if __name__ == "__main__":
    unittest.main()
