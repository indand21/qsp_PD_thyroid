"""
Unit tests for the expanded QSP model (qsp_expanded).

These assert structural/qualitative properties that must hold regardless of exact
parameter calibration (the model is intentionally NOT calibrated to specific
incidence numbers): baseline euthyroid rest state, delayed-onset disease in a
susceptible patient, a biphasic thyrotoxic->hypothyroid trajectory, bounded
physiological ranges, and that every drug/regimen runs.
"""
import numpy as np
import pytest

from qsp_expanded import (
    STATE_NAMES,
    ExpandedParameters,
    DRUG_PK,
    REGIMENS,
    simulate_expanded_patient,
    expanded_risk_score,
)

ALL_TREATMENTS = list(DRUG_PK.keys()) + list(REGIMENS.keys())


def test_state_vector_size():
    assert len(STATE_NAMES) == 19
    assert STATE_NAMES[0] == "O_pd1"
    assert STATE_NAMES[-1] == "TSH"


@pytest.mark.parametrize("treatment", ALL_TREATMENTS)
def test_all_treatments_run(treatment):
    df = simulate_expanded_patient(treatment, ExpandedParameters(susceptibility=1.5), t_span=(0, 180))
    assert len(df) == 181
    # No NaNs/infs in the trajectory
    assert np.isfinite(df[STATE_NAMES].to_numpy()).all()
    # Classification columns present
    for col in ("thyroid_status", "hypo_grade", "hyper_grade"):
        assert col in df.columns


def test_baseline_euthyroid_start():
    """At t=0 the patient rests at euthyroid setpoints."""
    df = simulate_expanded_patient("nivolumab", ExpandedParameters(susceptibility=1.0), t_span=(0, 180))
    assert df["T4"].iloc[0] == pytest.approx(12.0, abs=0.5)
    assert df["T3"].iloc[0] == pytest.approx(4.8, abs=0.3)
    assert df["TSH"].iloc[0] == pytest.approx(1.5, abs=0.3)
    assert df["thyroid_status"].iloc[0] == "euthyroid"


def test_tsh_bounded_nonnegative():
    """TSH stays non-negative and below the physiological ceiling."""
    df = simulate_expanded_patient("nivolumab_ipilimumab", ExpandedParameters(susceptibility=2.0), t_span=(0, 180))
    assert df["TSH"].min() >= 0.0
    assert df["TSH"].max() <= 205.0


def test_susceptible_patient_develops_disease():
    """A high-susceptibility patient on a strong regimen develops hypothyroidism."""
    df = simulate_expanded_patient("nivolumab_ipilimumab", ExpandedParameters(susceptibility=2.0), t_span=(0, 180))
    r = expanded_risk_score(df)
    assert r["any_hypothyroidism"] is True
    # Onset is delayed (not immediate)
    assert r["hypo_onset_days"] > 30.0


def test_biphasic_trajectory_possible():
    """The model can produce a biphasic thyrotoxic->hypothyroid course."""
    df = simulate_expanded_patient("nivolumab", ExpandedParameters(susceptibility=1.8, baseline_TPOAb=0.5), t_span=(0, 180))
    r = expanded_risk_score(df)
    assert r["any_hyperthyroidism"] is True
    assert r["any_hypothyroidism"] is True
    assert r["biphasic"] is True
    assert r["hyper_onset_days"] < r["hypo_onset_days"]


def test_low_susceptibility_is_protected_early():
    """A low-susceptibility patient is still euthyroid at day 30 (no instant crash)."""
    df = simulate_expanded_patient("nivolumab", ExpandedParameters(susceptibility=0.6), t_span=(0, 30))
    assert df["thyroid_status"].iloc[-1] == "euthyroid"


def test_combination_stronger_than_monotherapy():
    """Combination therapy drives stronger effector expansion than either agent alone."""
    p = ExpandedParameters(susceptibility=1.5)
    combo = simulate_expanded_patient("nivolumab_ipilimumab", p, t_span=(0, 180))
    nivo = simulate_expanded_patient("nivolumab", p, t_span=(0, 180))
    assert combo["T_eff"].max() > nivo["T_eff"].max()
