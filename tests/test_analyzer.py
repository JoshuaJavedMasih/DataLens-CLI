import tempfile
import unittest
from pathlib import Path

from datalens.analyzer import infer_type, profile_csv
from datalens.report import render_html, render_terminal


class AnalyzerTests(unittest.TestCase):
    def test_infers_common_types(self):
        self.assertEqual(infer_type(["1", "2", "3"]), "integer")
        self.assertEqual(infer_type(["1.5", "2"]), "number")
        self.assertEqual(infer_type(["yes", "no"]), "boolean")
        self.assertEqual(infer_type(["2026-01-01", "2026-02-01"]), "date")
        self.assertEqual(infer_type(["Ada", "Grace"]), "text")

    def test_profiles_missing_values_duplicates_and_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            path.write_text("name,amount\nAda,10\nBob,20\nAda,10\nN/A,\n", encoding="utf-8")
            profile = profile_csv(path)
        self.assertEqual(profile["rows"], 4)
        self.assertEqual(profile["duplicate_rows"], 1)
        self.assertEqual(profile["columns"][0]["missing"], 1)
        self.assertEqual(profile["columns"][1]["numeric"]["mean"], 13.333)

    def test_renderers_include_profile_content(self):
        profile = {"file": "tiny.csv", "rows": 1, "columns_count": 1, "duplicate_rows": 0, "columns": [{"name": "city", "type": "text", "missing": 0, "missing_percent": 0, "unique": 1, "top_values": [{"value": "Paris", "count": 1}]}]}
        self.assertIn("Paris", render_terminal(profile))
        self.assertIn("Paris", render_html(profile))


if __name__ == "__main__":
    unittest.main()
