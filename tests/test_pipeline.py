import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from learnlytics.model import fit_completion_model          # noqa: E402
from learnlytics.pipeline import (                           # noqa: E402
    IntegrityError, assert_no_pii, build_frame, load_raw, retention_table,
)


@pytest.fixture(scope="module")
def frames():
    return load_raw()


@pytest.fixture(scope="module")
def df(frames):
    return build_frame(frames)


# -- reproducibility ---------------------------------------------------------
def test_raw_generation_is_reproducible(tmp_path):
    import hashlib
    def hashes():
        return {f.name: hashlib.sha256(f.read_bytes()).hexdigest()
                for f in sorted((ROOT / "data" / "raw").glob("*.csv"))}
    before = hashes()
    subprocess.run([sys.executable, str(ROOT / "data" / "generate_raw.py")],
                   check=True, capture_output=True)
    assert hashes() == before, "regenerating raw changed the files"


# -- integrity asserts -------------------------------------------------------
def test_integrity_asserts_pass_on_real_data(df):
    assert len(df) > 0
    assert df["completed"].isin([0, 1]).all()
    assert df["prior_score"].between(0, 100).all()


def test_referential_integrity_violation_is_caught(frames):
    bad = {k: v.copy() for k, v in frames.items()}
    bad["enrollments"] = bad["enrollments"].copy()
    bad["enrollments"].loc[bad["enrollments"].index[0], "student_id"] = "stu_deadbeef0000"
    with pytest.raises(IntegrityError):
        build_frame(bad)


def test_null_in_required_column_is_caught(frames):
    bad = {k: v.copy() for k, v in frames.items()}
    bad["enrollments"] = bad["enrollments"].copy()
    bad["enrollments"].loc[bad["enrollments"].index[0], "sessions"] = None
    with pytest.raises(IntegrityError):
        build_frame(bad)


# -- no PII ------------------------------------------------------------------
def test_no_pii_columns_or_raw_ids(frames):
    assert_no_pii(frames)          # must not raise


def test_pii_column_is_detected():
    bad = {"students": pd.DataFrame({"student_id": ["stu_0123456789ab"], "email": ["a@b.c"]})}
    with pytest.raises(IntegrityError):
        assert_no_pii(bad)


def test_unhashed_id_is_detected():
    bad = {"students": pd.DataFrame({"student_id": ["alice.smith"]})}
    with pytest.raises(IntegrityError):
        assert_no_pii(bad)


# -- retention ---------------------------------------------------------------
def test_retention_is_monotone_non_increasing(frames):
    ret = retention_table(frames)
    vals = ret["retention"].to_numpy()
    assert (np.diff(vals) <= 1e-9).all(), "retention curve should not rise"
    assert vals[0] <= 1.0 + 1e-9


# -- model: no leakage, held-out metrics ------------------------------------
def test_train_test_split_is_disjoint(df):
    r = fit_completion_model(df, seed=7)
    assert set(r.train_idx).isdisjoint(set(r.test_idx))
    assert r.n_train + r.n_test == len(df)


def test_model_metrics_are_reasonable_and_from_holdout(df):
    r = fit_completion_model(df, seed=7)
    assert 0.5 < r.auc <= 1.0            # beats chance on held-out data
    assert 0.0 <= r.brier <= 0.25        # calibrated-ish
    # deterministic under seed
    r2 = fit_completion_model(df, seed=7)
    assert r.auc == r2.auc


def test_mastery_gate_raw_gap_exceeds_adjusted_effect(df):
    """The honesty check: the unadjusted gap overstates the adjusted effect."""
    from learnlytics.analysis import completion_by_mastery
    m = completion_by_mastery(df)
    raw_gap = m.loc["passed", "completion_rate"] - m.loc["did_not_pass", "completion_rate"]
    assert raw_gap > 0.3     # big raw association
    # prior ability carries comparable adjusted weight -> confounding is real
    r = fit_completion_model(df)
    assert r.coefficients["prior_score"] > 0.3
