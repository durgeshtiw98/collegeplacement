"""Analyze the supplied workbook exports without inventing unavailable joins."""

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .eda import cgpa_band
from .prepare import DataError
from .reports import export_csv, markdown_table
from .schema import rate
from .source_intake import HEADERS, NUMERIC, PK, load

def analyze(tables, quality, is_demo):
    students, apps, offers = tables["Student_Data"], tables["Applications"], tables["Offers"]
    placed = {a["Student_ID"] for a in apps if a["Placement_Status"].casefold() == "placed"}
    selected = {a["Student_ID"] for a in apps if a["Selection_Result"].casefold() == "selected"}
    joined = {o["Student_ID"] for o in offers if o["Joining_Status"].casefold() == "joined"}
    eligible_ids = {s["Student_ID"] for s in students if s["Eligibility_Status"].casefold() == "eligible"}
    facts = [{**s, "eligible": s["Student_ID"] in eligible_ids, "placed": s["Student_ID"] in placed,
              "applications": sum(a["Student_ID"] == s["Student_ID"] for a in apps),
              "interviews": sum(a["Student_ID"] == s["Student_ID"] and a["Interview_Status"].casefold() == "interviewed" for a in apps)} for s in students]

    def group(rows):
        ids = {s["Student_ID"] for s in rows}
        return {"students": len(ids), "eligible_students": len(ids & eligible_ids), "placed_students": len(ids & placed), "eligible_placed_students": len(ids & eligible_ids & placed), "eligible_placement_pct": rate(len(ids & eligible_ids & placed), len(ids & eligible_ids)), "all_student_placement_pct": rate(len(ids & placed), len(ids))}

    salaries = [o["Offered_Salary_LPA"] for o in offers if o["Offered_Salary_LPA"] is not None]
    overall = {**group(students), "selected_students": len(selected), "joined_students": len(joined), "offer_records": len(offers), "known_salary_offers": len(salaries), "salary_coverage_pct": rate(len(salaries), len(offers)), "average_offer_salary_lpa": round(sum(salaries) / len(salaries), 2) if salaries else None, "highest_offer_salary_lpa": max(salaries) if salaries else None, "unknown_eligibility": sum(not s["Eligibility_Status"] or s["Eligibility_Status"].casefold() == "review required" for s in students)}
    departments = [{"department": dept, **group([s for s in students if s["Department"] == dept])} for dept in sorted({s["Department"] for s in students})]
    job_companies = {j["Job_ID"]: j["Company_ID"] for j in tables["Job_Postings"]}
    companies = []
    for company in tables["Company_Data"]:
        subset = [a for a in apps if job_companies[a["Job_ID"]] == company["Company_ID"]]
        chosen = [a for a in subset if a["Selection_Result"].casefold() == "selected"]
        companies.append({**company, "applications": len(subset), "selected_applications": len(chosen), "unique_selected_students": len({a["Student_ID"] for a in chosen}), "selection_pct": rate(len(chosen), len(subset))})
    drives = [{**d, "participation_pct": rate(d["Attending_Students"], d["Registered_Students"]), "selection_of_attendees_pct": rate(d["Selected_Students"], d["Attending_Students"]), "selection_of_registrations_pct": rate(d["Selected_Students"], d["Registered_Students"])} for d in tables["Placement_Drives"]]
    history = [{**h, "placement_pct": rate(h["Placed_Students"], h["Eligible_Students"])} for h in tables["Historical_Placements"]]
    skills = sorted({v.strip().lower() for s in students for v in s["Skills_and_Certifications"].split(";") if v.strip()})
    skill_groups = [{"skill": skill, **group([s for s in students if skill in {v.strip().lower() for v in s["Skills_and_Certifications"].split(";")}])} for skill in skills]
    bands = [{"band": band, **group([s for s in students if cgpa_band(s["CGPA"]) == band])} for band in ["Below 6", "6–6.99", "7–7.99", "8–10", "Unknown"]]
    queue = [{"student_id": s["Student_ID"], "department": s["Department"], "eligibility": s["Eligibility_Status"], "applications": s["applications"], "interviews": s["interviews"], "action": "Review eligibility with placement cell" if not s["eligible"] else "Discuss available roles and participation" if not s["applications"] else "Review shortlisting feedback and skills evidence" if not s["interviews"] else "Review interview feedback and pending decisions"} for s in facts if not s["placed"]]
    checks = [
        ("Department student counts reconcile", sum(d["students"] for d in departments) == len(students)),
        ("Department eligible counts reconcile", sum(d["eligible_students"] for d in departments) == len(eligible_ids)),
        ("Eligible placement percentage matches source", overall["eligible_placement_pct"] == rate(len(eligible_ids & placed), len(eligible_ids))),
        ("Unique placed students reconcile", sum(d["placed_students"] for d in departments) == len(placed)),
        ("Company application counts reconcile", sum(c["applications"] for c in companies) == len(apps)),
        ("Company selected applications reconcile", sum(c["selected_applications"] for c in companies) == sum(a["Selection_Result"].casefold() == "selected" for a in apps)),
        ("Follow-up partitions current student cohort", len(queue) + len(placed) == len(students)),
        ("Recorded offers remain separate from joins", len(offers) >= len(joined)),
        ("Clean row counts match audited sources", all(q["source_rows"] == q["clean_rows"] + q["exact_duplicates_removed"] for q in quality["tables"].values())),
    ]
    recommendations = [{"owner": "Placement cell", "evidence": f"{len(eligible_ids - placed)} eligible students have no recorded placement", "action": "Use the follow-up queue to review participation and interview feedback", "measure": "Eligible unplaced count and subsequently verified outcomes"}, {"owner": "Data engineering / placement cell", "evidence": "No application-drive key or offer/application identifier", "action": "Capture stable offer IDs, application IDs and student-drive attendance in the portal", "measure": "Link completeness and unreconciled outcome count"}, {"owner": "Department coordinators", "evidence": f"{overall['unknown_eligibility']} students require eligibility review", "action": "Verify eligibility status without inferring backlogs from CGPA", "measure": "Unknown eligibility count"}]
    return {"metadata": {"data_label": "SUPPLIED SYNTHETIC WORKBOOK — NOT REAL COLLEGE OUTCOMES" if is_demo else "SUPPLIED SOURCE DATA — VERIFY COVERAGE", "is_demo": is_demo, "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "author": "Durgesh Tiwari", "mode": "supplied-workbook", "salary_unit": "INR LPA", "date_scope": "All supplied rows, including future demonstration events; generation timestamp is not a cutoff"}, "quality": quality, "overall": overall, "departments": departments, "companies": companies, "drives": drives, "history": history, "skills": skill_groups, "cgpa_bands": bands, "application_statuses": dict(Counter(a["Application_Status"] for a in apps)), "student_facts": facts, "follow_up": queue, "recommendations": recommendations, "validation": {"passed": all(v for _, v in checks), "checks": [{"check": n, "passed": v} for n, v in checks]}}


def write_outputs(tables, result, processed, output):
    processed, output = Path(processed), Path(output)
    processed.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    for name, rows in tables.items():
        export_csv(rows, processed / f"{name}.csv", HEADERS[name])
    with sqlite3.connect(processed / "supplied.sqlite3") as connection:
        for name, fields in HEADERS.items():
            connection.execute(f'DROP TABLE IF EXISTS "{name}"')
            columns = ", ".join(f'"{f}" {"REAL" if f in NUMERIC else "TEXT"}' for f in fields)
            key = ', PRIMARY KEY (' + ', '.join(f'"{f}"' for f in PK[name]) + ')' if name in PK else ''
            connection.execute(f'CREATE TABLE "{name}" ({columns}{key})')
            placeholders = ','.join('?' for _ in fields)
            connection.executemany(f'INSERT INTO "{name}" VALUES ({placeholders})', [[r[f] for f in fields] for r in tables[name]])
    for path in [processed / "quality.json", output / "quality.json"]:
        path.write_text(json.dumps(result["quality"], indent=2) + "\n", encoding="utf-8")
    (output / "analysis.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    prefix = f"**{result['metadata']['data_label']}**\n\nOwner: Durgesh Tiwari · Assigned: 26 October–15 December 2026.\n\nActual generation: {result['metadata']['generated_at']}. All supplied example rows are included; this is not a historical cutoff.\n\n"
    method = "## Definitions and limitations\n\nPlacement = unique student with Applications.Placement_Status = Placed. Eligibility = the explicit Student_Data.Eligibility_Status = Eligible, not an invented CGPA/backlog rule. Salary = recorded offers in INR LPA; acceptance is unknown and joined counts are reported separately. Company selection = selected application records / applications. Drive participation = attending / registered; drive selection = selected / attending. Historical summaries remain separate because their populations differ.\n\n"
    quality_rows = [{"source": k, **{f: v for f, v in q.items() if f != "missing_values"}} for k, q in result["quality"]["tables"].items()]
    warnings = "\n".join("- " + w for w in result["quality"]["warnings"])
    documents = {
        "01-data-preparation.md": "# Data preparation\n\n" + prefix + markdown_table(quality_rows, ["source", "source_rows", "clean_rows", "exact_duplicates_removed"]) + "\nTrimmed surrounding whitespace; validated numeric ranges, dates, primary keys and source links. Exact duplicates are audited. Conflicting keys and invalid references stop publication. Source fields and separate outcome statuses are preserved. No imputation or unsupported event joins are performed. Clean CSV and SQLite retain the original source schemas. Full missing counts and SHA-256 hashes are in quality.json.\n\n## Findings and limitations\n\n" + warnings,
        "02-exploratory-analysis.md": "# Exploratory data analysis\n\n" + prefix + "## Departments\n\n" + markdown_table(result["departments"], ["department", "students", "eligible_students", "placed_students", "eligible_placement_pct"]) + "\n## Academic performance\n\n" + markdown_table(result["cgpa_bands"], ["band", "students", "placed_students", "all_student_placement_pct"]) + "\n## Skills\n\n" + markdown_table(result["skills"], ["skill", "students", "placed_students", "all_student_placement_pct"]) + "\n## Application status distribution\n\n" + markdown_table([{"status": s, "applications": n} for s, n in result["application_statuses"].items()], ["status", "applications"]) + "\nSkills overlap; comparisons are descriptive. The small synthetic sample cannot establish successful-placement factors or causality. Selection_Result and Interview_Status are analyzed separately from Application_Status because the source fields contain progression inconsistencies.\n",
        "03-recruiter-drive-analysis.md": "# Recruiter and placement drive analytics\n\n" + prefix + "## Companies\n\n" + markdown_table(result["companies"], ["Company_Name", "Recruiter_Verification_Status", "applications", "selected_applications", "unique_selected_students", "selection_pct"]) + "\n## Drive aggregates\n\n" + markdown_table(result["drives"], ["Drive_ID", "Drive_Date", "Registered_Students", "Attending_Students", "Selected_Students", "participation_pct", "selection_of_attendees_pct", "selection_of_registrations_pct"]) + "\nNo individual recruiter activity logs or student-level drive linkage exists. Company verification status is available, but does not measure recruiter activity. Drive totals can overlap students and cannot establish unique participation across drives.\n\n" + method,
        "04-placement-performance.md": "# Placement performance\n\n" + prefix + markdown_table([{"metric": k, "value": v} for k, v in result["overall"].items()], ["metric", "value"]) + "\n" + method + "## Eligible and other unplaced students\n\n" + markdown_table(result["follow_up"], ["student_id", "department", "eligibility", "applications", "interviews", "action"]) + "\n## Supplied historical summaries\n\n" + markdown_table(result["history"], ["Academic_Year", "Department", "Eligible_Students", "Placed_Students", "placement_pct", "Average_Package_LPA", "Highest_Package_LPA"]) + "\nNo recorded placement does not prove unemployment. Historical summaries represent distinct populations and are not the current student-level cohort.\n",
        "05-validation-insights.md": "# Validation and recommendations\n\n" + prefix + markdown_table(result["validation"]["checks"], ["check", "passed"]) + "\n## Actionable recommendations\n\n" + markdown_table(result["recommendations"], ["owner", "evidence", "action", "measure"]) + "\n## Source inconsistencies and analytical limitations\n\n" + warnings,
        "06-final-report.md": "# Final project report\n\n" + prefix + "## Methodology\n\nInspected seven supplied CSV datasets and their Read_Me provenance; validated keys, ranges, dates and relationships; retained separate source grains; generated source-linked EDA, company and drive analysis, KPIs, historical comparisons, follow-up actions and an offline dashboard.\n\n## Findings within supplied demonstration records\n\n" + markdown_table([{"metric": k, "value": v} for k, v in result["overall"].items()], ["metric", "value"]) + "\n" + method + "## Recommendations\n\n" + markdown_table(result["recommendations"], ["owner", "evidence", "action", "measure"]) + "\n## Submission\n\nRequirements and methodology are in docs/. Cleaned CSV and SQLite are reproducible using the README command. This folder contains all six reports, analysis.json, quality.json, dashboard.html, CSV summaries and the follow-up queue. The eight dated weekly branches contain cumulative assignment artifacts with actual Git timestamps. This is an implementation completed ahead of the assigned schedule; it does not establish work performed on future dates or coordinator approval.\n\n## Data availability\n\n" + ("The supplied records are explicitly synthetic. Real institutional results and final placement-cell review remain dependent on authorized real datasets.\n" if result["metadata"]["is_demo"] else "Supplied records require placement-cell verification of completeness and current outcomes.\n"),
    }
    for name, text in documents.items():
        (output / name).write_text(text + "\n", encoding="utf-8")
    for name in ["departments", "companies", "drives", "history", "follow_up", "skills", "cgpa_bands"]:
        export_csv(result[name], output / f"{name}.csv")
    encoded = json.dumps({"tables": tables, "analysis": result}, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    template = template[:template.index("<script>\n'use strict';")] + "<script>\n" + Path(__file__).with_name("supplied-dashboard.js").read_text(encoding="utf-8") + "\n</script></body></html>"
    (output / "dashboard.html").write_text(template.replace("__PLACEMENT_PAYLOAD__", encoded), encoding="utf-8")


def run(source, processed, output):
    paths = [Path(p).resolve() for p in [source, processed, output]]
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(paths) for b in paths[i + 1:]):
        raise DataError("Source, processed and report directories must be separate, non-nested paths")
    tables, quality, is_demo = load(source)
    result = analyze(tables, quality, is_demo)
    if not result["validation"]["passed"]:
        raise DataError("Supplied source reconciliation failed")
    write_outputs(tables, result, processed, output)
    return result
