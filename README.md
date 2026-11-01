# Tech-College Placement Analytics

Data Scientist: Durgesh Tiwari. Project: October 26–December 15, 2026.

The supplied workbook contains **synthetic demonstration records**, not real college outcomes. CSVs in `data/raw` preserve its sheet values; the original workbook remains the source. Salary units are INR lakhs per annum (LPA).

## Run

Python 3.11 or newer; no third-party packages required:

```sh
python -m unittest discover -s tests
python src/pipeline.py --as-of 2026-11-06
```

Outputs: cleaned CSVs, validation findings, a Markdown report, metrics JSON, and a standalone HTML dashboard in `outputs/`. Reports are cumulative snapshots, not evidence of work on future dates. The initial dataset is static; trends require updated source files.

## Weekly delivery

GitHub Actions prepares a candidate Thursday at approximately 6 PM Central and publishes it Friday at approximately 8 AM Central. Both schedules use UTC after the November 1 daylight saving change. Each Friday run regenerates and validates the candidate before committing it. The final run is December 15 at approximately 8 AM Central. Runs outside November 5–December 15, 2026 exit without publishing. Scheduled jobs can be delayed by GitHub.

Generated deliverables are committed under `deliverables/YYYY-MM-DD/`; Thursday artifacts are available on the Actions run. Workflow permissions must allow `contents: write`. Manual dispatch is also available, restricted to the project window.

See `docs/phase1.md` for requirements, definitions, limitations, and the phase plan. Reports currently use a standard Markdown format; a separate Word template has not been supplied. The dashboard covers analytics only; this repository does not implement the student/recruiter portal.
