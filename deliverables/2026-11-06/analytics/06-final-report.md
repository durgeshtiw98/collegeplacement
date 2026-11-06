# Final project report

**SUPPLIED SYNTHETIC WORKBOOK — NOT REAL COLLEGE OUTCOMES**

Owner: Durgesh Tiwari · Assigned: 26 October–15 December 2026.

Actual generation: 2026-11-06T06:42:44+00:00. All supplied example rows are included; this is not a historical cutoff.

## Methodology

Inspected seven supplied CSV datasets and their Read_Me provenance; validated keys, ranges, dates and relationships; retained separate source grains; generated source-linked EDA, company and drive analysis, KPIs, historical comparisons, follow-up actions and an offline dashboard.

## Findings within supplied demonstration records

| metric | value |
| --- | --- |
| students | 12 |
| eligible_students | 11 |
| placed_students | 7 |
| eligible_placed_students | 7 |
| eligible_placement_pct | 63.64 |
| all_student_placement_pct | 58.33 |
| selected_students | 7 |
| joined_students | 4 |
| offer_records | 7 |
| known_salary_offers | 7 |
| salary_coverage_pct | 100.0 |
| average_offer_salary_lpa | 5.0 |
| highest_offer_salary_lpa | 6.0 |
| unknown_eligibility | 1 |

## Definitions and limitations

Placement = unique student with Applications.Placement_Status = Placed. Eligibility = the explicit Student_Data.Eligibility_Status = Eligible, not an invented CGPA/backlog rule. Salary = recorded offers in INR LPA; acceptance is unknown and joined counts are reported separately. Company selection = selected application records / applications. Drive participation = attending / registered; drive selection = selected / attending. Historical summaries remain separate because their populations differ.

## Recommendations

| owner | evidence | action | measure |
| --- | --- | --- | --- |
| Placement cell | 4 eligible students have no recorded placement | Use the follow-up queue to review participation and interview feedback | Eligible unplaced count and subsequently verified outcomes |
| Data engineering / placement cell | No application-drive key or offer/application identifier | Capture stable offer IDs, application IDs and student-drive attendance in the portal | Link completeness and unreconciled outcome count |
| Department coordinators | 1 students require eligibility review | Verify eligibility status without inferring backlogs from CGPA | Unknown eligibility count |

## Submission

Requirements and methodology are in docs/. Cleaned CSV and SQLite are reproducible using the README command. This folder contains all six reports, analysis.json, quality.json, dashboard.html, CSV summaries and the follow-up queue. The eight dated weekly branches contain cumulative assignment artifacts with actual Git timestamps. This is an implementation completed ahead of the assigned schedule; it does not establish work performed on future dates or coordinator approval.

## Data availability

The supplied records are explicitly synthetic. Real institutional results and final placement-cell review remain dependent on authorized real datasets.

