"""Independent reconciliations and data-backed operational recommendations."""

from collections import Counter

from .schema import PLACED_STATUSES, eligible, rate


def validate(tables, result):
    checks = []

    def check(name, condition):
        checks.append({"check": name, "passed": bool(condition)})

    overall = result["kpis"]["overall"]
    applications = {a["application_id"]: a for a in tables["applications"]}
    academics = {a["student_id"]: a for a in tables["academics"]}
    placed = {applications[p["application_id"]]["student_id"] for p in tables["placements"] if p["status"] in PLACED_STATUSES}
    eligible_ids = {s["student_id"] for s in tables["students"] if eligible(academics.get(s["student_id"])) is True}
    check("Unique placed students reconcile to accepted/joined source offers", overall["placed_students"] == len(placed))
    check("Eligible denominator reconciles to academic source", overall["eligible_students"] == len(eligible_ids))
    check("Eligible placement percentage reconciles independently", overall["eligible_placement_pct"] == rate(len(placed & eligible_ids), len(eligible_ids)))
    check("Student total reconciles across departments", sum(r["students"] for r in result["kpis"]["departments"]) == len(tables["students"]))
    check("Placed and unplaced partition student population", overall["placed_students"] + overall["unplaced_students"] == len(tables["students"]))
    check("Department placed counts reconcile", sum(r["placed_students"] for r in result["kpis"]["departments"]) == len(placed))
    check("Follow-up queue matches unplaced population", len(result["kpis"]["follow_up"]) == overall["unplaced_students"])
    check("Follow-up excludes placed students", not (placed & {r["student_id"] for r in result["kpis"]["follow_up"]}))
    check("Application statuses partition all application records", sum(result["eda"]["application_statuses"].values()) == len(applications))
    check("Drive application counts reconcile", sum(d["applications"] for d in result["recruitment"]["drives"]) == len(applications))
    check("Company application counts reconcile", sum(c["applications"] for c in result["recruitment"]["companies"]) == len(applications))
    check("Registration counts reconcile across drives", sum(d["registrations"] for d in result["recruitment"]["drives"]) == len(tables["registrations"]))
    amounts = [p["annual_ctc_inr"] for p in tables["placements"] if p["status"] in PLACED_STATUSES and p["annual_ctc_inr"] is not None]
    check("Known salary offer count reconciles", overall["known_salary_offers"] == len(amounts))
    check("Highest annual salary reconciles", overall["highest_ctc_inr"] == (max(amounts) if amounts else None))
    check("Average annual salary reconciles", overall["average_ctc_inr"] == (round(sum(amounts) / len(amounts), 2) if amounts else None))
    check("No source rows lost without duplicate audit", all(q["source_rows"] == q["clean_rows"] + q["exact_duplicates_removed"] for q in result["quality"]["tables"].values()))
    return {"passed": all(c["passed"] for c in checks), "checks": checks}


def recommendations(result):
    overall = result["kpis"]["overall"]
    queue = result["kpis"]["follow_up"]
    output = []
    if overall["unknown_eligibility"]:
        output.append({"owner": "Examination cell", "evidence": f"{overall['unknown_eligibility']} students have unknown eligibility", "action": "Complete missing CGPA/backlog records and rerun the cohort calculation", "measure": "Unknown eligibility count"})
    actions = Counter(r["recommended_follow_up"] for r in queue if r["eligible"] is True)
    for action, count in sorted(actions.items()):
        output.append({"owner": "Placement cell", "evidence": f"{count} eligible students in this follow-up group", "action": action, "measure": "Group count and subsequent verified outcomes"})
    if overall["known_salary_offers"] < overall["accepted_joined_offers"]:
        output.append({"owner": "Placement cell / recruiters", "evidence": f"{overall['accepted_joined_offers'] - overall['known_salary_offers']} accepted/joined offers have missing salary", "action": "Verify annual INR CTC against offer letters before compensation comparisons", "measure": "Known salary coverage percentage"})
    departments = [d for d in result["kpis"]["departments"] if d["eligible_placement_pct"] is not None]
    if departments:
        lowest = min(departments, key=lambda d: (d["eligible_placement_pct"], d["department"]))
        output.append({"owner": "Department placement coordinator", "evidence": f"{lowest['department']} has the lowest observed eligible placement rate ({lowest['eligible_placement_pct']}%; {lowest['eligible_placed_students']}/{lowest['eligible_students']})", "action": "Review student participation and recruiter feedback before choosing support interventions", "measure": "Eligible participation, interview progression and verified placement rate"})
    return output
