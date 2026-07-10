"""
Expanded QSP model (v1 objectives)
==================================

A single, self-contained mechanistic model that extends the legacy 7-state
`qsp_model_final` core to ~19 states across five physiological modules
(checkpoint pharmacology, T-cell dynamics, cytokine network, thyroid gland &
signaling, HPT axis). It adds the biology the v1 manuscript analyses require but
the legacy model lacks: a biphasic thyrotoxic->hypothyroid trajectory (via a
stored-hormone colloid pool), a multi-cytokine network (IFN-gamma, TNF-alpha,
IL-2, IL-17), regulatory T cells, autoantibody (TPOAb/TgAb) seroconversion, and
distinct CTLA-4 / combination-therapy mechanisms.

This package is ADDITIVE and top-level (not under the legacy `model/` package,
whose `__init__` eagerly imports pre-existingly-broken performance modules): the
legacy `qsp_model_final` path and its tests are untouched, and importing
`qsp_expanded` pulls in nothing from `model/`. The v1 pipeline scripts target
this expanded model.
"""

from .parameters import (
    STATE_NAMES,
    ExpandedParameters,
    DRUG_PK,
    REGIMENS,
    resolve_regimen,
    drug_class_of,
)
from .classification import classify_thyroid_status
from .simulate import (
    simulate_expanded_patient,
    run_expanded_population,
    expanded_risk_score,
)

__all__ = [
    "STATE_NAMES",
    "ExpandedParameters",
    "DRUG_PK",
    "REGIMENS",
    "resolve_regimen",
    "drug_class_of",
    "classify_thyroid_status",
    "simulate_expanded_patient",
    "run_expanded_population",
    "expanded_risk_score",
]
