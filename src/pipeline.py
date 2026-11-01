"""Reproducible, standard-library analytics for the supplied demonstration workbook."""
import argparse
import csv
import html
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEYS = {'Student_Data': 'Student_ID', 'Company_Data': 'Company_ID',
        'Job_Postings': 'Job_ID', 'Applications': 'Application_ID',
        'Placement_Drives': 'Drive_ID'}


def percent(n, d):
    return round(100 * n / d, 2) if d else None


def number(value, low=0, high=float('inf')):
    try:
        n = float(value)
        return n if low <= n <= high else None
    except (ValueError, TypeError):
        return None


def load_data(source):
    data, issues, errors = {}, [], []
    for path in sorted(source.glob('*.csv')):
        if path.stem == 'Read_Me':
            continue
        with path.open(newline='', encoding='utf-8') as f:
            rows = [{k: (v or '').strip() for k, v in row.items()} for row in csv.DictReader(f)]
        clean, seen = [], set()
        for row in rows:
            key = tuple(row.items())
            if key in seen:
                issues.append(f'{path.stem}: removed exact duplicate row')
                continue
            seen.add(key)
            clean.append(row)
        data[path.stem] = clean
        missing = sum(v == '' for row in clean for v in row.values())
        if missing:
            issues.append(f'{path.stem}: {missing} missing cells retained')
        if path.stem in KEYS:
            col = KEYS[path.stem]
            ids = [r[col] for r in clean]
            if '' in ids or len(ids) != len(set(ids)):
                errors.append(f'{path.stem}: missing or conflicting duplicate {col}')
    for name in [*KEYS, 'Offers', 'Historical_Placements']:
        if not data.get(name):
            errors.append(f'{name}: missing or empty source')
    return data, issues, errors


def analyze(data, issues, errors):
    students = {r['Student_ID']: r for r in data['Student_Data']}
    companies = {r['Company_ID']: r for r in data['Company_Data']}
    jobs = {r['Job_ID']: r for r in data['Job_Postings']}
    apps, offers = data['Applications'], data['Offers']
    for name, col, parent in [('Job_Postings', 'Company_ID', companies),
                              ('Applications', 'Student_ID', students),
                              ('Applications', 'Job_ID', jobs),
                              ('Offers', 'Student_ID', students),
                              ('Offers', 'Company_ID', companies),
                              ('Placement_Drives', 'Company_ID', companies)]:
        for r in data[name]:
            if r[col] not in parent:
                errors.append(f'{name}: unresolved {col}={r[col]}')
    for r in students.values():
        for col, high in [('CGPA', 10), ('Class_10_Percentage', 100), ('Class_12_Percentage', 100)]:
            if number(r[col], high=high) is None:
                issues.append(f"Student {r['Student_ID']}: missing/invalid {col}")
    eligible = {sid for sid, r in students.items() if r['Eligibility_Status'].casefold() == 'eligible'}
    placed = {r['Student_ID'] for r in apps if r['Placement_Status'].casefold() == 'placed'}
    selected = {r['Student_ID'] for r in apps if r['Selection_Result'].casefold() == 'selected'}
    offered = {r['Student_ID'] for r in offers}
    for sid in sorted(placed - eligible):
        issues.append(f'{sid}: recorded placed but not marked eligible; excluded from eligible placement numerator')
    for sid in sorted(offered ^ placed):
        issues.append(f'{sid}: offer records and application placement records disagree')
    for sid in sorted(placed - selected):
        issues.append(f'{sid}: placed without a selected application')
    for r in apps:
        if r['Selection_Result'].casefold() == 'selected' and r['Application_Status'].casefold() in {'applied', 'shortlisted'}:
            issues.append(f"{r['Application_ID']}: selected result with earlier-stage application status; statuses retained")
    department = []
    for dept in sorted({r['Department'] for r in students.values()}):
        ids = {sid for sid in eligible if students[sid]['Department'] == dept}
        department.append({'Department': dept, 'Eligible': len(ids), 'Placed': len(ids & placed),
                           'Placement_Percentage': percent(len(ids & placed), len(ids))})
    company = []
    for cid, r in companies.items():
        subset = [a for a in apps if a['Job_ID'] in jobs and jobs[a['Job_ID']]['Company_ID'] == cid]
        count = sum(a['Selection_Result'].casefold() == 'selected' for a in subset)
        company.append({'Company': r['Company_Name'], 'Applications': len(subset),
                        'Selected_Applications': count, 'Selection_Percentage': percent(count, len(subset))})
    drives = []
    for r in data['Placement_Drives']:
        cols = ['Registered_Students', 'Attending_Students', 'Shortlisted_Students', 'Selected_Students']
        values = [number(r[c]) for c in cols]
        valid = all(v is not None and v.is_integer() for v in values)
        if not valid or any(a < b for a, b in zip(values, values[1:])):
            issues.append(f"Drive {r['Drive_ID']}: invalid or inconsistent counts; rates unavailable")
            participation = selection = None
        else:
            participation, selection = percent(values[1], values[0]), percent(values[3], values[1])
        drives.append(dict(r, Participation_Percentage=participation, Selection_Percentage=selection))
    salaries = []
    for r in offers:
        value = number(r['Offered_Salary_LPA'])
        if value is None:
            issues.append(f"Offer for {r['Student_ID']}: invalid salary excluded")
        else:
            salaries.append(value)
    for r in data['Historical_Placements']:
        eligible_n, placed_n = number(r['Eligible_Students']), number(r['Placed_Students'])
        if eligible_n is None or placed_n is None or placed_n > eligible_n:
            issues.append(f"Historical {r['Academic_Year']} {r['Department']}: invalid placement counts")
        avg, maximum = number(r['Average_Package_LPA']), number(r['Highest_Package_LPA'])
        if avg is None or maximum is None or avg > maximum:
            issues.append(f"Historical {r['Academic_Year']} {r['Department']}: invalid salary summary")
    return {'synthetic_data': True, 'student_count': len(students), 'eligible_students': len(eligible),
            'placed_eligible_students': len(eligible & placed),
            'placement_percentage': percent(len(eligible & placed), len(eligible)),
            'offer_count': len(offers), 'valid_salary_count': len(salaries),
            'average_offer_salary_lpa': round(sum(salaries)/len(salaries), 2) if salaries else None,
            'highest_offer_salary_lpa': max(salaries) if salaries else None,
            'departments': department, 'companies': company, 'drives': drives,
            'application_statuses': dict(Counter(a['Application_Status'] for a in apps)),
            'unplaced_eligible_students': [students[sid] for sid in sorted(eligible - placed)]}


