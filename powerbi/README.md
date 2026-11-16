# Power BI model

Power BI Desktop files (`.pbix`) are a proprietary binary assembled in the Power BI
Desktop application — they are not scriptable from a repo. So this folder ships the
**model as reproducible inputs** instead, which load into Power BI Desktop in a minute:

1. `python -m learnlytics.star_schema` → writes `model/*.csv` (fact + dimensions).
2. In Power BI Desktop: **Get Data → Text/CSV**, load all four files.
3. In **Model view**, relate `fact_enrollment[StudentKey→dim_student]`,
   `[CourseKey→dim_course]`, `[CohortKey→dim_cohort]`.
4. Paste the measures from `measures.dax`.
5. Build the visuals: Completion Rate by Cohort (bar), Retention (line, from events),
   the unadjusted Gate Gap card — **with the confounding caveat** from `WRITEUP.md`.

The same KPIs are live in the Streamlit dashboard (`dashboard/app.py`) and in the Excel
what-if model (`excel/`), so the three BI surfaces agree by construction.
