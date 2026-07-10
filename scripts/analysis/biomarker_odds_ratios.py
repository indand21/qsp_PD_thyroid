#!/usr/bin/env python3
"""
v1 Phase 8b — Biomarker odds ratios (logistic regression).

Estimates univariate odds ratios (with 95% CIs) for candidate predictive
biomarkers of thyroid dysfunction, computed on the calibration cohort and
replicated on the external cohort:

  * baseline TPOAb positivity            -> any dysfunction
  * HLA-DQ2/DQ8 genetic risk             -> any dysfunction
  * early (week-6) TSH elevation >4 mU/L -> hypothyroidism
  * early (week-6) TSH suppression <0.4  -> hyperthyroidism

Requires cohort_calibration.csv and cohort_external.csv.

Outputs (results/v1/):
  biomarker_odds_ratios.csv, biomarker_odds_ratios.json

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
import statsmodels.api as sm

warnings.filterwarnings("ignore")

import v1_common as vc

TPOAB_POS_THRESHOLD = 1.5   # baseline TPOAb positivity (model titer units)


def _odds_ratio(df, predictor, outcome_col):
    """Univariate logistic OR of a predictor (binary 0/1 or continuous) for a
    binary outcome. For binary predictors the OR is exposed-vs-unexposed; for
    continuous predictors it is per one-unit (here per-SD, since inputs are
    standardized upstream)."""
    x = predictor.astype(float).to_numpy()
    y = df[outcome_col].astype(float).to_numpy()
    if len(np.unique(x)) < 2 or len(np.unique(y)) < 2:
        return {"or": None, "ci_low": None, "ci_high": None, "p_value": None,
                "note": "insufficient variation"}
    X = sm.add_constant(x)
    try:
        res = sm.Logit(y, X).fit(disp=0)
        beta, ci = res.params[1], res.conf_int()[1]
        # guard against perfect/quasi-separation producing absurd ORs
        if not np.isfinite(beta) or abs(beta) > 20:
            return {"or": None, "ci_low": None, "ci_high": None, "p_value": None,
                    "note": "quasi-complete separation"}
        return {"or": round(float(np.exp(beta)), 3),
                "ci_low": round(float(np.exp(ci[0])), 3),
                "ci_high": round(float(np.exp(ci[1])), 3),
                "p_value": float(res.pvalues[1])}
    except Exception as e:
        return {"or": None, "ci_low": None, "ci_high": None, "p_value": None,
                "note": f"fit failed: {type(e).__name__}"}


def _zscore(s):
    s = s.astype(float)
    sd = s.std(ddof=0)
    return (s - s.mean()) / sd if sd > 0 else s * 0.0


def _predictors(df):
    """Return (name, predictor_series, outcome, kind). Two robust binary
    predictors (baseline TPOAb positivity, HLA risk) and two continuous per-SD
    predictors (baseline IL-17, week-12 TSH) that carry signal without the
    perfect-separation issues of thresholded early-TSH in a late-onset model."""
    return [
        ("baseline_TPOAb_positive", (df["TPOAb_wk0"] >= TPOAB_POS_THRESHOLD).astype(float), "dysfunction", "binary"),
        ("HLA_DQ_risk", (df["hla_risk"] == 1).astype(float), "dysfunction", "binary"),
        ("baseline_IL17_per_SD", _zscore(df["IL17"]), "dysfunction", "continuous(per SD)"),
        ("TSH_wk12_per_SD", _zscore(df["TSH_wk12"]), "hypothyroidism", "continuous(per SD)"),
    ]


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 8b — Biomarker odds ratios")
    out_dir = vc.output_dir(cfg)
    calib_path, ext_path = out_dir / "cohort_calibration.csv", out_dir / "cohort_external.csv"
    if not (calib_path.exists() and ext_path.exists()):
        print("  ERROR: cohort CSVs not found. Run generate_synthetic_cohorts.py first.")
        sys.exit(1)

    calib = pd.read_csv(calib_path, comment="#")
    ext = pd.read_csv(ext_path, comment="#")

    payload, rows = {"tpoab_threshold": TPOAB_POS_THRESHOLD, "predictors": {}}, []
    ext_predictors = {nm: pb for nm, pb, oc, kd in _predictors(ext)}
    for name, pred_c, outcome, kind in _predictors(calib):
        internal = _odds_ratio(calib, pred_c, outcome)
        external = _odds_ratio(ext, ext_predictors[name], outcome)
        payload["predictors"][name] = {"outcome": outcome, "kind": kind,
                                       "internal": internal, "external": external}
        rows.append({"predictor": name, "outcome": outcome, "kind": kind,
                     "internal_OR": internal["or"], "internal_ci": f"[{internal['ci_low']}, {internal['ci_high']}]",
                     "internal_p": internal["p_value"],
                     "external_OR": external["or"], "external_ci": f"[{external['ci_low']}, {external['ci_high']}]"})

    vc.write_csv(out_dir / "biomarker_odds_ratios.csv", pd.DataFrame(rows))
    vc.write_json(out_dir / "biomarker_odds_ratios.json", payload)

    print("\n  Odds ratios (internal | external):")
    for r in rows:
        print(f"  {r['predictor']:<28s} -> {r['outcome']:<16s} "
              f"OR={r['internal_OR']} {r['internal_ci']}  |  OR={r['external_OR']} {r['external_ci']}")
    print(f"\n  Wrote biomarker_odds_ratios.csv, biomarker_odds_ratios.json to {out_dir}")


if __name__ == "__main__":
    main()
