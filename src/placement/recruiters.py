"""Company, recruiter and placement-drive aggregates with explicit denominators."""

from collections import Counter

from .kpis import salary_metrics
from .schema import PLACED_STATUSES, rate


def summarize(tables, drive_ids):
    apps = [a for a in tables["applications"] if a["drive_id"] in drive_ids]
    app_ids = {a["application_id"] for a in apps}
    offers = [p for p in tables["placements"] if p["application_id"] in app_ids]
    selected_ids = {a["application_id"] for a in apps if a["status"] == "selected"} | {p["application_id"] for p in offers}
    placed_app_ids = {p["application_id"] for p in offers if p["status"] in PLACED_STATUSES}
    selected_students = {a["student_id"] for a in apps if a["application_id"] in selected_ids}
    registrations = [r for r in tables["registrations"] if r["drive_id"] in drive_ids]
    registration_students = {r["student_id"] for r in registrations}
    attended = sum(r["attended"] is True for r in registrations)
    return {"drives": len(drive_ids), "applications": len(apps), "selected_applications": len(selected_ids),
            "unique_applicants": len({a["student_id"] for a in apps}),
            "unique_selected_students": len(selected_students),
            "unique_placed_students": len({a["student_id"] for a in apps if a["application_id"] in placed_app_ids}),
            "selection_rate_pct": rate(len(selected_ids), len(apps)),
            "registrations": len(registrations), "attended_registrations": attended,
            "unknown_attendance": sum(r["attended"] is None for r in registrations),
            "participation_rate_pct": rate(attended, len(registrations)),
            "registered_student_selection_pct": rate(len(selected_students & registration_students), len(registration_students)),
            **salary_metrics(offers)}


def analyze(tables):
    companies = [{**c, **summarize(tables, {d["drive_id"] for d in tables["drives"] if d["company_id"] == c["company_id"]})}
                 for c in tables["companies"]]
    drives = [{**d, **summarize(tables, {d["drive_id"]})} for d in tables["drives"]]
    recruiters = [{**r, **summarize(tables, {d["drive_id"] for d in tables["drives"] if d["recruiter_id"] == r["recruiter_id"]})}
                  for r in tables["recruiters"]]
    monthly = dict(sorted(Counter(d["drive_date"][:7] for d in tables["drives"]).items()))
    return {"companies": companies, "drives": drives, "recruiters": recruiters, "observed_drives_by_month": monthly}
