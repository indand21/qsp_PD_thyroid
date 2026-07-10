#!/usr/bin/env python3
"""
External benchmark validation — score the QSP model's EMERGENT thyroid behaviours
against held-out published literature and real-world FDA FAERS pharmacovigilance.

This is an INDEPENDENT external validation: it compares only NON-calibrated
(emergent) model outputs against benchmarks that were NOT used to fit the model
(calibration used per-drug hypothyroidism incidence + class ordering + a 60-140 d
onset window from refs [10,11,20,21], all excluded here).

Inputs:
  * Model outputs (results/v1/): incidence_by_class.csv, incidence_by_drug.csv,
    biphasic_temporal.json, seroconversion.json, class_risk_stats.json.
  * external_benchmarks/literature_targets.yaml  (held-out literature, hand-curated
    with DOI/PMID provenance).
  * results/v1/external_faers_benchmarks.json     (real FAERS, from fetch script).

Each endpoint gets a verdict PASS / PARTIAL / FAIL against a pre-registered rule
plus a standardized distance. FAERS is spontaneous reporting, so FAERS endpoints
validate RANK ORDER and RATIO DIRECTION, not absolute incidence.

Output: results/v1/external_validation_scorecard.{json,csv}
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np
import pandas as pd
import yaml

import v1_common as vc

MONO_CLASSES = ["PD-1", "PD-L1", "CTLA-4"]   # FAERS cannot isolate Combination


# --------------------------------------------------------------------------- #
# Model emergent-value extraction
# --------------------------------------------------------------------------- #
def _model_values(out_dir) -> dict:
    inc_c = pd.read_csv(out_dir / "incidence_by_class.csv", comment="#")
    inc_d = pd.read_csv(out_dir / "incidence_by_drug.csv", comment="#")
    biph = json.loads((out_dir / "biphasic_temporal.json").read_text(encoding="utf-8"))
    sero = json.loads((out_dir / "seroconversion.json").read_text(encoding="utf-8"))
    crs = json.loads((out_dir / "class_risk_stats.json").read_text(encoding="utf-8"))

    def class_rate(df, kind):
        r = df[df.kind == kind].set_index("group")["rate_pct"]
        return {c: float(r[c]) for c in r.index}

    hyper_by_class = class_rate(inc_c, "hyperthyroidism")
    hypo_by_class = class_rate(inc_c, "hypothyroidism")

    # weighted overall biphasic proportion across classes
    bw = biph["by_class"]
    n_tot = sum(v["n_dysfunction"] for v in bw.values())
    biph_cases = sum(v["n_dysfunction"] * v["pct_biphasic"] / 100.0 for v in bw.values())
    biphasic_overall = round(100 * biph_cases / n_tot, 1) if n_tot else None

    return {
        "hyper_pct": hyper_by_class,
        "hypo_pct": hypo_by_class,
        "biphasic_by_class": {c: bw[c]["pct_biphasic"] for c in bw},
        "biphasic_overall": biphasic_overall,
        "thyrotoxic_onset_weeks": {c: bw[c]["hyper_onset_weeks"]["median"] for c in bw},
        "hypo_onset_weeks": {c: bw[c]["hypo_onset_weeks"]["median"] for c in bw},
        "seroconv_pct": {c: sero["by_class"][c]["tpoab_seroconversion_pct"] for c in sero["by_class"]},
        "onset_median_days": {r["drug"]: r["onset_median_days"]
                              for _, r in inc_d[inc_d.kind == "hypothyroidism"].iterrows()},
        "rr_pd1_vs_pdl1_hypo": crs["relative_risk_PD1_vs_PDL1"]["hypothyroidism"]["rr"],
        "rr_pd1_vs_pdl1_hyper": crs["relative_risk_PD1_vs_PDL1"]["hyperthyroidism"]["rr"],
    }


def _resolve(model_values: dict, key: str):
    """Resolve a dotted model_key like 'hyper_pct.PD-1' into model_values."""
    cur = model_values
    for part in key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


# --------------------------------------------------------------------------- #
# Verdict helpers
# --------------------------------------------------------------------------- #
def _range_verdict(model, low, high, margin=0.20):
    """PASS if model in [low,high]; PARTIAL within a proportional margin; else FAIL."""
    if model is None or low is None or high is None:
        return "SKIP", None
    span = high - low
    mid = (low + high) / 2.0
    dist = round(abs(model - mid) / mid, 3) if mid else None
    if low <= model <= high:
        return "PASS", dist
    if (low - margin * max(span, abs(low))) <= model <= (high + margin * max(span, abs(high))):
        return "PARTIAL", dist
    return "FAIL", dist


def _spearman(a, b):
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    if len(ra) < 2 or np.std(ra) == 0 or np.std(rb) == 0:
        return None
    return float(np.corrcoef(ra, rb)[0, 1])


# --------------------------------------------------------------------------- #
def main() -> None:
    cfg = vc.load_config()
    vc.banner("External benchmark validation - literature + FAERS scorecard")
    out_dir = vc.output_dir(cfg)

    lit_path = _ROOT and os.path.join(_ROOT, "external_benchmarks", "literature_targets.yaml")
    faers_path = out_dir / "external_faers_benchmarks.json"
    missing = [p for p in (lit_path, faers_path) if not os.path.exists(p)]
    if missing:
        print(f"  ERROR: missing inputs: {missing}")
        print("  Run fetch_faers_benchmarks.py and create external_benchmarks/literature_targets.yaml first.")
        sys.exit(1)

    mv = _model_values(out_dir)
    lit = yaml.safe_load(open(lit_path, encoding="utf-8"))
    faers = json.loads(faers_path.read_text(encoding="utf-8"))

    endpoints = []

    # --- Literature-driven endpoints (E1-E4) ---
    for e in lit.get("literature_endpoints", []):
        model = _resolve(mv, e["model_key"])
        if e.get("scored", True):
            verdict, dist = _range_verdict(model, e.get("benchmark_low"), e.get("benchmark_high"))
        else:
            verdict, dist = "REPORTED", None
        endpoints.append({
            "id": e["id"], "domain": "literature", "description": e["description"],
            "model_value": model,
            "benchmark": {"low": e.get("benchmark_low"), "high": e.get("benchmark_high"),
                          "point": e.get("benchmark_point")},
            "verdict": verdict, "std_distance": dist,
            "source": e.get("source"), "ref_id": e.get("ref_id"), "note": e.get("note", ""),
        })

    # --- FAERS E5: class rank-ordering of thyroid (hypothyroidism) reporting ---
    fbc = faers["by_class"]
    model_hypo = [mv["hypo_pct"][c] for c in MONO_CLASSES]
    faers_hypo = [fbc[c]["hypo_reporting_pct"] for c in MONO_CLASSES]
    rho = _spearman(model_hypo, faers_hypo)
    e5_verdict = "PASS" if (rho is not None and rho >= 0.6) else ("PARTIAL" if (rho is not None and rho >= 0.3) else "FAIL")
    endpoints.append({
        "id": "E5_faers_class_ordering", "domain": "faers",
        "description": "Rank-ordering of hypothyroidism reporting across monotherapy classes (model incidence vs FAERS reporting proportion)",
        "model_value": dict(zip(MONO_CLASSES, model_hypo)),
        "benchmark": dict(zip(MONO_CLASSES, faers_hypo)),
        "verdict": e5_verdict, "std_distance": None, "spearman_rho": round(rho, 3) if rho is not None else None,
        "source": faers["source"], "ref_id": f"FAERS {faers['fetch_date_utc']}",
        "note": "FAERS is spontaneous reporting; CTLA-4 (ipilimumab) inflated by combination co-reporting.",
    })

    # --- FAERS E6: PD-1 vs PD-L1 direction (hypothyroidism) ---
    model_dir = mv["hypo_pct"]["PD-1"] > mv["hypo_pct"]["PD-L1"]
    faers_dir = fbc["PD-1"]["hypo_reporting_pct"] > fbc["PD-L1"]["hypo_reporting_pct"]
    endpoints.append({
        "id": "E6_pd1_vs_pdl1_direction", "domain": "faers",
        "description": "PD-1 > PD-L1 hypothyroidism (model RR direction vs FAERS reporting-proportion direction)",
        "model_value": {"rr_pd1_vs_pdl1": mv["rr_pd1_vs_pdl1_hypo"],
                        "pd1_pct": mv["hypo_pct"]["PD-1"], "pdl1_pct": mv["hypo_pct"]["PD-L1"]},
        "benchmark": {"faers_pd1_report_pct": fbc["PD-1"]["hypo_reporting_pct"],
                      "faers_pdl1_report_pct": fbc["PD-L1"]["hypo_reporting_pct"]},
        "verdict": "PASS" if (model_dir and faers_dir) else "FAIL", "std_distance": None,
        "source": faers["source"], "ref_id": f"FAERS {faers['fetch_date_utc']}",
        "note": "Direction agreement only (both put PD-1 above PD-L1).",
    })

    # --- FAERS supplementary: hypo:hyper ratio direction (all classes hypo-dominant) ---
    model_ratio_ok = all(mv["hypo_pct"][c] > mv["hyper_pct"][c] for c in MONO_CLASSES)
    faers_ratio_ok = all((fbc[c]["hypo_hyper_ratio"] or 0) > 1 for c in MONO_CLASSES)
    endpoints.append({
        "id": "E7_hypo_hyper_dominance", "domain": "faers",
        "description": "Hypothyroidism > hyperthyroidism in every class (model vs FAERS hypo:hyper ratio)",
        "model_value": {c: round(mv["hypo_pct"][c] / mv["hyper_pct"][c], 2) if mv["hyper_pct"][c] else None for c in MONO_CLASSES},
        "benchmark": {c: fbc[c]["hypo_hyper_ratio"] for c in MONO_CLASSES},
        "verdict": "PASS" if (model_ratio_ok and faers_ratio_ok) else "PARTIAL", "std_distance": None,
        "source": faers["source"], "ref_id": f"FAERS {faers['fetch_date_utc']}", "note": "",
    })

    scored = [e for e in endpoints if e["verdict"] in ("PASS", "PARTIAL", "FAIL")]
    summary = {v: sum(1 for e in scored if e["verdict"] == v) for v in ("PASS", "PARTIAL", "FAIL")}
    summary["reported_unscored"] = sum(1 for e in endpoints if e["verdict"] in ("REPORTED", "SKIP"))

    payload = {
        "_provenance": (
            "External validation scorecard. Compares the QSP model's EMERGENT "
            "(non-calibrated) outputs (in-silico) against HELD-OUT published "
            "literature and REAL-WORLD FDA FAERS pharmacovigilance. Calibration "
            "targets and their sources are excluded. FAERS endpoints validate rank "
            "order / ratio direction, not absolute incidence."
        ),
        "excluded_calibration_refs": lit.get("excluded_calibration_refs", []),
        "faers_fetch_date": faers["fetch_date_utc"],
        "summary": summary,
        "endpoints": endpoints,
    }
    vc.write_json(out_dir / "external_validation_scorecard.json", payload)
    rows = [{"id": e["id"], "domain": e["domain"], "verdict": e["verdict"],
             "std_distance": e.get("std_distance"), "spearman_rho": e.get("spearman_rho"),
             "description": e["description"], "source": e.get("source"), "ref_id": e.get("ref_id")}
            for e in endpoints]
    vc.write_csv(out_dir / "external_validation_scorecard.csv", pd.DataFrame(rows))

    print(f"  Summary: {summary}")
    for e in endpoints:
        print(f"  [{e['verdict']:8s}] {e['id']:32s} {e['description'][:60]}")
    print(f"\n  Wrote external_validation_scorecard.json/.csv to {out_dir}")


if __name__ == "__main__":
    main()
