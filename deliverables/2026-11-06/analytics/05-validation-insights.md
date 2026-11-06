# Validation and recommendations

**SUPPLIED SYNTHETIC WORKBOOK — NOT REAL COLLEGE OUTCOMES**

Owner: Durgesh Tiwari · Assigned: 26 October–15 December 2026.

Actual generation: 2026-11-06T20:23:13+00:00. All supplied example rows are included; this is not a historical cutoff.

| check | passed |
| --- | --- |
| Department student counts reconcile | True |
| Department eligible counts reconcile | True |
| Eligible placement percentage matches source | True |
| Unique placed students reconcile | True |
| Company application counts reconcile | True |
| Company selected applications reconcile | True |
| Follow-up partitions current student cohort | True |
| Recorded offers remain separate from joins | True |
| Clean row counts match audited sources | True |

## Actionable recommendations

| owner | evidence | action | measure |
| --- | --- | --- | --- |
| Placement cell | 4 eligible students have no recorded placement | Use the follow-up queue to review participation and interview feedback | Eligible unplaced count and subsequently verified outcomes |
| Data engineering / placement cell | No application-drive key or offer/application identifier | Capture stable offer IDs, application IDs and student-drive attendance in the portal | Link completeness and unreconciled outcome count |
| Department coordinators | 1 students require eligibility review | Verify eligibility status without inferring backlogs from CGPA | Unknown eligibility count |

## Source inconsistencies and analytical limitations

- Applications:11: future demonstration event 2026-11-09; no as-of cutoff applied
- Applications:12: future demonstration event 2026-11-10; no as-of cutoff applied
- Applications:13: future demonstration event 2026-11-11; no as-of cutoff applied
- Applications:14: future demonstration event 2026-11-12; no as-of cutoff applied
- Applications:15: future demonstration event 2026-11-13; no as-of cutoff applied
- Applications:16: future demonstration event 2026-11-16; no as-of cutoff applied
- Placement_Drives:3: future demonstration event 2026-11-12; no as-of cutoff applied
- Placement_Drives:4: future demonstration event 2026-11-18; no as-of cutoff applied
- Placement_Drives:5: future demonstration event 2026-11-24; no as-of cutoff applied
- APP001: selected result retains earlier application status; source fields preserved
- APP002: selected result retains earlier application status; source fields preserved
- APP004: selected result retains earlier application status; source fields preserved
- APP006: selected result retains earlier application status; source fields preserved
- APP010: selected result retains earlier application status; source fields preserved
- APP011: selected result retains earlier application status; source fields preserved
- APP013: selected result retains earlier application status; source fields preserved
- APP015: selected result retains earlier application status; source fields preserved
- No reliable offer-to-application/Job_ID or application-to-drive key: these joins are not performed.
- Drive data is aggregated; student-level attendance and department filters cannot be inferred.
- Historical summaries use different populations and are not reconciled to the current 12-student example.
- Recruiter verification is available; individual recruiter activity and timestamps are unavailable.
