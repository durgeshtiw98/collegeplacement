# Data preparation

**SUPPLIED SYNTHETIC WORKBOOK — NOT REAL COLLEGE OUTCOMES**

Owner: Durgesh Tiwari · Assigned: 26 October–15 December 2026.

Actual generation: 2026-11-06T06:42:44+00:00. All supplied example rows are included; this is not a historical cutoff.

| source | source_rows | clean_rows | exact_duplicates_removed |
| --- | --- | --- | --- |
| Student_Data | 12 | 12 | 0 |
| Company_Data | 5 | 5 | 0 |
| Job_Postings | 6 | 6 | 0 |
| Applications | 15 | 15 | 0 |
| Placement_Drives | 4 | 4 | 0 |
| Offers | 7 | 7 | 0 |
| Historical_Placements | 6 | 6 | 0 |

Trimmed surrounding whitespace; validated numeric ranges, dates, primary keys and source links. Exact duplicates are audited. Conflicting keys and invalid references stop publication. Source fields and separate outcome statuses are preserved. No imputation or unsupported event joins are performed. Clean CSV and SQLite retain the original source schemas. Full missing counts and SHA-256 hashes are in quality.json.

## Findings and limitations

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
