"""Portable Markdown reports and safe CSV exports."""

import csv
import json
from collections import Counter
from pathlib import Path


def display(value):
    if value is None:
        return "N/A"
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown_table(rows, columns):
    header = "| " + " | ".join(columns) + " |\n| " + " | ".join("---" for _ in columns) + " |\n"
    return header + "".join("| " + " | ".join(display(row.get(c)) for c in columns) + " |\n" for row in rows)


def safe_cell(value):
    """Neutralize spreadsheet formula payloads in downloadable text cells."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def export_csv(rows, path, columns=None):
    columns = columns or (list(rows[0]) if rows else ["no_records"])
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows({key: safe_cell(row.get(key)) for key in columns} for row in rows)


def generate(result, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    metadata = result["metadata"]
    prefix = f"**{metadata['data_label']}** · Generated {metadata['generated_at']}\n\n"
    prefix += "Owner: Durgesh Tiwari · Assigned project: 26 October–15 December 2026.\n\n"
    prefix += "Values describe supplied records only. N/A means an unavailable value or zero denominator.\n\n"
    (output / "analysis.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    quality = result["quality"]
    quality_rows = [{"table": name, **{k: v for k, v in info.items() if k != "missing_values"}} for name, info in quality["tables"].items()]
    (output / "01-data-preparation.md").write_text("# Data preparation report\n\n" + prefix + markdown_table(quality_rows, ["table", "source_rows", "clean_rows", "exact_duplicates_removed"]) + "\n## Missing values after cleaning\n\n```json\n" + json.dumps({k: v["missing_values"] for k, v in quality["tables"].items()}, indent=2) + "\n```\n\n## Audit and method\n\nSources are hashed in `analysis.json`. Exact duplicates are removed; conflicts and invalid links stop analysis. No academic or salary values are imputed. Clean CSV files and a relational SQLite database are written to the processed directory.\n\nWarnings: " + ("; ".join(quality["warnings"]) or "None") + "\n", encoding="utf-8")
    eda = result["eda"]
    (output / "02-exploratory-analysis.md").write_text("# Exploratory data analysis\n\n" + prefix + "## Departments\n\n" + markdown_table(result["kpis"]["departments"], ["department", "students", "eligible_students", "placed_students", "eligible_placement_pct", "unknown_eligibility"]) + "\n## Academic performance\n\n" + markdown_table(eda["cgpa_bands"], ["band", "students", "placed_students", "all_student_placement_pct"]) + "\n## Skills and outcomes\n\n" + markdown_table(eda["skills"], ["skill", "students", "placed_students", "all_student_placement_pct"]) + "\n## Application statuses\n\n" + markdown_table([{"status": k, "applications": v} for k, v in eda["application_statuses"].items()], ["status", "applications"]) + "\n## Recorded progression evidence\n\n" + markdown_table([eda["evidence_counts"]], list(eda["evidence_counts"])) + "\n" + "\n".join("- " + text for text in eda["limitations"]) + "\n", encoding="utf-8")
    recruitment = result["recruitment"]
    (output / "03-recruiter-drive-analysis.md").write_text("# Recruiter and placement drive analytics\n\n" + prefix + "## Companies\n\n" + markdown_table(recruitment["companies"], ["company_name", "drives", "applications", "unique_selected_students", "selection_rate_pct", "average_ctc_inr", "highest_ctc_inr", "salary_coverage_pct"]) + "\n## Recruiters\n\n" + markdown_table(recruitment["recruiters"], ["recruiter_id", "company_id", "drives", "applications", "selected_applications"]) + "\n## Drives\n\n" + markdown_table(recruitment["drives"], ["drive_id", "drive_date", "registrations", "attended_registrations", "participation_rate_pct", "applications", "selected_applications", "selection_rate_pct"]) + "\n## Observed calendar coverage\n\n" + markdown_table([{"month": k, "drives": v} for k, v in recruitment["observed_drives_by_month"].items()], ["month", "drives"]) + "\nOnly months represented in the source are shown. Company unique student counts overlap and must not be added to obtain the college total.\n", encoding="utf-8")
    overall = result["kpis"]["overall"]
    (output / "04-placement-performance.md").write_text("# Placement KPI and performance report\n\n" + prefix + markdown_table([{"metric": k, "value": v} for k, v in overall.items()], ["metric", "value"]) + "\n## Definitions\n\nEligible placement percentage uses unique eligible placed students / eligible students. Analytical eligibility is CGPA ≥ 6 and zero backlogs, with unknown values excluded from that denominator. All-student placement percentage is reported separately. Accepted/joined offers establish observed placement. Salary summaries use known positive annual INR CTC for accepted/joined offers at offer grain.\n\nCompany selection rates use selected applications / applications, including withdrawals in the denominator. Drive participation uses known attended registrations / all registrations, with unknown attendance disclosed. N/A is preserved for empty denominators and absent compensation.\n\n## Follow-up\n\n" + markdown_table([{"action": k, "students": v} for k, v in sorted(Counter(r["recommended_follow_up"] for r in result["kpis"]["follow_up"]).items())], ["action", "students"]) + "\nThe complete pseudonymous queue is in `follow-up.csv`. No observed accepted/joined offer means unplaced in these records; it does not prove a student is unemployed.\n", encoding="utf-8")
    for key, rows in [("departments", result["kpis"]["departments"]), ("companies", recruitment["companies"]), ("drives", recruitment["drives"]), ("follow-up", result["kpis"]["follow_up"])]:
        export_csv(rows, output / f"{key}.csv")
