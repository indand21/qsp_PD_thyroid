"""
Expanded model parameters, drug PK, and treatment regimens.

State ordering (STATE_NAMES) is the single source of truth for the ~19-state
vector and is imported by the ODE system, classifier, and simulator.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

# ---------------------------------------------------------------------------
# State vector (5 modules, 19 states)
# ---------------------------------------------------------------------------
STATE_NAMES: List[str] = [
    # Module 1 — checkpoint pharmacology (receptor occupancy, 0-1)
    "O_pd1", "O_ctla4",
    # Module 2 — T-cell dynamics
    "T_naive", "T_eff", "T_reg",
    # Module 3 — cytokine network (pg/mL scale)
    "IFN", "TNF", "IL2", "IL17",
    # Module 4 — thyroid gland & signaling
    "Thyro", "Colloid", "TPO", "cumulative_damage", "immune_memory", "TPOAb", "TgAb",
    # Module 5 — HPT axis
    "T4", "T3", "TSH",
]
STATE_INDEX: Dict[str, int] = {name: i for i, name in enumerate(STATE_NAMES)}
N_STATES = len(STATE_NAMES)


# ---------------------------------------------------------------------------
# Drug pharmacology (PK + target axis + occupancy EC50).
#
# `axis` selects which receptor-occupancy state a drug drives:
#   'PD1'   -> O_pd1  (anti-PD-1 and anti-PD-L1 both suppress PD-1 pathway signaling)
#   'CTLA4' -> O_ctla4
# EC50_occ (ng/mL) sets the concentration for half-maximal occupancy; values are
# anchored to the legacy `drug_activation_thresholds` so the occupancy scale
# tracks the existing calibration intuition.
# ---------------------------------------------------------------------------
DRUG_PK: Dict[str, Dict[str, float]] = {
    "nivolumab":     dict(CL=0.20, V=6.0, dose_mg_kg=3,  interval=14, EC50_occ=6600.0,  potency=1.00, axis="PD1"),
    "pembrolizumab": dict(CL=0.22, V=6.0, dose_mg_kg=2,  interval=21, EC50_occ=5800.0,  potency=0.95, axis="PD1"),
    "atezolizumab":  dict(CL=0.25, V=6.5, dose_mg_kg=15, interval=21, EC50_occ=45000.0, potency=0.55, axis="PD1"),
    "durvalumab":    dict(CL=0.24, V=6.2, dose_mg_kg=10, interval=14, EC50_occ=35000.0, potency=0.62, axis="PD1"),
    "ipilimumab":    dict(CL=0.15, V=7.0, dose_mg_kg=3,  interval=21, EC50_occ=20000.0, potency=0.85, axis="CTLA4"),
}

# Multi-drug regimens (monotherapies resolve to [drug] automatically).
REGIMENS: Dict[str, List[str]] = {
    "nivolumab_ipilimumab": ["nivolumab", "ipilimumab"],
}

# Drug/regimen -> mechanistic class (for aggregation & reporting).
DRUG_CLASS: Dict[str, str] = {
    "nivolumab": "PD-1",
    "pembrolizumab": "PD-1",
    "atezolizumab": "PD-L1",
    "durvalumab": "PD-L1",
    "ipilimumab": "CTLA-4",
    "nivolumab_ipilimumab": "Combination",
}


def resolve_regimen(name: str) -> List[str]:
    """Return the list of component drugs for a drug or regimen name."""
    if name in REGIMENS:
        return list(REGIMENS[name])
    if name in DRUG_PK:
        return [name]
    raise ValueError(f"Unknown drug/regimen: {name!r}")


def drug_class_of(name: str) -> str:
    """Return the mechanistic class for a drug or regimen name."""
    return DRUG_CLASS.get(name, "Unknown")


@dataclass
class ExpandedParameters:
    """
    Physiological/mechanistic parameters for the expanded model.

    Values are anchored to the legacy `FinalModelParameters` where a counterpart
    exists, extended with new rate constants for the added biology (Treg, extra
    cytokines, colloid/biphasic release, autoantibodies). The onset/damage/CTLA-4
    parameters here, together with the bimodal susceptibility mixture in
    `population.py`, are CALIBRATED so that 180-day per-drug hypothyroidism
    incidence lands in published ranges with correct class ordering and 60-140 day
    onset (see scripts/calibration/calibrate_expanded_model.py and
    results/v1/calibration_report.json).
    """

    # --- Module 1: checkpoint pharmacology ---
    k_occ: float = 0.5          # occupancy relaxation rate toward equilibrium (1/day)

    # --- Module 2: T-cell dynamics ---
    # Effector pool is driven by a baseline source S_eff0 = beta_eff * T_eff0
    # (computed in the RHS so baseline rests at T_eff0) amplified by checkpoint
    # occupancy. This mirrors the legacy source/decay balance and is robust.
    s_naive: float = 5.0        # naive T-cell source
    d_naive: float = 0.02       # naive death
    k_prime: float = 0.010      # naive->effector priming drain (CTLA-4 enhanced)
    w_ctla4_prime: float = 6.0  # CTLA-4 blockade enhancement of naive priming drain
    w_pd1_eff: float = 15.0     # PD-1 blockade relief of effector expansion
    w_ctla4_eff: float = 5.5   # CTLA-4 blockade contribution to effector activation
    treg_synergy: float = 0.95  # CTLA-4 blockade weakening of Treg suppression (0-1);
                                # drives super-additive PD-1 + CTLA-4 combination synergy
    beta_eff: float = 0.12      # effector death (S_eff0 = beta_eff * T_eff0)
    delta_il2: float = 0.004    # IL-2-driven effector proliferation
    k_treg_src: float = 15.0    # Treg source (baseline SS = k_treg_src / d_treg)
    d_treg: float = 0.05        # Treg turnover
    k_ctla4_treg: float = 0.08  # CTLA-4 blockade impairment/depletion of Treg
    treg_supp: float = 1.0      # baseline Treg suppressive strength on effectors
    T_eff0: float = 1500.0      # baseline effector scale
    T_reg0: float = 300.0       # baseline Treg scale (== k_treg_src / d_treg)
    T_naive0: float = 167.0     # baseline naive scale (== s_naive / (k_prime+d_naive))

    # --- Module 3: cytokine network ---
    eps_ifn: float = 20.0
    k_clear_ifn: float = 1.2
    eps_tnf: float = 1.2
    k_clear_tnf: float = 1.5
    eps_il2: float = 1.0
    k_clear_il2: float = 2.0
    eps_il17: float = 0.8
    k_clear_il17: float = 1.4
    ifn_tnf_crosstalk: float = 0.3   # TNF potentiates IFN production

    # --- Module 4: thyroid gland & signaling ---
    EC50_IFN_death: float = 85.0     # IFN EC50 for cytotoxic thyrocyte death
    Hill_IFN: float = 1.2
    cytokine_threshold_pg_ml: float = 60.0    # damage-accumulation cytokine gate
    base_damage_threshold: float = 0.020   # re-tuned with graded activation (was 0.025)
    damage_threshold_growth_rate: float = 5e-5
    # Damage accumulates at a SATURATING rate in cytokine drive:
    #   d(damage)/dt = damage_rate * drive/(drive+damage_half_sat) * gate * susc.
    # Saturation compresses the wide inter-drug cytokine range so that per-patient
    # susceptibility (not raw cytokine magnitude) governs whether the damage
    # threshold is crossed -> smooth, non-degenerate incidence differentiation.
    damage_half_sat: float = 150.0
    damage_rate: float = 7.0e-4
    damage_decay_rate: float = 0.0005
    # Damage repair/turnover (always active). Creates a sub-threshold equilibrium
    # so low-drive/low-susceptibility patients plateau below the disease threshold
    # (never develop dysfunction), while sufficiently-driven patients cross. This
    # decouples incidence (who crosses) from onset timing (how fast they cross).
    k_damage_repair: float = 0.010
    # Width of the graded disease-activation band above the damage threshold.
    # Damage settling just above threshold -> partial gland involvement (subclinical/
    # mild hypothyroidism); damage this far above -> full activation (overt disease).
    # Sets the SEVERITY spread among crossers without changing incidence (activation
    # is still exactly 0 at/below threshold).
    disease_activation_width: float = 0.028
    minimum_exposure_days: float = 25.0
    damage_ramp_time: float = 12.0
    k_death: float = 0.06            # cytotoxic thyrocyte death scale (gated)
    k_regen: float = 0.020           # follicular regeneration
    Thyro_max: float = 1.0
    memory_accumulation_rate: float = 0.0005
    immune_memory_factor: float = 1.1
    # TPO (thyroid peroxidase activity, 0-1) suppression/recovery
    k_tpo_rec: float = 0.05
    k_tpo_sup: float = 0.35
    # Colloid (stored preformed hormone pool); baseline SS = k_coll_syn/k_coll_rel.
    # A large reservoir sustains a multi-day thyrotoxic release when destruction
    # begins, before it depletes and synthetic failure drives hypothyroidism.
    k_coll_syn: float = 0.8          # colloid synthesis (proportional to Thyro*TPO)
    k_coll_rel: float = 0.02         # slow baseline colloid release (SS ~ 40)
    k_coll_burst: float = 5.4        # destructive release per unit thyrocyte death
                                     # (raised from 2.3 to restore the thyrotoxic/biphasic
                                     # spike under graded activation, which lowers the
                                     # instantaneous death rate feeding the colloid burst)
    # Autoantibodies (TPOAb, TgAb; titer units)
    k_tpoab_prod: float = 0.06
    k_tpoab_decay: float = 0.01
    k_tgab_prod: float = 0.04
    k_tgab_decay: float = 0.012
    ab_effector_ref: float = 3000.0  # effector level scaling antibody production

    # --- Module 5: HPT axis ---
    # Synthesis rates are balanced so that at baseline (Thyro=1, TPO=1) the axis
    # rests at the euthyroid setpoints: k_syn_T4 = (k_deg_T4+k_conv)*T4_set, and
    # k_syn_T3 = k_deg_T3*T3_set - k_conv*T4_set.
    k_syn_T4: float = 1.788          # (0.099+0.05)*12
    k_syn_T3: float = 2.726          # 0.693*4.8 - 0.05*12
    k_deg_T4: float = 0.099
    k_deg_T3: float = 0.693
    k_conv_T4_T3: float = 0.05       # peripheral T4->T3 conversion (DIO)
    release_T4_frac: float = 0.8     # fraction of colloid burst appearing as T4
    release_T3_frac: float = 0.2     # fraction appearing as T3
    T4_set: float = 12.0
    T3_set: float = 4.8
    TSH_set: float = 1.5
    # Bounded negative feedback: TSH relaxes toward TSH_set * (T4_set/T4)^hill,
    # so TSH stays >= 0, rises when hormone falls (hypo), is suppressed when
    # hormone spikes (thyrotoxic phase).
    TSH_feedback_hill: float = 2.5
    k_metab_TSH: float = 0.15
    TSH_ceiling: float = 200.0       # smooth saturation ceiling on TSH (mIU/L)
    # TSH is trophic: elevated TSH (above setpoint) up-regulates synthetic output
    # of the SURVIVING gland, buffering T4. This compensatory reserve makes partial
    # thyroid destruction yield a graded hypothyroid spectrum (subclinical -> overt)
    # rather than an all-or-none collapse that pins TSH at the ceiling. The factor
    # rests at 1.0 at baseline (TSH == TSH_set) so the euthyroid setpoint and the
    # thyrotoxic phase (TSH suppressed) are unchanged.
    k_tsh_trophic: float = 8.0       # max fold-increase in synthesis at saturating TSH excess
    tsh_trophic_half: float = 12.0   # TSH excess above setpoint at half-maximal trophic drive

    # --- Patient covariates (multiplicative modifiers) ---
    susceptibility: float = 1.0      # overall damage susceptibility (0.5-2.0)
    sex_factor: float = 1.0
    age_factor: float = 1.0
    HLA_factor: float = 1.0
    baseline_TPOAb: float = 0.0      # baseline autoantibody propensity

    def occupancy_equilibrium(self, conc_by_axis: Dict[str, float]) -> Dict[str, float]:
        """Placeholder kept for API symmetry; occupancy EC50 lives in DRUG_PK."""
        return conc_by_axis
