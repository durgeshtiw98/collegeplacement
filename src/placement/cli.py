"""Command-line entry point for reproducible, explicitly demo or source-backed runs."""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import eda, recruiters
from .dashboard import render
from .demo import generate as generate_demo, write_tables
from .kpis import compute
from .prepare import DataError, read_sources, save_prepared
from .reports import generate as generate_reports, markdown_table
from .validate import recommendations, validate


def analyze(tables, quality, is_demo=False):
    kpis = compute(tables)
    result = {"metadata": {"project": "Tech-College Placement Management Portal",
                           "author": "Durgesh Tiwari", "assigned_period": "2026-10-26/2026-12-15",
                           "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                           "is_demo": is_demo, "data_label": "SYNTHETIC DEMO — NOT INSTITUTIONAL FINDINGS" if is_demo else "SUPPLIED SOURCE DATA — VERIFY SOURCE COVERAGE",
                           "salary_unit": "annual INR CTC", "eligibility_proxy": "CGPA >= 6 and zero backlogs"},
              "quality": quality, "kpis": kpis,
              "eda": eda.analyze(tables, kpis["student_facts"]), "recruitment": recruiters.analyze(tables)}
    result["validation"] = validate(tables, result)
    result["recommendations"] = recommendations(result)
    return result


def final_reports(result, output):
    output = Path(output)
    label = result["metadata"]["data_label"]
    generated = result["metadata"]["generated_at"]
    prefix = f"**{label}** · Actual generation: {generated}\n\n"
    check_rows = [{"check": c["check"], "result": "PASS" if c["passed"] else "FAIL"} for c in result["validation"]["checks"]]
    limitations = "\n## Analytical limitations\n\n- Snapshot records do not establish historical trends or causation.\n- Academic eligibility is a documented proxy, not recruiter policy.\n- Missing academic and salary data can bias comparisons.\n- Skills are self-reported and group membership overlaps.\n- Company unique student totals overlap across companies.\n- Missing accepted/joined records do not establish unemployment.\n- No source-system authentication or independent verification of supplied facts is performed.\n"
    (output / "05-validation-insights.md").write_text("# Validation and actionable insights\n\n" + prefix + markdown_table(check_rows, ["check", "result"]) + "\n## Recommendations\n\n" + markdown_table(result["recommendations"], ["owner", "evidence", "action", "measure"]) + limitations, encoding="utf-8")
    o = result["kpis"]["overall"]
    text = f"# Final project report\n\n{prefix}Prepared by Durgesh Tiwari, Data Scientist. Assigned schedule: 26 October–15 December 2026. This schedule is not the actual completion timestamp; generated files and Git record actual execution dates.\n\n## Methodology\n\nValidated eight source tables, standardized field values, removed audited exact duplicates, checked foreign keys, produced normalized CSV and SQLite, calculated descriptive statistics and reconciled results against source records. The self-contained dashboard applies department, cohort, company and drive filters without transmitting data.\n\n## Findings within supplied records\n\n"
    text += markdown_table([{"metric": k, "value": o[k]} for k in ["students", "eligible_students", "unknown_eligibility", "placed_students", "eligible_placement_pct", "average_ctc_inr", "highest_ctc_inr", "salary_coverage_pct"]], ["metric", "value"])
    text += "\n## Actions\n\n" + markdown_table(result["recommendations"], ["owner", "evidence", "action", "measure"]) + limitations
    text += "\n## Submission inventory\n\n1. `docs/data-requirements.md`, `docs/methodology.md`, `01-data-preparation.md`: requirements and preparation.\n2. Processed CSV and `placement.sqlite3`: cleaned data, subject to source availability.\n3. `02-exploratory-analysis.md`: EDA.\n4. `03-recruiter-drive-analysis.md`: recruiter and drive report.\n5. `04-placement-performance.md`: KPIs and follow-up.\n6. `dashboard.html`: consolidated interactive visualizations.\n7. `05-validation-insights.md`, this report, `analysis.json`, CSV summaries and weekly evidence: validation, documentation and supporting files.\n\n## Real-data acceptance\n\n"
    text += "Institutional findings remain pending because no real datasets were present in the supplied folder. The committed results demonstrate the pipeline with fictional inputs. Run with authorized real source files to replace this limitation.\n" if result["metadata"]["is_demo"] else "These findings use supplied source files. Confirm the source manifest, student cohort, salary units, current outcome status and record completeness with the placement cell before institutional submission.\n"
    (output / "06-final-report.md").write_text(text, encoding="utf-8")


def parser():
    root = argparse.ArgumentParser(description="College placement analytics by Durgesh Tiwari")
    commands = root.add_subparsers(dest="command", required=True)
    supplied = commands.add_parser("supplied", help="Analyze the original supplied workbook CSV exports")
    supplied.add_argument("--input", type=Path, default=Path("data/raw"))
    supplied.add_argument("--processed", type=Path, default=Path("data/processed-supplied"))
    supplied.add_argument("--output", type=Path, default=Path("reports/supplied"))
    demo = commands.add_parser("demo", help="Generate fictional sources; never institutional findings")
    demo.add_argument("--output", type=Path, default=Path("data/sample"))
    template = commands.add_parser("templates", help="Write header-only intake templates")
    template.add_argument("--output", type=Path, default=Path("data/templates"))
    for name in ["prepare", "run", "validate"]:
        command = commands.add_parser(name)
        command.add_argument("--input", type=Path, default=Path("data/raw"))
        command.add_argument("--demo", action="store_true", help="Use data/sample and label every output synthetic")
        command.add_argument("--processed", type=Path, default=Path("data/processed"))
        if name == "run":
            command.add_argument("--output", type=Path, default=Path("reports/generated"))
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "supplied":
            from .supplied import run
            result = run(args.input, args.processed, args.output)
            print(result["metadata"]["data_label"])
            print(f"{len(result['validation']['checks'])} supplied-data reconciliation checks passed")
            print(f"Dashboard: {(args.output / 'dashboard.html').resolve()}")
            return 0
        if args.command == "demo":
            generate_demo(args.output)
            print(f"SYNTHETIC DEMO sources written to {args.output}")
            return 0
        if args.command == "templates":
            write_tables({}, args.output)
            print(f"CSV templates written to {args.output}")
            return 0
        source = Path("data/sample") if args.demo else args.input
        destinations = [args.processed] + ([args.output] if args.command == "run" else [])
        resolved = [source.resolve()] + [p.resolve() for p in destinations]
        for i, left in enumerate(resolved):
            for right in resolved[i + 1:]:
                if left == right or left in right.parents or right in left.parents:
                    raise DataError("Source, processed and report directories must be separate, non-nested paths")
        tables, quality = read_sources(source)
        if args.command == "prepare":
            save_prepared(tables, quality, args.processed)
            print(f"Prepared {len(tables['students'])} students in {args.processed}")
            return 0
        result = analyze(tables, quality, args.demo)
        if not result["validation"]["passed"]:
            raise DataError("Reconciliation failed; outputs were not published")
        if args.command == "validate":
            print(json.dumps(result["validation"], indent=2))
            return 0
        save_prepared(tables, quality, args.processed)
        generate_reports(result, args.output)
        final_reports(result, args.output)
        render(result, tables, args.output / "dashboard.html")
        print(result["metadata"]["data_label"])
        print(f"{len(result['validation']['checks'])} reconciliation checks passed")
        print(f"Dashboard: {(args.output / 'dashboard.html').resolve()}")
        return 0
    except (DataError, OSError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
