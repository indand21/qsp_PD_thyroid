"""
Simulation entry points for the expanded model.

Public API:
    simulate_expanded_patient(...)  -> per-patient trajectory DataFrame
    expanded_risk_score(...)        -> per-patient scalar risk/outcome dict
    run_expanded_population(...)     -> per-patient outcome DataFrame
"""
from __future__ import annotations

import copy
from dataclasses import replace
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from .parameters import ExpandedParameters, STATE_NAMES, resolve_regimen, drug_class_of
from .ode_system import rhs, initial_conditions, drug_concentration
from .classification import classify_thyroid_status


def simulate_expanded_patient(
    drug: str = "nivolumab",
    params: Optional[ExpandedParameters] = None,
    t_span: tuple[float, float] = (0.0, 180.0),
    n_points: int = 181,
    patient_id: str = "VP0001",
) -> pd.DataFrame:
    """Simulate one patient and return a trajectory DataFrame.

    Columns: time, the 19 state variables, drug_conc (summed ng/mL), and the
    classification columns (thyroid_status, hypo_grade, hyper_grade).
    """
    p = params or ExpandedParameters()
    drugs = resolve_regimen(drug)
    y0 = initial_conditions(p)
    t_eval = np.linspace(t_span[0], t_span[1], n_points)

    sol = solve_ivp(
        fun=lambda t, y: rhs(t, y, p, drugs),
        t_span=t_span,
        y0=y0,
        method="LSODA",
        t_eval=t_eval,
        rtol=1e-6,
        atol=1e-9,
        max_step=1.0,
    )
    if not sol.success:
        # Fallback: looser tolerances / smaller step
        sol = solve_ivp(
            fun=lambda t, y: rhs(t, y, p, drugs),
            t_span=t_span,
            y0=y0,
            method="LSODA",
            t_eval=t_eval,
            rtol=1e-4,
            atol=1e-7,
            max_step=0.5,
        )

    df = pd.DataFrame(sol.y.T, columns=STATE_NAMES)
    df.insert(0, "time", sol.t)
    df["patient_id"] = patient_id
    df["drug"] = drug
    df["drug_class"] = drug_class_of(drug)
    df["drug_conc"] = [sum(drug_concentration(t, d) for d in drugs) for t in sol.t]
    df = classify_thyroid_status(df)
    return df


def expanded_risk_score(df: pd.DataFrame) -> Dict[str, object]:
    """Reduce a trajectory to scalar per-patient outcomes.

    Detects the biphasic pattern: a hyperthyroid (thyrotoxic) phase and/or a
    subsequent hypothyroid phase, with onset times for each.
    """
    time = df["time"].to_numpy()

    hypo_mask = df["hypo_grade"].to_numpy() > 0
    hyper_mask = df["hyper_grade"].to_numpy() > 0

    any_hypo = bool(hypo_mask.any())
    any_hyper = bool(hyper_mask.any())
    grade2plus = bool((df["hypo_grade"].to_numpy() >= 2).any())

    hypo_onset = float(time[hypo_mask][0]) if any_hypo else np.nan
    hyper_onset = float(time[hyper_mask][0]) if any_hyper else np.nan

    # Biphasic = a hyper phase that precedes a hypo phase.
    biphasic = bool(any_hyper and any_hypo and hyper_onset < hypo_onset)

    return {
        "patient_id": df["patient_id"].iloc[0],
        "drug": df["drug"].iloc[0],
        "drug_class": df["drug_class"].iloc[0],
        "any_hypothyroidism": any_hypo,
        "grade2plus_hypothyroidism": grade2plus,
        "any_hyperthyroidism": any_hyper,
        "biphasic": biphasic,
        "hypo_onset_days": hypo_onset,
        "hyper_onset_days": hyper_onset,
        "peak_TSH": float(df["TSH"].max()),
        "min_T4": float(df["T4"].min()),
        "peak_T4": float(df["T4"].max()),
        "min_T3": float(df["T3"].min()),
        "peak_IFN": float(df["IFN"].max()),
        "peak_TPOAb": float(df["TPOAb"].max()),
        "peak_TgAb": float(df["TgAb"].max()),
        "final_thyro": float(df["Thyro"].iloc[-1]),
    }


def run_expanded_population(
    drug: str,
    n_patients: int,
    param_overrides: Optional[List[Dict[str, float]]] = None,
    base_params: Optional[ExpandedParameters] = None,
    t_span: tuple[float, float] = (0.0, 180.0),
    rng: Optional[np.random.Generator] = None,
    susceptibility_draws: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    """Simulate a population and return one outcome row per patient.

    Per-patient parameters come from `param_overrides` (a list of dicts applied on
    top of `base_params`) when provided; otherwise a susceptibility factor is drawn
    (from `susceptibility_draws` or U[0.5, 2.0]).
    """
    base = base_params or ExpandedParameters()
    rng = rng or np.random.default_rng(0)
    if susceptibility_draws is None:
        from .population import sample_susceptibility
        susceptibility_draws = sample_susceptibility(n_patients, rng)

    rows = []
    for i in range(n_patients):
        if param_overrides is not None:
            p = replace(base, **param_overrides[i])
        else:
            p = replace(base, susceptibility=float(susceptibility_draws[i]))
        df = simulate_expanded_patient(
            drug=drug, params=p, t_span=t_span, patient_id=f"{drug}_{i:04d}"
        )
        rows.append(expanded_risk_score(df))
    return pd.DataFrame(rows)
