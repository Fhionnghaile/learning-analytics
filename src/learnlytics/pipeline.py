"""Load raw CSVs -> clean -> integrity-assert -> tidy analytic frame.

Integrity checks run as asserts *in the pipeline* (not just in tests): the build
fails loudly if row counts, nulls, ranges, or PII expectations are violated.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[2] / "data" / "raw"

# A pseudonymous id looks like 'stu_' + 12 hex chars; anything else is suspect PII.
_ID_RE = re.compile(r"^stu_[0-9a-f]{12}$")
_PII_HINTS = ("name", "email", "phone", "address", "dob", "birth", "ssn")


class IntegrityError(AssertionError):
    pass


def _check(cond: bool, msg: str) -> None:
    if not cond:
        raise IntegrityError(msg)


def load_raw(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    raw_dir = raw_dir or RAW
    frames = {name: pd.read_csv(raw_dir / f"{name}.csv")
              for name in ("students", "enrollments", "events")}
    return frames


def assert_no_pii(frames: dict[str, pd.DataFrame]) -> None:
    for name, df in frames.items():
        for col in df.columns:
            _check(not any(h in col.lower() for h in _PII_HINTS),
                   f"{name}.{col}: column name looks like PII")
        if "student_id" in df.columns:
            bad = ~df["student_id"].astype(str).str.match(_ID_RE)
            _check(not bad.any(), f"{name}: {int(bad.sum())} student_id(s) are not pseudonymised")


def build_frame(frames: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Join to one enrollment-level analytic frame, with integrity asserts."""
    frames = frames or load_raw()
    assert_no_pii(frames)
    students, enr, events = frames["students"], frames["enrollments"], frames["events"]

    # row-count / key integrity
    _check(len(students) > 0 and len(enr) > 0, "empty input frames")
    _check(enr["enrollment_id"].is_unique, "enrollment_id not unique")
    _check(enr["student_id"].isin(set(students["student_id"])).all(),
           "enrollment references unknown student (referential integrity)")

    df = enr.merge(students[["student_id", "prior_score"]], on="student_id", how="left",
                   suffixes=("", "_s"))

    # null handling: required columns must be complete
    required = ["sessions", "active_minutes", "mastery_gate_passed", "completed", "prior_score"]
    for c in required:
        _check(df[c].notna().all(), f"nulls present in required column {c!r}")

    # range validity
    _check(df["prior_score"].between(0, 100).all(), "prior_score out of [0,100]")
    _check(df["sessions"].ge(0).all(), "negative sessions")
    _check(df["completed"].isin([0, 1]).all(), "completed not binary")
    _check(df["mastery_gate_passed"].isin([0, 1]).all(), "mastery_gate_passed not binary")

    # weeks_to_complete must be present iff completed
    wtc = pd.to_numeric(df["weeks_to_complete"], errors="coerce")
    _check(wtc[df["completed"] == 1].notna().all(), "completed rows missing weeks_to_complete")
    df["weeks_to_complete"] = wtc

    # weekly events coverage (used for retention)
    _check(events["week"].ge(1).all(), "event week < 1")
    return df


def retention_table(frames: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Fraction of enrollments still active at each week (survival-style)."""
    frames = frames or load_raw()
    events = frames["events"]
    total = frames["enrollments"]["enrollment_id"].nunique()
    active_by_week = events.groupby("week")["enrollment_id"].nunique()
    out = (active_by_week.reindex(range(1, int(events["week"].max()) + 1), fill_value=0)
           / total).rename("retention").reset_index().rename(columns={"index": "week"})
    return out
