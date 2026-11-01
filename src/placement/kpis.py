"""Metrics at explicitly stated student, application and offer grains."""

import statistics
from collections import Counter

from .schema import PLACED_STATUSES, eligible, rate


def student_facts(tables):
    academics = {r["student_id"]: r for r in tables["academics"]}
    applications = {r["application_id"]: r for r in tables["applications"]}
    placed = {applications[p["application_id"]]["student_id"] for p in tables["placements"] if p["status"] in PLACED_STATUSES}
    app_count = Counter(r["student_id"] for r in tables["applications"])
    interview_count = Counter(r["student_id"] for r in tables["applications"] if r["interview_attended"] is True)
    return [{**s, **academics.get(s["student_id"], {"cgpa": None, "backlogs": None}),
             "eligible": eligible(academics.get(s["student_id"])),
             "placed": s["student_id"] in placed,
             "applications": app_count[s["student_id"]],
             "interviews": interview_count[s["student_id"]]} for s in tables["students"]]


def cohort_metrics(facts):
    count = len(facts)
    eligible_facts = [s for s in facts if s["eligible"] is True]
    placed = sum(s["placed"] for s in facts)
    eligible_placed = sum(s["placed"] for s in eligible_facts)
    return {"students": count, "eligible_students": len(eligible_facts),
            "unknown_eligibility": sum(s["eligible"] is None for s in facts),
            "placed_students": placed, "eligible_placed_students": eligible_placed,
            "unplaced_students": count - placed,
            "eligible_placement_pct": rate(eligible_placed, len(eligible_facts)),
            "all_student_placement_pct": rate(placed, count)}


def salary_metrics(offers):
    accepted = [p for p in offers if p["status"] in PLACED_STATUSES]
    salaries = [p["annual_ctc_inr"] for p in accepted if p["annual_ctc_inr"] is not None]
    return {"accepted_joined_offers": len(accepted), "known_salary_offers": len(salaries),
            "salary_coverage_pct": rate(len(salaries), len(accepted)),
            "average_ctc_inr": round(statistics.mean(salaries), 2) if salaries else None,
            "median_ctc_inr": round(statistics.median(salaries), 2) if salaries else None,
            "highest_ctc_inr": max(salaries) if salaries else None}


def follow_up(facts):
    output = []
    for student in facts:
        if student["placed"]:
            continue
        if student["eligible"] is None:
            action = "Verify academic records before assessing eligibility"
        elif student["eligible"] is False:
            action = "Review academic support and company-specific eligibility"
        elif not student["applications"]:
            action = "Contact student about participation and available roles"
        elif not student["interviews"]:
            action = "Review applications, skills evidence and shortlisting feedback"
        else:
            action = "Review interview feedback and pending offer outcomes"
        output.append({"student_id": student["student_id"], "department": student["department"],
                       "eligible": student["eligible"], "applications": student["applications"],
                       "interviews": student["interviews"], "recommended_follow_up": action})
    return output


def compute(tables):
    facts = student_facts(tables)
    departments = [{"department": dept, **cohort_metrics([s for s in facts if s["department"] == dept])}
                   for dept in sorted({s["department"] for s in facts})]
    return {"overall": {**cohort_metrics(facts), **salary_metrics(tables["placements"])},
            "departments": departments, "student_facts": facts, "follow_up": follow_up(facts)}
