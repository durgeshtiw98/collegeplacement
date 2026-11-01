# Verification evidence

The implementation was verified against the supplied synthetic workbook and additional deterministic fixtures. Actual timestamps are recorded in generated metadata and Git; the assigned eight-week schedule is not a history of work performed on those future dates.

| Check | Observed result |
| --- | --- |
| Python regression suite | 34 tests passed, including the original 3 tests |
| New analytics package coverage | 99% combined statement/branch coverage; required minimum 80% |
| Supplied-workbook reconciliation | 9 checks passed |
| Optional normalized-mode reconciliation | 16 checks passed |
| Dependency audit | No known vulnerabilities found for requirements.txt and resolved dependencies |
| Supplied dashboard desktop browser | 15/15 interaction checks passed at 1440 × 1100 |
| Supplied dashboard mobile browser | Initial 14 interaction checks passed; strict mobile viewport verification was stopped at user request |
| JavaScript syntax | Source dashboard script passed node --check |
| Existing Word reporting | Legacy pipeline generated its dashboard, CSV, JSON, Markdown and Weekly_Status_Report.docx successfully |
| Raw-source preservation | Tracked original source exports were not edited |

Regression tests cover distinct student/offer grains, duplicate keys and business pairs, orphan links, conflicting source statuses, malformed CSVs, dates, invalid numeric ranges, missing salaries and academics, zero denominators, independent reconciliations, empty sources, SQLite integrity, spreadsheet formula escaping, safe JSON embedding and full output generation.

Browser checks exercise navigation, source/Python parity, filters, resets, queue search, filtered CSV downloads, quality views and viewport overflow. The Playwright connector lacked its Chrome extension; the committed dependency-free smoke harness ran local headless Chrome instead. The desktop screenshot is in docs/screenshots. The initial mobile image was omitted from the submission because it was captured without an enforced viewport; a stricter check exposed a smoke-harness result element expanding the viewport. That element was hidden; the corrected mobile test was not rerun at the user’s request.

Reproduce verification using the README commands. Coverage measures the new placement package; the legacy pipeline retains its original regression tests and was also run end to end. Automated verification does not establish source truth, coordinator approval, complete institutional data or causal explanations.
