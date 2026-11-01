# Methodology and reproducibility

The primary command is `PYTHONPATH=src python3 -m placement supplied`. It reads the original seven workbook exports in data/raw and detects their synthetic provenance. The separate normalized run command supports a future export contract; its data and definitions differ.

1. Preserve original CSV bytes and calculate SHA-256 for each source, including Read_Me.
2. Check required headers, keys, numeric ranges, statuses, dates and references. Remove audited exact duplicates; reject conflicting primary keys.
3. Retain original columns and independent status fields. Earlier application statuses with selected outcomes are warnings, not guessed corrections.
4. Validate selected ≤ shortlisted ≤ attending ≤ registered for drives, and placed ≤ eligible / mean salary ≤ highest for historical summaries.
5. Calculate placement from unique IDs with explicit eligibility and recorded placement. Keep selected, offered and joined counts separate. Salary remains annual INR LPA at recorded-offer grain.
6. Produce department, skill and CGPA EDA, company selection, aggregate drive metrics, compensation coverage, historical summaries and a follow-up queue. Perform no unsupported offer/job or application/drive joins.
7. Reconcile counts against source populations. Export Markdown, JSON, spreadsheet-safe CSV and SQLite. Render a self-contained dashboard that makes no external requests.
8. Run regression tests, coverage, dependency audit and desktop/mobile interaction checks. Document action owners and limitations. No coordinator approval is implied.

Missing values remain unknown. Skills overlap and are self-reported. A small synthetic sample does not support causal conclusions or a predictive model. No recorded placement does not establish unemployment. All example events are included, including future dates. Historical summaries describe separate populations.

Git records actual execution time. Branch names, commit messages and daily evidence name the assigned dates without backdating. The original pipeline, Word template and scheduled reporting workflow are preserved. No future scheduled run or institutional submission is claimed to have occurred.
