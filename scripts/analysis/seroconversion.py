#!/usr/bin/env python3
"""
v1 Phase 3b — Autoantibody (TPOAb / TgAb) seroconversion.

A patient "seroconverts" when a previously-negative autoantibody titer rises
above its positivity threshold during treatment. This script simulates
trajectories per drug, detects TPOAb and TgAb seroconversion and its timing, and
aggregates per-class seroconversion rates and temporal kinetics (cumulative
fraction converted by week band).

Outputs (results/v1/):
  seroconversion_by_class.csv, seroconversion_kinetics.csv, seroconversion.json

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
from qsp_expanded import simulate_expanded_patient, ExpandedParameters
from qsp_expanded.population import sample_susceptibility

# Positivity thresholds (titer units in the model's TPOAb/TgAb states), chosen to
# sit within the on-treatment titer distribution so seroconversion is graded
# across drug classes rather than saturating. (Synthetic model units.)
TPOAB_POS = 35.0
TGAB_POS = 20.0
WEEK_BANDS = [(0, 4), (5, 8), (9, 12), (13, 24), (25, 52)]


def _seroconvert_day(series_time, series_titer, threshold, baseline_val):
    """Return day of first crossing above threshold if baseline was negative, else None."""
    if baseline_val >= threshold:
        return None  # already positive at baseline -> not a seroconversion
    above = np.where(series_titer >= threshold)[0]
    return float(series_time[above[0]]) if above.size else None


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 3b — Autoantibody seroconversion")
    n = cfg["population"]["n_per_drug"]
    t_span = (0.0, float(cfg["population"]["t_span_days"]))
    treatments = cfg["population"]["drugs"] + cfg["population"]["regimens"]
    classes = cfg["population"]["drug_classes"]

    records = {d: [] for d in treatments}
    for i, drug in enumerate(treatments):
        print(f"  simulating {drug} (n={n}) ...")
        rng = vc.rng(cfg, offset=200 + i)
        susc = sample_susceptibility(n, rng)
        base_tpo = rng.uniform(0.0, 3.0, n)  # baseline (negative) TPOAb propensity
        for j in range(n):
            p = replace(ExpandedParameters(), susceptibility=float(susc[j]), baseline_TPOAb=float(base_tpo[j]))
            df = simulate_expanded_patient(drug, p, t_span=t_span, patient_id=f"{drug}_{j:04d}")
            t = df["time"].to_numpy()
            tpo_day = _seroconvert_day(t, df["TPOAb"].to_numpy(), TPOAB_POS, df["TPOAb"].iloc[0])
            tg_day = _seroconvert_day(t, df["TgAb"].to_numpy(), TGAB_POS, df["TgAb"].iloc[0])
            records[drug].append({"tpo_day": tpo_day, "tg_day": tg_day})

    payload = {"n_simulated_per_drug": n, "tpoab_threshold": TPOAB_POS, "tgab_threshold": TGAB_POS, "by_class": {}}
    rows, kinetic_rows = [], []
    for cls, members in classes.items():
        recs = [rr for d in members for rr in records.get(d, [])]
        if not recs:
            continue
        n_all = len(recs)
        tpo_days = [r["tpo_day"] for r in recs if r["tpo_day"] is not None]
        tg_days = [r["tg_day"] for r in recs if r["tg_day"] is not None]
        either = sum(1 for r in recs if r["tpo_day"] is not None or r["tg_day"] is not None)
        cls_sum = {
            "n": n_all,
            "tpoab_seroconversion_pct": round(100 * len(tpo_days) / n_all, 1),
            "tgab_seroconversion_pct": round(100 * len(tg_days) / n_all, 1),
            "either_pct": round(100 * either / n_all, 1),
            "tpoab_median_week": round(float(np.median(tpo_days)) / 7.0, 1) if tpo_days else None,
            "tgab_median_week": round(float(np.median(tg_days)) / 7.0, 1) if tg_days else None,
        }
        payload["by_class"][cls] = cls_sum
        rows.append({"drug_class": cls, **cls_sum})

        # temporal kinetics: cumulative fraction of eventual TPOAb converters by week band
        total_conv = len(tpo_days)
        for lo, hi in WEEK_BANDS:
            converted_by = sum(1 for d in tpo_days if d / 7.0 <= hi)
            kinetic_rows.append({
                "drug_class": cls, "week_band": f"{lo}-{hi}",
                "cumulative_pct_of_converters": round(100 * converted_by / total_conv, 1) if total_conv else None,
            })

    out_dir = vc.output_dir(cfg)
    vc.write_csv(out_dir / "seroconversion_by_class.csv", pd.DataFrame(rows))
    vc.write_csv(out_dir / "seroconversion_kinetics.csv", pd.DataFrame(kinetic_rows))
    vc.write_json(out_dir / "seroconversion.json", payload)

    print("\nSeroconversion by class:")
    for _, r in pd.DataFrame(rows).iterrows():
        print(f"  {r['drug_class']:<12s} TPOAb={r['tpoab_seroconversion_pct']}%  "
              f"TgAb={r['tgab_seroconversion_pct']}%  either={r['either_pct']}%  "
              f"TPOAb_median_wk={r['tpoab_median_week']}")
    print(f"\nWrote seroconversion_by_class.csv, seroconversion_kinetics.csv, seroconversion.json to {out_dir}")


if __name__ == "__main__":
    main()
