#!/usr/bin/env python3
"""
v1 Phase 2 — Incidence by drug & class, with risk-hierarchy statistics.

Simulates a population for every drug/regimen defined in the expanded model,
aggregates hypothyroidism / hyperthyroidism / biphasic incidence by drug and by
mechanistic class (PD-1, PD-L1, CTLA-4, Combination), and computes:
  * binomial (Wilson) confidence intervals per rate,
  * a chi-square test of hypothyroidism incidence across classes,
  * relative risk (PD-1 vs PD-L1) for hypo- and hyperthyroidism with 95% CI.

Per-drug and per-class median hypothyroid onset (days) are emitted alongside the
rates (onset_median_days column, on the hypothyroidism row) so that incidence and
onset are reported from the SAME simulated draw.

Outputs (results/v1/):
  incidence_by_drug.csv, incidence_by_class.csv, class_risk_stats.json

Numbers are SYNTHETIC/in-silico (see results/v1/README.md).
"""
from __future__ import annotations

import os
import sys

# --- path shim: make repo root and scripts/ importable when run from anywhere ---
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint

import v1_common as vc
from qsp_expanded import run_expanded_population, drug_class_of


def _rate_row(label: str, kind: str, successes: int, n: int) -> dict:
    p = successes / n if n else 0.0
    lo, hi = proportion_confint(successes, n, alpha=0.05, method="wilson") if n else (0.0, 0.0)
    return {"group": label, "kind": kind, "n": n, "events": int(successes),
            "rate_pct": round(100 * p, 2), "ci_low_pct": round(100 * lo, 2),
            "ci_high_pct": round(100 * hi, 2)}


def _median_hypo_onset(frame) -> float | None:
    """Median day of hypothyroid onset among affected patients in one draw.

    Matches the calibration script's definition (median of non-NaN
    hypo_onset_days) so incidence and onset are reported from the SAME
    simulated population, rather than stitched across two pipeline stages.
    """
    if "hypo_onset_days" not in getattr(frame, "columns", []):
        return None
    onset = frame.loc[frame["hypo_onset_days"].notna(), "hypo_onset_days"]
    return round(float(onset.median()), 0) if len(onset) else None


