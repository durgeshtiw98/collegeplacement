"""Explicit CSV contracts and shared parsing rules."""

SCHEMAS = {
    "students": ["student_id", "department", "graduation_year", "skills"],
    "academics": ["student_id", "cgpa", "backlogs"],
    "companies": ["company_id", "company_name", "industry"],
    "recruiters": ["recruiter_id", "company_id", "role"],
    "drives": ["drive_id", "company_id", "recruiter_id", "drive_date", "job_role", "min_cgpa"],
    "registrations": ["registration_id", "student_id", "drive_id", "attended"],
    "applications": ["application_id", "student_id", "drive_id", "applied_at", "status", "shortlisted_at", "interview_attended"],
    "placements": ["placement_id", "application_id", "status", "annual_ctc_inr", "outcome_date"],
}
KEYS = {name: fields[0] for name, fields in SCHEMAS.items()}
FOREIGN_KEYS = {
    "academics": [("student_id", "students")],
    "recruiters": [("company_id", "companies")],
    "drives": [("company_id", "companies"), ("recruiter_id", "recruiters")],
    "registrations": [("student_id", "students"), ("drive_id", "drives")],
    "applications": [("student_id", "students"), ("drive_id", "drives")],
    "placements": [("application_id", "applications")],
}
APPLICATION_STATUSES = {"applied", "shortlisted", "interviewed", "selected", "rejected", "withdrawn"}
PLACEMENT_STATUSES = {"offered", "accepted", "joined", "declined", "revoked"}
STATUS_ALIASES = {"hired": "selected", "pending": "applied", "short listed": "shortlisted"}
PLACED_STATUSES = {"accepted", "joined"}
OPTIONAL = {
    "students": {"skills"}, "academics": {"cgpa", "backlogs"},
    "companies": {"industry"}, "recruiters": {"role"}, "drives": {"min_cgpa"},
    "registrations": {"attended"},
    "applications": {"shortlisted_at", "interview_attended"},
    "placements": {"annual_ctc_inr"},
}


def rate(numerator, denominator):
    """Return null for an undefined rate, never a fabricated zero."""
    return round(100 * numerator / denominator, 2) if denominator else None


def eligible(academic):
    """Analytical cohort proxy; not a company's actual eligibility decision."""
    if not academic or academic["cgpa"] is None or academic["backlogs"] is None:
        return None
    return academic["cgpa"] >= 6 and academic["backlogs"] == 0