def write_csv(path, rows):
    if rows:
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def run(source, output, as_of):
    output.mkdir(parents=True, exist_ok=True)
    data, issues, errors = load_data(source)
    metrics = analyze(data, issues, errors) if not errors else {}
    for name, col in [('Applications', 'Application_Date'), ('Placement_Drives', 'Drive_Date')]:
        for row in data.get(name, []):
            try:
                event_date = date.fromisoformat(row[col][:10])
                if event_date > as_of:
                    issues.append(f'{name}: synthetic {col}={event_date} is later than generation date; included as demonstration input')
            except ValueError:
                issues.append(f'{name}: invalid {col} retained')
    (output/'validation.json').write_text(json.dumps({'warnings': issues, 'errors': errors}, indent=2))
    if errors:
        raise ValueError('Publication blocked: ' + '; '.join(errors))
    cleaned = output/'cleaned'
    cleaned.mkdir(exist_ok=True)
    for name, rows in data.items():
        write_csv(cleaned/f'{name}.csv', rows)
    metrics['as_of'] = as_of.isoformat()
    (output/'metrics.json').write_text(json.dumps(metrics, indent=2))
    for key in ['departments', 'companies', 'drives', 'unplaced_eligible_students']:
        write_csv(output/f'{key}.csv', metrics[key])
    stage = min(8, max(1, (as_of-date(2026, 10, 26)).days//7+1))
    report = [f'# Placement analysis — {as_of}', '', '**Synthetic demonstration data; not actual college results.**',
              '', f'Project week: {stage}. Cumulative automated snapshot.', '',
              'Date labels describe report generation, not a historical cutoff. All supplied synthetic records are included, including future-dated demonstrations.', '',
              f"Eligible students: {metrics['eligible_students']}; recorded placed: {metrics['placed_eligible_students']}; placement: {metrics['placement_percentage']}%.",
              f"Recorded offers: {metrics['offer_count']}; mean offer salary: {metrics['average_offer_salary_lpa']} LPA; highest: {metrics['highest_offer_salary_lpa']} LPA.",
              '', '## Validation findings', '', *(['- '+s for s in issues] or ['No automated warnings.']),
              '', '## Interpretation and next steps', '',
              '- Review reconciliation warnings before interpreting outcomes.',
              '- Use the eligible unplaced list for follow-up; confirm each student’s actual status.',
              '- Keep offer, selection and joining counts separate.',
              '- Small synthetic samples cannot establish causal placement factors or real trends.',
              '- Student-level drive data and reliable offer/job identifiers are needed for deeper joins.',
              '- Friday snapshots exclude later weekend work. See docs/phase1.md for scheduled activities.',
              '- Automated checks ran; no manual review is implied. Standard report format pending a supplied template.']
    (output/'report.md').write_text('\n'.join(report)+'\n')
    sections = []
    for label, key in [('Department placement', 'departments'), ('Company selection', 'companies'), ('Drive participation', 'drives')]:
        rows = metrics[key]
        header = ''.join('<th>'+html.escape(k)+'</th>' for k in rows[0]) if rows else ''
        body = ''.join('<tr>'+''.join('<td>'+html.escape(str(v) if v is not None else 'N/A')+'</td>' for v in r.values())+'</tr>' for r in rows)
        sections.append(f'<h2>{label}</h2><div class="scroll"><table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table></div>')
    page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Placement analytics</title><style>body{font:16px system-ui;margin:32px;max-width:1200px;background:#f5f7fb;color:#17243a}table{border-collapse:collapse;background:white;width:100%}td,th{padding:12px;border-bottom:1px solid #ddd;text-align:left}th{background:#17365b;color:white}.scroll{overflow:auto}pre{white-space:pre-wrap}h1{color:#17365b}</style>'
    page += f'<h1>Placement analytics</h1><p>As of {as_of} · Synthetic demonstration data</p>'
    page += '<p>Date is generation date; all synthetic input records are included.</p>'
    for r in metrics['departments']:
        value = r['Placement_Percentage']
        page += '<p>'+html.escape(r['Department'])+f': {value if value is not None else "N/A"}% <meter min="0" max="100" value="{value or 0}"></meter></p>'
    page += ''.join(sections)
    page += '<h2>Report and limitations</h2><pre>'+html.escape('\n'.join(report))+'</pre></html>'
    (output/'dashboard.html').write_text(page)
    return metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--as-of', type=date.fromisoformat, required=True)
    parser.add_argument('--source', type=Path, default=ROOT/'data/raw')
    parser.add_argument('--output', type=Path, default=ROOT/'outputs')
    args = parser.parse_args()
    run(args.source, args.output, args.as_of)
