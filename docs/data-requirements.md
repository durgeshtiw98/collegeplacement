# Data requirements and analysis plan

Owner: Durgesh Tiwari · Data Scientist · Assigned: 26 October–15 December 2026.

The initially empty local workspace was populated from the existing GitHub main branch. Its data/raw/Read_Me.csv identifies all provided records as synthetic examples. The original CSV bytes are preserved. Findings are demonstrations, not real college outcomes.

## Workflow and analytical questions

Student profile and academics → company/recruiter verification → job posting → application → interview → selection → offer → placement and joining. Drive participation is a separate aggregate source. This deliverable covers the data scientist assignment; operational student/recruiter login and application-submission features belong to the source portal.

Questions: How does placement vary by department? How do skills and CGPA relate to outcomes? How do application, interview, selection, placement and joining statuses differ? Which companies select applicants? How do drive participation and selection compare? Which eligible students need follow-up? What salaries and historical comparisons are available?

## Available sources

| CSV | Grain / key | Fields and source links |
| --- | --- | --- |
| Student_Data | student / Student_ID | department, grades, CGPA, skills, graduation year, explicit eligibility |
| Company_Data | company / Company_ID | name, industry, recruiter verification |
| Job_Postings | job / Job_ID | Company_ID, role, location, required skills, salary LPA, verification |
| Applications | application / Application_ID | Student_ID, Job_ID, date, separate application/interview/selection/placement statuses |
| Placement_Drives | drive / Drive_ID | Company_ID, date, eligible department description, aggregate registration/attendance/shortlist/selection |
| Offers | recorded offer / no stable offer ID | Student_ID, Company_ID, role, offered LPA, letter status, joining status |
| Historical_Placements | year and department | eligible/placed counts, companies/drives, average/highest LPA |

Exact headers are validated in src/placement/source_intake.py. Source owners are the student registry, placement cell, job/application modules and offer register. Read_Me supplies provenance and units. CSV is UTF-8; identifiers remain strings; dates are ISO YYYY-MM-DD; salaries are annual INR lakhs per annum (LPA).

## KPI contract

| Metric | Definition |
| --- | --- |
| Eligible placement % | unique explicitly eligible students with an application marked Placed / unique explicitly eligible students × 100 |
| All-student placement % | unique students with an application marked Placed / supplied students × 100 |
| Company selection % | selected application records / application records joined by Job_ID to Company_ID × 100 |
| Drive participation % | Attending_Students / Registered_Students × 100 |
| Drive attendee selection % | Selected_Students / Attending_Students × 100 |
| Drive registration selection % | Selected_Students / Registered_Students × 100 |
| Average / highest salary | mean / maximum known positive Offered_Salary_LPA at recorded-offer grain |
| Salary coverage | known positive recorded offer salaries / recorded offers × 100 |
| Joined students | unique students with Joining_Status = Joined |
| Follow-up | students with no recorded Placed application, with eligible and review-required statuses distinguished |

Multiple applications never inflate unique placed-student counts. Zero denominators are N/A. Review Required means unknown eligibility; no backlog or academic eligibility rule is invented. Selection, placement, offers and joining remain separate.

## Unavailable fields and limitations

No stable offer IDs, offer-to-application/job keys, student-level drive attendance, application-drive key, recruiter IDs/activity timestamps or event history are supplied. Do not match offers by role text, allocate aggregate drive counts to departments or invent registrations. Historical populations differ from the current student example and remain separate. Future synthetic events are included; generation date is not an as-of cutoff.

Request those stable keys and event logs for future portal integration. docs/normalized-contract.md and data/templates/ describe an optional richer schema. Its academic proxy and accepted/joined placement definitions apply only to that separate mode.

## Preparation, analysis and acceptance

Validate required headers, primary/foreign keys, numbers, dates, statuses and nested aggregate counts. Trim whitespace; audit exact duplicates; reject conflicting keys. Preserve missing academic/salary values without imputation. Hash all inputs. Retain conflicting source progression fields with warnings. Analyze EDA, company/drive outcomes, KPIs, compensation, historical summaries and follow-up. Reconcile outputs and test dashboard interactions. Real institutional review and coordinator approval remain separate from automated checks.
