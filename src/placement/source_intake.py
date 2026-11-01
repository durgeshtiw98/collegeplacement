"""Validated ingestion of the original workbook exports; source fields stay separate."""

import csv
import hashlib
import math
from datetime import date, datetime, timezone
from pathlib import Path

from .prepare import DataError

HEADERS = {
    "Student_Data": "Student_ID Anonymized_Student_Label Department Class_10_Percentage Class_12_Percentage CGPA Skills_and_Certifications Graduation_Year Eligibility_Status".split(),
    "Company_Data": "Company_ID Company_Name Industry Recruiter_Verification_Status".split(),
    "Job_Postings": "Job_ID Company_ID Job_Role Job_Location Required_Skills Salary_Package_LPA Job_Verification_Status".split(),
    "Applications": "Application_ID Student_ID Job_ID Application_Date Application_Status Interview_Status Selection_Result Placement_Status".split(),
    "Placement_Drives": "Drive_ID Company_ID Drive_Date Eligible_Departments Registered_Students Attending_Students Shortlisted_Students Selected_Students".split(),
    "Offers": "Student_ID Company_ID Job_Role Offered_Salary_LPA Offer_Letter_Status Joining_Status".split(),
    "Historical_Placements": "Academic_Year Department Eligible_Students Placed_Students Participating_Companies Placement_Drives Highest_Package_LPA Average_Package_LPA".split(),
}
PK = {"Student_Data": ["Student_ID"], "Company_Data": ["Company_ID"], "Job_Postings": ["Job_ID"], "Applications": ["Application_ID"], "Placement_Drives": ["Drive_ID"], "Historical_Placements": ["Academic_Year", "Department"]}
NUMERIC = {"Class_10_Percentage", "Class_12_Percentage", "CGPA", "Salary_Package_LPA", "Registered_Students", "Attending_Students", "Shortlisted_Students", "Selected_Students", "Offered_Salary_LPA", "Eligible_Students", "Placed_Students", "Participating_Companies", "Placement_Drives", "Highest_Package_LPA", "Average_Package_LPA"}
COUNTS = {"Registered_Students", "Attending_Students", "Shortlisted_Students", "Selected_Students", "Eligible_Students", "Placed_Students", "Participating_Companies", "Placement_Drives"}
ENUMS = {"Eligibility_Status": {"eligible", "not eligible", "ineligible", "review required"}, "Application_Status": {"applied", "shortlisted", "interviewed", "selected", "rejected", "withdrawn"}, "Interview_Status": {"interviewed", "not scheduled", "scheduled", "absent", "pending"}, "Selection_Result": {"selected", "not selected", "pending"}, "Placement_Status": {"placed", "not placed", "pending"}, "Joining_Status": {"joined", "pending", "declined", "not joined"}}


