"""Export a star schema (fact + dimensions) for Power BI / SQL BI tools.

    python -m learnlytics.star_schema   ->   powerbi/model/*.csv
A classic grain: one row per enrollment in the fact table, with conformed
dimensions for student, course, and cohort.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .pipeline import build_frame, load_raw

OUT = Path(__file__).resolve().parents[2] / "powerbi" / "model"


def export() -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    frames = load_raw()
    df = build_frame(frames)

    dim_student = frames["students"].rename(columns={"student_id": "StudentKey"})
    dim_course = pd.DataFrame({"CourseKey": sorted(df["course"].unique())})
    dim_cohort = pd.DataFrame({"CohortKey": sorted(df["cohort"].unique())})

    fact = df.rename(columns={
        "enrollment_id": "EnrollmentKey", "student_id": "StudentKey",
        "course": "CourseKey", "cohort": "CohortKey",
    })[["EnrollmentKey", "StudentKey", "CourseKey", "CohortKey", "sessions",
        "active_minutes", "mastery_gate_passed", "completed", "weeks_to_complete"]]

    paths = []
    for name, d in [("fact_enrollment", fact), ("dim_student", dim_student),
                    ("dim_course", dim_course), ("dim_cohort", dim_cohort)]:
        p = OUT / f"{name}.csv"
        d.to_csv(p, index=False)
        paths.append(p)
    return paths


if __name__ == "__main__":
    for p in export():
        print("wrote", p.relative_to(OUT.parent))
