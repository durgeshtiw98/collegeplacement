"""Render a self-contained dashboard; data never leaves the user's browser."""

import json
from pathlib import Path


def render(result, tables, path):
    payload = {"analysis": result, "tables": tables}
    encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False)
    encoded = encoded.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    template = Path(__file__).with_name("dashboard.html").read_text(encoding="utf-8")
    Path(path).write_text(template.replace("__PLACEMENT_PAYLOAD__", encoded), encoding="utf-8")