def load(directory):
    directory = Path(directory)
    tables, quality = {}, {"source_files": {}, "tables": {}, "warnings": []}
    today = datetime.now(timezone.utc).date().isoformat()
    for table, fields in HEADERS.items():
        path = directory / f"{table}.csv"
        if not path.is_file():
            raise DataError(f"Missing supplied source {path}")
        quality["source_files"][path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        rows, identities, exact = [], set(), set()
        raw_count = 0
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(fields) - set(reader.fieldnames):
                raise DataError(f"{table}: missing or duplicate required headers")
            if set(reader.fieldnames) - set(fields):
                quality["warnings"].append(f"{table}: extra columns excluded from analysis")
            for line, raw in enumerate(reader, 2):
                if None in raw:
                    raise DataError(f"{table}:{line}: too many CSV values")
                raw_count += 1
                row = {f: (raw.get(f) or "").strip() for f in fields}
                identity = tuple(row[f] for f in PK.get(table, []))
                if any(not value for value in identity):
                    raise DataError(f"{table}:{line}: missing key")
                for field, value in row.items():
                    if field in ENUMS and value and value.casefold() not in ENUMS[field]:
                        raise DataError(f"{table}:{line}: unknown {field} {value!r}")
                    if field in NUMERIC:
                        try:
                            number = float(value) if value else None
                            maximum = 10 if field == "CGPA" else 100 if field.endswith("Percentage") else math.inf
                            valid = number is None or (math.isfinite(number) and 0 <= number <= maximum and (field not in COUNTS or number.is_integer()))
                        except ValueError:
                            valid = False
                        if not valid:
                            raise DataError(f"{table}:{line}: invalid {field}")
                        if field.endswith("_LPA") and number is not None and number == 0:
                            raise DataError(f"{table}:{line}: zero salary must be recorded as missing if unknown")
                        row[field] = number
                    if field.endswith("_Date") and value:
                        try:
                            row[field] = date.fromisoformat(value).isoformat()
                        except ValueError as exc:
                            raise DataError(f"{table}:{line}: invalid date") from exc
                        if value > today:
                            quality["warnings"].append(f"{table}:{line}: future demonstration event {value}; no as-of cutoff applied")
                fingerprint = tuple(row.items())
                if fingerprint in exact:
                    continue
                exact.add(fingerprint)
                if identity and identity in identities:
                    raise DataError(f"{table}:{line}: conflicting duplicate key {identity}")
                identities.add(identity)
                rows.append(row)
        tables[table] = rows
        quality["tables"][table] = {"source_rows": raw_count, "clean_rows": len(rows), "exact_duplicates_removed": raw_count - len(rows), "missing_values": {f: sum(r[f] in (None, "") for r in rows) for f in fields}}
    students = {r["Student_ID"] for r in tables["Student_Data"]}
    companies = {r["Company_ID"] for r in tables["Company_Data"]}
    jobs = {r["Job_ID"] for r in tables["Job_Postings"]}
    for table, field, parents in [("Job_Postings", "Company_ID", companies), ("Applications", "Student_ID", students), ("Applications", "Job_ID", jobs), ("Placement_Drives", "Company_ID", companies), ("Offers", "Student_ID", students), ("Offers", "Company_ID", companies)]:
        if any(r[field] not in parents for r in tables[table]):
            raise DataError(f"{table}: unresolved {field}")
    for r in tables["Placement_Drives"]:
        values = [r[f] for f in ["Registered_Students", "Attending_Students", "Shortlisted_Students", "Selected_Students"]]
        if any(v is None for v in values) or any(a < b for a, b in zip(values, values[1:])):
            raise DataError(f"Placement_Drives: invalid nested counts for {r['Drive_ID']}")
    for r in tables["Historical_Placements"]:
        e, p = r["Eligible_Students"], r["Placed_Students"]
        avg, high = r["Average_Package_LPA"], r["Highest_Package_LPA"]
        if (e is not None and p is not None and p > e) or (avg is not None and high is not None and avg > high):
            raise DataError("Historical_Placements: contradictory summary")
    for a in tables["Applications"]:
        if a["Selection_Result"].casefold() == "selected" and a["Application_Status"].casefold() in {"applied", "shortlisted"}:
            quality["warnings"].append(f"{a['Application_ID']}: selected result retains earlier application status; source fields preserved")
    marker = directory / "Read_Me.csv"
    is_demo = marker.exists() and "synthetic" in marker.read_text(encoding="utf-8-sig").lower()
    if marker.exists():
        quality["source_files"][marker.name] = {"sha256": hashlib.sha256(marker.read_bytes()).hexdigest()}
    quality["warnings"].extend([
        "No reliable offer-to-application/Job_ID or application-to-drive key: these joins are not performed.",
        "Drive data is aggregated; student-level attendance and department filters cannot be inferred.",
        "Historical summaries use different populations and are not reconciled to the current 12-student example.",
        "Recruiter verification is available; individual recruiter activity and timestamps are unavailable.",
    ])
    return tables, quality, is_demo

