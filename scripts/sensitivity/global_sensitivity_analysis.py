#!/usr/bin/env python3
"""
v1 Phase 4 — Global sensitivity analysis (Morris screening + Sobol variance).

Uses SALib to quantify how expanded-model parameters influence thyroid
dysfunction, computed on the ACTUAL mechanistic model (a deterministic
single-patient severity metric: fractional thyrocyte loss for a nivolumab
patient whose susceptibility is itself one of the varied parameters).

  * Morris one-at-a-time screening -> mu_star (importance), sigma (interactions).
  * Sobol variance decomposition -> S1 (first-order), ST (total-order).

Sample sizes come from config/v1_pipeline.yaml (reduced-but-real by default).

Outputs (results/v1/):
  gsa_morris.csv, gsa_sobol.csv, gsa_summary.json

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

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

import v1_common as vc
from qsp_expanded import simulate_expanded_patient, ExpandedParameters
from dataclasses import replace

from SALib.sample import saltelli
from SALib.sample.morris import sample as morris_sample
from SALib.analyze import sobol as sobol_analyze
from SALib.analyze import morris as morris_analyze

# Parameters varied, mapped to the v1 "rate-limiting steps" plus key drivers.
# Each entry: (attribute, default, low_factor, high_factor, label)
PARAM_SPEC = [
    ("w_pd1_eff", 15.0, 0.5, 1.5, "PD-1 effector activation"),
    ("eps_ifn", 20.0, 0.5, 1.5, "IFN-gamma production"),
    ("EC50_IFN_death", 85.0, 0.5, 1.5, "IFN cytotoxic potency (EC50)"),
    ("treg_supp", 1.0, 0.5, 1.5, "Treg suppressive capacity"),
    ("k_death", 0.06, 0.5, 1.5, "Thyrocyte death rate"),
    ("k_tpo_sup", 0.35, 0.5, 1.5, "TPO suppression"),
    ("damage_rate", 3.5e-4, 0.5, 1.5, "Damage accumulation"),
    ("k_conv_T4_T3", 0.05, 0.5, 1.5, "DIO2 T4->T3 conversion"),
    ("k_regen", 0.02, 0.5, 1.5, "Thyroid regeneration"),
    ("susceptibility", 1.25, 0.4, 1.6, "Patient susceptibility"),
]


def _make_problem():
    names = [s[0] for s in PARAM_SPEC]
    bounds = [[s[1] * s[2], s[1] * s[3]] for s in PARAM_SPEC]
    return {"num_vars": len(PARAM_SPEC), "names": names, "bounds": bounds}


def _dysfunction_index(df) -> float:
    """Bounded composite thyroid-dysfunction score in [0, 1].

    Combines thyroid destruction (fractional thyrocyte loss) with hormone
    derangement (peak TSH elevation above setpoint), so that parameters acting
    through the gland (death, damage), through synthesis (TPO), and through the
    HPT axis (DIO2 conversion) all register influence.
    """
    thyrocyte_loss = 1.0 - float(df["Thyro"].iloc[-1])
    tsh_term = float(np.clip((df["TSH"].max() - 1.5) / 48.5, 0.0, 1.0))  # 0 at setpoint, 1 at TSH~50
    return 0.6 * thyrocyte_loss + 0.4 * tsh_term


def _evaluate(param_matrix: np.ndarray) -> np.ndarray:
    """Map each parameter row to the composite dysfunction index."""
    names = [s[0] for s in PARAM_SPEC]
    y = np.empty(param_matrix.shape[0])
    for i, row in enumerate(param_matrix):
        overrides = {name: float(val) for name, val in zip(names, row)}
        p = replace(ExpandedParameters(), **overrides)
        df = simulate_expanded_patient("nivolumab", p, t_span=(0.0, 180.0))
        y[i] = _dysfunction_index(df)
        if (i + 1) % 250 == 0:
            print(f"    evaluated {i+1}/{param_matrix.shape[0]} ...")
    return y


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 4 — Global sensitivity analysis (Morris + Sobol)")
    scfg = cfg["sensitivity"]
    problem = _make_problem()
    labels = {s[0]: s[4] for s in PARAM_SPEC}

    # --- Morris screening ---
    print(f"  Morris: {scfg['n_morris_trajectories']} trajectories, {scfg['morris_levels']} levels")
    Xm = morris_sample(problem, N=scfg["n_morris_trajectories"], num_levels=scfg["morris_levels"])
    print(f"    {Xm.shape[0]} model evaluations ...")
    Ym = _evaluate(Xm)
    Sm = morris_analyze.analyze(problem, Xm, Ym, num_levels=scfg["morris_levels"])
    morris_df = pd.DataFrame({
        "parameter": problem["names"],
        "label": [labels[n] for n in problem["names"]],
        "mu_star": np.round(Sm["mu_star"], 5),
        "sigma": np.round(Sm["sigma"], 5),
    }).sort_values("mu_star", ascending=False)

    # --- Sobol variance decomposition ---
    print(f"  Sobol: base N={scfg['n_sobol_base']}")
    Xs = saltelli.sample(problem, scfg["n_sobol_base"], calc_second_order=False)
    print(f"    {Xs.shape[0]} model evaluations ...")
    Ys = _evaluate(Xs)
    Ss = sobol_analyze.analyze(problem, Ys, calc_second_order=False)
    sobol_df = pd.DataFrame({
        "parameter": problem["names"],
        "label": [labels[n] for n in problem["names"]],
        "S1": np.round(Ss["S1"], 5),
        "ST": np.round(Ss["ST"], 5),
    }).sort_values("ST", ascending=False)

    # --- Summary: variance from the top-4 total-order parameters ---
    top4 = sobol_df.head(4)
    top4_var = float(np.clip(top4["ST"].sum(), 0, None))
    summary = {
        "metric": "composite thyroid-dysfunction index (0.6*thyrocyte_loss + 0.4*TSH_elevation), nivolumab, t=180d",
        "n_morris_evals": int(Xm.shape[0]),
        "n_sobol_evals": int(Xs.shape[0]),
        "top_parameters_by_ST": top4[["parameter", "label", "ST"]].to_dict("records"),
        "sum_ST_top4": round(top4_var, 4),
        "morris_ranking": morris_df[["parameter", "mu_star"]].to_dict("records"),
    }

    out_dir = vc.output_dir(cfg)
    vc.write_csv(out_dir / "gsa_morris.csv", morris_df)
    vc.write_csv(out_dir / "gsa_sobol.csv", sobol_df)
    vc.write_json(out_dir / "gsa_summary.json", summary)

    print("\nMorris ranking (mu_star):")
    for _, r in morris_df.iterrows():
        print(f"  {r['label']:<32s} mu*={r['mu_star']:.4f}  sigma={r['sigma']:.4f}")
    print("\nSobol total-order (ST):")
    for _, r in sobol_df.iterrows():
        print(f"  {r['label']:<32s} S1={r['S1']:.4f}  ST={r['ST']:.4f}")
    print(f"\nTop-4 parameters account for sum(ST)={top4_var:.3f}")
    print(f"Wrote gsa_morris.csv, gsa_sobol.csv, gsa_summary.json to {out_dir}")


if __name__ == "__main__":
    main()
