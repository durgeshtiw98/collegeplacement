"""Prepare honest daily evidence and commit the eight cumulative weekly checkpoints.

Run without flags to prepare notes. --commit creates local Git commits/branches only.
Commit timestamps are actual execution times; assigned dates appear only as labels.
"""

import argparse
import hashlib
import json
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEEKS = [
    ("Project Understanding and Data Requirements", [
        ("Review project workflow, portal modules and objectives", "docs/data-requirements.md", "Mapped profiles, jobs, applications, interviews, offers, placement and joining; scoped the data scientist deliverable."),
        ("Identify student, academic, application and placement data requirements", "docs/data-requirements.md", "Identified Student_Data and Applications fields, explicit eligibility and distinct outcome statuses."),
        ("Identify recruiter, company and placement drive fields", "docs/data-requirements.md", "Mapped Company_Data, Job_Postings and aggregate Placement_Drives; individual recruiter activity is unavailable."),
        ("Define placement, participation and recruitment analytical questions", "docs/data-requirements.md", "Defined department, skills, academic, company, participation, salary and follow-up questions."),
        ("Prepare data requirements and proposed KPIs", "docs/data-requirements.md", "Documented unique eligible student placement, company selection, drive participation and distinct salary grains."),
        ("Map data sources and proposed structure", "docs/normalized-contract.md", "Mapped the original seven exports separately from an optional richer eight-table portal contract."),
        ("Review and finalize data analysis plan", "docs/methodology.md", "Documented the reproducible method and acceptance criteria. Coordinator approval has not been supplied."),
    ]),
    ("Data Collection, Cleaning, and Preparation", [
        ("Organize student and academic datasets", "data/raw/Student_Data.csv", "Preserved 12 supplied synthetic student records, grades, CGPA, skills and explicit eligibility."),
        ("Collect application and placement records", "data/raw/Applications.csv", "Preserved 15 application records and separate selection and placement evidence; retained seven offer records separately."),
        ("Review recruiter, company and drive datasets", "data/raw/Placement_Drives.csv", "Inspected company verification, job postings and four aggregate drives; no unsupported student-drive linkage was created."),
        ("Identify missing, duplicate and inconsistent records", "data/cleaned-supplied/quality.json", "Audited missing fields and duplicates; documented selected records retaining earlier application status."),
        ("Clean and standardize available datasets", "src/placement/source_intake.py", "Validated headers, numeric ranges, dates, status values, keys and links; preserved raw source bytes."),
        ("Integrate relevant datasets and verify consistency", "src/placement/prepare.py", "Validated supported student/job/company links and isolated unavailable offer/application and application/drive links."),
        ("Prepare analysis-ready data and preparation documentation", "reports/supplied/01-data-preparation.md", "Delivered cleaned source-schema CSVs, SHA-256 audit and reproducible SQLite generation without imputations."),
    ]),
    ("Exploratory Data Analysis", [
        ("Analyze departments, academics and eligibility", "reports/supplied/02-exploratory-analysis.md", "Grouped students by department and explicit eligibility; kept Review Required separate from an ineligible conclusion."),
        ("Examine qualifications, skills and placement outcomes", "reports/supplied/skills.csv", "Computed overlapping skill-group and CGPA-band outcomes; associations are descriptive, not causal."),
        ("Analyze applications and status distributions", "reports/supplied/02-exploratory-analysis.md", "Counted source application statuses independently from selection and interview fields."),
        ("Study shortlist, interview, selection and placement counts", "src/placement/eda.py", "Kept application counts distinct from unique students and explicitly disclosed conflicting progression fields."),
        ("Identify department and student-group placement patterns", "reports/supplied/cgpa_bands.csv", "Compared department and CGPA groups without inferring unavailable demographic attributes."),
        ("Create initial charts and visual summaries", "reports/supplied/eda-visuals.svg", "Created a standalone vector figure for department and skill placement percentages, labeled synthetic."),
        ("Prepare exploratory analysis report", "reports/supplied/02-exploratory-analysis.md", "Consolidated department, academic, skill and application observations with sample and causal limitations."),
    ]),
    ("Recruiter and Placement Drive Analytics", [
        ("Analyze company recruitment and student selection", "reports/supplied/companies.csv", "Joined applications to companies through Job_ID; counted selected applications and unique selected students separately."),
        ("Evaluate recruiter activity and job opportunities", "reports/supplied/03-recruiter-drive-analysis.md", "Analyzed available company verification and job evidence; individual recruiter activity timestamps are unavailable."),
        ("Analyze drive registrations and participation", "reports/supplied/drives.csv", "Calculated drive attendance / registrations from supplied aggregate counts."),
        ("Examine interview, shortlist and selection trends", "reports/supplied/03-recruiter-drive-analysis.md", "Compared available aggregate stages and separate application interview/selection evidence without inventing event history."),
        ("Analyze average and highest salary packages", "reports/supplied/04-placement-performance.md", "Seven recorded offers average INR 5 LPA and peak at INR 6 LPA; acceptance is not inferred."),
        ("Compare companies, departments and placement drives", "reports/supplied/03-recruiter-drive-analysis.md", "Compared source-supported groups and explicitly excluded unsupported department-level drive allocations."),
        ("Prepare recruiter and drive analytics report", "reports/supplied/03-recruiter-drive-analysis.md", "Delivered company and drive tables, denominator definitions and recruiter-data limitations."),
    ]),
    ("Placement KPIs and Performance Reporting", [
        ("Define placement percentage and supporting metrics", "src/placement/kpis.py", "Used explicit source eligibility and unique recorded placed students in the supplied mode; documented separate normalized-mode definitions."),
        ("Calculate department placement percentages", "reports/supplied/departments.csv", "Reconciled unique eligible and placed counts by department."),
        ("Analyze company student selection rates", "reports/supplied/companies.csv", "Calculated selected application records / all applications to each company; did not sum overlapping unique students."),
        ("Calculate drive participation and selection KPIs", "reports/supplied/drives.csv", "Reported attendance / registrations, selection / attendees and selection / registrations separately."),
        ("Analyze average and highest available salaries", "reports/supplied/04-placement-performance.md", "Reported compensation at recorded-offer grain in annual INR LPA with salary coverage."),
        ("Identify unplaced students and follow-up insights", "reports/supplied/follow_up.csv", "Identified five students with no recorded placement, including four eligible students and one eligibility review."),
        ("Consolidate placement KPIs and performance report", "reports/supplied/04-placement-performance.md", "Consolidated current placement 7/11 = 63.64%, compensation and follow-up; historical populations remain separate."),
    ]),
    ("Dashboard and Data Visualization", [
        ("Plan placement dashboard structure", "src/placement/dashboard.html", "Designed overview, recruitment, student follow-up and data-methodology views with accessible filters."),
        ("Develop department charts and KPI summaries", "reports/supplied/dashboard.html", "Rendered unique placement counts and explicit source-eligibility percentages with department/cohort filtering."),
        ("Create company selection visualizations", "src/placement/supplied-dashboard.js", "Added company selection rates using valid Job_ID-to-company links and distinct offer compensation."),
        ("Develop drive participation and selection charts", "reports/supplied/dashboard.html", "Added drive-level aggregate filtering; department/cohort filters do not allocate aggregate attendance."),
        ("Add salary and unplaced student analysis", "reports/supplied/dashboard.html", "Added recorded offer salary summaries, follow-up search and filtered CSV export."),
        ("Integrate consolidated dashboard and reports", "src/placement/cli.py", "Delivered one-command generation of six reports, audits, CSV/SQLite and self-contained offline HTML."),
        ("Review dashboard clarity, accuracy and consistency", "docs/validation.md", "Reviewed desktop output and source/Python parity; documented remaining strict mobile viewport verification limits."),
    ]),
    ("Validation and Analytical Insights", [
        ("Validate metrics and visualizations against sources", "tests/test_supplied.py", "Passed source-count, denominator, duplicate, reference and output regression checks with independent reconciliation."),
        ("Review missing data and analytical limitations", "reports/supplied/05-validation-insights.md", "Documented missing stable offer IDs, drive links, event history and individual recruiter activity."),
        ("Identify factors associated with recorded placement", "reports/supplied/skills.csv", "Compared skills and CGPA groups while rejecting causal or predictive claims from this small synthetic sample."),
        ("Develop placement improvement recommendations", "reports/supplied/05-validation-insights.md", "Assigned actions for follow-up, stable source identifiers, eligibility verification and outcome review."),
        ("Prepare insights for placement cell and administration", "reports/supplied/05-validation-insights.md", "Linked recommendations to observed evidence, responsible owners and measurable follow-up indicators."),
        ("Incorporate validation and finalize analytical reports", "docs/validation.md", "Recorded 34 passing tests, 99% new-package coverage and a clean dependency audit; no human approval is implied."),
        ("Review dashboard, KPIs and recommendations", "docs/validation.md", "Reconciled supplied and normalized outputs separately; preserved source warnings and disclosed uncompleted strict mobile rerun."),
    ]),
    ("Final Documentation and Project Submission", [
        ("Prepare final methodology, findings, visuals and recommendations", "reports/supplied/06-final-report.md", "Delivered the complete report set, reproducible commands, methodology, limitations and weekly task evidence."),
        ("Package final analysis, dashboard, supporting files and summary", "README.md", "Packaged GitHub submission with eight weekly checkpoints and main; real institutional findings still require authorized data and review."),
    ]),
]

