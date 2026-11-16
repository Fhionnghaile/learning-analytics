# Learning Analytics — reproducible pipeline, honest model, three dashboards

<!-- at-a-glance -->
> **A reproducible learning-analytics pipeline with an honest model — no leakage, stated limits.**  
> **Result:** 11 tests; a reproducible end-to-end run.  
> **Reproduce:** `pytest -q`  
> ![CI](https://github.com/fhionnghaile/learning-analytics/actions/workflows/ci.yml/badge.svg)
>
> **What this is worth:** Turns raw learning data into decisions you can defend, because the pipeline is reproducible and the model's limits are stated.


A rigorous, **reproducible** analysis of (synthetic, anonymised) learning data: what
predicts course completion, how retention decays, and what the mastery gate is really
worth — with a methods section that is honest about confounding.

> **What it proves:** data analysis, visualisation, **statistical honesty**, and the BI
> stack — a Python/Streamlit dashboard, a **Power BI** model, and an **Excel** what-if
> model, all reading the same numbers.

## Reproducible by construction

```
make all        # raw -> figures -> star schema, all from a fixed seed
make test       # integrity asserts, no-leakage model checks, reproducibility
make dashboard  # streamlit run dashboard/app.py
```

`make all` regenerates every figure from raw; `data/generate_raw.py` is deterministic
(regenerating yields byte-identical CSVs — enforced by a test).

## Layout

```
data/
  generate_raw.py     deterministic synthetic dataset (stands in for anonymised Derry data)
  SCHEMA.md           schema + anonymisation (salted-hash ids, no PII)
  raw/                generated CSVs
src/learnlytics/
  pipeline.py         load -> clean -> INTEGRITY ASSERTS (row counts, nulls, ranges, no PII)
  analysis.py         retention, mastery-gate effect, time-to-completion, engagement quartiles
  model.py            logistic regression, held-out split, no leakage, coefficients
  figures.py          regenerate every figure deterministically
  star_schema.py      export fact + dimensions for Power BI / SQL
dashboard/app.py      Streamlit dashboard (same pipeline as the figures)
excel/                Excel what-if model (formula-driven ROI)
powerbi/              star-schema CSVs + measures.dax + load instructions
figures/              generated PNGs
tests/                integrity, reproducibility, no-PII, no-leakage
WRITEUP.md            what the data does — and doesn't — show (confounders, limitations)
```

## The honest finding (see WRITEUP.md)

The mastery gate shows a 31% → **69%** raw completion gap — but that gap is
**confounded by prior ability**. Adjusted in a held-out logistic model (AUC ≈ 0.76),
prior ability (≈ 0.59 standardised log-odds) carries weight comparable to the gate
(≈ 0.61), and engagement's own effect is modest. The write-up says so plainly, and a
test (`test_mastery_gate_raw_gap_exceeds_adjusted_effect`) keeps the claim honest.

## Quality gates (the spec's acceptance cases)

- **Reproducible:** `test_raw_generation_is_reproducible` (byte-identical re-gen).
- **Integrity asserts in the pipeline:** referential integrity, nulls, ranges, binary
  targets — each with a test that a violation is *caught*.
- **No PII:** column-name and un-hashed-id detection, tested both ways.
- **No leakage:** scaler + model fit on train only; metrics from a disjoint held-out set.
- **Honest methods:** `WRITEUP.md` lists confounders and limitations explicitly.

Data is synthetic — the **method** is the deliverable, not the effect sizes.

## Key decisions

- Reproducible pipeline (fixed seeds, versioned steps) over a one-off notebook.
- Leakage-safe train/test discipline, with the model's honest performance reported.
- Interpretable features, so a result can be explained to a non-technical stakeholder.

## Scope & limits

- Illustrative dataset; the method transfers, the numbers are re-measured on real data.

