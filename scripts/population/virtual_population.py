#!/usr/bin/env python3
"""
v1 Phase 7 — Virtual patient population (Python NLME-style sampler).

Generates a virtual population from a population model with fixed + random
effects (a Python stand-in for the manuscript's R `nlme` workflow; no R needed):

  * covariate model: age, sex, HLA-DQ2/DQ8, baseline TSH -> typical parameter values
  * between-subject random effects (lognormal, CV from config) on key parameters
    (susceptibility, PD-1 effector activation, thyrocyte death rate)

Each virtual patient is simulated over 12 months; a continuous risk score
(composite dysfunction index) and a binary outcome are recorded. Monte-Carlo
bootstrap gives confidence intervals on population incidence, and patients are
stratified into 3 mechanistic risk tiers.

Outputs (results/v1/):
  virtual_population.csv, virtual_population_summary.json

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

import v1_common as vc
from qsp_expanded import simulate_expanded_patient, expanded_risk_score, ExpandedParameters, drug_class_of

TYPICAL = {"susceptibility_intercept": 0.60, "w_pd1_eff": 15.0, "k_death": 0.06}


def _dysfunction_index(df) -> float:
    loss = 1.0 - float(df["Thyro"].iloc[-1])
    tsh = float(np.clip((df["TSH"].max() - 1.5) / 48.5, 0.0, 1.0))
    return 0.6 * loss + 0.4 * tsh


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 7 — Virtual patient population")
    vp = cfg["virtual_population"]
    n = vp["n_patients"]
    bsv = vp["bsv_cv"]
    treatments = cfg["population"]["drugs"] + cfg["population"]["regimens"]
    weights = np.array([0.24, 0.24, 0.14, 0.14, 0.10, 0.14]); weights /= weights.sum()
    rng = vc.rng(cfg, offset=700)

    rows = []
    for i in range(n):
        # covariate model
        age = float(np.clip(rng.normal(62, 11), 30, 88))
        sex = "F" if rng.random() < 0.45 else "M"
        hla = bool(rng.random() < 0.25)
        base_tsh = float(np.clip(rng.lognormal(np.log(1.6), 0.35), 0.4, 5.0))
        drug = str(rng.choice(treatments, p=weights))

        age_mult = 1.0 + 0.010 * (age - 60.0)
        sex_mult = 1.20 if sex == "F" else 0.90
        hla_mult = 1.50 if hla else 1.0
        # random effects (lognormal BSV)
        eta_susc = float(np.exp(rng.normal(0.0, bsv)))
        eta_wpd1 = float(np.exp(rng.normal(0.0, bsv)))
        eta_kdeath = float(np.exp(rng.normal(0.0, bsv)))

        susceptibility = float(np.clip(
            TYPICAL["susceptibility_intercept"] * age_mult * sex_mult * hla_mult * eta_susc, 0.4, 2.4))
        p = replace(ExpandedParameters(),
                    susceptibility=susceptibility,
                    HLA_factor=1.5 if hla else 1.0,
                    baseline_TPOAb=(2.5 if hla else 0.5),
                    TSH_set=base_tsh,
                    w_pd1_eff=TYPICAL["w_pd1_eff"] * eta_wpd1,
                    k_death=TYPICAL["k_death"] * eta_kdeath)
        df = simulate_expanded_patient(drug, p, t_span=(0.0, 365.0), n_points=366, patient_id=f"VP_{i:04d}")
        r = expanded_risk_score(df)
        rows.append({
            "vp_id": f"VP_{i:04d}", "age": round(age, 1), "sex": sex, "hla_risk": int(hla),
            "baseline_TSH": round(base_tsh, 3), "drug": drug, "drug_class": drug_class_of(drug),
            "peak_TSH": round(float(r["peak_TSH"]), 3),
            "susceptibility": round(susceptibility, 4), "risk_score": round(_dysfunction_index(df), 4),
            "dysfunction": int(r["any_hypothyroidism"] or r["any_hyperthyroidism"]),
            "hyperthyroidism": int(r["any_hyperthyroidism"]),
            "hypo_onset_days": r["hypo_onset_days"],
        })
        if (i + 1) % 50 == 0:
            print(f"    {i+1}/{n}")
    df_vp = pd.DataFrame(rows)

    # --- Monte-Carlo bootstrap CI on incidence ---
    n_mc = vp["n_monte_carlo"]
    boot = rng.choice(df_vp["dysfunction"].to_numpy(), size=(n_mc, len(df_vp)), replace=True).mean(axis=1)
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    # --- 3-tier risk stratification (by risk score) ---
    hi, inter = vp["risk_tiers"]["high"], vp["risk_tiers"]["intermediate"]
    def tier(s):
        return "high" if s >= hi else ("intermediate" if s >= inter else "low")
    df_vp["risk_tier"] = df_vp["risk_score"].apply(tier)
    tier_counts = df_vp["risk_tier"].value_counts(normalize=True).mul(100).round(1).to_dict()
    tier_incidence = df_vp.groupby("risk_tier")["dysfunction"].mean().mul(100).round(1).to_dict()

    onset = df_vp.loc[df_vp["hypo_onset_days"].notna(), "hypo_onset_days"]
    summary = {
        "n_virtual_patients": int(len(df_vp)),
        "n_monte_carlo": int(n_mc),
        "bsv_cv": bsv,
        "overall_dysfunction_pct": round(100 * df_vp.dysfunction.mean(), 1),
        "overall_dysfunction_ci95_pct": [round(100 * ci[0], 1), round(100 * ci[1], 1)],
        "hyperthyroidism_pct": round(100 * df_vp.hyperthyroidism.mean(), 1),
        "median_hypo_onset_days": round(float(onset.median()), 1) if len(onset) else None,
        "risk_tier_distribution_pct": {t: tier_counts.get(t, 0.0) for t in ["high", "intermediate", "low"]},
        "risk_tier_incidence_pct": {t: tier_incidence.get(t, 0.0) for t in ["high", "intermediate", "low"]},
    }

    out_dir = vc.output_dir(cfg)
    vc.write_csv(out_dir / "virtual_population.csv", df_vp)
    vc.write_json(out_dir / "virtual_population_summary.json", summary)

    print(f"\n  Overall 12-mo dysfunction: {summary['overall_dysfunction_pct']}% "
          f"[{summary['overall_dysfunction_ci95_pct'][0]}, {summary['overall_dysfunction_ci95_pct'][1]}]")
    print(f"  Risk-tier distribution: {summary['risk_tier_distribution_pct']}")
    print(f"  Risk-tier incidence:    {summary['risk_tier_incidence_pct']}")
    print(f"  Wrote virtual_population.csv, virtual_population_summary.json to {out_dir}")


if __name__ == "__main__":
    main()
