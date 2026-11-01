# Proposed normalized export contract

Owner: Durgesh Tiwari · Data Scientist  
Assigned duration: 26 October–15 December 2026

## Evidence and scope

The original workbook exports are analyzed by the supplied-workbook command. This separate contract supports richer future portal exports; it does not describe the supplied workbook schema. `data/sample/` contains deterministic, fictional records generated with seed 2026. All committed findings and visualizations are **SYNTHETIC DEMO**, not college performance claims. Replace with authorized CSV exports to produce real findings. Real exports and generated output are ignored by Git.

The scope is the data scientist assignment: intake contracts, cleaning, integration, descriptive analytics, KPIs, reports, dashboard, validation and recommendations. Student login, recruiter accounts, application submission and placement-cell operational workflows are source systems, not features of this analytics deliverable.

## Portal workflow and analytical questions

Student profile → academic record → company/recruiter → drive → registration → application → placement outcome.

Questions: Which departments have the lowest observed placement percentages? How do skills and CGPA bands relate to outcomes? Where does the recorded recruitment funnel lose participation? Which companies and drives select candidates? How complete is compensation reporting? Which eligible students have no recorded accepted/joined placement?

## Sources, grain and keys

| CSV export | Grain / primary key | Source owner | Links |
| --- | --- | --- | --- |
| students | student / student_id | student registry | department, cohort, pipe-separated skills |
| academics | current academic summary / student_id | examination cell | student_id |
| companies | company / company_id | placement cell | industry |
| recruiters | recruiter / recruiter_id | placement cell | company_id |
| drives | drive / drive_id | placement cell | company_id, recruiter_id |
| registrations | student-drive registration / registration_id | event module | student_id, drive_id |
| applications | student-drive application / application_id | application module | student_id, drive_id |
| placements | latest offer outcome / placement_id | verified offer register | application_id |

`data/templates/` gives the exact required headers. Files are UTF-8 CSV (BOM accepted); dates use YYYY-MM-DD; CGPA is on a 0–10 scale; backlogs are nonnegative integers. Salary is positive annual CTC in INR, not take-home pay. Missing compensation is blank. Boolean fields accept true/false, yes/no, 1/0. Identifiers remain strings, preserving leading zeroes. Header aliases and currency conversion require an explicit upstream mapping; neither is guessed.

## KPI contract

An academic analytical cohort proxy is CGPA ≥ 6.0 with zero backlogs. Missing academics means unknown eligibility and is reported separately. This proxy is not a company eligibility policy. A student is recorded placed only with an accepted or joined offer. Offer count and unique placed students differ; multiple offers never inflate student placement counts.

Primary placement percentage = eligible students with an accepted/joined placement / eligible students × 100. Also report all-student observed placement percentage separately. Company selection rate = selected application records / application records (including withdrawn records, explicitly). A selected application has status selected or a placement record; revoked/declined offers remain historical selection evidence. Registration participation = registrations marked attended / all registrations. Drive selection rate = selected applications / applications; registered-student selection is a separate metric. Shortlisting and interview attendance require explicit fields; rejected candidates are not automatically assumed never shortlisted.

Salaries summarize accepted/joined offers with known positive annual INR CTC, at offer grain. Coverage = known-salary accepted/joined offers / accepted/joined offers. Highest and average are null when absent, never zero. Compensation trends and causal placement predictions require further evidence. No protected demographic comparisons or model-derived individual risk scores are inferred.

## Preparation and validation

Trim text; uppercase department codes; lowercase normalized statuses; normalize skills without inferring missing values; validate dates, ranges, enums, keys and links. Remove exact normalized duplicates with an audit entry. Reject conflicting duplicate keys and duplicate student-drive applications/registrations rather than arbitrarily picking a winner. Missing required files/headers, invalid numbers, orphans and contradictory company links stop publication. Do not impute salaries or CGPA. Publish normalized CSV, SQLite tables, a source SHA-256 manifest and field-level quality counts.

Analyze only supplied records; no absent calendar periods or students are inferred. No longitudinal or causal claims follow from a cross-sectional snapshot. Sources must contain current outcomes, one academic summary per student and one current placement outcome per application. Updates must be resolved upstream before ingestion.
