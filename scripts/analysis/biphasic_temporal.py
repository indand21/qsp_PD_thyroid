#!/usr/bin/env python3
"""
v1 Phase 3a — Biphasic / temporal dynamics.

Simulates trajectories per drug, and for patients who develop thyroid
dysfunction characterizes the biphasic course: thyrotoxic (hyper) onset,
hypothyroid onset, the transition gap between phases, the fraction of
dysfunction cases that are biphasic, and the peak-timing windows for each phase.
Aggregated by mechanistic class.

Outputs (results/v1/):
  biphasic_temporal_by_class.csv, biphasic_temporal.json

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

import v1_common as vc
from qsp_expanded import simulate_expanded_patient, expanded_risk_score, ExpandedParameters
from qsp_expanded.population import sample_susceptibility
from dataclasses import replace


def _days_to_weeks(d):
    return None if d is None or (isinstance(d, float) and np.isnan(d)) else round(d / 7.0, 1)


def _summ(arr):
    a = np.array([x for x in arr if x is not None and np.isfinite(x)], dtype=float)
    if a.size == 0:
        return {"n": 0, "median": None, "q1": None, "q3": None}
    return {"n": int(a.size), "median": round(float(np.median(a)), 1),
            "q1": round(float(np.percentile(a, 25)), 1),
            "q3": round(float(np.percentile(a, 75)), 1)}


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 3a — Biphasic / temporal dynamics")
    # Trajectory analysis is heavier; use a bounded per-drug n.
    n = cfg["population"]["n_per_drug"]
    t_span = (0.0, float(cfg["population"]["t_span_days"]))
    treatments = cfg["population"]["drugs"] + cfg["population"]["regimens"]
    classes = cfg["population"]["drug_classes"]

    # drug -> list of per-patient temporal records (dysfunction cases only)
    records = {d: [] for d in treatments}
    for i, drug in enumerate(treatments):
        print(f"  simulating {drug} (n={n}) ...")
        rng = vc.rng(cfg, offset=100 + i)
        susc = sample_susceptibility(n, rng)
        for j in range(n):
            p = replace(ExpandedParameters(), susceptibility=float(susc[j]))
            df = simulate_expanded_patient(drug, p, t_span=t_span, patient_id=f"{drug}_{j:04d}")
            r = expanded_risk_score(df)
            if not (r["any_hypothyroidism"] or r["any_hyperthyroidism"]):
                continue
            # peak-timing windows
            hyper_peak_day = float(df.loc[df["hyper_grade"].idxmax(), "time"]) if r["any_hyperthyroidism"] else None
            hypo_peak_day = float(df.loc[df["TSH"].idxmax(), "time"]) if r["any_hypothyroidism"] else None
            gap = (r["hypo_onset_days"] - r["hyper_onset_days"]) if r["biphasic"] else None
            records[drug].append({
                "hyper_onset": r["hyper_onset_days"] if r["any_hyperthyroidism"] else None,
                "hypo_onset": r["hypo_onset_days"] if r["any_hypothyroidism"] else None,
                "hyper_peak": hyper_peak_day, "hypo_peak": hypo_peak_day,
                "transition_gap": gap, "biphasic": bool(r["biphasic"]),
            })

    # --- Aggregate by class ---
    payload = {"n_simulated_per_drug": n, "by_class": {}}
    rows = []
    for cls, members in classes.items():
        recs = [rr for d in members for rr in records.get(d, [])]
        if not recs:
            continue
        n_dys = len(recs)
        n_bip = sum(r["biphasic"] for r in recs)
        cls_summary = {
            "n_dysfunction": n_dys,
            "pct_biphasic": round(100 * n_bip / n_dys, 1) if n_dys else None,
            "hyper_onset_weeks": {k: _days_to_weeks(v) if k != "n" else v
                                  for k, v in _summ([r["hyper_onset"] for r in recs]).items()},
            "hypo_onset_weeks": {k: _days_to_weeks(v) if k != "n" else v
                                 for k, v in _summ([r["hypo_onset"] for r in recs]).items()},
            "hyper_peak_weeks": {k: _days_to_weeks(v) if k != "n" else v
                                 for k, v in _summ([r["hyper_peak"] for r in recs]).items()},
            "hypo_peak_weeks": {k: _days_to_weeks(v) if k != "n" else v
                                for k, v in _summ([r["hypo_peak"] for r in recs]).items()},
            "transition_gap_weeks": {k: _days_to_weeks(v) if k != "n" else v
                                     for k, v in _summ([r["transition_gap"] for r in recs]).items()},
        }
        payload["by_class"][cls] = cls_summary
        rows.append({
            "drug_class": cls, "n_dysfunction": n_dys, "pct_biphasic": cls_summary["pct_biphasic"],
            "hyper_onset_wk_median": cls_summary["hyper_onset_weeks"]["median"],
            "hypo_onset_wk_median": cls_summary["hypo_onset_weeks"]["median"],
            "hyper_peak_wk_median": cls_summary["hyper_peak_weeks"]["median"],
            "hypo_peak_wk_median": cls_summary["hypo_peak_weeks"]["median"],
            "transition_gap_wk_median": cls_summary["transition_gap_weeks"]["median"],
        })

    out_dir = vc.output_dir(cfg)
    vc.write_csv(out_dir / "biphasic_temporal_by_class.csv", pd.DataFrame(rows))
    vc.write_json(out_dir / "biphasic_temporal.json", payload)

    print("\nBiphasic/temporal summary by class (weeks, medians):")
    for _, r in pd.DataFrame(rows).iterrows():
        print(f"  {r['drug_class']:<12s} biphasic={r['pct_biphasic']}%  "
              f"hyper_onset={r['hyper_onset_wk_median']}  hypo_onset={r['hypo_onset_wk_median']}  "
              f"gap={r['transition_gap_wk_median']}")
    print(f"\nWrote biphasic_temporal_by_class.csv, biphasic_temporal.json to {out_dir}")


if __name__ == "__main__":
    main()
