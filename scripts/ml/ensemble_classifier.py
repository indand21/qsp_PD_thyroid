#!/usr/bin/env python3
"""
v1 Phase 8a — Machine-learning ensemble for dysfunction prediction.

Trains a 4-algorithm ensemble (logistic regression, random forest, XGBoost,
LightGBM) on early-phase features (baseline covariates + cytokines + week-6/12
biomarkers) to predict 12-month thyroid dysfunction. XGBoost hyperparameters are
tuned with Optuna (Bayesian TPE) to maximize cross-validated AUC; the ensemble
averages the four calibrated probabilities with equal weight. Evaluated by
repeated stratified CV on the calibration cohort and on the external cohort.

Requires cohort_calibration.csv and cohort_external.csv.

Outputs (results/v1/):
  ml_ensemble_metrics.json

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

import optuna
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import RepeatedStratifiedKFold, cross_val_score, StratifiedKFold
from sklearn.metrics import roc_auc_score, confusion_matrix
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

import v1_common as vc
from cohort_features import build_early_features

optuna.logging.set_verbosity(optuna.logging.WARNING)


def _sens_spec(y, p, thr=0.5):
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(
        sensitivity=round(tp / (tp + fn) if (tp + fn) else 0.0, 3),
        specificity=round(tn / (tn + fp) if (tn + fp) else 0.0, 3),
        ppv=round(tp / (tp + fp) if (tp + fp) else 0.0, 3),
        npv=round(tn / (tn + fn) if (tn + fn) else 0.0, 3),
    )


def _base_models(cfg, xgb_params):
    return {
        "logistic_regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)),
        "random_forest": RandomForestClassifier(
            n_estimators=cfg["ml"]["rf_n_estimators"], max_depth=15, random_state=int(cfg["seed"])),
        "xgboost": XGBClassifier(
            n_estimators=cfg["ml"]["xgb_n_estimators"], eval_metric="logloss",
            random_state=int(cfg["seed"]), **xgb_params),
        "lightgbm": LGBMClassifier(
            n_estimators=cfg["ml"]["lgbm_n_estimators"], learning_rate=0.05,
            random_state=int(cfg["seed"]), verbose=-1),
    }


def _ensemble_proba(models, Xtr, ytr, Xte):
    probas = []
    for mdl in models.values():
        mdl.fit(Xtr, ytr)
        probas.append(mdl.predict_proba(Xte)[:, 1])
    return np.mean(probas, axis=0)


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 8a — ML ensemble")
    out_dir = vc.output_dir(cfg)
    calib_path, ext_path = out_dir / "cohort_calibration.csv", out_dir / "cohort_external.csv"
    if not (calib_path.exists() and ext_path.exists()):
        print("  ERROR: cohort CSVs not found. Run generate_synthetic_cohorts.py first.")
        sys.exit(1)

    calib = pd.read_csv(calib_path, comment="#")
    ext = pd.read_csv(ext_path, comment="#")
    Xc, yc = build_early_features(calib)
    Xe, ye = build_early_features(ext)
    seed = int(cfg["seed"])

    # --- Optuna Bayesian HPO for XGBoost (maximize 5-fold CV AUC) ---
    print(f"  Optuna HPO for XGBoost ({cfg['ml']['hpo_trials']} trials) ...")
    inner_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)

    def objective(trial):
        params = {
            "max_depth": trial.suggest_int("max_depth", 2, 6),
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.3, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        }
        clf = XGBClassifier(n_estimators=cfg["ml"]["xgb_n_estimators"], eval_metric="logloss",
                            random_state=seed, **params)
        return cross_val_score(clf, Xc, yc, cv=inner_cv, scoring="roc_auc").mean()

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=cfg["ml"]["hpo_trials"], show_progress_bar=False)
    best_xgb = study.best_params
    print(f"    best XGB params: {best_xgb} (CV AUC={study.best_value:.3f})")

    # --- Per-model + ensemble repeated-CV AUC on calibration ---
    rkf = RepeatedStratifiedKFold(n_splits=10, n_repeats=cfg["ml"]["cv_repeats"], random_state=seed)
    per_model_auc = {}
    for name, mdl in _base_models(cfg, best_xgb).items():
        per_model_auc[name] = round(float(cross_val_score(mdl, Xc, yc, cv=rkf, scoring="roc_auc").mean()), 3)

    ens_auc = []
    for tr, te in rkf.split(Xc, yc):
        proba = _ensemble_proba(_base_models(cfg, best_xgb), Xc.iloc[tr], yc.iloc[tr], Xc.iloc[te])
        ens_auc.append(roc_auc_score(yc.iloc[te], proba))
    ens_auc = np.array(ens_auc)

    # --- Ensemble trained on full calibration, evaluated on external ---
    ext_proba = _ensemble_proba(_base_models(cfg, best_xgb), Xc, yc, Xe)
    ext_auc = roc_auc_score(ye, ext_proba)
    ext_metrics = _sens_spec(ye.to_numpy(), ext_proba)

    payload = {
        "features": list(Xc.columns),
        "n_calibration": int(len(yc)), "n_external": int(len(ye)),
        "optuna": {"n_trials": cfg["ml"]["hpo_trials"], "best_xgb_params": best_xgb,
                   "best_cv_auc": round(float(study.best_value), 3)},
        "per_model_cv_auc": per_model_auc,
        "ensemble_cv": {"auc_mean": round(float(ens_auc.mean()), 3),
                        "auc_ci95": [round(float(np.percentile(ens_auc, 2.5)), 3),
                                     round(float(np.percentile(ens_auc, 97.5)), 3)],
                        "n_splits": 10, "n_repeats": cfg["ml"]["cv_repeats"]},
        "ensemble_external": {"auc": round(float(ext_auc), 3), **ext_metrics},
    }
    vc.write_json(out_dir / "ml_ensemble_metrics.json", payload)

    print(f"  Per-model CV AUC: {per_model_auc}")
    print(f"  Ensemble CV AUC:  {payload['ensemble_cv']['auc_mean']} {payload['ensemble_cv']['auc_ci95']}")
    print(f"  Ensemble external: AUC={round(float(ext_auc),3)} "
          f"sens={ext_metrics['sensitivity']} spec={ext_metrics['specificity']} "
          f"PPV={ext_metrics['ppv']} NPV={ext_metrics['npv']}")
    print(f"  Wrote ml_ensemble_metrics.json to {out_dir}")


if __name__ == "__main__":
    main()
