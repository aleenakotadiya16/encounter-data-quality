"""Build three synthetic encounter extracts with known data errors."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
AS_OF = dt.date(2026, 11, 6)
DEPARTMENTS = ["Emergency", "Inpatient", "Outpatient", "Imaging"]
SEXES = ["Female", "Male"]
TYPES = ["Clinic", "Emergency", "Inpatient", "Telehealth"]


def _base_frame(n: int, seed: int, start: dt.date) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    event_dates = [
        start + dt.timedelta(days=int(day))
        for day in rng.integers(0, 60, size=n)
    ]
    return pd.DataFrame(
        {
            "encounter_id": [f"E{seed}{i:04d}" for i in range(n)],
            "mrn": [f"{100000 + seed + i}" for i in range(n)],
            "event_date": event_dates,
            "zip": rng.choice(["75201", "75001", "76102", "77002", "78701"], size=n),
            "age": rng.integers(0, 96, size=n),
            "sex": rng.choice(SEXES, size=n),
            "encounter_type": rng.choice(TYPES, size=n),
            "department": rng.choice(DEPARTMENTS, size=n),
        }
    )


def inject_errors(frame: pd.DataFrame, seed: int, rates: dict) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dirty = frame.copy()
    n = len(dirty)

    def pick(rate: float) -> np.ndarray:
        count = int(round(n * rate))
        return rng.choice(n, size=count, replace=False) if count else np.array([], dtype=int)

    dirty.loc[pick(rates["null_mrn"]), "mrn"] = None
    for index in pick(rates["duplicate_id"]):
        dirty.loc[index, "encounter_id"] = dirty.loc[0, "encounter_id"]
    for index in pick(rates["future_date"]):
        dirty.loc[index, "event_date"] = AS_OF + dt.timedelta(days=30)
    for index in pick(rates["bad_zip"]):
        dirty.loc[index, "zip"] = rng.choice(["12", "00000", "7520"])
    for index in pick(rates["bad_age"]):
        dirty.loc[index, "age"] = int(rng.choice([-1, 130, 250]))
    for index in pick(rates["bad_sex"]):
        dirty.loc[index, "sex"] = "X9"
    for index in pick(rates["null_department"]):
        dirty.loc[index, "department"] = None
    dirty["event_date"] = pd.to_datetime(dirty["event_date"])
    return dirty


WEEKS = [
    ("week-1", 21, {"null_mrn": 0.08, "duplicate_id": 0.04, "future_date": 0.05, "bad_zip": 0.07, "bad_age": 0.04, "bad_sex": 0.03, "null_department": 0.05}),
    ("week-2", 22, {"null_mrn": 0.04, "duplicate_id": 0.02, "future_date": 0.02, "bad_zip": 0.03, "bad_age": 0.02, "bad_sex": 0.01, "null_department": 0.02}),
    ("week-3", 23, {"null_mrn": 0.01, "duplicate_id": 0.00, "future_date": 0.01, "bad_zip": 0.01, "bad_age": 0.00, "bad_sex": 0.00, "null_department": 0.01}),
]


def write_extracts(directory: Path = DATA_DIR) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, seed, rates in WEEKS:
        frame = inject_errors(_base_frame(200, seed, dt.date(2026, 8, 1)), seed + 100, rates)
        path = directory / f"encounters-{name}.csv"
        frame.to_csv(path, index=False)
        paths.append(path)
    return paths


if __name__ == "__main__":
    for path in write_extracts():
        print(path)
