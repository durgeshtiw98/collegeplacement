"""Deterministic fictional data, deliberately including missing and duplicate values."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from .schema import SCHEMAS


def write_tables(tables, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, fields in SCHEMAS.items():
        with (directory / f"{name}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(tables.get(name, []))


def generate(directory, seed=2026):
    rng = random.Random(seed)
    tables = {name: [] for name in SCHEMAS}
    departments = ["CSE", "IT", "ECE", "ME", "CE"]
    for i in range(1, 181):
        student = f"S{i:04}"
        tables["students"].append(dict(zip(SCHEMAS["students"], [
            student, departments[(i - 1) % 5], 2026,
            "|".join(rng.sample(["Python", "SQL", "Java", "Excel", "Communication", "CAD"], rng.randint(1, 4))),
        ])))
        tables["academics"].append(dict(zip(SCHEMAS["academics"], [
            student, "" if i % 31 == 0 else round(rng.uniform(4.8, 9.8), 2),
            "" if i % 43 == 0 else rng.choices([0, 1, 2], weights=[85, 10, 5])[0],
        ])))
    for i, name in enumerate(["Aster Systems", "Bluebird Analytics", "Cedar Engineering", "Delta Cloud", "Elm Digital", "Finch Technologies"], 1):
        tables["companies"].append(dict(zip(SCHEMAS["companies"], [f"C{i:02}", name, "Technology" if i != 3 else "Engineering"])))
        tables["recruiters"].append(dict(zip(SCHEMAS["recruiters"], [f"R{i:02}", f"C{i:02}", "Campus recruitment"])))
    for i in range(1, 19):
        company = (i - 1) % 6 + 1
        day = (date(2026, 7, 1) + timedelta(days=i * 5)).isoformat()
        drive = f"D{i:03}"
        tables["drives"].append(dict(zip(SCHEMAS["drives"], [drive, f"C{company:02}", f"R{company:02}", day, "Graduate trainee", 6.0])))
        for student in rng.sample(tables["students"], rng.randint(30, 48)):
            sid = student["student_id"]
            attended = rng.random() < .83
            tables["registrations"].append(dict(zip(SCHEMAS["registrations"], [f"G{len(tables['registrations']) + 1:04}", sid, drive, str(attended).lower()])))
            if rng.random() > .88:
                continue
            interviewed = attended and rng.random() < .65
            selected = interviewed and rng.random() < .38
            shortlisted = interviewed or (attended and rng.random() < .2)
            status = "selected" if selected else rng.choice(["interviewed", "rejected"]) if interviewed else "shortlisted" if shortlisted else rng.choice(["applied", "rejected", "withdrawn"])
            appid = f"A{len(tables['applications']) + 1:04}"
            tables["applications"].append(dict(zip(SCHEMAS["applications"], [appid, sid, drive, day, status, day if shortlisted else "", str(interviewed).lower()])))
            if selected:
                tables["placements"].append(dict(zip(SCHEMAS["placements"], [f"P{len(tables['placements']) + 1:04}", appid, rng.choices(["accepted", "joined", "declined", "offered"], weights=[50, 30, 10, 10])[0], "" if rng.random() < .15 else rng.randrange(350000, 1500001, 50000), (date.fromisoformat(day) + timedelta(days=2)).isoformat()])))
    tables["students"].append(tables["students"][0].copy())
    write_tables(tables, directory)
    return tables
