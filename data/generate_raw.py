"""Generate a deterministic, anonymised synthetic learning dataset.

This stands in for anonymised Derry platform data: same shape, no real people.
Ground-truth relationships are built in *on purpose* so the downstream analysis
can be checked for honesty — in particular a **confounder** (prior ability drives
both engagement and completion), so the write-up can show why a naive "engagement
causes completion" reading is overstated.

Run:  python data/generate_raw.py   ->   data/raw/{students,enrollments,events}.csv
Deterministic under SEED: regenerating yields byte-identical files.
"""
from __future__ import annotations

import hashlib
import math
import random
from pathlib import Path

SEED = 20260910
N_STUDENTS = 4000
COURSES = ["algebra-i", "geometry", "biology", "chemistry", "world-history"]
COHORTS = ["2025-spring", "2025-autumn", "2026-spring"]
RAW = Path(__file__).resolve().parent / "raw"


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def anon_id(i: int) -> str:
    """Stable pseudonymous id — a salted hash, never a real identifier."""
    return "stu_" + hashlib.sha256(f"derry-salt::{i}".encode()).hexdigest()[:12]


def generate() -> None:
    rng = random.Random(SEED)
    RAW.mkdir(parents=True, exist_ok=True)

    students, enrollments, events = [], [], []
    enroll_id = 0

    for i in range(N_STUDENTS):
        sid = anon_id(i)
        cohort = rng.choice(COHORTS)
        # prior_score ~ the confounder: latent prior ability, 0..100
        prior = max(0, min(100, rng.gauss(62, 16)))
        students.append({"student_id": sid, "cohort": cohort, "prior_score": round(prior, 1)})

        # each student enrolls in 1-3 courses
        for course in rng.sample(COURSES, rng.randint(1, 3)):
            enroll_id += 1
            # engagement is driven by prior ability (confounding) + noise
            base_sessions = 4 + 0.18 * prior + rng.gauss(0, 4)
            sessions = max(0, int(round(base_sessions)))
            minutes = max(0, int(sessions * rng.gauss(22, 6)))

            # mastery gate: more likely passed with higher prior + more sessions
            gate_logit = -3.2 + 0.035 * prior + 0.09 * sessions
            mastery_passed = rng.random() < _sigmoid(gate_logit)

            # completion: true drivers are prior ability, the gate, and engagement
            # (engagement's *own* effect is modest; prior ability inflates the naive view)
            comp_logit = (-4.0 + 0.045 * prior + 1.3 * (1 if mastery_passed else 0)
                          + 0.03 * sessions + {"2025-spring": 0.0, "2025-autumn": 0.15,
                                               "2026-spring": 0.3}[cohort]
                          + rng.gauss(0, 0.5))
            completed = rng.random() < _sigmoid(comp_logit)

            # time-to-complete (weeks) only meaningful if completed
            weeks = round(max(1.0, rng.gauss(10, 2) - 0.03 * sessions), 1) if completed else ""

            enrollments.append({
                "enrollment_id": enroll_id, "student_id": sid, "course": course,
                "cohort": cohort, "sessions": sessions, "active_minutes": minutes,
                "mastery_gate_passed": int(mastery_passed), "completed": int(completed),
                "weeks_to_complete": weeks,
            })

            # weekly activity events -> retention curve raw material
            active_weeks = min(12, 2 + sessions // 2)
            for wk in range(1, active_weeks + 1):
                # drop-off hazard: lower prior + not passing gate -> earlier drop
                if wk > 1 and rng.random() < 0.06 + 0.002 * (70 - prior):
                    break
                events.append({"enrollment_id": enroll_id, "week": wk,
                               "minutes": max(0, int(rng.gauss(minutes / max(active_weeks,1), 8)))})

    _write("students.csv", ["student_id", "cohort", "prior_score"], students)
    _write("enrollments.csv",
           ["enrollment_id", "student_id", "course", "cohort", "sessions",
            "active_minutes", "mastery_gate_passed", "completed", "weeks_to_complete"],
           enrollments)
    _write("events.csv", ["enrollment_id", "week", "minutes"], events)
    print(f"generated {len(students)} students, {len(enrollments)} enrollments, "
          f"{len(events)} events into {RAW}")


def _write(name: str, cols: list[str], rows: list[dict]) -> None:
    import csv
    with (RAW / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    generate()
