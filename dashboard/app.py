"""Interactive learning-analytics dashboard (Streamlit).

    pip install streamlit plotly
    streamlit run dashboard/app.py

Reads the same tested pipeline as the notebook/figures, so the numbers on the
dashboard are the numbers in the write-up.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from learnlytics.analysis import (  # noqa: E402
    completion_by_cohort, completion_by_mastery, engagement_quartile_completion,
)
from learnlytics.model import FEATURES, fit_completion_model  # noqa: E402
from learnlytics.pipeline import build_frame, load_raw, retention_table  # noqa: E402


@st.cache_data
def _load():
    frames = load_raw()
    return build_frame(frames), retention_table(frames)


def main() -> None:
    st.set_page_config(page_title="Derry Learning Analytics", layout="wide")
    st.title("Learning Analytics — completion & retention")
    st.caption("Anonymised synthetic learning data · figures reproduce from raw")

    df, ret = _load()

    cohorts = st.multiselect("Cohorts", sorted(df["cohort"].unique()),
                             default=sorted(df["cohort"].unique()))
    courses = st.multiselect("Courses", sorted(df["course"].unique()),
                             default=sorted(df["course"].unique()))
    view = df[df["cohort"].isin(cohorts) & df["course"].isin(courses)]
    if view.empty:
        st.warning("No rows for this filter."); return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Enrollments", f"{len(view):,}")
    c2.metric("Completion rate", f"{view['completed'].mean():.0%}")
    c3.metric("Mastery-gate pass", f"{view['mastery_gate_passed'].mean():.0%}")
    med = pd.to_numeric(view['weeks_to_complete'], errors='coerce').median()
    c4.metric("Median weeks to complete", f"{med:.1f}" if pd.notna(med) else "—")

    left, right = st.columns(2)
    with left:
        st.subheader("Retention by week")
        st.line_chart(ret.set_index("week")["retention"])
        st.subheader("Completion by mastery gate (unadjusted)")
        st.bar_chart(completion_by_mastery(view)["completion_rate"])
    with right:
        st.subheader("Completion by engagement quartile")
        st.bar_chart(engagement_quartile_completion(view)["completion_rate"])
        st.subheader("Completion by cohort")
        st.bar_chart(completion_by_cohort(view)["completion_rate"])

    st.subheader("Adjusted drivers (held-out model)")
    if view["completed"].nunique() > 1 and len(view) > 200:
        r = fit_completion_model(view)
        st.caption(f"Held-out AUC {r.auc:.2f} · accuracy {r.accuracy:.2f} · "
                   f"Brier {r.brier:.2f} (n_test={r.n_test})")
        st.bar_chart(pd.Series(r.coefficients).reindex(FEATURES))
        st.info("Coefficients are **associational**, not causal: prior ability "
                "confounds the mastery-gate and engagement effects. See WRITEUP.md.")
    else:
        st.write("Not enough data in this filter to fit the model.")


if __name__ == "__main__":
    main()
