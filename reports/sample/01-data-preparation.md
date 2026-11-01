# Data preparation report

**SYNTHETIC DEMO — NOT INSTITUTIONAL FINDINGS** · Generated 2026-11-01T04:52:54+00:00

Owner: Durgesh Tiwari · Assigned project: 26 October–15 December 2026.

Values describe supplied records only. N/A means an unavailable value or zero denominator.

| table | source_rows | clean_rows | exact_duplicates_removed |
| --- | --- | --- | --- |
| students | 181 | 180 | 1 |
| academics | 180 | 180 | 0 |
| companies | 6 | 6 | 0 |
| recruiters | 6 | 6 | 0 |
| drives | 18 | 18 | 0 |
| registrations | 764 | 764 | 0 |
| applications | 672 | 672 | 0 |
| placements | 133 | 133 | 0 |

## Missing values after cleaning

```json
{
  "students": {
    "student_id": 0,
    "department": 0,
    "graduation_year": 0,
    "skills": 0
  },
  "academics": {
    "student_id": 0,
    "cgpa": 5,
    "backlogs": 4
  },
  "companies": {
    "company_id": 0,
    "company_name": 0,
    "industry": 0
  },
  "recruiters": {
    "recruiter_id": 0,
    "company_id": 0,
    "role": 0
  },
  "drives": {
    "drive_id": 0,
    "company_id": 0,
    "recruiter_id": 0,
    "drive_date": 0,
    "job_role": 0,
    "min_cgpa": 0
  },
  "registrations": {
    "registration_id": 0,
    "student_id": 0,
    "drive_id": 0,
    "attended": 0
  },
  "applications": {
    "application_id": 0,
    "student_id": 0,
    "drive_id": 0,
    "applied_at": 0,
    "status": 0,
    "shortlisted_at": 275,
    "interview_attended": 0
  },
  "placements": {
    "placement_id": 0,
    "application_id": 0,
    "status": 0,
    "annual_ctc_inr": 22,
    "outcome_date": 0
  }
}
```

## Audit and method

Sources are hashed in `analysis.json`. Exact duplicates are removed; conflicts and invalid links stop analysis. No academic or salary values are imputed. Clean CSV files and a relational SQLite database are written to the processed directory.

Warnings: None
