# Placement analysis — 2026-11-06

**Synthetic demonstration data; not actual college results.**

Project week: 2. Cumulative automated snapshot.

Date labels describe report generation, not a historical cutoff. All supplied synthetic records are included, including future-dated demonstrations.

Eligible students: 11; recorded placed: 7; placement: 63.64%.
Recorded offers: 7; mean offer salary: 5.0 LPA; highest: 6.0 LPA.

## Validation findings

- APP001: selected result with earlier-stage application status; statuses retained
- APP002: selected result with earlier-stage application status; statuses retained
- APP004: selected result with earlier-stage application status; statuses retained
- APP006: selected result with earlier-stage application status; statuses retained
- APP010: selected result with earlier-stage application status; statuses retained
- APP011: selected result with earlier-stage application status; statuses retained
- APP013: selected result with earlier-stage application status; statuses retained
- APP015: selected result with earlier-stage application status; statuses retained
- Applications: synthetic Application_Date=2026-11-09 is later than generation date; included as demonstration input
- Applications: synthetic Application_Date=2026-11-10 is later than generation date; included as demonstration input
- Applications: synthetic Application_Date=2026-11-11 is later than generation date; included as demonstration input
- Applications: synthetic Application_Date=2026-11-12 is later than generation date; included as demonstration input
- Applications: synthetic Application_Date=2026-11-13 is later than generation date; included as demonstration input
- Applications: synthetic Application_Date=2026-11-16 is later than generation date; included as demonstration input
- Placement_Drives: synthetic Drive_Date=2026-11-12 is later than generation date; included as demonstration input
- Placement_Drives: synthetic Drive_Date=2026-11-18 is later than generation date; included as demonstration input
- Placement_Drives: synthetic Drive_Date=2026-11-24 is later than generation date; included as demonstration input

## Interpretation and next steps

- Review reconciliation warnings before interpreting outcomes.
- Use the eligible unplaced list for follow-up; confirm each student’s actual status.
- Keep offer, selection and joining counts separate.
- Small synthetic samples cannot establish causal placement factors or real trends.
- Student-level drive data and reliable offer/job identifiers are needed for deeper joins.
- Friday snapshots exclude later weekend work. See docs/phase1.md for scheduled activities.
- Automated checks ran; no manual review is implied. The accompanying Word status report uses the supplied template.
