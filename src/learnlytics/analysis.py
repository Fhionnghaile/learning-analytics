"""Descriptive analyses: retention, mastery-gate effect, time-to-completion."""
from __future__ import annotations

import pandas as pd


def completion_by_mastery(df: pd.DataFrame) -> pd.DataFrame:
    """Completion rate split by whether the mastery gate was passed.

    NOTE (surfaced in the write-up): this is an *association*. Students who pass
    the gate differ systematically (higher prior ability), so the raw gap
    overstates the gate's own causal effect — see the model's adjusted estimate.
    """
    g = df.groupby("mastery_gate_passed")["completed"].agg(["mean", "count"])
    g.index = g.index.map({0: "did_not_pass", 1: "passed"})
    return g.rename(columns={"mean": "completion_rate", "count": "n"})


def completion_by_cohort(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("cohort")["completed"].agg(["mean", "count"])
            .rename(columns={"mean": "completion_rate", "count": "n"}))


def time_to_complete(df: pd.DataFrame) -> pd.Series:
    done = df[df["completed"] == 1]["weeks_to_complete"].dropna()
    return done.describe()


def engagement_quartile_completion(df: pd.DataFrame) -> pd.DataFrame:
    """Completion by engagement quartile — the naive 'engagement works' view."""
    q = pd.qcut(df["sessions"], 4, labels=["Q1", "Q2", "Q3", "Q4"], duplicates="drop")
    return (df.groupby(q, observed=True)["completed"].agg(["mean", "count"])
            .rename(columns={"mean": "completion_rate", "count": "n"}))
