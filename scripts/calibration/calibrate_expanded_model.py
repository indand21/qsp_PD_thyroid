#!/usr/bin/env python3
"""
v1 calibration — verify the expanded model against literature targets & report.

Calibration of the expanded model was performed by staged tuning of documented
levers (in `qsp_expanded/parameters.py` and `qsp_expanded/population.py`):

  * onset timing  -> minimum_exposure_days, damage_ramp_time, damage_rate
  * sub-threshold plateau (decouples incidence from onset) -> k_damage_repair
  * incidence level -> bimodal susceptibility mixture (population.HIGHRISK_FRACTION,
    MEDIAN_HIGH/LOW) representing a high-risk (HLA / autoantibody-predisposed)
    subpopulation
  * per-drug spread -> DRUG_PK potency / EC50_occ
  * CTLA-4-mono vs combination balance -> w_ctla4_eff (low) + treg_synergy (high,
    super-additive PD-1 + CTLA-4 synergy)

This script re-evaluates the CURRENT (calibrated) model over a population per
drug/regimen, compares 180-day hypothyroidism incidence to literature targets,
checks class ordering and onset timing, and writes a calibration report.

Outputs (results/v1/):
  calibration_report.json

Numbers are model outputs; the cohorts elsewhere in the pipeline remain
risk-enriched by design (see cohort docstrings).
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

import v1_common as vc
from qsp_expanded import run_expanded_population, drug_class_of, DRUG_PK, ExpandedParameters
from qsp_expanded import population as pop

# 180-day hypothyroidism incidence targets (this repo's manuscript + v1).
TARGETS = {
    "nivolumab": (9.0, 6, 12), "pembrolizumab": (8.5, 5, 11),
    "atezolizumab": (7.2, 4, 10), "durvalumab": (6.8, 3, 9),
    "ipilimumab": (4.0, 2, 7), "nivolumab_ipilimumab": (16.0, 12, 21),
}
CLASS_ORDER = ["CTLA-4", "PD-L1", "PD-1", "Combination"]  # ascending expected incidence


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 calibration — verify against literature targets")
    n = max(cfg["population"]["n_per_drug"], 300)  # larger n -> lower incidence-estimate variance
    treatments = list(TARGETS.keys())

    rows, class_inc = [], {}
    for i, drug in enumerate(treatments):
        print(f"  simulating {drug} (n={n}) ...")
        out = run_expanded_population(drug, n, rng=vc.rng(cfg, offset=900 + i), t_span=(0.0, 180.0))
        hypo = 100 * out["any_hypothyroidism"].mean()
        hyper = 100 * out["any_hyperthyroidism"].mean()
        onset = out.loc[out["hypo_onset_days"].notna(), "hypo_onset_days"]
        onset_med = float(onset.median()) if len(onset) else float("nan")
        tgt, lo, hi = TARGETS[drug]
        in_range = lo <= hypo <= hi
        cls = drug_class_of(drug)
        class_inc.setdefault(cls, []).append(hypo)
        rows.append({"drug": drug, "class": cls, "hypo_pct": round(hypo, 1),
                     "target_pct": tgt, "accept_range": [lo, hi], "in_range": bool(in_range),
                     "hyper_pct": round(hyper, 1), "onset_median_days": round(onset_med, 0)})
        flag = "OK " if in_range else "OUT"
        print(f"    [{flag}] {drug}: hypo={hypo:.1f}% (target {tgt}, [{lo},{hi}]), "
              f"hyper={hyper:.1f}%, onset={onset_med:.0f}d")

    class_means = {c: round(float(np.mean(v)), 1) for c, v in class_inc.items()}
    ordering_ok = all(class_means.get(CLASS_ORDER[k], 0) <= class_means.get(CLASS_ORDER[k + 1], 0)
                      for k in range(len(CLASS_ORDER) - 1))
    onsets = [r["onset_median_days"] for r in rows if not np.isnan(r["onset_median_days"])]

    report = {
        "horizon_days": 180, "n_per_drug": n,
        "calibrated_parameters": {
            "susceptibility_mixture": {
                "highrisk_fraction": pop.HIGHRISK_FRACTION, "median_high": pop.MEDIAN_HIGH,
                "median_low": pop.MEDIAN_LOW, "sigma": pop.SIGMA},
            "onset": {k: getattr(ExpandedParameters(), k)
                      for k in ("minimum_exposure_days", "damage_ramp_time", "damage_rate", "k_damage_repair")},
            "ctla4_combo": {k: getattr(ExpandedParameters(), k) for k in ("w_ctla4_eff", "treg_synergy")},
            "drug_potency": {d: DRUG_PK[d]["potency"] for d in DRUG_PK},
        },
        "per_drug": rows,
        "class_mean_incidence_pct": class_means,
        "class_ordering_ok": bool(ordering_ok),
        "all_in_range": bool(all(r["in_range"] for r in rows)),
        "onset_all_within_60_140d": bool(all(60 <= o <= 140 for o in onsets)),
    }
    out_dir = vc.output_dir(cfg)
    vc.write_json(out_dir / "calibration_report.json", report)

    vc.banner("Calibration summary")
    print(f"  all drugs in target range: {report['all_in_range']}")
    print(f"  class ordering (CTLA-4<=PD-L1<=PD-1<=Combination): {ordering_ok}  {class_means}")
    print(f"  onset medians within 60-140d: {report['onset_all_within_60_140d']}")
    print(f"  wrote calibration_report.json to {out_dir}")


if __name__ == "__main__":
    main()
