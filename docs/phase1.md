# Phase 1 — Requirements and analysis plan

Owner: Durgesh Tiwari | Role: Data Scientist | Project period: October 26–December 15, 2026

## Scope and sources

The workflow covers student registration, recruiter verification, verified job posts, applications, interviews, offers, drive participation, and placement reporting. Analytics supports the placement cell; portal development is a separate scope.

Inputs are the supplied synthetic workbook and the portal workflow document. All reported outcomes must be identified as demonstration results. Preserve raw records and record inconsistencies rather than inventing corrections.

| Dataset | Grain | Identifier / joins | Required checks |
| --- | --- | --- | --- |
| Student_Data | One student | Student_ID; department | Unique ID, CGPA 0–10, percentages 0–100, eligibility |
| Company_Data | One company | Company_ID | Unique ID, verification status |
| Job_Postings | One posting | Job_ID → Company_ID | Company reference, salary nonnegative, verification |
| Applications | One application | Application_ID → Student_ID, Job_ID | References, duplicates, status consistency |
| Placement_Drives | One drive | Drive_ID → Company_ID | Nonnegative counts; selected ≤ shortlisted ≤ attending ≤ registered |
| Offers | One recorded offer | Student_ID, Company_ID | References, duplicate rows, salary, letter and joining status |
| Historical_Placements | Academic year and department | Academic_Year + Department | Placed ≤ eligible; highest salary ≥ average |

The workbook has no offer ID, offer-to-job ID, application status event history, student-level drive attendance, or recruiter activity timestamps. Do not join offers to applications by role text and assume a reliable match. Drive aggregates cannot establish unique students across drives. Historical summaries must remain separate from current student records.

## Questions and KPI definitions

1. Which departments have the highest eligible-student placement percentage?
2. Where do applications stop in the recruitment process?
3. Which companies select applicants, and how does drive attendance compare with registration?
4. What salaries are recorded, and which eligible students have no recorded placement?
5. What associations appear between skills, CGPA and outcomes? Small samples support descriptive observations only.

| Metric | Definition |
| --- | --- |
| Placement percentage | Unique eligible students with Applications.Placement_Status = Placed / unique eligible students × 100 |
| Company selection rate | Selected applications / applications to that company × 100; application-level, not unique students |
| Drive participation | Attending_Students / Registered_Students × 100 for each drive |
| Drive selection rate | Selected_Students / Attending_Students × 100 for each drive |
| Offer salary average / highest | Mean / maximum valid Offered_Salary_LPA; recorded-offer basis, not accepted or joined compensation |
| Unplaced follow-up | Eligible students without a Placed application record; treat as no recorded placement, not proof of unemployment |

Zero denominators produce an unavailable value, not zero percent. Department and company comparisons use matching populations. Offers, selections and joining are different events; report disagreements separately. No fabricated imputation of eligibility, outcomes, IDs, or salaries. Missing fields remain missing; whitespace is trimmed; exact duplicate rows are removed with an audit count. Conflicting duplicate IDs block publication.

## Preparation and validation

1. Preserve all raw CSVs from the workbook and keep source sheet names.
2. Validate schema and identifiers; standardize surrounding whitespace.
3. Record missing cells and exact duplicates; exclude invalid numeric values from calculations with a warning.
4. Validate reference keys before any join; block publication on orphan references or conflicting IDs.
5. Reconcile student placement, offers and joining without silently changing statuses.
6. Calculate metrics at their declared grain; export source-linked CSV summaries and checks.
7. Review reports and dashboard, including data limitations, before release.

## Milestones

| Period | Work | Friday checkpoint |
| --- | --- | --- |
| Oct 26–Nov 1 | Requirements, KPIs, source mapping, analysis plan | Oct 30 has passed; initial documentation prepared retrospectively without backdated commits |
| Nov 2–8 | Cleaning, integration, data-quality documentation | Nov 6: progress through Friday; weekend tasks remain scheduled |
| Nov 9–15 | EDA, application statuses, departmental outcomes | Nov 13 |
| Nov 16–22 | Company and drive analysis | Nov 20 |
| Nov 23–29 | KPI and performance report | Nov 27 |
| Nov 30–Dec 6 | Dashboard and visualizations | Dec 4 |
| Dec 7–13 | Validation, limitations, recommendations | Dec 11 |
| Dec 14–15 | Final documentation and handover | Dec 15 final submission |

Friday reports describe completed work and outstanding weekend tasks. Thursday preparation targets 6 PM and Friday publishing targets 8 AM America/Chicago, before the requested 10 AM deadline. Timing is subject to scheduler availability. Future phase reports must not claim manual validation or completed research that did not occur.
