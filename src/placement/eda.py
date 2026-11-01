"""Descriptive associations; no predictive or causal interpretation."""

from collections import Counter

from .kpis import cohort_metrics


def cgpa_band(value):
    if value is None:
        return "Unknown"
    if value < 6:
        return "Below 6"
    if value < 7:
        return "6–6.99"
    if value < 8:
        return "7–7.99"
    return "8–10"


def analyze(tables, facts):
    bands = [{"band": band, **cohort_metrics([s for s in facts if cgpa_band(s["cgpa"]) == band])}
             for band in ["Below 6", "6–6.99", "7–7.99", "8–10", "Unknown"]]
    skills = sorted({skill for s in facts for skill in s["skills"].split("|") if skill})
    skill_groups = [{"skill": skill, **cohort_metrics([s for s in facts if skill in s["skills"].split("|")])} for skill in skills]
    apps = tables["applications"]
    selected = {a["application_id"] for a in apps if a["status"] == "selected"} | {p["application_id"] for p in tables["placements"]}
    return {"cgpa_bands": bands, "skills": skill_groups,
            "application_statuses": dict(sorted(Counter(a["status"] for a in apps).items())),
            "evidence_counts": {"applications": len(apps),
                                "shortlisted_applications": sum(bool(a["shortlisted_at"]) for a in apps),
                                "interviewed_applications": sum(a["interview_attended"] is True for a in apps),
                                "selected_applications": len(selected),
                                "unique_selected_students": len({a["student_id"] for a in apps if a["application_id"] in selected}),
                                "unique_interviewed_students": len({a["student_id"] for a in apps if a["interview_attended"] is True})},
            "limitations": ["Descriptive snapshot associations do not establish causality.",
                            "Skills are self-reported and overlapping; group counts cannot be summed.",
                            "Funnel evidence counts are application-level; placement counts are student-level.",
                            "No historical snapshots or protected demographic attributes were supplied."]}
