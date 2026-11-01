"""Strict intake with auditable normalization, deduplication and referential checks."""

import csv
import hashlib
import json
import math
import sqlite3
from datetime import date
from pathlib import Path

from .demo import write_tables
from .schema import (APPLICATION_STATUSES, FOREIGN_KEYS, KEYS, OPTIONAL,
                     PLACEMENT_STATUSES, SCHEMAS, STATUS_ALIASES)


class DataError(ValueError):
    """Source data violates the documented intake contract."""


def numeric(value, field, integer=False, minimum=0, maximum=None):
    if not value:
        return None
    number = float(value)
    if not math.isfinite(number) or number < minimum or (maximum is not None and number > maximum):
        raise DataError(f"{field}: number outside allowed range")
    if integer and not number.is_integer():
        raise DataError(f"{field}: expected an integer")
    return int(number) if integer else number


def boolean(value, field):
    if not value:
        return None
    if value.lower() in {"true", "yes", "1"}:
        return True
    if value.lower() in {"false", "no", "0"}:
        return False
    raise DataError(f"{field}: expected true/false, yes/no or 1/0")


def normalize(table, row):
    result = {field: (row.get(field) or "").strip() for field in SCHEMAS[table]}
    for field, value in result.items():
        if not value and field not in OPTIONAL[table]:
            raise DataError(f"{field}: required value is missing")
    for field in ["cgpa", "min_cgpa"]:
        if field in result:
            result[field] = numeric(result[field], field, maximum=10)
    for field in ["backlogs", "graduation_year"]:
        if field in result:
            result[field] = numeric(result[field], field, integer=True,
                                    minimum=1900 if field == "graduation_year" else 0,
                                    maximum=2200 if field == "graduation_year" else None)
    if "annual_ctc_inr" in result:
        result["annual_ctc_inr"] = numeric(result["annual_ctc_inr"], "annual_ctc_inr", minimum=1)
    for field in ["attended", "interview_attended"]:
        if field in result:
            result[field] = boolean(result[field], field)
    for field in ["drive_date", "applied_at", "shortlisted_at", "outcome_date"]:
        if field in result and result[field]:
            result[field] = date.fromisoformat(result[field]).isoformat()
    if "department" in result:
        result["department"] = result["department"].upper()
    if "skills" in result:
        result["skills"] = "|".join(sorted({s.strip().lower() for s in result["skills"].split("|") if s.strip()}))
    if "status" in result:
        status = result["status"].lower()
        status = STATUS_ALIASES.get(status, status) if table == "applications" else status
        allowed = APPLICATION_STATUSES if table == "applications" else PLACEMENT_STATUSES
        if status not in allowed:
            raise DataError(f"status: unrecognized value {status!r}")
        result["status"] = status
    return result


