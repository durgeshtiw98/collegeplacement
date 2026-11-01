"""Package the dashboard and report downloads for GitHub Pages."""

import html
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports/supplied"
DESTINATION = ROOT / "_site"


def main():
    dashboard = SOURCE / "dashboard.html"
    if not dashboard.is_file():
        raise SystemExit("Generate the reports first: PYTHONPATH=src python -m placement supplied")
    DESTINATION.mkdir(parents=True, exist_ok=True)
    download_directory = DESTINATION / "reports"
    download_directory.mkdir(parents=True, exist_ok=True)
    files = []
    for source in sorted(SOURCE.iterdir()):
        if source.is_file() and source.suffix in {".md", ".csv", ".json"}:
            shutil.copyfile(source, download_directory / source.name)
            files.append(source.name)
    page = dashboard.read_text(encoding="utf-8")
    report_link = '<a class="button" href="reports.html" style="text-decoration:none;margin-right:8px">Download reports ↓</a>'
    page = page.replace('<button class="button" id="print">', '<div>' + report_link + '<button class="button" id="print">', 1)
    page = page.replace('Print report ↗</button></div>', 'Print report ↗</button></div></div>', 1)
    (DESTINATION / "index.html").write_text(page, encoding="utf-8")
    (DESTINATION / ".nojekyll").write_text("", encoding="utf-8")
    groups = [("Analytical reports", ".md"), ("Supporting datasets", ".csv"), ("Analysis and source audit", ".json")]
    sections = []
    for title, suffix in groups:
        links = "".join('<li><a download href="reports/' + html.escape(name, quote=True) + '">' + html.escape(name) + '</a></li>' for name in files if name.endswith(suffix))
        sections.append('<section><h2>' + title + '</h2><ul>' + links + '</ul></section>')
    downloads = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Download the placement analysis reports, datasets and source audit by Durgesh Tiwari.">
<title>Reports · Placement Atlas</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f4f6f8;color:#192a38;font:15px/1.6 system-ui,sans-serif}main{max-width:1000px;margin:40px auto;padding:0 20px}h1{font-size:32px;letter-spacing:-1px}h2{font-size:18px}a{color:#087d63;text-underline-offset:4px}p{color:#657582}.notice{padding:14px 18px;background:#fffbec;border:1px solid #e5d8ac;border-radius:8px;color:#7b652b}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-top:25px}section{background:white;border:1px solid #e4e9ed;border-radius:10px;padding:20px}ul{list-style:none;padding:0}li{margin:12px 0;overflow-wrap:anywhere}footer{margin-top:30px;color:#657582;font-size:12px}</style>
</head><body><main><a href="./">← Back to dashboard</a><h1>Reports & supporting files</h1><p>Tech-College Placement Analytics · Durgesh Tiwari</p>
<p class="notice">See the data label in the dashboard and reports. The supplied workbook contains synthetic examples, not real college outcomes.</p>
<div class="grid">''' + "".join(sections) + '''</div><footer>Reports download as Markdown, datasets as CSV and audit records as JSON. Assigned project duration: 26 October–15 December 2026.</footer></main></body></html>'''
    (DESTINATION / "reports.html").write_text(downloads, encoding="utf-8")
    print(f"GitHub Pages website: {DESTINATION} ({len(files)} report downloads)")


if __name__ == "__main__":
    main()