# File introduction dates. Each daily commit also includes its specific task evidence.
FILES = {
    "2026-10-26": [".gitignore"],
    "2026-10-27": ["src/placement/__init__.py", "src/placement/schema.py"],
    "2026-10-30": ["docs/data-requirements.md"],
    "2026-10-31": ["docs/normalized-contract.md"],
    "2026-11-01": ["docs/methodology.md"],
    "2026-11-02": ["src/placement/demo.py", "data/sample", "data/templates"],
    "2026-11-05": ["src/placement/prepare.py"],
    "2026-11-06": ["src/placement/source_intake.py", "requirements.txt", "pyproject.toml"],
    "2026-11-08": ["data/cleaned-supplied", "reports/supplied/01-data-preparation.md", "reports/supplied/quality.json"],
    "2026-11-09": ["src/placement/kpis.py", "src/placement/eda.py"],
    "2026-11-10": ["reports/supplied/skills.csv"],
    "2026-11-13": ["reports/supplied/cgpa_bands.csv"],
    "2026-11-14": ["reports/supplied/eda-visuals.svg"],
    "2026-11-15": ["reports/supplied/02-exploratory-analysis.md"],
    "2026-11-16": ["src/placement/recruiters.py", "reports/supplied/companies.csv"],
    "2026-11-18": ["reports/supplied/drives.csv"],
    "2026-11-22": ["reports/supplied/03-recruiter-drive-analysis.md"],
    "2026-11-23": ["src/placement/reports.py", "src/placement/validate.py", "src/placement/supplied.py"],
    "2026-11-24": ["reports/supplied/departments.csv"],
    "2026-11-28": ["reports/supplied/follow_up.csv"],
    "2026-11-29": ["reports/supplied/04-placement-performance.md", "reports/supplied/history.csv", "reports/supplied/analysis.json"],
    "2026-11-30": ["src/placement/dashboard.py", "src/placement/dashboard.html"],
    "2026-12-02": ["src/placement/supplied-dashboard.js"],
    "2026-12-05": ["src/placement/cli.py", "src/placement/__main__.py", "reports/supplied/dashboard.html", "reports/sample"],
    "2026-12-06": ["docs/screenshots"],
    "2026-12-07": ["tests/test_analytics.py", "tests/test_supplied.py", "tests/browser-smoke.mjs"],
    "2026-12-10": ["reports/supplied/05-validation-insights.md"],
    "2026-12-12": ["requirements-dev.txt", ".github/workflows/analytics.yml", ".github/workflows/weekly.yml", "docs/validation.md"],
    "2026-12-14": ["reports/supplied/06-final-report.md"],
    "2026-12-15": ["README.md", "scripts/weekly_delivery.py", "docs/delivery-plan.json", "submission-manifest.json"],
}


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def prepare():
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    plan = []
    start = date(2026, 10, 26)
    for number, (phase, tasks) in enumerate(WEEKS, 1):
        week_start = start + timedelta(weeks=number - 1)
        week_end = week_start + timedelta(days=len(tasks) - 1)
        branch = f"week-{number:02}_{week_start}_to_{week_end}"
        directory = ROOT / "docs/weekly" / branch
        directory.mkdir(parents=True, exist_ok=True)
        days = []
        summary = [f"# Week {number}: {phase}", "", f"Assigned range: **{week_start}–{week_end}**", f"Branch: `{branch}`", f"Actual preparation: {timestamp}", "", "Implemented ahead of the assigned schedule using supplied synthetic data. Assigned dates do not claim work occurred on those dates. Coordinator approval and real institutional validation are not recorded.", "", "| Assigned date | Task | Evidence |", "| --- | --- | --- |"]
        for offset, (task, artifact, evidence) in enumerate(tasks):
            assigned = str(week_start + timedelta(days=offset))
            note = directory / f"{assigned}.md"
            note.write_text(f"# {assigned}: {task}\n\nOwner: Durgesh Tiwari · Data Scientist.\nAssigned week {number}: {week_start}–{week_end}.\nActual preparation: {timestamp}.\n\n## Implementation evidence\n\n{evidence}\n\nPrimary artifact: `{artifact}`. This artifact is introduced at its relevant cumulative checkpoint; earlier notes may reference the final submission.\n\n## Status and limits\n\nImplementation evidence is prepared for the assigned task. The source is explicitly synthetic; no real institutional outcome, future work date or coordinator approval is claimed. Automated verification and known limits are in `docs/validation.md`.\n", encoding="utf-8")
            summary.append(f"| {assigned} | {task} | [{assigned}.md]({assigned}.md) |")
            days.append({"assigned_date": assigned, "task": task, "note": str(note.relative_to(ROOT)), "files": FILES.get(assigned, [])})
        (directory / "README.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
        plan.append({"week": number, "phase": phase, "start": str(week_start), "end": str(week_end), "branch": branch, "summary": str((directory / "README.md").relative_to(ROOT)), "days": days})
    (ROOT / "docs/delivery-plan.json").write_text(json.dumps({"prepared_at": timestamp, "timestamp_policy": "Actual Git timestamps; assigned dates are labels only", "weeks": plan}, indent=2) + "\n")
    paths = sorted([*ROOT.glob("reports/supplied/*"), *ROOT.glob("data/cleaned-supplied/*"), *ROOT.glob("docs/weekly/**/*.md")])
    inventory = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
    (ROOT / "submission-manifest.json").write_text(json.dumps({"author": "Durgesh Tiwari", "prepared_at": timestamp, "source_type": "supplied synthetic workbook", "weekly_branches": [w["branch"] for w in plan], "daily_tasks": sum(len(w["days"]) for w in plan), "sha256": inventory}, indent=2) + "\n")
    return plan


def commit(plan):
    for week in plan:
        if subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{week['branch']}"], cwd=ROOT).returncode == 0:
            raise RuntimeError(f"Branch already exists: {week['branch']}; refusing to overwrite it")
    if git("branch", "--show-current") != "main":
        raise RuntimeError("Start from main; existing branches are not overwritten")
    for week in plan:
        for index, day in enumerate(week["days"]):
            files = [day["note"], *day["files"]]
            if index == len(week["days"]) - 1:
                files.append(week["summary"])
            git("add", "--", *files)
            # No author/committer dates are changed.
            git("commit", "-m", f"week {week['week']} | assigned {day['assigned_date']}: {day['task']}")
        git("branch", week["branch"])
        print(f"Created {week['branch']}: {len(week['days'])} daily task commits", flush=True)
    print(git("status", "--short"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", action="store_true", help="Create the 51 local commits and eight branches; never pushes")
    args = parser.parse_args()
    delivery = prepare()
    if args.commit:
        commit(delivery)
    else:
        print("Prepared eight weekly summaries, 51 daily evidence notes and the submission manifest")
