# Final project report

**SYNTHETIC DEMO — NOT INSTITUTIONAL FINDINGS** · Actual generation: 2026-11-01T04:52:54+00:00

Prepared by Durgesh Tiwari, Data Scientist. Assigned schedule: 26 October–15 December 2026. This schedule is not the actual completion timestamp; generated files and Git record actual execution dates.

## Methodology

Validated eight source tables, standardized field values, removed audited exact duplicates, checked foreign keys, produced normalized CSV and SQLite, calculated descriptive statistics and reconciled results against source records. The self-contained dashboard applies department, cohort, company and drive filters without transmitting data.

## Findings within supplied records

| metric | value |
| --- | --- |
| students | 180 |
| eligible_students | 126 |
| unknown_eligibility | 9 |
| placed_students | 78 |
| eligible_placement_pct | 39.68 |
| average_ctc_inr | 818539.33 |
| highest_ctc_inr | 1500000.0 |
| salary_coverage_pct | 81.65 |

## Actions

| owner | evidence | action | measure |
| --- | --- | --- | --- |
| Examination cell | 9 students have unknown eligibility | Complete missing CGPA/backlog records and rerun the cohort calculation | Unknown eligibility count |
| Placement cell | 3 eligible students in this follow-up group | Contact student about participation and available roles | Group count and subsequent verified outcomes |
| Placement cell | 14 eligible students in this follow-up group | Review applications, skills evidence and shortlisting feedback | Group count and subsequent verified outcomes |
| Placement cell | 59 eligible students in this follow-up group | Review interview feedback and pending offer outcomes | Group count and subsequent verified outcomes |
| Placement cell / recruiters | 20 accepted/joined offers have missing salary | Verify annual INR CTC against offer letters before compensation comparisons | Known salary coverage percentage |
| Department placement coordinator | IT has the lowest observed eligible placement rate (21.74%; 5/23) | Review student participation and recruiter feedback before choosing support interventions | Eligible participation, interview progression and verified placement rate |

## Analytical limitations

- Snapshot records do not establish historical trends or causation.
- Academic eligibility is a documented proxy, not recruiter policy.
- Missing academic and salary data can bias comparisons.
- Skills are self-reported and group membership overlaps.
- Company unique student totals overlap across companies.
- Missing accepted/joined records do not establish unemployment.
- No source-system authentication or independent verification of supplied facts is performed.

## Submission inventory

1. `docs/data-requirements.md`, `docs/methodology.md`, `01-data-preparation.md`: requirements and preparation.
2. Processed CSV and `placement.sqlite3`: cleaned data, subject to source availability.
3. `02-exploratory-analysis.md`: EDA.
4. `03-recruiter-drive-analysis.md`: recruiter and drive report.
5. `04-placement-performance.md`: KPIs and follow-up.
6. `dashboard.html`: consolidated interactive visualizations.
7. `05-validation-insights.md`, this report, `analysis.json`, CSV summaries and weekly evidence: validation, documentation and supporting files.

## Real-data acceptance

Institutional findings remain pending because no real datasets were present in the supplied folder. The committed results demonstrate the pipeline with fictional inputs. Run with authorized real source files to replace this limitation.
