"""
Population-level susceptibility sampling for the expanded model.

Susceptibility is modeled as a two-component MIXTURE: a minority "high-risk"
subpopulation (genetic / pre-existing-autoimmunity predisposition, e.g. HLA-DQ
risk or baseline thyroid autoantibodies) that develops thyroid dysfunction under
checkpoint blockade, and a "low-risk" majority that mostly plateaus below the
disease threshold. This decouples incidence (set by the high-risk fraction and
per-drug conversion) from onset timing (set by how fast high-risk patients cross),
which a single unimodal distribution cannot do.

Default parameters are the CALIBRATED population values (see
scripts/calibration/calibrate_expanded_model.py and
results/v1/calibration_report.json).
"""
from __future__ import annotations

import numpy as np

# Calibrated mixture parameters.
HIGHRISK_FRACTION = 0.092   # fraction in the high-risk component
MEDIAN_HIGH = 1.70         # lognormal median of high-risk susceptibility
MEDIAN_LOW = 0.45          # lognormal median of low-risk susceptibility
SIGMA = 0.30               # shared log-space spread
SUSC_CLIP = (0.20, 2.8)


def sample_susceptibility(n: int, rng: np.random.Generator,
                          highrisk_fraction: float = HIGHRISK_FRACTION,
                          median_high: float = MEDIAN_HIGH,
                          median_low: float = MEDIAN_LOW,
                          sigma: float = SIGMA) -> np.ndarray:
    """Draw n susceptibility multipliers from the calibrated bimodal mixture."""
    is_high = rng.random(n) < highrisk_fraction
    med = np.where(is_high, median_high, median_low)
    draws = rng.lognormal(mean=np.log(med), sigma=sigma)
    return np.clip(draws, *SUSC_CLIP)
