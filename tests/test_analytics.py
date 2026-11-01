"""Regression tests for denominators, input integrity and complete deliverables."""

import contextlib
import copy
import csv
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from placement import eda, recruiters
from placement.cli import analyze, main
from placement.dashboard import render
from placement.demo import generate, write_tables
from placement.kpis import compute, follow_up, salary_metrics
from placement.prepare import DataError, boolean, check_relations, normalize, numeric, read_sources, save_prepared
from placement.reports import display, export_csv, safe_cell
from placement.schema import SCHEMAS, eligible, rate
from placement.validate import validate


def fixture():
    """Two offers for one student must still produce one placed student."""
    rows = {
        "students": [["001", "CSE", 2026, "python|sql"], ["002", "CSE", 2026, "sql"], ["003", "ME", 2026, ""], ["004", "ME", 2026, "cad"]],
        "academics": [["001", 8.0, 0], ["002", 7.0, 0], ["003", None, 0], ["004", 5.0, 1]],
        "companies": [["C1", "Company One", "IT"]],
        "recruiters": [["R1", "C1", "Recruiter"]],
        "drives": [["D1", "C1", "R1", "2026-10-01", "Analyst", 6.0], ["D2", "C1", "R1", "2026-10-02", "Engineer", 6.0]],
        "registrations": [["G1", "001", "D1", True], ["G2", "001", "D2", True], ["G3", "002", "D1", None]],
        "applications": [["A1", "001", "D1", "2026-10-01", "selected", "2026-10-01", True], ["A2", "001", "D2", "2026-10-02", "selected", "2026-10-02", True], ["A3", "002", "D1", "2026-10-01", "withdrawn", "", False]],
        "placements": [["P1", "A1", "accepted", 600000.0, "2026-10-03"], ["P2", "A2", "joined", None, "2026-10-03"]],
    }
    return {name: [dict(zip(SCHEMAS[name], row)) for row in records] for name, records in rows.items()}


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def read(self, tables):
        write_tables(tables, self.path)
        return read_sources(self.path)

    def test_normalization_preserves_leading_zero_ids(self):
        row = normalize("students", {"student_id": " 001 ", "department": " cse ", "graduation_year": "2026", "skills": "SQL| python | sql "})
        self.assertEqual(row, {"student_id": "001", "department": "CSE", "graduation_year": 2026, "skills": "python|sql"})
        self.assertEqual(normalize("applications", {"application_id": "1", "student_id": "001", "drive_id": "1", "applied_at": "2026-10-01", "status": " HIRED ", "interview_attended": "yes", "shortlisted_at": "2026-10-01"})["status"], "selected")

    def test_invalid_numeric_and_boolean_boundaries(self):
        for value in ["nan", "inf", "-1", "11"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                numeric(value, "cgpa", maximum=10)
        with self.assertRaises(DataError):
            numeric("1.2", "backlogs", integer=True)
        with self.assertRaises(DataError):
            boolean("perhaps", "attended")
        self.assertIsNone(numeric("", "cgpa"))
        self.assertIsNone(boolean("", "attended"))
        self.assertTrue(boolean("YES", "attended"))
        self.assertFalse(boolean("0", "attended"))

    def test_missing_required_values_dates_and_status(self):
        for table, row in [("students", {}), ("placements", {"placement_id": "P", "application_id": "A", "status": "unknown", "outcome_date": "2026-10-01"}), ("drives", {"drive_id": "D", "company_id": "C", "recruiter_id": "R", "drive_date": "2026-02-30", "job_role": "Analyst"})]:
            with self.subTest(table=table), self.assertRaises(ValueError):
                normalize(table, row)

    def test_exact_duplicate_audited_and_conflicting_duplicate_rejected(self):
        tables = fixture()
        tables["students"].append(tables["students"][0].copy())
        cleaned, audit = self.read(tables)
        self.assertEqual(len(cleaned["students"]), 4)
        self.assertEqual(audit["tables"]["students"]["exact_duplicates_removed"], 1)
        self.assertEqual(len(audit["source_files"]["students.csv"]["sha256"]), 64)
        tables["students"][-1]["department"] = "ECE"
        with self.assertRaisesRegex(DataError, "conflicting duplicate"):
            self.read(tables)

    def test_missing_files_headers_and_malformed_rows(self):
        with self.assertRaisesRegex(DataError, "Missing source"):
            read_sources(self.path)
        for text, message in [("student_id,student_id\n1,1\n", "duplicate headers"), ("student_id\n1\n", "missing headers"), (",".join(SCHEMAS["students"]) + "\n1,CSE,2026,sql,extra\n", "more values"), (",".join(SCHEMAS["students"]) + "\n1,CSE,bad,sql\n", "graduation_year|could not convert")]:
            (self.path / "students.csv").write_text(text)
            with self.subTest(message=message), self.assertRaisesRegex(DataError, message):
                read_sources(self.path)

    def test_extra_columns_are_audited_and_not_carried_forward(self):
        self.read(fixture())
        path = self.path / "students.csv"
        lines = path.read_text().splitlines()
        path.write_text(lines[0] + ",unused\n" + "\n".join(line + ",x" for line in lines[1:]) + "\n")
        tables, audit = read_sources(self.path)
        self.assertTrue(audit["warnings"])
        self.assertNotIn("unused", tables["students"][0])

    def test_foreign_keys_conflicts_and_chronology(self):
        cases = [
            ("academics", 0, "student_id", "orphan", "orphan"),
            ("drives", 0, "company_id", "orphan", "orphan"),
            ("applications", 0, "shortlisted_at", "2026-09-01", "precedes"),
            ("applications", 0, "applied_at", "2026-11-01", "precedes|follows"),
            ("applications", 0, "shortlisted_at", "", "shortlist evidence"),
            ("applications", 0, "interview_attended", False, "interview evidence"),
            ("applications", 0, "status", "withdrawn", "requires a selected"),
            ("placements", 0, "outcome_date", "2026-01-01", "precedes"),
        ]
        for table, index, field, value, message in cases:
            tables = fixture()
            tables[table][index][field] = value
            with self.subTest(field=field, value=value), self.assertRaisesRegex(DataError, message):
                check_relations(tables)
        tables = fixture()
        tables["companies"].append({"company_id": "C2", "company_name": "Two", "industry": "IT"})
        tables["drives"][0]["company_id"] = "C2"
        with self.assertRaisesRegex(DataError, "company mismatch"):
            check_relations(tables)

    def test_business_duplicate_and_missing_registration(self):
        for table, key in [("applications", "application_id"), ("registrations", "registration_id"), ("placements", "placement_id")]:
            tables = fixture()
            tables[table].append({**tables[table][0], key: "new"})
            with self.subTest(table=table), self.assertRaisesRegex(DataError, "multiple"):
                check_relations(tables)
        tables = fixture()
        tables["registrations"].pop(0)
        with self.assertRaisesRegex(DataError, "registration is missing"):
            check_relations(tables)

    def test_missing_academic_record_remains_unknown(self):
        tables = fixture()
        tables["academics"].pop(0)
        cleaned, audit = self.read(tables)
        self.assertTrue(audit["warnings"])
        self.assertIsNone(compute(cleaned)["student_facts"][0]["eligible"])

    def test_sqlite_has_keys_types_and_reconciled_counts(self):
        tables, audit = self.read(fixture())
        output = self.path / "processed"
        save_prepared(tables, audit, output)
        save_prepared(tables, audit, output)
        with sqlite3.connect(output / "placement.sqlite3") as conn:
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM students").fetchone()[0], 4)
            self.assertEqual(conn.execute("SELECT student_id FROM students ORDER BY student_id LIMIT 1").fetchone()[0], "001")
            self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
            self.assertEqual(conn.execute("SELECT SUM(annual_ctc_inr) FROM placements").fetchone()[0], 600000)


class MetricTests(unittest.TestCase):
    def test_student_offer_grains_and_denominators(self):
        result = compute(fixture())
        o = result["overall"]
        self.assertEqual(o["students"], 4)
        self.assertEqual(o["placed_students"], 1)
        self.assertEqual(o["accepted_joined_offers"], 2)
        self.assertEqual(o["eligible_students"], 2)
        self.assertEqual(o["unknown_eligibility"], 1)
        self.assertEqual(o["eligible_placement_pct"], 50)
        self.assertEqual(o["all_student_placement_pct"], 25)
        self.assertEqual(o["salary_coverage_pct"], 50)
        self.assertEqual(o["average_ctc_inr"], 600000)
        self.assertEqual(len(result["follow_up"]), 3)

    def test_zero_denominators_and_missing_salaries(self):
        self.assertIsNone(rate(0, 0))
        self.assertIsNone(eligible(None))
        self.assertFalse(eligible({"cgpa": 8, "backlogs": 1}))
        self.assertIsNone(salary_metrics([])["highest_ctc_inr"])
        self.assertIsNone(salary_metrics([{"status": "joined", "annual_ctc_inr": None}])["average_ctc_inr"])

    def test_offered_declined_revoked_do_not_establish_placement(self):
        for status in ["offered", "declined", "revoked"]:
            tables = fixture()
            for p in tables["placements"]:
                p["status"] = status
            self.assertEqual(compute(tables)["overall"]["placed_students"], 0)
            self.assertEqual(recruiters.analyze(tables)["companies"][0]["selected_applications"], 2)

    def test_company_application_and_registration_rates_differ(self):
        result = recruiters.analyze(fixture())["companies"][0]
        self.assertEqual(result["unique_selected_students"], 1)
        self.assertEqual(result["selected_applications"], 2)
        self.assertEqual(result["selection_rate_pct"], 66.67)
        self.assertEqual(result["registered_student_selection_pct"], 50)
        self.assertEqual(result["participation_rate_pct"], 66.67)
        self.assertEqual(result["unknown_attendance"], 1)

    def test_eda_bands_skills_and_interview_evidence(self):
        tables = fixture()
        result = eda.analyze(tables, compute(tables)["student_facts"])
        self.assertEqual(result["evidence_counts"]["interviewed_applications"], 2)
        self.assertEqual(result["evidence_counts"]["unique_interviewed_students"], 1)
        self.assertEqual(result["application_statuses"]["withdrawn"], 1)
        self.assertEqual([eda.cgpa_band(v) for v in [None, 5, 6.5, 7.5, 9]], ["Unknown", "Below 6", "6–6.99", "7–7.99", "8–10"])
        self.assertEqual(next(r for r in result["skills"] if r["skill"] == "sql")["students"], 2)

    def test_follow_up_actions_cover_evidence_gaps(self):
        base = {"student_id": "x", "department": "CSE", "placed": False, "eligible": True, "applications": 1, "interviews": 1}
        cases = [{"eligible": None}, {"eligible": False}, {"applications": 0}, {"interviews": 0}, {}]
        actions = [follow_up([{**base, **c}])[0]["recommended_follow_up"] for c in cases]
        self.assertEqual(len(set(actions)), 5)

    def test_validation_detects_deliberately_corrupted_kpi(self):
        with tempfile.TemporaryDirectory() as temp:
            write_tables(fixture(), temp)
            tables, quality = read_sources(temp)
            result = analyze(tables, quality)
            self.assertTrue(result["validation"]["passed"])
            result["kpis"]["overall"]["eligible_placement_pct"] = 99
            self.assertFalse(validate(tables, result)["passed"])


class DeliverableTests(unittest.TestCase):
    def test_demo_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            a = Path(temp) / "a"
            b = Path(temp) / "b"
            generate(a)
            generate(b)
            for name in SCHEMAS:
                self.assertEqual((a / f"{name}.csv").read_bytes(), (b / f"{name}.csv").read_bytes())

    def test_safe_exports_and_escaped_dashboard_payload(self):
        self.assertEqual(safe_cell(" =HYPERLINK(1)"), "' =HYPERLINK(1)")
        self.assertEqual(safe_cell(42), 42)
        self.assertEqual(display(None), "N/A")
        self.assertEqual(display("a|b\nc"), "a\\|b c")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            export_csv([{"label": "@SUM(1)"}], path / "test.csv")
            self.assertIn("'@SUM(1)", (path / "test.csv").read_text())
            export_csv([], path / "empty.csv")
            self.assertEqual((path / "empty.csv").read_text().strip(), "no_records")
            render({"test": "</script><script>alert(1)</script>"}, {}, path / "test.html")
            html = (path / "test.html").read_text()
            self.assertNotIn("</script><script>alert(1)", html)
            self.assertIn("\\u003c/script\\u003e", html)

    def test_complete_pipeline_templates_prepare_validate_and_failure(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(temp)
            source, processed, reports = (str(root / name) for name in ["source", "processed", "reports"])
            self.assertEqual(main(["templates", "--output", source]), 0)
            self.assertEqual(main(["demo", "--output", source]), 0)
            self.assertEqual(main(["prepare", "--input", source, "--processed", processed]), 0)
            self.assertEqual(main(["validate", "--input", source]), 0)
            self.assertEqual(main(["run", "--input", source, "--processed", processed, "--output", reports]), 0)
            report_path = Path(reports)
            self.assertEqual(len(list(report_path.glob("*.md"))), 6)
            self.assertEqual(len(list(report_path.glob("*.csv"))), 4)
            self.assertTrue((report_path / "dashboard.html").is_file())
            self.assertTrue(json.loads((report_path / "analysis.json").read_text())["validation"]["passed"])
            self.assertEqual(main(["run", "--input", str(root / "missing")]), 2)
            self.assertEqual(main(["run", "--input", source, "--processed", source]), 2)

    def test_header_only_sources_produce_explicit_unavailable_metrics(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(temp)
            source = root / "source"
            write_tables({}, source)
            self.assertEqual(main(["run", "--input", str(source), "--processed", str(root / "clean"), "--output", str(root / "out")]), 0)
            result = json.loads((root / "out" / "analysis.json").read_text())
            self.assertIsNone(result["kpis"]["overall"]["eligible_placement_pct"])
            self.assertTrue(result["quality"]["warnings"])
            self.assertEqual(result["recommendations"], [])


if __name__ == "__main__":
    unittest.main()
