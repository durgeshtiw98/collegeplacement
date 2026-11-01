"""End-to-end verification against the original seven workbook exports."""

import contextlib
import csv
import io
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from placement.cli import main
from placement.prepare import DataError
from placement.supplied import HEADERS, analyze, load, run

ROOT = Path(__file__).resolve().parents[1]


class SuppliedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source"
        shutil.copytree(ROOT / "data/raw", self.source)

    def update(self, table, field, value, index=0, duplicate=False):
        path = self.source / f"{table}.csv"
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            fields, rows = reader.fieldnames, list(reader)
        if duplicate:
            rows.append(rows[index].copy())
            index = len(rows) - 1
        if field:
            rows[index][field] = value
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def test_supplied_workbook_metrics_match_manual_counts(self):
        tables, quality, demo = load(self.source)
        result = analyze(tables, quality, demo)
        self.assertTrue(demo)
        self.assertEqual(result["overall"]["students"], 12)
        self.assertEqual(result["overall"]["eligible_students"], 11)
        self.assertEqual(result["overall"]["placed_students"], 7)
        self.assertEqual(result["overall"]["eligible_placement_pct"], 63.64)
        self.assertEqual(result["overall"]["offer_records"], 7)
        self.assertEqual(result["overall"]["joined_students"], 4)
        self.assertEqual(result["overall"]["average_offer_salary_lpa"], 5)
        self.assertEqual(result["overall"]["highest_offer_salary_lpa"], 6)
        self.assertEqual(len(result["follow_up"]), 5)
        self.assertTrue(result["validation"]["passed"])
        self.assertEqual(sum(c["selected_applications"] for c in result["companies"]), 8)
        self.assertTrue(any("earlier application status" in w for w in quality["warnings"]))

    def test_no_fabricated_offer_drive_or_recruiter_links(self):
        tables, quality, demo = load(self.source)
        self.assertEqual(set(tables), set(HEADERS))
        self.assertNotIn("recruiters", tables)
        self.assertNotIn("Drive_ID", tables["Applications"][0])
        self.assertNotIn("Application_ID", tables["Offers"][0])
        result = analyze(tables, quality, demo)
        self.assertEqual(result["drives"][0]["selection_of_attendees_pct"], 28.57)
        self.assertEqual(result["drives"][0]["selection_of_registrations_pct"], 25)
        self.assertEqual(result["history"][0]["placement_pct"], 60)

    def test_complete_supplied_cli_preserves_raw_and_exports_database(self):
        before = {p.name: p.read_bytes() for p in self.source.glob("*.csv")}
        output = self.root / "reports"
        processed = self.root / "processed"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["supplied", "--input", str(self.source), "--processed", str(processed), "--output", str(output)]), 0)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.source.glob("*.csv")})
        self.assertEqual(len(list(output.glob("*.md"))), 6)
        self.assertTrue((output / "dashboard.html").is_file())
        self.assertNotIn("__PLACEMENT_PAYLOAD__", (output / "dashboard.html").read_text())
        with sqlite3.connect(processed / "supplied.sqlite3") as connection:
            self.assertEqual(connection.execute('SELECT COUNT(*) FROM "Student_Data"').fetchone()[0], 12)
            self.assertEqual(connection.execute('SELECT AVG(Offered_Salary_LPA) FROM Offers').fetchone()[0], 5)
        result = json.loads((output / "analysis.json").read_text())
        self.assertEqual(len(result["quality"]["source_files"]), 8)

    def test_exact_duplicates_audited_but_conflicting_keys_block(self):
        self.update("Student_Data", None, None, duplicate=True)
        tables, quality, _ = load(self.source)
        self.assertEqual(len(tables["Student_Data"]), 12)
        self.assertEqual(quality["tables"]["Student_Data"]["exact_duplicates_removed"], 1)
        self.update("Student_Data", "Department", "Different", index=12)
        with self.assertRaisesRegex(DataError, "conflicting duplicate"):
            load(self.source)

    def test_invalid_numeric_counts_dates_and_enums_block(self):
        cases = [("Student_Data", "CGPA", "nan"), ("Student_Data", "CGPA", "11"), ("Student_Data", "CGPA", "bad"), ("Offers", "Offered_Salary_LPA", "0"), ("Placement_Drives", "Attending_Students", "1.5"), ("Placement_Drives", "Attending_Students", "-1"), ("Applications", "Application_Date", "2026-02-30"), ("Applications", "Selection_Result", "mystery")]
        for i, (table, field, value) in enumerate(cases):
            source = self.root / f"case{i}"
            shutil.copytree(ROOT / "data/raw", source)
            old = self.source
            self.source = source
            self.update(table, field, value)
            with self.subTest(field=field, value=value), self.assertRaises(DataError):
                load(self.source)
            self.source = old

    def test_missing_source_header_key_or_reference_blocks(self):
        path = self.source / "Student_Data.csv"
        original = path.read_text()
        path.unlink()
        with self.assertRaisesRegex(DataError, "Missing supplied"):
            load(self.source)
        path.write_text("Student_ID,Student_ID\n1,1\n")
        with self.assertRaisesRegex(DataError, "headers"):
            load(self.source)
        path.write_text(original)
        self.update("Student_Data", "Student_ID", "")
        with self.assertRaisesRegex(DataError, "missing key"):
            load(self.source)
        path.write_text(original)
        self.update("Applications", "Student_ID", "orphan")
        with self.assertRaisesRegex(DataError, "unresolved Student_ID"):
            load(self.source)

    def test_missing_salary_stays_unknown_and_non_demo_is_not_mislabeled(self):
        self.update("Offers", "Offered_Salary_LPA", "")
        (self.source / "Read_Me.csv").unlink()
        tables, quality, demo = load(self.source)
        self.assertFalse(demo)
        self.assertIsNone(tables["Offers"][0]["Offered_Salary_LPA"])
        self.assertEqual(quality["tables"]["Offers"]["missing_values"]["Offered_Salary_LPA"], 1)
        result = analyze(tables, quality, demo)
        self.assertEqual(result["overall"]["known_salary_offers"], 6)
        self.assertEqual(result["overall"]["salary_coverage_pct"], 85.71)
        self.assertFalse(result["metadata"]["is_demo"])

    def test_drive_and_historical_inconsistencies_block(self):
        self.update("Placement_Drives", "Attending_Students", "100")
        with self.assertRaisesRegex(DataError, "invalid nested counts"):
            load(self.source)
        self.update("Placement_Drives", "Attending_Students", "7")
        self.update("Historical_Placements", "Placed_Students", "100")
        with self.assertRaisesRegex(DataError, "contradictory summary"):
            load(self.source)

    def test_malformed_csv_blocks(self):
        path = self.source / "Student_Data.csv"
        path.write_text(path.read_text() + "1,2,3,4,5,6,7,8,9,10\n")
        with self.assertRaisesRegex(DataError, "too many CSV"):
            load(self.source)

    def test_empty_supplied_tables_and_output_path_validation(self):
        for table, fields in HEADERS.items():
            (self.source / f"{table}.csv").write_text(",".join(fields) + "\n")
        result = run(self.source, self.root / "processed", self.root / "output")
        self.assertIsNone(result["overall"]["eligible_placement_pct"])
        self.assertIsNone(result["overall"]["average_offer_salary_lpa"])
        self.assertTrue(result["validation"]["passed"])
        with self.assertRaisesRegex(DataError, "separate"):
            run(self.source, self.source, self.root / "output")


if __name__ == "__main__":
    unittest.main()
