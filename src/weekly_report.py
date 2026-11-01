"""Generate an honest status report using the user's original Word template."""
import base64
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from docx import Document
from docx.shared import Pt


def generate(output, as_of, metrics, warnings):
    root = Path(__file__).resolve().parents[1]
    doc = Document(BytesIO(base64.b64decode((root/'templates/weekly-status.docx.b64').read_text())))
    week = min(8, max(1, (as_of-date(2026,10,26)).days//7+1))
    start = date(2026,10,26)+timedelta(weeks=week-1)
    end = min(start+timedelta(days=6), date(2026,12,15))
    phases = ['Project Understanding and Data Requirements', 'Data Collection, Cleaning, and Preparation', 'Exploratory Data Analysis', 'Recruiter and Placement Drive Analytics', 'Placement KPIs and Performance Reporting', 'Dashboard and Data Visualization', 'Validation and Analytical Insights', 'Final Documentation and Project Submission']
    replacements = {
        0: 'Weekly Status Report',
        5: f'This report records available work for Phase {week}: {phases[week-1]}. Generated on {as_of:%d %B %Y}; later activities in the reporting period remain pending.',
        6: 'Reviewed the supplied portal workflow and synthetic workbook. Student, recruiter and admin modules inform the analytics scope. All source records are demonstration examples, not actual college outcomes.',
        7: 'Documented source grain, identifiers, joins, analytical questions, KPI definitions and limitations in docs/phase1.md. Raw source exports remain unchanged.',
        8: f'The pipeline processes {metrics["student_count"]} synthetic students, including {metrics["eligible_students"]} marked eligible. It generates validation findings, KPI summaries, supporting CSV/JSON files and an HTML dashboard.',
        9: 'Three initial automated tests passed. The report distinguishes generated outputs from review and approval; coordinator review is pending.',
        12: 'Data requirements and source mapping', 13: 'KPI definitions and analysis plan', 14: 'Raw synthetic dataset exports',
        15: 'Reproducible preparation and analytics pipeline', 16: 'Automated validation findings', 17: 'Department and company summaries',
        18: 'Drive and salary summaries', 19: 'Dashboard and supporting files', 20: 'Initial automated tests',
        23: f'{len(warnings)} automated warnings; detailed findings are in validation.json.',
        24: 'Some selected records retain an earlier application-stage status. Future-dated synthetic records are included; report generation date is not a historical cutoff.',
        25: 'Phase-specific implementation and final review remain pending. Automated reporting alone does not confirm completion of all assigned activities.',
        30: f'Phase {min(week+1,8)} - {phases[min(week,7)]}', 31: 'Activities to be initiated or reviewed:',
        32: 'Review the next phase tasks against docs/phase1.md.', 33: 'Check source consistency and unresolved discrepancies.',
        34: 'Complete phase-specific analysis and review findings.', 35: 'Validate reports and visualizations against source data.',
        36: 'Prepare the next Friday checkpoint before 10 AM Central.',
        38: 'Submitted By:\nDurgesh Tiwari\nData Scientist\nTechmentee INC,',
        39: 'For Review By:\nVaishali Pujari\nProject Coordinator\nTechmentee INC,\nReview status: Pending'
    }
    for i, text in replacements.items():
        p = doc.paragraphs[i]
        p.clear()
        p.add_run(text)
    doc.tables[0].cell(0,0).text = ('Project: Tech-College Placement Management Portal\nEmployee Name: Durgesh Tiwari\nDesignation: Data Scientist\nCompany: Techmentee INC,\nProject Coordinator: Vaishali Pujari\n'
        f'Reporting Period: {start:%d-%m-%Y} to {end:%d-%m-%Y}\nGenerated On: {as_of:%d-%m-%Y}\nProject Phase: Phase {week} - {phases[week-1]}\nReporting Week: Week {week}\nOverall Status: In progress; final review pending')
    tasks = [
        ('Review workflow and portal modules', 'Completed', '100%', 'Reviewed supplied student, recruiter and admin workflows; documented analytics scope.'),
        ('Define data requirements and KPIs', 'Completed', '100%', 'Defined sources, joins, metric formulas, denominators and limitations.'),
        ('Map sources and prepare analysis plan', 'Completed', '100%', 'Mapped seven analytical source sheets; exported raw CSVs and documented the analysis plan.'),
        ('Review and finalize analysis plan', 'Pending', 'Not assessed', 'November 1 review remains pending. No coordinator approval is recorded.')
    ] if week == 1 else [
        ('Prepare data and run validation', 'Generated', 'Not assessed', 'Exported cleaned data and validation findings.'),
        ('Calculate recruitment and placement metrics', 'Generated', 'Not assessed', 'Generated department, company, drive and salary summaries.'),
        ('Generate reports and dashboard', 'Generated', 'Not assessed', 'Produced supporting files, dashboard and template-based report.'),
        ('Review phase-specific completion', 'Pending', 'Not assessed', f'Review Phase {week}: {phases[week-1]}. Generated outputs do not establish completion of every assigned activity.')
    ]
    for row, values in zip(doc.tables[1].rows[1:], tasks):
        for cell, value in zip(row.cells, values):
            cell.text = value
    values = ['Pending final review', 'Checkpoint generated; review pending', 'Automated checks only', 'Requirements and outputs available', 'Subject to review']
    for row, value in zip(doc.tables[2].rows[1:], values):
        row.cells[1].text = value
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next = False
                    for run in p.runs:
                        run.font.size = Pt(10)
    for row in doc.tables[2].rows[:-1]:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    doc.paragraphs[27].paragraph_format.page_break_before = True
    doc.save(output/'Weekly_Status_Report.docx')
