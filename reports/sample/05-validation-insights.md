# Validation and actionable insights

**SYNTHETIC DEMO — NOT INSTITUTIONAL FINDINGS** · Actual generation: 2026-11-01T04:52:54+00:00

| check | result |
| --- | --- |
| Unique placed students reconcile to accepted/joined source offers | PASS |
| Eligible denominator reconciles to academic source | PASS |
| Eligible placement percentage reconciles independently | PASS |
| Student total reconciles across departments | PASS |
| Placed and unplaced partition student population | PASS |
| Department placed counts reconcile | PASS |
| Follow-up queue matches unplaced population | PASS |
| Follow-up excludes placed students | PASS |
| Application statuses partition all application records | PASS |
| Drive application counts reconcile | PASS |
| Company application counts reconcile | PASS |
| Registration counts reconcile across drives | PASS |
| Known salary offer count reconciles | PASS |
| Highest annual salary reconciles | PASS |
| Average annual salary reconciles | PASS |
| No source rows lost without duplicate audit | PASS |

## Recommendations

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
