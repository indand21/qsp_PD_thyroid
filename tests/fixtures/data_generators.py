"""
Test data generators for QSP_PD_Thyroid testing framework.

This module provides functions to generate synthetic test data for various scenarios.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
import yaml
import json

from config import ModelParameters, NivolumabParameters, PembrolizumabParameters


def generate_patient_data(
    n_patients: int = 10,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic patient data for testing.
    
    Args:
        n_patients: Number of patients to generate
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with patient data
    """
    if seed is not None:
        np.random.seed(seed)
    
    patient_ids = [f"TEST{i:04d}" for i in range(1, n_patients + 1)]
    
    # Generate realistic patient characteristics
    data = {
        'patient_id': patient_ids,
        'age': np.random.normal(65, 12, n_patients),  # Age around 65 ± 12 years
        'sex': np.random.choice(['M', 'F'], n_patients, p=[0.6, 0.4]),
        'damage_susceptibility': np.random.beta(2, 5, n_patients) * 1.5 + 0.5,  # 0.5-2.0 range
        'HLA_risk': np.random.choice([0.8, 1.0, 1.2, 1.5], n_patients, p=[0.3, 0.4, 0.2, 0.1]),
        'TPO_Ab_positive': np.random.choice([0, 1], n_patients, p=[0.7, 0.3]),
        'baseline_TSH': np.random.normal(1.5, 0.5, n_patients),
        'baseline_T3': np.random.normal(4.8, 0.3, n_patients),
        'baseline_T4': np.random.normal(12.0, 1.0, n_patients)
    }
    
    df = pd.DataFrame(data)
    
    # Calculate derived factors
    df['age_factor'] = np.clip(1.0 + (df['age'] - 50) * 0.01, 0.8, 1.3)
    df['sex_factor'] = np.where(df['sex'] == 'F', 1.2, 1.0)
    df['HLA_factor'] = df['HLA_risk']
    df['TPO_Ab_titer'] = np.where(df['TPO_Ab_positive'], np.random.uniform(50, 200, n_patients), 0.0)
    
    # Ensure physiological constraints
    df['damage_susceptibility'] = np.clip(df['damage_susceptibility'], 0.5, 2.0)
    df['baseline_TSH'] = np.clip(df['baseline_TSH'], 0.4, 4.0)
    df['baseline_T3'] = np.clip(df['baseline_T3'], 3.5, 6.5)
    df['baseline_T4'] = np.clip(df['baseline_T4'], 8.0, 18.0)
    
    return df