def read_sources(directory):
    directory = Path(directory)
    tables, audit = {}, {"source_files": {}, "tables": {}, "warnings": []}
    for table, fields in SCHEMAS.items():
        path = directory / f"{table}.csv"
        if not path.is_file():
            raise DataError(f"Missing source: {path}. Use data/templates/ for the CSV contract.")
        audit["source_files"][path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise DataError(f"{path.name}: empty or duplicate headers")
            missing_headers = set(fields) - set(reader.fieldnames)
            if missing_headers:
                raise DataError(f"{path.name}: missing headers {sorted(missing_headers)}")
            extra_headers = set(reader.fieldnames) - set(fields)
            if extra_headers:
                audit["warnings"].append(f"{path.name}: ignored columns {sorted(extra_headers)}")
            records, seen, duplicates, raw_count = [], {}, 0, 0
            missing_counts = dict.fromkeys(fields, 0)
            for line, row in enumerate(reader, 2):
                if None in row:
                    raise DataError(f"{path.name}:{line}: more values than CSV headers")
                raw_count += 1
                try:
                    item = normalize(table, row)
                except (ValueError, TypeError) as exc:
                    raise DataError(f"{path.name}:{line}: {exc}") from exc
                key = item[KEYS[table]]
                if key in seen:
                    if seen[key] != item:
                        raise DataError(f"{path.name}:{line}: conflicting duplicate key {key}")
                    duplicates += 1
                    continue
                seen[key] = item
                records.append(item)
                for field, value in item.items():
                    missing_counts[field] += value is None or value == ""
            tables[table] = records
            audit["tables"][table] = {"source_rows": raw_count, "clean_rows": len(records), "exact_duplicates_removed": duplicates, "missing_values": missing_counts}
    check_relations(tables)
    if not tables["students"]:
        audit["warnings"].append("No student records: student placement percentages are undefined.")
    missing_academics = len({s["student_id"] for s in tables["students"]} - {a["student_id"] for a in tables["academics"]})
    if missing_academics:
        audit["warnings"].append(f"{missing_academics} students lack academic records; eligibility is unknown.")
    return tables, audit


def check_relations(tables):
    indexes = {name: {row[KEYS[name]]: row for row in rows} for name, rows in tables.items()}
    for table, constraints in FOREIGN_KEYS.items():
        for row in tables[table]:
            for field, target in constraints:
                if row[field] not in indexes[target]:
                    raise DataError(f"{table}: orphan {field}={row[field]}")
    for drive in tables["drives"]:
        if indexes["recruiters"][drive["recruiter_id"]]["company_id"] != drive["company_id"]:
            raise DataError("drives: recruiter and drive company mismatch")
    for table in ["applications", "registrations"]:
        pairs = [(r["student_id"], r["drive_id"]) for r in tables[table]]
        if len(pairs) != len(set(pairs)):
            raise DataError(f"{table}: multiple records for one student-drive pair")
    offer_apps = [p["application_id"] for p in tables["placements"]]
    if len(offer_apps) != len(set(offer_apps)):
        raise DataError("placements: multiple current outcomes for one application")
    registrations = {(r["student_id"], r["drive_id"]) for r in tables["registrations"]}
    for app in tables["applications"]:
        if (app["student_id"], app["drive_id"]) not in registrations:
            raise DataError("applications: student-drive registration is missing")
        if app["shortlisted_at"] and app["shortlisted_at"] < app["applied_at"]:
            raise DataError("applications: shortlist date precedes application")
        if app["applied_at"] > indexes["drives"][app["drive_id"]]["drive_date"]:
            raise DataError("applications: application date follows drive date")
        if app["status"] in {"shortlisted", "interviewed", "selected"} and not app["shortlisted_at"]:
            raise DataError("applications: shortlist evidence required for progressed status")
        if app["status"] in {"interviewed", "selected"} and app["interview_attended"] is not True:
            raise DataError("applications: interview evidence required for progressed status")
    for offer in tables["placements"]:
        app = indexes["applications"][offer["application_id"]]
        if app["status"] != "selected":
            raise DataError("placements: outcome requires a selected application")
        if offer["outcome_date"] < app["applied_at"]:
            raise DataError("placements: outcome precedes application")


def save_prepared(tables, audit, directory):
    directory = Path(directory)
    write_tables(tables, directory)
    (directory / "quality.json").write_text(json.dumps(audit, indent=2) + "\n")
    database = directory / "placement.sqlite3"
    if database.exists():
        database.unlink()
    with sqlite3.connect(database) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        for table, fields in SCHEMAS.items():
            definitions = []
            for field in fields:
                kind = "REAL" if field in {"cgpa", "min_cgpa", "annual_ctc_inr"} else "INTEGER" if field in {"graduation_year", "backlogs", "attended", "interview_attended"} else "TEXT"
                definition = f'"{field}" {kind}' + (" PRIMARY KEY" if field == KEYS[table] else "")
                definitions.append(definition)
            for field, target in FOREIGN_KEYS.get(table, []):
                definitions.append(f'FOREIGN KEY ("{field}") REFERENCES "{target}" ("{KEYS[target]}")')
            conn.execute(f'CREATE TABLE "{table}" ({", ".join(definitions)})')
            placeholders = ",".join("?" for _ in fields)
            conn.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', [[r[f] for f in fields] for r in tables[table]])
