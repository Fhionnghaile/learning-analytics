"""An interpretable completion model with a strict held-out evaluation.

Logistic regression on standardised features. Metrics are computed ONLY on a
held-out test split (no leakage), and coefficients are reported as log-odds with
an explicit associational — not causal — caveat.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURES = ["prior_score", "sessions", "active_minutes", "mastery_gate_passed"]


@dataclass
class ModelReport:
    auc: float
    accuracy: float
    brier: float
    coefficients: dict[str, float]
    intercept: float
    n_train: int
    n_test: int
    train_idx: np.ndarray
    test_idx: np.ndarray


def fit_completion_model(df: pd.DataFrame, *, seed: int = 7, test_size: float = 0.25) -> ModelReport:
    X = df[FEATURES].to_numpy(dtype=float)
    y = df["completed"].to_numpy(dtype=int)
    idx = np.arange(len(df))

    Xtr, Xte, ytr, yte, itr, ite = train_test_split(
        X, y, idx, test_size=test_size, random_state=seed, stratify=y
    )
    # scaler fit on TRAIN ONLY — no peeking at test
    scaler = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=1000)
    clf.fit(scaler.transform(Xtr), ytr)

    proba = clf.predict_proba(scaler.transform(Xte))[:, 1]
    pred = (proba >= 0.5).astype(int)
    coefs = dict(zip(FEATURES, clf.coef_[0].tolist()))
    return ModelReport(
        auc=float(roc_auc_score(yte, proba)),
        accuracy=float((pred == yte).mean()),
        brier=float(brier_score_loss(yte, proba)),
        coefficients=coefs,
        intercept=float(clf.intercept_[0]),
        n_train=len(itr), n_test=len(ite),
        train_idx=itr, test_idx=ite,
    )
