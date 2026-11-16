# What the learning data does — and doesn't — show

A short, deliberately careful read of the completion analysis. Every number below
traces to a figure in `figures/` or a test in `tests/`, and all of it regenerates from
raw with `make all`.

## The headline, and why it's only half the story

Students who pass the **mastery gate** complete at **69%**; those who don't, at **31%**
(`figures/mastery_gate.png`). Taken at face value that's a 38-point swing — an easy
slide to put in front of a board under the title *"the mastery gate works."*

It is also **confounded**. Passing the gate is not random: higher-prior-ability
students pass it *and* complete more often regardless. When we hold prior ability,
engagement, and cohort constant in a logistic model, the gate's **adjusted** weight
(standardised log-odds ≈ 0.61) is comparable to prior ability's (≈ 0.59)
(`figures/model_coefficients.png`). The gate still matters — but a large part of the
raw 38-point gap is prior ability wearing the gate's coat.

`tests/test_pipeline.py::test_mastery_gate_raw_gap_exceeds_adjusted_effect` pins this
relationship so the claim can't silently drift.

## Engagement: real, modest, and the easiest thing to overclaim

Completion rises across engagement quartiles (`figures/engagement_quartile.png`), the
classic "engaged students succeed" chart. But in the adjusted model, `sessions` and
`active_minutes` carry **small** weights (≈ 0.15 and ≈ 0.07). Engagement is partly a
*marker* of students who were going to complete anyway, not a lever of equal size.
Spending to lift sessions is not the same bet as the chart implies.

## Retention

The retention curve (`figures/retention.png`) falls fastest in the first few weeks and
flattens after — so interventions aimed at week-1–3 drop-off touch the most people.
`test_retention_is_monotone_non_increasing` guards the curve's shape.

## Model, honestly

- **Logistic regression** — chosen because it is interpretable, not because it is the
  most accurate thing possible. Held-out **AUC ≈ 0.76**, Brier ≈ 0.20.
- **No leakage.** The scaler and model are fit on the training split only; all metrics
  come from a held-out 25% test set (`test_train_test_split_is_disjoint`,
  `test_model_metrics_are_reasonable_and_from_holdout`).
- **Associational, not causal.** None of these coefficients are the result of an
  experiment. They describe who completes, not what *makes* someone complete.

## Limitations & confounders (the part that's usually missing)

1. **Prior ability confounds everything.** It drives engagement, gate-passing, and
   completion, so every unadjusted comparison is biased upward.
2. **Selection into the gate** is not modelled as a treatment; a cleaner estimate would
   need a design (RCT or a natural experiment / regression discontinuity on the gate
   threshold).
3. **Survivorship.** `weeks_to_complete` exists only for completers, so any timing
   analysis is conditioned on success.
4. **Synthetic data.** This dataset has known built-in relationships; real Derry data
   would have messier, unknown ones. The *method* is the deliverable here, not the
   effect sizes.

## What I'd actually tell a stakeholder

The mastery gate and prior preparation are the big signals; engagement helps but is
oversold by the raw charts; the first three weeks are where retention is won or lost.
Before spending against any of these, run a real experiment on the one you want to move
— the observational numbers are a hypothesis generator, not a business case.
