#!/usr/bin/env python3
"""
v1 Phase 9a — Figure generation.

Reads the result artifacts produced by the v1 pipeline and renders diagnostic
figures to results/v1/figures/. Each figure is guarded: if its input file is
missing, it is skipped with a note (so this can run after a partial pipeline).

All figures are SYNTHETIC/in-silico (see results/v1/README.md).
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
for _p in (_ROOT, os.path.join(_ROOT, "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import v1_common as vc


def _read_csv(path):
    return pd.read_csv(path, comment="#") if path.exists() else None


def _read_json(path):
    if not path.exists():
        return None
    with open(path) as fh:
        return json.load(fh)


def fig_class_incidence(out_dir, fig_dir, cfg):
    df = _read_csv(out_dir / "incidence_by_class.csv")
    if df is None:
        return None
    piv = df.pivot(index="group", columns="kind", values="rate_pct")
    order = ["PD-1", "PD-L1", "CTLA-4", "Combination"]
    piv = piv.reindex([o for o in order if o in piv.index])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(piv)); w = 0.38
    ax.bar(x - w/2, piv.get("hypothyroidism", 0), w, label="Hypothyroidism", color="#3b6fb0")
    ax.bar(x + w/2, piv.get("hyperthyroidism", 0), w, label="Hyperthyroidism", color="#c85a54")
    ax.set_xticks(x); ax.set_xticklabels(piv.index)
    ax.set_ylabel("12-mo incidence (%)")
    ax.legend(); fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig1_incidence_by_class.png", cfg)


def fig_gsa_tornado(out_dir, fig_dir, cfg):
    df = _read_csv(out_dir / "gsa_sobol.csv")
    if df is None:
        return None
    df = df.sort_values("ST")
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.barh(df["label"], df["ST"], color="#4a8", label="Total-order (ST)")
    ax.barh(df["label"], df["S1"], color="#276", label="First-order (S1)", alpha=0.9)
    ax.set_xlabel("Sobol index")
    ax.legend(); fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig5_gsa_tornado.png", cfg)


def fig_seroconversion(out_dir, fig_dir, cfg):
    df = _read_csv(out_dir / "seroconversion_by_class.csv")
    if df is None:
        return None
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(df)); w = 0.38
    ax.bar(x - w/2, df["tpoab_seroconversion_pct"], w, label="TPOAb", color="#3b6fb0")
    ax.bar(x + w/2, df["tgab_seroconversion_pct"], w, label="TgAb", color="#e0a458")
    ax.set_xticks(x); ax.set_xticklabels(df["drug_class"])
    ax.set_ylabel("Seroconversion (%)")
    ax.legend(); fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig4_seroconversion.png", cfg)


def fig_virtual_population(out_dir, fig_dir, cfg):
    df = _read_csv(out_dir / "virtual_population.csv")
    summ = _read_json(out_dir / "virtual_population_summary.json")
    if df is None or summ is None:
        return None
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.3))
    ax1.hist(df["risk_score"], bins=30, color="#3b6fb0", alpha=0.85)
    ax1.set_xlabel("Mechanistic risk score"); ax1.set_ylabel("Virtual patients")
    ax1.set_title(f"VP risk distribution (n={summ['n_virtual_patients']})")
    tiers = summ["risk_tier_distribution_pct"]
    ax2.bar(list(tiers.keys()), list(tiers.values()), color=["#c85a54", "#e0a458", "#4a8"])
    ax2.set_ylabel("% of virtual population"); ax2.set_title("3-tier risk stratification")
    fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig6_virtual_population.png", cfg)


def fig_model_performance(out_dir, fig_dir, cfg):
    ml = _read_json(out_dir / "ml_ensemble_metrics.json")
    val = _read_json(out_dir / "validation_internal.json")
    if ml is None and val is None:
        return None
    labels, aucs = [], []
    if val:
        labels.append("Logistic\n(internal CV)"); aucs.append(val["repeated_cv"]["auc_mean"])
    if ml:
        for k, v in ml["per_model_cv_auc"].items():
            labels.append(k.replace("_", "\n")); aucs.append(v)
        labels.append("ensemble\n(CV)"); aucs.append(ml["ensemble_cv"]["auc_mean"])
        labels.append("ensemble\n(external)"); aucs.append(ml["ensemble_external"]["auc"])
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(labels, aucs, color="#3b6fb0")
    ax.axhline(0.5, ls="--", c="gray", lw=1)
    ax.set_ylim(0.4, 1.0); ax.set_ylabel("AUC-ROC")
    fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig8_model_performance.png", cfg)


def fig_vpc(out_dir, fig_dir, cfg):
    df = _read_csv(out_dir / "validation_vpc.csv")
    if df is None:
        return None
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.fill_between(df["visit_week"], df["pi90_low"], df["pi90_high"], alpha=0.25, color="#3b6fb0",
                    label="Model 90% PI")
    ax.plot(df["visit_week"], df["sim_median_TSH"], "-o", color="#276", label="Model median")
    ax.plot(df["visit_week"], df["obs_median_TSH"], "--s", color="#c85a54", label="Observed median")
    ax.set_xlabel("Visit week"); ax.set_ylabel("TSH (mU/L)")
    ax.legend(); fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig7_vpc_tsh.png", cfg)


def fig_external_validation(out_dir, fig_dir, cfg):
    sc = _read_json(out_dir / "external_validation_scorecard.json")
    if sc is None:
        return None
    eps = sc["endpoints"][::-1]   # render top-down
    colors = {"PASS": "#2e8b57", "PARTIAL": "#d9a441", "FAIL": "#c0392b",
              "REPORTED": "#8a8a8a", "SKIP": "#8a8a8a"}
    fig, ax = plt.subplots(figsize=(10, 0.55 * len(eps) + 1.6))
    for i, e in enumerate(eps):
        ax.barh(i, 1.0, color=colors.get(e["verdict"], "#8a8a8a"), alpha=0.9, height=0.6)
        note = e["verdict"]
        if e.get("spearman_rho") is not None:
            note += f"  (rho = {e['spearman_rho']})"
        elif e.get("std_distance") is not None:
            note += f"  (dist = {e['std_distance']})"
        ax.text(1.04, i, note, va="center", fontsize=8, color="#222")
        ax.text(0.02, i, e["id"], va="center", ha="left", fontsize=7.5, color="white", fontweight="bold")
    ax.set_yticks([]); ax.set_xlim(0, 1.9); ax.set_xticks([])
    for s in ("top", "right", "bottom", "left"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    return vc.save_figure(fig, fig_dir / "fig9_external_validation.png", cfg)


def main() -> None:
    cfg = vc.load_config()
    vc.banner("v1 Phase 9a — Figure generation")
    out_dir = vc.output_dir(cfg)
    fig_dir = vc.output_dir(cfg, "figures")
    builders = [fig_class_incidence, fig_gsa_tornado, fig_seroconversion,
                fig_virtual_population, fig_model_performance, fig_vpc,
                fig_external_validation]
    made = []
    for b in builders:
        try:
            path = b(out_dir, fig_dir, cfg)
            if path:
                made.append(path.name); print(f"  wrote {path.name}")
            else:
                print(f"  skipped {b.__name__} (input missing)")
        except Exception as e:
            print(f"  ERROR in {b.__name__}: {type(e).__name__}: {e}")
    print(f"\n  {len(made)} figures written to {fig_dir}")


if __name__ == "__main__":
    main()
