"""
Expanded 19-state ODE system (5 modules).

The right-hand side is a pure function of (t, y, context) — all previously
instance-mutated quantities (notably `immune_memory`) are now genuine ODE states,
so the system is autonomous in the solver's sense and safe for adaptive steppers.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .parameters import ExpandedParameters, STATE_INDEX, N_STATES, DRUG_PK, resolve_regimen

_BODY_WEIGHT_KG = 70.0


def drug_concentration(t: float, drug: str, dosing_interval: float | None = None) -> float:
    """Analytic 1-compartment multi-dose concentration (ng/mL) for a single drug.

    Mirrors the legacy superposition PK (`qsp_model_final.drug_concentration`).
    """
    pk = DRUG_PK[drug]
    CL, V, dose_mg_kg = pk["CL"], pk["V"], pk["dose_mg_kg"]
    interval = dosing_interval if dosing_interval is not None else pk["interval"]
    dose_mg = dose_mg_kg * _BODY_WEIGHT_KG
    conc = 0.0
    # dose times up to and including t
    n_doses = int(t // interval) + 1
    for k in range(n_doses):
        dose_time = k * interval
        if dose_time <= t:
            conc += (dose_mg * 1e6 / (V * 1000.0)) * np.exp(-CL * (t - dose_time) / V)
    return max(conc, 0.0)


def axis_occupancy_equilibrium(t: float, drugs: List[str]) -> Dict[str, float]:
    """Equilibrium receptor occupancy (0-1) for each axis given active drugs."""
    occ = {"PD1": 0.0, "CTLA4": 0.0}
    for drug in drugs:
        pk = DRUG_PK[drug]
        c = drug_concentration(t, drug)
        f = c / (c + pk["EC50_occ"]) * pk["potency"]
        occ[pk["axis"]] = min(1.0, occ[pk["axis"]] + f)
    return occ


def initial_conditions(p: ExpandedParameters) -> np.ndarray:
    """Baseline (pre-treatment) steady-ish state."""
    y0 = np.zeros(N_STATES)
    y0[STATE_INDEX["O_pd1"]] = 0.0
    y0[STATE_INDEX["O_ctla4"]] = 0.0
    y0[STATE_INDEX["T_naive"]] = p.T_naive0
    y0[STATE_INDEX["T_eff"]] = p.T_eff0
    y0[STATE_INDEX["T_reg"]] = p.T_reg0
    y0[STATE_INDEX["IFN"]] = 0.0
    y0[STATE_INDEX["TNF"]] = 0.0
    y0[STATE_INDEX["IL2"]] = 0.08
    y0[STATE_INDEX["IL17"]] = 0.0
    y0[STATE_INDEX["Thyro"]] = p.Thyro_max
    y0[STATE_INDEX["Colloid"]] = 1.0
    y0[STATE_INDEX["TPO"]] = 1.0
    y0[STATE_INDEX["cumulative_damage"]] = 0.0
    y0[STATE_INDEX["immune_memory"]] = 0.0
    y0[STATE_INDEX["TPOAb"]] = p.baseline_TPOAb
    y0[STATE_INDEX["TgAb"]] = 0.0
    y0[STATE_INDEX["T4"]] = p.T4_set
    y0[STATE_INDEX["T3"]] = p.T3_set
    y0[STATE_INDEX["TSH"]] = p.TSH_set
    return y0


def rhs(t: float, y: np.ndarray, p: ExpandedParameters, drugs: List[str]) -> np.ndarray:
    """Expanded 19-state right-hand side."""
    s = STATE_INDEX
    # Unpack (clip to non-negative where physiological)
    O_pd1 = y[s["O_pd1"]]
    O_ctla4 = y[s["O_ctla4"]]
    T_naive = max(y[s["T_naive"]], 0.0)
    T_eff = max(y[s["T_eff"]], 0.0)
    T_reg = max(y[s["T_reg"]], 0.0)
    IFN = max(y[s["IFN"]], 0.0)
    TNF = max(y[s["TNF"]], 0.0)
    IL2 = max(y[s["IL2"]], 0.0)
    IL17 = max(y[s["IL17"]], 0.0)
    Thyro = np.clip(y[s["Thyro"]], 0.0, p.Thyro_max)
    Colloid = max(y[s["Colloid"]], 0.0)
    TPO = np.clip(y[s["TPO"]], 0.0, 1.0)
    damage = max(y[s["cumulative_damage"]], 0.0)
    memory = max(y[s["immune_memory"]], 0.0)
    TPOAb = max(y[s["TPOAb"]], 0.0)
    TgAb = max(y[s["TgAb"]], 0.0)
    T4 = max(y[s["T4"]], 0.0)
    T3 = max(y[s["T3"]], 0.0)
    TSH = max(y[s["TSH"]], 0.0)

    dydt = np.zeros(N_STATES)

    # === Module 1: checkpoint pharmacology ===
    occ_eq = axis_occupancy_equilibrium(t, drugs)
    dydt[s["O_pd1"]] = p.k_occ * (occ_eq["PD1"] - O_pd1)
    dydt[s["O_ctla4"]] = p.k_occ * (occ_eq["CTLA4"] - O_ctla4)

    # === Module 2: T-cell dynamics ===
    # Effector pool: baseline source (S_eff0 = beta_eff*T_eff0) amplified by
    # checkpoint occupancy. PD-1 blockade relieves effector expansion; CTLA-4
    # blockade adds priming; Treg suppresses (suppression weakened by CTLA-4
    # blockade, which impairs Treg function). Naive pool drains faster under
    # CTLA-4 blockade; Treg is depleted by CTLA-4 blockade.
    supp_strength = p.treg_supp * (1.0 - p.treg_synergy * O_ctla4)
    suppression = 1.0 / (1.0 + supp_strength * (T_reg / p.T_reg0))
    activation = (p.w_pd1_eff * O_pd1 + p.w_ctla4_eff * O_ctla4) * suppression
    S_eff0 = p.beta_eff * p.T_eff0
    prime_drain = p.k_prime * (1.0 + p.w_ctla4_prime * O_ctla4)
    dydt[s["T_naive"]] = p.s_naive - prime_drain * T_naive - p.d_naive * T_naive
    dydt[s["T_eff"]] = (
        S_eff0 * (1.0 + activation)
        + p.delta_il2 * IL2 * T_eff * suppression
        - p.beta_eff * T_eff
    )
    dydt[s["T_reg"]] = (
        p.k_treg_src - p.d_treg * T_reg - p.k_ctla4_treg * O_ctla4 * T_reg
    )

    # === Module 3: cytokine network ===
    eff_norm = T_eff / p.T_eff0
    dydt[s["IFN"]] = (
        p.eps_ifn * eff_norm * (1.0 + IFN / (IFN + 80.0)) * (1.0 + p.ifn_tnf_crosstalk * TNF / (TNF + 50.0))
        - p.k_clear_ifn * IFN
    )
    dydt[s["TNF"]] = p.eps_tnf * eff_norm - p.k_clear_tnf * TNF
    dydt[s["IL2"]] = p.eps_il2 * eff_norm - p.k_clear_il2 * IL2
    dydt[s["IL17"]] = (
        p.eps_il17 * eff_norm / (1.0 + T_reg / p.T_reg0) - p.k_clear_il17 * IL17
    )

    # === Module 4: thyroid gland & signaling ===
    # Time-gated cumulative damage (delayed onset), driven by IFN (+TNF) and
    # scaled by patient susceptibility (so low-susceptibility patients may never
    # cross threshold -> incidence < 100%).
    cytokine_drive = IFN + 0.5 * TNF
    time_gate = np.clip((t - p.minimum_exposure_days) / p.damage_ramp_time, 0.0, 1.0)
    memory_amp = 1.0 + (p.immune_memory_factor - 1.0) * memory
    if cytokine_drive >= p.cytokine_threshold_pg_ml and time_gate > 0.0:
        drive_effect = cytokine_drive / (cytokine_drive + p.damage_half_sat)
        accum = p.damage_rate * drive_effect * time_gate * memory_amp * p.susceptibility
        d_memory = p.memory_accumulation_rate * (cytokine_drive / 150.0)
    else:
        accum = 0.0
        d_memory = -0.0005 * memory
    # Repair/turnover always active -> sub-threshold equilibrium for low drive.
    d_damage = accum - p.k_damage_repair * damage
    dydt[s["cumulative_damage"]] = d_damage
    dydt[s["immune_memory"]] = d_memory

    # Disease is "active" once accumulated damage exceeds a (slowly growing)
    # threshold. All thyroid injury (cytotoxic death AND TPO suppression) is gated
    # on this, so the delayed-onset thyroiditis unfolds as: destruction ->
    # colloid release (thyrotoxic spike) -> gland depletion + TPO loss (hypo).
    damage_threshold = p.base_damage_threshold + p.damage_threshold_growth_rate * t
    # Graded activation: exactly 0 below the threshold (low-risk patients never
    # activate, so incidence — who crosses at all — is unchanged), then ramps
    # smoothly to full over a band above it. Patients whose accumulated damage
    # settles just above threshold get PARTIAL gland involvement (subclinical/mild
    # hypothyroidism); those well above progress to overt disease. This replaces a
    # hard 0/1 switch that sent every crosser straight to overt destruction.
    disease_active = min(1.0, max(0.0, (damage - damage_threshold) / p.disease_activation_width))
    IFN_effect = (IFN ** p.Hill_IFN) / (p.EC50_IFN_death ** p.Hill_IFN + IFN ** p.Hill_IFN)
    thyrocyte_death = disease_active * p.k_death * IFN_effect * Thyro * p.susceptibility * memory_amp
    regen = p.k_regen * (p.Thyro_max - Thyro)
    dydt[s["Thyro"]] = -thyrocyte_death + regen

    # TPO activity: suppressed by chronic inflammation only after disease onset
    # (gated), recovers toward 1 otherwise. This lag lets the thyrotoxic release
    # precede synthetic failure.
    tpo_suppression = disease_active * p.k_tpo_sup * (IFN_effect + TNF / (TNF + 100.0))
    dydt[s["TPO"]] = p.k_tpo_rec * (1.0 - TPO) - tpo_suppression * TPO

    # Colloid: synthesized by functional gland, slow baseline release, plus a
    # destructive burst proportional to thyrocyte death (drives thyrotoxic spike).
    colloid_burst = p.k_coll_burst * thyrocyte_death * Colloid
    dydt[s["Colloid"]] = p.k_coll_syn * Thyro * TPO - p.k_coll_rel * Colloid - colloid_burst

    # Autoantibodies: production scales with effector EXPANSION above baseline
    # (so an untreated/non-responding patient does not auto-seroconvert) times
    # baseline propensity and susceptibility (overall autoimmune drive).
    ab_drive = (
        max(0.0, T_eff - p.T_eff0) / p.ab_effector_ref
        * (1.0 + p.HLA_factor * p.baseline_TPOAb)
        * p.susceptibility
    )
    dydt[s["TPOAb"]] = p.k_tpoab_prod * ab_drive - p.k_tpoab_decay * TPOAb
    dydt[s["TgAb"]] = p.k_tgab_prod * ab_drive - p.k_tgab_decay * TgAb

    # === Module 5: HPT axis ===
    # TSH-trophic compensation: elevated TSH (above setpoint) up-regulates the
    # surviving gland's synthetic output, buffering T4 so partial destruction
    # produces graded (subclinical -> overt) hypothyroidism instead of collapse.
    # Rests at 1.0 at baseline (TSH == TSH_set), so euthyroid state is preserved.
    tsh_excess = max(0.0, TSH - p.TSH_set)
    trophic = 1.0 + p.k_tsh_trophic * tsh_excess / (tsh_excess + p.tsh_trophic_half)
    synth = Thyro * TPO * trophic
    release_T4 = p.release_T4_frac * colloid_burst
    release_T3 = p.release_T3_frac * colloid_burst
    dydt[s["T4"]] = (
        p.k_syn_T4 * synth + release_T4 - p.k_deg_T4 * T4 - p.k_conv_T4_T3 * T4
    )
    dydt[s["T3"]] = (
        p.k_syn_T3 * synth + p.k_conv_T4_T3 * T4 + release_T3 - p.k_deg_T3 * T3
    )
    # TSH: bounded negative feedback. TSH relaxes toward TSH_set*(T4_set/T4)^hill,
    # which stays >= 0, rises when T4 falls (hypothyroid) and is suppressed when
    # T4 spikes during the thyrotoxic phase. Smoothly saturated near a ceiling.
    fb_ratio = (p.T4_set / max(T4, 1.0)) ** p.TSH_feedback_hill
    raw_target = p.TSH_set * fb_ratio
    # Smooth saturation toward the physiological ceiling (approaches but never pins
    # at the cap), replacing a hard clamp that flattened all overt cases onto 200.
    TSH_target = raw_target / (1.0 + (raw_target / p.TSH_ceiling) ** 2) ** 0.5
    dydt[s["TSH"]] = p.k_metab_TSH * (TSH_target - TSH)

    return dydt
