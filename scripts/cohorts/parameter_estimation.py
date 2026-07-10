#!/usr/bin/env python3
"""
v1 Phase 5b — Parameter estimation (Nelder-Mead) against the calibration cohort.

Calibrates two global expanded-model parameters (damage_rate, k_death) by
minimizing the squared error between model-predicted per-class 12-month
dysfunction incidence and the incidence observed in the synthetic calibration
cohort. Patients are re-simulated using their stored latent susceptibility and
assigned drug. Uses scipy.optimize.minimize(method="Nelder-Mead").

Requires: results/v1/cohort_calibration.csv (from generate_synthetic_cohorts.py).

Outputs (results/v1/):
  parameter_estimation.json

Numbers are SYNTHETIC/in-silico (see results/v1/README.md).
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
from dataclasses import replace
from scipy.optimize import minimize

import v1_common as vc
from qsp_expanded import simulate_expanded_patient, expanded_risk_score, ExpandedParameters

DEFAULTS = {"damage_rate": 3.5e-4, "k_death": 0.06}


def _predicted_incidence(patients, damage_rate, k_death):
    """Per-class predicted dysfunction fraction for the given parameter set."""
    by_class = {}
    for drug_class, susc, drug in patients:
        p = replace(ExpandedParameters(), susceptibility=float(susc),
                    damage_rate=float(damage_rate), k_death=float(k_death))
        df = simulate_expanded_patient(drug, p, t_span=(0.0, 365.0), n_points=120)
        r = expanded_risk_score(df)
        dys = int(r["any_hypothyroidism"] or r["any_hyperthyroidism"])
        by_class.setdefault(drug_class, []).append(dys)
    return {c: float(np.mean(v)) for c, v in by_class.items()}


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 5b — Parameter estimation (Nelder-Mead)")
    out_dir = vc.output_dir(cfg)
    calib_path = out_dir / "cohort_calibration.csv"
    if not calib_path.exists():
        print(f"  ERROR: {calib_path} not found. Run generate_synthetic_cohorts.py first.")
        sys.exit(1)

    calib = pd.read_csv(calib_path, comment="#")
    # Observed per-class incidence (targets)
    observed = calib.groupby("drug_class")["dysfunction"].mean().to_dict()

    # Subsample for tractable optimization
    n_fit = min(24, len(calib))
    fit = calib.sample(n=n_fit, random_state=int(cfg["seed"]))
    patients = list(zip(fit["drug_class"], fit["latent_susceptibility"], fit["drug"]))
    classes = sorted(observed.keys())

    n_eval = {"count": 0}

    def objective(theta):
        damage_rate, k_death = theta
        # keep within physiological positive bounds
        if damage_rate <= 0 or k_death <= 0:
            return 1e6
        pred = _predicted_incidence(patients, damage_rate, k_death)
        sse = sum((pred.get(c, 0.0) - observed.get(c, 0.0)) ** 2 for c in classes)
        n_eval["count"] += 1
        print(f"    eval {n_eval['count']}: damage_rate={damage_rate:.2e} k_death={k_death:.4f} SSE={sse:.4f}")
        return sse

    x0 = np.array([DEFAULTS["damage_rate"], DEFAULTS["k_death"]])
    print(f"  Fitting on {n_fit} patients; targets (observed per-class incidence): "
          f"{ {c: round(observed[c],3) for c in classes} }")
    res = minimize(objective, x0, method="Nelder-Mead",
                   options={"maxiter": 10, "xatol": 1e-6, "fatol": 1e-4,
                            "initial_simplex": np.array([x0, x0 * [1.4, 1.0], x0 * [1.0, 1.4]])})

    fitted = {"damage_rate": float(res.x[0]), "k_death": float(res.x[1])}
    pred_final = _predicted_incidence(patients, *res.x)

    payload = {
        "method": "Nelder-Mead",
        "n_fit_patients": n_fit,
        "parameters_estimated": ["damage_rate", "k_death"],
        "initial_values": DEFAULTS,
        "fitted_values": fitted,
        "final_sse": float(res.fun),
        "n_evaluations": int(n_eval["count"]),
        "converged": bool(res.success),
        "observed_incidence_by_class": {c: round(observed[c], 4) for c in classes},
        "predicted_incidence_by_class": {c: round(pred_final.get(c, 0.0), 4) for c in classes},
    }
    vc.write_json(out_dir / "parameter_estimation.json", payload)

    print(f"\n  Fitted: damage_rate={fitted['damage_rate']:.3e}, k_death={fitted['k_death']:.4f}")
    print(f"  Final SSE={res.fun:.4f} in {n_eval['count']} evals (converged={res.success})")
    print(f"  Wrote parameter_estimation.json to {out_dir}")


if __name__ == "__main__":
    main()
