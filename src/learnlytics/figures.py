"""Regenerate every figure from the raw data, deterministically.

    python -m learnlytics.figures   ->   figures/*.png
Each figure is produced from the pipeline output only, so `make all` (raw -> figures)
reproduces the exact images used in the write-up.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from .analysis import (  # noqa: E402
    completion_by_mastery, engagement_quartile_completion,
)
from .model import FEATURES, fit_completion_model  # noqa: E402
from .pipeline import build_frame, load_raw, retention_table  # noqa: E402

FIG = Path(__file__).resolve().parents[2] / "figures"
BLUE, MUTED, GOOD = "#2f6df6", "#9aa7bd", "#1f9d6b"


def _style(ax, title):
    ax.set_title(title, fontsize=12, fontweight="600", loc="left", color="#1c2230")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#e3e6ea", linewidth=0.8)
    ax.set_axisbelow(True)


def generate() -> list[Path]:
    FIG.mkdir(exist_ok=True)
    frames = load_raw()
    df = build_frame(frames)
    out = []

    # 1. retention curve
    ret = retention_table(frames)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.plot(ret["week"], ret["retention"], color=BLUE, linewidth=2.2, marker="o", ms=4)
    ax.fill_between(ret["week"], ret["retention"], color=BLUE, alpha=0.08)
    ax.set_xlabel("Week"); ax.set_ylabel("Fraction still active"); ax.set_ylim(0, 1)
    _style(ax, "Retention — active enrollments by week")
    out.append(_save(fig, "retention.png"))

    # 2. mastery-gate completion (raw, with caveat in caption/writeup)
    m = completion_by_mastery(df)
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.bar(m.index, m["completion_rate"], color=[MUTED, GOOD], width=0.55)
    for i, v in enumerate(m["completion_rate"]):
        ax.text(i, v + 0.02, f"{v:.0%}", ha="center", fontsize=11, fontweight="600")
    ax.set_ylim(0, 1); ax.set_ylabel("Completion rate")
    _style(ax, "Completion by mastery gate (unadjusted)")
    out.append(_save(fig, "mastery_gate.png"))

    # 3. engagement quartile completion
    q = engagement_quartile_completion(df)
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    ax.bar(q.index.astype(str), q["completion_rate"], color=BLUE, width=0.6)
    ax.set_ylim(0, 1); ax.set_ylabel("Completion rate"); ax.set_xlabel("Engagement quartile (sessions)")
    _style(ax, "Completion by engagement quartile (unadjusted)")
    out.append(_save(fig, "engagement_quartile.png"))

    # 4. model coefficients (adjusted, standardised log-odds)
    r = fit_completion_model(df)
    names = FEATURES
    vals = [r.coefficients[n] for n in names]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = [GOOD if v >= 0 else "#d9480f" for v in vals]
    ax.barh(names, vals, color=colors)
    ax.axvline(0, color="#1c2230", linewidth=0.8)
    ax.set_xlabel("Standardised log-odds (adjusted)")
    _style(ax, f"Adjusted completion drivers · test AUC {r.auc:.2f}")
    ax.grid(axis="x", color="#e3e6ea", linewidth=0.8); ax.grid(axis="y", visible=False)
    out.append(_save(fig, "model_coefficients.png"))

    return out


def _save(fig, name: str) -> Path:
    fig.tight_layout()
    p = FIG / name
    fig.savefig(p, dpi=130)
    plt.close(fig)
    return p


if __name__ == "__main__":
    for p in generate():
        print("wrote", p.name)
