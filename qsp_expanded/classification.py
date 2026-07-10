"""
Thyroid-status classification with both hyperthyroid and hypothyroid grades.

Extends the legacy hypothyroid-only CTCAE grading to also detect the thyrotoxic
(hyperthyroid) phase, enabling biphasic-dysfunction analysis.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _classify_scalar(TSH: float, T4: float, T3: float) -> tuple[str, int, int]:
    """Return (status, hypo_grade, hyper_grade) for one time point.

    status in {'hyper', 'euthyroid', 'hypo'}.
    hypo_grade 0-4 (CTCAE-style); hyper_grade 0-3 (subclinical/overt/thyrotoxic).
    """
    # Hyperthyroid (thyrotoxic phase): overt disease is defined by elevated
    # circulating hormone; subclinical by a suppressed TSH with normal/high T4.
    # (Clinically, destructive thyrotoxicosis presents with high fT4; TSH
    # suppression follows on its own slower timescale.)
    # Overt thyrotoxicosis is defined by clearly elevated circulating hormone
    # (the acute destructive-release spike). Patients whose destruction is slow
    # enough that T4 never spikes above the overt threshold progress to
    # hypothyroidism without a detected thyrotoxic phase, so hyperthyroidism
    # incidence sits at or below hypothyroidism (the destructive-thyroiditis course).
    if T4 >= 22.0 or T3 >= 8.5:
        return "hyper", 0, 3              # thyrotoxic / overt-severe
    if T4 >= 16.0 or T3 >= 6.5:
        return "hyper", 0, 2              # overt
    # Hypothyroid: elevated TSH and/or low hormone.
    if TSH > 50.0 or T3 < 2.0:
        return "hypo", 4, 0
    if TSH > 20.0 or T3 < 2.5:
        return "hypo", 3, 0
    if TSH > 10.0 or T3 < 3.1:
        return "hypo", 2, 0
    if TSH > 4.5:
        return "hypo", 1, 0
    return "euthyroid", 0, 0


def classify_thyroid_status(df: pd.DataFrame) -> pd.DataFrame:
    """Add `thyroid_status`, `hypo_grade`, `hyper_grade` columns to a trajectory.

    Expects columns TSH, T4, T3. Returns the same DataFrame with the three columns
    added (in place-safe: operates on a copy's columns and assigns back).
    """
    statuses, hypo_grades, hyper_grades = [], [], []
    for TSH, T4, T3 in zip(df["TSH"].to_numpy(), df["T4"].to_numpy(), df["T3"].to_numpy()):
        st, hypo, hyper = _classify_scalar(float(TSH), float(T4), float(T3))
        statuses.append(st)
        hypo_grades.append(hypo)
        hyper_grades.append(hyper)
    out = df.copy()
    out["thyroid_status"] = statuses
    out["hypo_grade"] = hypo_grades
    out["hyper_grade"] = hyper_grades
    return out
