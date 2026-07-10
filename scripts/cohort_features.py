"""
Shared feature construction for the synthetic cohorts (Phases 6 & 8).

Builds numeric design matrices from a cohort DataFrame for predicting the
`dysfunction` outcome, keeping feature definitions consistent across the
validation harness and the ML ensemble.
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

CYTOKINES = ["IL16", "IL12p70", "IL17", "CCL15", "IL1a"]
DRUG_CLASSES = ["PD-1", "PD-L1", "CTLA-4", "Combination"]


def _common(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["age"] = df["age"]
    X["sex_F"] = (df["sex"] == "F").astype(int)
    X["hla_risk"] = df["hla_risk"]
    X["baseline_TSH"] = df["baseline_TSH"]
    X["TPOAb_wk0"] = df["TPOAb_wk0"]
    X["TgAb_wk0"] = df["TgAb_wk0"]
    for ck in CYTOKINES:
        X[ck] = df[ck]
    for dc in DRUG_CLASSES:
        X[f"class_{dc}"] = (df["drug_class"] == dc).astype(int)
    return X


def build_baseline_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Baseline-only features (pre-treatment): covariates, baseline antibodies, cytokines, drug class."""
    X = _common(df)
    y = df["dysfunction"].astype(int)
    return X, y


def build_early_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Baseline + early on-treatment biomarkers (weeks 6 & 12)."""
    X = _common(df)
    for col in ["TSH_wk6", "TSH_wk12", "fT4_wk6", "fT4_wk12", "TPOAb_wk12"]:
        if col in df.columns:
            X[col] = df[col]
    y = df["dysfunction"].astype(int)
    return X, y


def feature_names(X: pd.DataFrame) -> List[str]:
    return list(X.columns)