def _relative_risk(a: int, na: int, b: int, nb: int) -> dict:
    """RR of group A vs group B with 95% CI (log method)."""
    pa = a / na if na else 0.0
    pb = b / nb if nb else 0.0
    if pa == 0 or pb == 0:
        rr = float("nan") if pb == 0 else pa / pb
        return {"rr": None if np.isnan(rr) else round(rr, 3), "ci_low": None, "ci_high": None,
                "note": "RR undefined/unstable (zero events in a group)"}
    rr = pa / pb
    se_log = np.sqrt((1 - pa) / a + (1 - pb) / b)
    lo = np.exp(np.log(rr) - 1.96 * se_log)
    hi = np.exp(np.log(rr) + 1.96 * se_log)
    return {"rr": round(rr, 3), "ci_low": round(lo, 3), "ci_high": round(hi, 3)}


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 2 — Incidence by drug & class")
    n = cfg["population"]["n_per_drug"]
    t_span = (0.0, float(cfg["population"]["t_span_days"]))
    treatments = cfg["population"]["drugs"] + cfg["population"]["regimens"]

    # --- Simulate each drug/regimen population ---
    per_patient = {}
    drug_rows = []
    for i, drug in enumerate(treatments):
        print(f"  simulating {drug} (n={n}) ...")
        out = run_expanded_population(drug, n, rng=vc.rng(cfg, offset=i), t_span=t_span)
        per_patient[drug] = out
        onset_med = _median_hypo_onset(out)
        for kind, col in [("hypothyroidism", "any_hypothyroidism"),
                          ("grade2_hypothyroidism", "grade2plus_hypothyroidism"),
                          ("hyperthyroidism", "any_hyperthyroidism"),
                          ("biphasic", "biphasic")]:
            row = {"drug": drug, "drug_class": drug_class_of(drug),
                   **_rate_row(drug, kind, int(out[col].sum()), len(out))}
            if kind == "hypothyroidism":
                row["onset_median_days"] = onset_med
            drug_rows.append(row)
    drug_df = pd.DataFrame(drug_rows)

    # --- Aggregate by class ---
    classes = cfg["population"]["drug_classes"]
    class_rows = []
    class_pooled = {}  # class -> combined per-patient frame
    for cls, members in classes.items():
        frames = [per_patient[d] for d in members if d in per_patient]
        pooled = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        class_pooled[cls] = pooled
        onset_med_cls = _median_hypo_onset(pooled)
        for kind, col in [("hypothyroidism", "any_hypothyroidism"),
                          ("hyperthyroidism", "any_hyperthyroidism"),
                          ("biphasic", "biphasic")]:
            row = _rate_row(cls, kind, int(pooled[col].sum()), len(pooled))
            if kind == "hypothyroidism":
                row["onset_median_days"] = onset_med_cls
            class_rows.append(row)
    class_df = pd.DataFrame(class_rows)

    # --- Risk-hierarchy statistics ---
    # Chi-square: class x hypothyroidism(yes/no)
    ct = []
    ct_labels = []
    for cls, pooled in class_pooled.items():
        if len(pooled):
            yes = int(pooled["any_hypothyroidism"].sum())
            ct.append([yes, len(pooled) - yes])
            ct_labels.append(cls)
    chi2, p_chi2, dof, _ = stats.chi2_contingency(np.array(ct)) if len(ct) >= 2 else (np.nan, np.nan, 0, None)

    pd1, pdl1 = class_pooled.get("PD-1", pd.DataFrame()), class_pooled.get("PD-L1", pd.DataFrame())
    rr_hypo = _relative_risk(int(pd1["any_hypothyroidism"].sum()), len(pd1),
                             int(pdl1["any_hypothyroidism"].sum()), len(pdl1)) if len(pd1) and len(pdl1) else {}
    rr_hyper = _relative_risk(int(pd1["any_hyperthyroidism"].sum()), len(pd1),
                              int(pdl1["any_hyperthyroidism"].sum()), len(pdl1)) if len(pd1) and len(pdl1) else {}

    stats_payload = {
        "n_per_drug": n,
        "chi2_hypothyroidism_across_classes": {
            "classes": ct_labels, "chi2": round(float(chi2), 3) if np.isfinite(chi2) else None,
            "dof": int(dof), "p_value": float(p_chi2) if np.isfinite(p_chi2) else None,
        },
        "relative_risk_PD1_vs_PDL1": {"hypothyroidism": rr_hypo, "hyperthyroidism": rr_hyper},
    }

    # --- Write outputs ---
    out_dir = vc.output_dir(cfg)
    vc.write_csv(out_dir / "incidence_by_drug.csv", drug_df)
    vc.write_csv(out_dir / "incidence_by_class.csv", class_df)
    vc.write_json(out_dir / "class_risk_stats.json", stats_payload)

    # --- Console summary ---
    print("\nHypothyroidism incidence by drug:")
    for _, r in drug_df[drug_df.kind == "hypothyroidism"].iterrows():
        print(f"  {r['drug']:<22s} {r['rate_pct']:5.1f}%  [{r['ci_low_pct']:.1f}, {r['ci_high_pct']:.1f}]")
    print("\nBy class (hypothyroidism):")
    for _, r in class_df[class_df.kind == "hypothyroidism"].iterrows():
        print(f"  {r['group']:<12s} {r['rate_pct']:5.1f}%  [{r['ci_low_pct']:.1f}, {r['ci_high_pct']:.1f}]")
    print(f"\nChi-square across classes: chi2={stats_payload['chi2_hypothyroidism_across_classes']['chi2']}, "
          f"p={stats_payload['chi2_hypothyroidism_across_classes']['p_value']}")
    print(f"RR PD-1 vs PD-L1 (hypo): {rr_hypo}")
    print(f"\nWrote incidence_by_drug.csv, incidence_by_class.csv, class_risk_stats.json to {out_dir}")


if __name__ == "__main__":
    main()
