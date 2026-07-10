#!/usr/bin/env python3
"""
v1 Phase 6 — Internal & external validation + biomarker VPC.

Validates a baseline-feature risk predictor for 12-month thyroid dysfunction:
  * Internal: 70/30 stratified split + 10x repeated stratified CV on the
    calibration cohort (AUC, accuracy, sensitivity, specificity, with CIs).
  * External: apply the calibration-fit predictor to the external cohort
    (sensitivity/specificity/PPV/NPV, AUC, calibration slope & intercept).
  * Biomarker VPC/RMSE: compare observed external-cohort TSH against the model's
    simulated population prediction interval at each visit week (coverage + RMSE).

Requires cohort_calibration.csv and cohort_external.csv.

Outputs (results/v1/):
  validation_internal.json, validation_external.json, validation_vpc.csv

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

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score, confusion_matrix

import v1_common as vc
from cohort_features import build_baseline_features
from qsp_expanded import simulate_expanded_patient, ExpandedParameters
from dataclasses import replace


def _sens_spec_ppv_npv(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    ppv = tp / (tp + fp) if (tp + fp) else 0.0
    npv = tn / (tn + fn) if (tn + fn) else 0.0
    return dict(sensitivity=round(sens, 3), specificity=round(spec, 3),
                ppv=round(ppv, 3), npv=round(npv, 3))


def _model():
    return make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 6 — Internal & external validation")
    out_dir = vc.output_dir(cfg)
    calib_path, ext_path = out_dir / "cohort_calibration.csv", out_dir / "cohort_external.csv"
    if not (calib_path.exists() and ext_path.exists()):
        print("  ERROR: cohort CSVs not found. Run generate_synthetic_cohorts.py first.")
        sys.exit(1)

    calib = pd.read_csv(calib_path, comment="#")
    ext = pd.read_csv(ext_path, comment="#")
    Xc, yc = build_baseline_features(calib)
    Xe, ye = build_baseline_features(ext)

    # --- Internal: 70/30 split ---
    Xtr, Xte, ytr, yte = train_test_split(Xc, yc, test_size=0.30, stratify=yc, random_state=int(cfg["seed"]))
    m = _model().fit(Xtr, ytr)
    proba_te = m.predict_proba(Xte)[:, 1]
    pred_te = (proba_te >= 0.5).astype(int)
    internal_split = {"auc": round(roc_auc_score(yte, proba_te), 3),
                      "accuracy": round(float((pred_te == yte).mean()), 3),
                      **_sens_spec_ppv_npv(yte, pred_te)}

    # --- Internal: 10x repeated stratified CV ---
    rkf = RepeatedStratifiedKFold(n_splits=10, n_repeats=cfg["ml"]["cv_repeats"], random_state=int(cfg["seed"]))
    auc_scores = cross_val_score(_model(), Xc, yc, cv=rkf, scoring="roc_auc")
    acc_scores = cross_val_score(_model(), Xc, yc, cv=rkf, scoring="accuracy")
    internal_cv = {"n_splits": 10, "n_repeats": cfg["ml"]["cv_repeats"],
                   "auc_mean": round(float(auc_scores.mean()), 3),
                   "auc_ci95": [round(float(np.percentile(auc_scores, 2.5)), 3),
                                round(float(np.percentile(auc_scores, 97.5)), 3)],
                   "accuracy_mean": round(float(acc_scores.mean()), 3)}

    vc.write_json(out_dir / "validation_internal.json",
                  {"split_70_30": internal_split, "repeated_cv": internal_cv})

    # --- External validation (fit on full calibration, evaluate on external) ---
    m_full = _model().fit(Xc, yc)
    proba_e = m_full.predict_proba(Xe)[:, 1]
    pred_e = (proba_e >= 0.5).astype(int)
    # calibration slope/intercept: logistic of outcome on the predicted logit
    eps = 1e-6
    logit = np.log(np.clip(proba_e, eps, 1 - eps) / np.clip(1 - proba_e, eps, 1 - eps))
    cal = LogisticRegression(max_iter=2000).fit(logit.reshape(-1, 1), ye)
    external = {"n": int(len(ye)), "auc": round(roc_auc_score(ye, proba_e), 3),
                "accuracy": round(float((pred_e == ye).mean()), 3),
                **_sens_spec_ppv_npv(ye, pred_e),
                "calibration_slope": round(float(cal.coef_[0][0]), 3),
                "calibration_intercept": round(float(cal.intercept_[0]), 3),
                "by_center_auc": {}}
    for c in sorted(ext["center"].dropna().unique()):
        mask = (ext["center"] == c).to_numpy()
        if mask.sum() > 5 and len(np.unique(ye[mask])) == 2:
            external["by_center_auc"][c] = round(roc_auc_score(ye[mask], proba_e[mask]), 3)
    vc.write_json(out_dir / "validation_external.json", external)

    # --- Biomarker VPC/RMSE (TSH) on a sample of external patients ---
    visit_weeks = cfg["cohorts"]["visit_weeks"]
    vpc_sample = ext.sample(n=min(60, len(ext)), random_state=int(cfg["seed"]))
    # Model population prediction interval per visit week (re-simulate patients, no noise)
    sim_tsh = {wk: [] for wk in visit_weeks}
    obs_tsh = {wk: [] for wk in visit_weeks}
    for _, row in vpc_sample.iterrows():
        p = replace(ExpandedParameters(), susceptibility=float(row["latent_susceptibility"]),
                    HLA_factor=1.5 if row["hla_risk"] else 1.0, TSH_set=float(row["baseline_TSH"]))
        df = simulate_expanded_patient(row["drug"], p, t_span=(0.0, 365.0), n_points=366)
        t = df["time"].to_numpy()
        for wk in visit_weeks:
            sim_tsh[wk].append(float(np.interp(min(wk * 7, t[-1]), t, df["TSH"].to_numpy())))
            obs_tsh[wk].append(float(row[f"TSH_wk{wk}"]))
    vpc_rows = []
    for wk in visit_weeks:
        sim = np.array(sim_tsh[wk]); obs = np.array(obs_tsh[wk])
        lo, hi = np.percentile(sim, 5), np.percentile(sim, 95)
        coverage = float(np.mean((obs >= lo) & (obs <= hi)))
        rmse = float(np.sqrt(np.mean((obs - sim) ** 2)))
        vpc_rows.append({"visit_week": wk, "sim_median_TSH": round(float(np.median(sim)), 3),
                         "obs_median_TSH": round(float(np.median(obs)), 3),
                         "pi90_low": round(float(lo), 3), "pi90_high": round(float(hi), 3),
                         "coverage_frac": round(coverage, 3), "rmse": round(rmse, 3)})
    vc.write_csv(out_dir / "validation_vpc.csv", pd.DataFrame(vpc_rows))

    print(f"  Internal 70/30: AUC={internal_split['auc']} acc={internal_split['accuracy']} "
          f"sens={internal_split['sensitivity']} spec={internal_split['specificity']}")
    print(f"  Internal CV:    AUC={internal_cv['auc_mean']} {internal_cv['auc_ci95']}")
    print(f"  External:       AUC={external['auc']} sens={external['sensitivity']} spec={external['specificity']} "
          f"PPV={external['ppv']} NPV={external['npv']} cal_slope={external['calibration_slope']}")
    print(f"  VPC TSH coverage by week: {[ (r['visit_week'], r['coverage_frac']) for r in vpc_rows ]}")
    print(f"  Wrote validation_internal.json, validation_external.json, validation_vpc.csv to {out_dir}")


if __name__ == "__main__":
    main()
