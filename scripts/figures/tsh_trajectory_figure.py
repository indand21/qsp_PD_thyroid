#!/usr/bin/env python3
"""
Standalone figure: serum-TSH trajectory over 1 year by checkpoint-inhibitor regimen.

Simulates a virtual population per drug/regimen (calibrated susceptibility mixture)
with the expanded model and renders two figures into results/v1/figures/:

  1. fig2_tsh_trajectory_by_drug.png
     Population mean TSH trajectory + bootstrap 95% CI (small multiples, one panel
     per regimen). The median stays euthyroid (~1.5) because most patients never
     develop dysfunction, so the mean is used to show the dysfunction contribution.

  2. fig3_tsh_trajectory_affected.png
     Affected patients only (peak TSH > 4.5), ONSET-ALIGNED: each affected patient's
     trajectory is aligned to their hypothyroidism onset (first TSH > 4.5 crossing)
     and averaged (mean + bootstrap 95% CI). Alignment removes onset-time
     heterogeneity and exposes the biphasic pattern: a transient thyrotoxic dip
     (TSH suppressed as T4 spikes) just before onset, then the hypothyroid rise.

This is a standalone analysis script (not part of run_v1_pipeline). Numbers are
IN-SILICO / SYNTHETIC (see results/v1/README.md).

Usage:
    python scripts/figures/tsh_trajectory_figure.py
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from dataclasses import replace

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qsp_expanded import ExpandedParameters, simulate_expanded_patient
from qsp_expanded.population import sample_susceptibility

# ---- config -----------------------------------------------------------------
N = 300                       # patients per regimen
NPTS = 74                     # output points over the horizon (~5-day spacing)
HORIZON = 365.0
HYPO_THR = 4.5                # subclinical-hypothyroid threshold (mIU/L)
OVERT_THR = 10.0
SEED = 2026

DRUGS = [
    ("nivolumab",            "Nivolumab",              "PD-1"),
    ("pembrolizumab",        "Pembrolizumab",          "PD-1"),
    ("atezolizumab",         "Atezolizumab",           "PD-L1"),
    ("durvalumab",           "Durvalumab",             "PD-L1"),
    ("ipilimumab",           "Ipilimumab",             "CTLA-4"),
    ("nivolumab_ipilimumab", "Nivolumab + Ipilimumab", "Combination"),
]
# Okabe-Ito-derived, colorblind-safe, one hue per mechanistic class.
CLASS_COLOR = {"PD-1": "#0072B2", "PD-L1": "#009E73", "CTLA-4": "#C77A00", "Combination": "#D55E00"}
INK, MUTED, GRID, SURFACE = "#1a1a1a", "#6b6b6b", "#e6e6e2", "#ffffff"


def simulate_all():
    """Return {drug: TSH matrix (N x NPTS)} and the shared time grid (days)."""
    tgrid = np.linspace(0.0, HORIZON, NPTS)
    base = ExpandedParameters()
    mats = {}
    for i, (key, _, _) in enumerate(DRUGS):
        susc = sample_susceptibility(N, np.random.default_rng(100 + i))
        M = np.empty((N, NPTS))
        for k, s in enumerate(susc):
            p = replace(base, susceptibility=float(s))
            df = simulate_expanded_patient(key, p, t_span=(0.0, HORIZON),
                                           n_points=NPTS, patient_id=f"{key}_{k}")
            M[k] = df["TSH"].to_numpy()
        mats[key] = M
        print(f"  simulated {key} (n={N})")
    return mats, tgrid


def _style_panel(ax, title, cls):
    for thr, lab in [(HYPO_THR, "subclinical"), (OVERT_THR, "overt")]:
        ax.axhline(thr, color=GRID, lw=1.0, ls=(0, (4, 3)), zorder=1)
    ax.set_yscale("log")
    ax.set_ylim(0.7, 200)
    ax.set_yticks([1, 4.5, 10, 50, 100])
    ax.set_yticklabels(["1", "4.5", "10", "50", "100"])
    ax.set_title(title, fontsize=11, color=INK, pad=6, loc="left", fontweight="bold")
    ax.text(0.98, 0.03, cls, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color=CLASS_COLOR[cls], fontweight="bold")
    ax.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(colors=MUTED, labelsize=8.5)


def _boot_mean_ci(M, rng, B=1000):
    """Bootstrap mean + 95% CI across rows (patients), NaN-aware, per column."""
    n = M.shape[0]
    idx = rng.integers(0, n, size=(B, n))
    boot = np.nanmean(M[idx], axis=1)               # (B, T)
    lo, hi = np.nanpercentile(boot, [2.5, 97.5], axis=0)
    return np.nanmean(M, axis=0), lo, hi


def figure_population(mats, tgrid, out_dir):
    rng = np.random.default_rng(SEED)
    weeks = tgrid / 7.0
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2), sharex=True, sharey=True)
    for ax, (key, name, cls) in zip(axes.ravel(), DRUGS):
        M = mats[key]
        mean, lo, hi = _boot_mean_ci(M, rng)
        med = np.median(M, axis=0)
        c = CLASS_COLOR[cls]
        for thr, lab in [(HYPO_THR, "subclinical"), (OVERT_THR, "overt")]:
            ax.text(weeks[-1], thr, f"{lab} ", va="center", ha="right",
                    fontsize=6.5, color=MUTED, zorder=1)
        ax.fill_between(weeks, lo, hi, color=c, alpha=0.22, lw=0, zorder=2)
        ax.plot(weeks, mean, color=c, lw=2.0, zorder=4)
        ax.plot(weeks, med, color=MUTED, lw=1.1, ls=(0, (2, 2)), zorder=3)
        ax.set_xlim(0, weeks[-1])
        _style_panel(ax, name, cls)
    for ax in axes[-1]:
        ax.set_xlabel("Time since first dose (weeks)", fontsize=9.5, color=INK)
    for ax in axes[:, 0]:
        ax.set_ylabel("Serum TSH (mIU/L, log)", fontsize=9.5, color=INK)
    h = [plt.Line2D([], [], color=INK, lw=2.0),
         plt.Line2D([], [], color=MUTED, lw=1.1, ls=(0, (2, 2))),
         plt.Rectangle((0, 0), 1, 1, color=INK, alpha=0.22)]
    fig.legend(h, ["Population mean", "Population median", "Mean 95% CI (bootstrap)"],
               loc="lower center", ncol=3, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.03, 1, 0.99))
    path = os.path.join(out_dir, "fig2_tsh_trajectory_by_drug.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


def _onset_aligned(M, tgrid, rel_weeks):
    """Align each affected patient (peak TSH > HYPO_THR) to hypo onset; interpolate
    TSH onto rel_weeks (weeks relative to onset). Returns (aligned matrix, n_affected)."""
    rel_days = rel_weeks * 7.0
    rows = []
    for tsh in M:
        if tsh.max() <= HYPO_THR:
            continue
        onset = tgrid[np.argmax(tsh > HYPO_THR)]           # first crossing (days)
        rel = tgrid - onset
        y = np.interp(rel_days, rel, tsh, left=np.nan, right=np.nan)
        rows.append(y)
    if not rows:
        return np.empty((0, len(rel_weeks))), 0
    return np.vstack(rows), len(rows)


def figure_affected(mats, tgrid, out_dir):
    rng = np.random.default_rng(SEED + 1)
    rel_weeks = np.linspace(-10, 30, 81)                    # weeks relative to onset
    fig, axes = plt.subplots(2, 3, figsize=(12.5, 7.2), sharex=True, sharey=True)
    for ax, (key, name, cls) in zip(axes.ravel(), DRUGS):
        A, n_aff = _onset_aligned(mats[key], tgrid, rel_weeks)
        c = CLASS_COLOR[cls]
        for thr, lab in [(HYPO_THR, "subclinical"), (OVERT_THR, "overt")]:
            ax.text(rel_weeks[-1], thr, f"{lab} ", va="center", ha="right",
                    fontsize=6.5, color=MUTED, zorder=1)
        ax.axvline(0.0, color=GRID, lw=1.0, zorder=1)
        ax.text(0.4, 0.78, "onset", rotation=90, va="bottom", ha="left",
                fontsize=6.5, color=MUTED)
        if n_aff >= 3:
            mean, lo, hi = _boot_mean_ci(A, rng)
            ax.fill_between(rel_weeks, lo, hi, color=c, alpha=0.22, lw=0, zorder=2)
            ax.plot(rel_weeks, mean, color=c, lw=2.0, zorder=4)
        ax.set_xlim(rel_weeks[0], rel_weeks[-1])
        _style_panel(ax, name, cls)
        ax.text(0.02, 0.93, f"n affected = {n_aff}", transform=ax.transAxes,
                fontsize=8, color=MUTED, va="top")
    for ax in axes[-1]:
        ax.set_xlabel("Weeks relative to hypothyroidism onset", fontsize=9.5, color=INK)
    for ax in axes[:, 0]:
        ax.set_ylabel("Serum TSH (mIU/L, log)", fontsize=9.5, color=INK)
    h = [plt.Line2D([], [], color=INK, lw=2.0),
         plt.Rectangle((0, 0), 1, 1, color=INK, alpha=0.22)]
    fig.legend(h, ["Onset-aligned mean (affected)", "95% CI (bootstrap)"],
               loc="lower center", ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.03, 1, 0.99))
    path = os.path.join(out_dir, "fig3_tsh_trajectory_affected.png")
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {path}")


def main():
    out_dir = os.path.join(_ROOT, "results", "v1", "figures")
    os.makedirs(out_dir, exist_ok=True)
    print(f"Simulating TSH trajectories (n={N}/regimen) ...")
    mats, tgrid = simulate_all()
    figure_population(mats, tgrid, out_dir)
    figure_affected(mats, tgrid, out_dir)
    print("Done.")


if __name__ == "__main__":
    main()
