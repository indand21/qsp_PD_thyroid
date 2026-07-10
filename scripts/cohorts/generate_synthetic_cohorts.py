#!/usr/bin/env python3
"""
v1 Phase 5a — Synthetic (in-silico) patient cohorts.

Builds labelled SYNTHETIC cohorts by (1) sampling patient covariates (age, sex,
HLA-DQ2/DQ8 risk, baseline TSH, cancer type, assigned drug/regimen), (2) mapping
those covariates onto expanded-model parameters, (3) simulating each patient over
12 months, and (4) recording serial thyroid biomarkers (TSH, fT4, fT3, TPOAb,
TgAb) with measurement noise, a baseline serum cytokine panel (IL-16, IL-12p70,
IL-17, CCL-15, IL-1a), and the thyroid-dysfunction outcome.

Two cohorts are produced: a calibration cohort and an independent external cohort
whose "centers" are distinct covariate strata (there is no real multi-center data).

NOTE: cohort membership is COVARIATE-SAMPLED — each patient's susceptibility is
derived from their risk factors (age, sex, HLA-DQ, baseline TSH) plus a random
effect, so the resulting 12-month event rate (~12-19%) is modestly higher than
the marginal calibrated population incidence and is driven by covariate risk
(mild risk enrichment). This gives the ML / validation / odds-ratio stages a
realistic prevalence with enough positive cases to fit. See results/v1/README.md.

THIS IS NOT REAL PATIENT DATA. Every row is model-generated. See results/v1/README.md.

Outputs (results/v1/):
  cohort_calibration.csv, cohort_external.csv, cohorts_summary.json
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

CANCER_TYPES = ["melanoma", "NSCLC", "RCC", "urothelial", "HNSCC"]
CYTOKINES = ["IL16", "IL12p70", "IL17", "CCL15", "IL1a"]
CYTOKINE_BASE = {"IL16": 120.0, "IL12p70": 2.5, "IL17": 8.0, "CCL15": 3000.0, "IL1a": 1.2}


def _covariate_to_params(age, sex, hla_pos, base_tsh, rng):
    """Map covariates -> ExpandedParameters (with a lognormal random effect)."""
    age_mult = 1.0 + 0.010 * (age - 60.0)          # older -> higher susceptibility
    sex_mult = 1.20 if sex == "F" else 0.90         # female predominance in thyroid autoimmunity
    hla_mult = 1.50 if hla_pos else 1.0
    random_effect = float(np.exp(rng.normal(0.0, 0.20)))
    # Intercept 0.60 targets a balanced ~50% 12-month dysfunction rate across the
    # assigned-drug mix (both outcome classes well-represented for ML/odds-ratios).
    susceptibility = float(np.clip(0.60 * age_mult * sex_mult * hla_mult * random_effect, 0.4, 2.2))
    baseline_TPOAb = float(max(0.0, (2.5 if hla_pos else 0.5) + rng.normal(0.0, 0.5)))
    p = replace(
        ExpandedParameters(),
        susceptibility=susceptibility,
        baseline_TPOAb=baseline_TPOAb,
        HLA_factor=1.5 if hla_pos else 1.0,
        sex_factor=sex_mult,
        age_factor=age_mult,
        TSH_set=float(base_tsh),
    )
    return p, susceptibility


def _sample_biomarkers(df, visit_weeks, noise_cv, rng):
    """Interpolate serial biomarkers at visit weeks and apply lognormal noise."""
    t = df["time"].to_numpy()
    out = {}
    for wk in visit_weeks:
        day = min(wk * 7.0, t[-1])
        for col, tag in [("TSH", "TSH"), ("T4", "fT4"), ("T3", "fT3"), ("TPOAb", "TPOAb"), ("TgAb", "TgAb")]:
            val = float(np.interp(day, t, df[col].to_numpy()))
            val *= float(np.exp(rng.normal(0.0, noise_cv)))  # measurement noise
            out[f"{tag}_wk{wk}"] = round(val, 4)
    return out


def _baseline_cytokines(susceptibility, rng):
    """Baseline serum cytokine panel, shifted upward with susceptibility + noise."""
    out = {}
    shift = 0.35 * (susceptibility - 1.0)
    for ck in CYTOKINES:
        mu = np.log(CYTOKINE_BASE[ck]) + shift
        out[ck] = round(float(np.exp(rng.normal(mu, 0.30))), 4)
    return out


def _build_cohort(name, n, treatments, drug_weights, center_labels, cfg, rng):
    visit_weeks = cfg["cohorts"]["visit_weeks"]
    noise_cv = cfg["cohorts"]["measurement_noise_cv"]
    t_span = (0.0, 365.0)  # 12-month follow-up
    rows = []
    for i in range(n):
        center = center_labels[i % len(center_labels)] if center_labels else "single"
        age = float(np.clip(rng.normal(62, 11), 30, 88))
        sex = "F" if rng.random() < 0.45 else "M"
        hla_pos = bool(rng.random() < 0.25)
        base_tsh = float(np.clip(rng.lognormal(np.log(1.6), 0.35), 0.4, 5.0))
        cancer = CANCER_TYPES[int(rng.integers(len(CANCER_TYPES)))]
        drug = str(rng.choice(treatments, p=drug_weights))

        p, susc = _covariate_to_params(age, sex, hla_pos, base_tsh, rng)
        df = simulate_expanded_patient(drug, p, t_span=t_span, n_points=366, patient_id=f"{name}_{i:04d}")
        r = expanded_risk_score(df)

        row = {
            "patient_id": f"{name}_{i:04d}", "center": center, "age": round(age, 1), "sex": sex,
            "hla_risk": int(hla_pos), "cancer_type": cancer, "drug": drug, "drug_class": drug_class_of(drug),
            "baseline_TSH": round(base_tsh, 3), "latent_susceptibility": round(susc, 4),
        }
        row.update(_baseline_cytokines(susc, rng))
        row.update(_sample_biomarkers(df, visit_weeks, noise_cv, rng))
        # Outcomes
        row["dysfunction"] = int(r["any_hypothyroidism"] or r["any_hyperthyroidism"])
        row["hypothyroidism"] = int(r["any_hypothyroidism"])
        row["hyperthyroidism"] = int(r["any_hyperthyroidism"])
        row["grade2plus"] = int(r["grade2plus_hypothyroidism"])
        row["hypo_onset_days"] = r["hypo_onset_days"]
        rows.append(row)
        if (i + 1) % 50 == 0:
            print(f"    {name}: {i+1}/{n}")
    return pd.DataFrame(rows)


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 5a — Synthetic patient cohorts")
    treatments = cfg["population"]["drugs"] + cfg["population"]["regimens"]
    # Assignment mix (roughly clinical): PD-1 common, combination less so.
    weights = np.array([0.24, 0.24, 0.14, 0.14, 0.10, 0.14])
    weights = weights / weights.sum()

    calib_n = cfg["cohorts"]["calibration_n"]
    ext_n = cfg["cohorts"]["external_n"]
    n_centers = cfg["cohorts"]["external_centers"]

    print(f"  Calibration cohort (n={calib_n}) ...")
    calib = _build_cohort("CAL", calib_n, treatments, weights, None, cfg, vc.rng(cfg, offset=500))

    print(f"  External cohort (n={ext_n}, {n_centers} centers) ...")
    centers = [f"center_{c+1}" for c in range(n_centers)]
    ext = _build_cohort("EXT", ext_n, treatments, weights, centers, cfg, vc.rng(cfg, offset=600))

    out_dir = vc.output_dir(cfg)
    vc.write_csv(out_dir / "cohort_calibration.csv", calib, note="SYNTHETIC calibration cohort")
    vc.write_csv(out_dir / "cohort_external.csv", ext, note="SYNTHETIC external-validation cohort")

    summary = {
        "calibration": {"n": len(calib), "dysfunction_pct": round(100 * calib.dysfunction.mean(), 1),
                        "hypothyroidism_pct": round(100 * calib.hypothyroidism.mean(), 1),
                        "hla_pos_pct": round(100 * calib.hla_risk.mean(), 1),
                        "female_pct": round(100 * (calib.sex == "F").mean(), 1),
                        "mean_age": round(calib.age.mean(), 1)},
        "external": {"n": len(ext), "dysfunction_pct": round(100 * ext.dysfunction.mean(), 1),
                     "hypothyroidism_pct": round(100 * ext.hypothyroidism.mean(), 1),
                     "by_center": {c: round(100 * ext[ext.center == c].dysfunction.mean(), 1)
                                   for c in centers}},
        "cytokine_panel": CYTOKINES, "visit_weeks": cfg["cohorts"]["visit_weeks"],
    }
    vc.write_json(out_dir / "cohorts_summary.json", summary)

    print(f"\n  Calibration: n={len(calib)}, dysfunction={summary['calibration']['dysfunction_pct']}%")
    print(f"  External:    n={len(ext)}, dysfunction={summary['external']['dysfunction_pct']}%")
    print(f"  Wrote cohort_calibration.csv, cohort_external.csv, cohorts_summary.json to {out_dir}")


if __name__ == "__main__":
    main()