def generate_time_series_data(
    time_span: Tuple[float, float] = (0, 180),
    dt: float = 1.0,
    noise_level: float = 0.05,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic time series data for testing.
    
    Args:
        time_span: Time range (start, end) in days
        dt: Time step in days
        noise_level: Level of random noise to add (0-1)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with time series data
    """
    if seed is not None:
        np.random.seed(seed)
    
    time_points = np.arange(time_span[0], time_span[1] + dt, dt)
    n_points = len(time_points)
    
    # Generate realistic biomarker trajectories
    data = {
        'time': time_points,
        
        # Drug concentration (exponential decay with periodic dosing)
        'drug_conc': 1000 * np.exp(-time_points / 14) * (1 + 0.3 * np.sin(2 * np.pi * time_points / 14)),
        
        # Immune response
        'T_eff': 1500 * (1 + 0.5 * np.exp(-time_points / 30) * np.sin(2 * np.pi * time_points / 7)),
        'IFN': 50 * np.exp(-time_points / 20) * (1 + 0.2 * np.sin(2 * np.pi * time_points / 5)),
        
        # Thyroid function
        'Thyro': 1.0 * np.exp(-0.001 * time_points) * (1 - 0.1 * np.exp(-time_points / 60)),
        'T3': 4.8 * (1 - 0.1 * (1 - np.exp(-time_points / 90))),
        'TSH': 1.5 * (1 + 0.2 * (1 - np.exp(-time_points / 80))),
        
        # Damage accumulation
        'cumulative_damage': np.clip(0.001 * time_points * (1 + 0.5 * np.exp(-time_points / 40)), 0, 0.1)
    }
    
    df = pd.DataFrame(data)
    
    # Add noise if requested
    if noise_level > 0:
        for col in ['drug_conc', 'T_eff', 'IFN', 'Thyro', 'T3', 'TSH']:
            noise = np.random.normal(0, noise_level * df[col].std(), n_points)
            df[col] = np.maximum(0, df[col] + noise)
    
    # Calculate derived quantities
    df['thyrocyte_loss_pct'] = (1.0 - df['Thyro']) * 100
    df['hypothyroid_grade'] = classify_hypothyroidism_simple(df['TSH'], df['T3'])
    
    return df


def classify_hypothyroidism_simple(TSH: pd.Series, T3: pd.Series) -> pd.Series:
    """
    Simple hypothyroidism classification for test data generation.
    
    Args:
        TSH: TSH values
        T3: T3 values
        
    Returns:
        Hypothyroidism grades (0-4)
    """
    grades = pd.Series(0, index=TSH.index)
    grades[(TSH > 4.5) & (TSH <= 10.0) & (T3 >= 3.1)] = 1
    grades[(TSH > 10.0) | (T3 < 3.1)] = 2
    grades[(TSH > 20.0) | (T3 < 2.5)] = 3
    grades[(TSH > 50.0) | (T3 < 2.0)] = 4
    return grades


def generate_population_simulation_results(
    n_patients: int = 100,
    drug_type: str = 'nivolumab',
    incidence_rate: float = 0.15,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generate synthetic population simulation results for testing.
    
    Args:
        n_patients: Number of patients
        drug_type: Type of drug
        incidence_rate: Target incidence rate for hypothyroidism
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with population results
    """
    if seed is not None:
        np.random.seed(seed)
    
    patient_data = generate_patient_data(n_patients, seed)
    
    # Simulate outcomes based on risk factors
    risk_scores = (
        patient_data['damage_susceptibility'] *
        patient_data['sex_factor'] *
        patient_data['HLA_factor'] *
        (1 + 0.5 * patient_data['TPO_Ab_positive'])
    )
    
    # Normalize risk scores to target incidence rate
    risk_scores = risk_scores / risk_scores.max()
    hypothyroidism_prob = risk_scores * incidence_rate * 2  # Scale to hit target
    
    # Generate outcomes
    any_hypothyroidism = np.random.random(n_patients) < hypothyroidism_prob
    grade2_hypothyroidism = any_hypothyroidism & (np.random.random(n_patients) < 0.4)
    
    # Generate time to onset (log-normal distribution)
    time_to_onset = np.full(n_patients, np.nan)
    onset_mask = grade2_hypothyroidism
    n_onset = onset_mask.sum()
    if n_onset > 0:
        time_to_onset[onset_mask] = np.random.lognormal(
            np.log(90), 0.3, n_onset
        ).clip(30, 180)
    
    # Generate hormone values
    peak_TSH = np.where(
        any_hypothyroidism,
        np.random.normal(15, 5, n_patients).clip(5, 50),
        np.random.normal(2, 0.5, n_patients).clip(0.5, 4.5)
    )
    
    min_T3 = np.where(
        any_hypothyroidism,
        np.random.normal(3.0, 0.5, n_patients).clip(1.5, 4.5),
        np.random.normal(4.8, 0.3, n_patients).clip(4.0, 6.0)
    )
    
    # Generate other metrics
    max_thyrocyte_loss = np.where(
        any_hypothyroidism,
        np.random.beta(2, 5, n_patients) * 50,
        np.random.beta(1, 10, n_patients) * 10
    )
    
    peak_IFN = np.random.exponential(20, n_patients).clip(5, 200)
    
    # Create results dataframe
    results = pd.DataFrame({
        'patient_id': patient_data['patient_id'],
        'damage_susceptibility': patient_data['damage_susceptibility'],
        'drug_type': drug_type,
        'any_hypothyroidism': any_hypothyroidism.astype(float),
        'grade2_hypothyroidism': grade2_hypothyroidism.astype(float),
        'time_to_onset_days': time_to_onset,
        'peak_TSH_mIU_per_L': peak_TSH,
        'min_T3_pmol_per_L': min_T3,
        'peak_IFN_pg_per_mL': peak_IFN,
        'max_thyrocyte_loss_percent': max_thyrocyte_loss,
        'age': patient_data['age'],
        'sex': patient_data['sex'],
        'HLA_risk': patient_data['HLA_risk'],
        'TPO_Ab_positive': patient_data['TPO_Ab_positive']
    })
    
    return results


def generate_config_variations(
    base_params: ModelParameters,
    variation_percent: float = 0.1
) -> List[Dict[str, Any]]:
    """
    Generate parameter variations for sensitivity testing.
    
    Args:
        base_params: Base parameters to vary
        variation_percent: Percentage variation for each parameter
        
    Returns:
        List of parameter dictionaries
    """
    variations = []
    
    # Get parameter names that can be varied
    param_names = [
        'alpha', 'beta', 'gamma', 'delta', 'T_eff0',
        'epsilon', 'k_clear_IFN', 'EC50_IFN_death', 'Hill_IFN',
        'base_damage_threshold', 'damage_accumulation_rate', 'damage_decay_rate',
        'cytokine_threshold_pg_ml', 'k_death', 'k_regen',
        'k_syn_T3', 'k_syn_T4', 'k_deg_T3', 'k_deg_T4',
        'TSH_set', 'T3_set', 'T4_set', 'theta', 'k_metab_TSH'
    ]
    
    # Create base variation
    base_dict = {}
    for name in param_names:
        if hasattr(base_params, name):
            base_dict[name] = getattr(base_params, name)
    variations.append(base_dict)
    
    # Create individual parameter variations
    for name in param_names:
        if hasattr(base_params, name):
            base_value = getattr(base_params, name)
            if base_value > 0:
                # Increase parameter
                varied_dict = base_dict.copy()
                varied_dict[name] = base_value * (1 + variation_percent)
                variations.append(varied_dict)
                
                # Decrease parameter
                varied_dict = base_dict.copy()
                varied_dict[name] = base_value * (1 - variation_percent)
                variations.append(varied_dict)
    
    return variations


def generate_test_config_file(
    params: Dict[str, Any],
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> Path:
    """
    Generate a test configuration file.
    
    Args:
        params: Parameter dictionary
        output_path: Path to save the config file
        metadata: Optional metadata to include
        
    Returns:
        Path to the created config file
    """
    config_data = {
        'model_parameters': params,
        'metadata': metadata or {
            'version': '1.0.0',
            'created_for': 'testing',
            'description': 'Generated test configuration'
        }
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(config_data, f, default_flow_style=False)
    
    return output_path


def generate_benchmark_data(
    n_simulations: int = 50,
    time_span: Tuple[float, float] = (0, 180),
    seed: Optional[int] = None
) -> Dict[str, List[float]]:
    """
    Generate benchmark data for performance testing.
    
    Args:
        n_simulations: Number of simulations to generate
        time_span: Time span for simulations
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with benchmark metrics
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Generate realistic performance metrics
    base_time = 0.5  # Base simulation time in seconds
    time_complexity = time_span[1] / 180.0  # Normalize to 180 days
    
    simulation_times = np.random.lognormal(
        np.log(base_time * time_complexity), 0.3, n_simulations
    ).clip(0.1, 10.0)
    
    memory_usage = np.random.normal(50, 10, n_simulations).clip(20, 100)
    ode_steps = np.random.poisson(1000 * time_complexity, n_simulations).clip(100, 5000)
    
    return {
        'simulation_times': simulation_times.tolist(),
        'memory_usage_mb': memory_usage.tolist(),
        'ode_solver_steps': ode_steps.tolist()
    }


def create_invalid_config_scenarios() -> List[Dict[str, Any]]:
    """
    Create invalid configuration scenarios for error testing.
    
    Returns:
        List of invalid parameter dictionaries
    """
    scenarios = []
    
    # Negative values
    scenarios.append({
        'alpha': -0.001,
        'beta': 0.12,
        'error_type': 'negative_parameter'
    })
    
    # Zero values where not allowed
    scenarios.append({
        'alpha': 0.0,
        'beta': 0.12,
        'error_type': 'zero_parameter'
    })
    
    # Extremely large values
    scenarios.append({
        'alpha': 1e6,
        'beta': 0.12,
        'error_type': 'extreme_parameter'
    })
    
    # Missing required parameters
    scenarios.append({
        'beta': 0.12,
        'gamma': 1.0,
        'error_type': 'missing_parameter'
    })
    
    # Invalid types
    scenarios.append({
        'alpha': 'invalid_string',
        'beta': 0.12,
        'error_type': 'invalid_type'
    })
    
    return scenarios