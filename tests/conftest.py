"""
Pytest configuration and common fixtures for QSP_PD_Thyroid testing.

This module provides shared fixtures and configuration for all test modules.
"""

import pytest
import numpy as np
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import project modules
from config import ModelParameters, NivolumabParameters, ConfigurationManager
from utils import get_logger

# Configure test logging
logger = get_logger("test_framework")


@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "random_seed": 42,
        "test_patient_id": "TEST001",
        "test_time_span": (0, 30),  # Shorter for faster tests
        "tolerance": 1e-6,
        "performance_threshold": {
            "single_simulation": 5.0,  # seconds
            "population_simulation": 30.0  # seconds
        }
    }


@pytest.fixture(scope="session")
def numpy_random_seed(test_config):
    """Set numpy random seed for reproducible tests."""
    seed = test_config["random_seed"]
    np.random.seed(seed)
    yield seed
    # No cleanup needed


@pytest.fixture
def temp_directory():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_model_parameters():
    """Create sample model parameters for testing."""
    return ModelParameters()


@pytest.fixture
def sample_nivolumab_parameters():
    """Create sample nivolumab parameters for testing."""
    return NivolumabParameters()


@pytest.fixture
def sample_patient_data():
    """Create sample patient data for testing."""
    return {
        "patient_id": "TEST001",
        "damage_susceptibility": 1.0,
        "sex_factor": 1.0,
        "age_factor": 1.0,
        "HLA_factor": 1.0,
        "TPO_Ab_titer": 0.0
    }


@pytest.fixture
def sample_time_series_data():
    """Create sample time series data for testing."""
    time_points = np.linspace(0, 30, 31)
    return pd.DataFrame({
        'time': time_points,
        'TSH': 1.5 + 0.1 * np.sin(time_points / 5),
        'T3': 4.8 + 0.2 * np.cos(time_points / 7),
        'T4': 12.0 + 0.5 * np.sin(time_points / 10),
        'IFN': 10.0 * np.exp(-time_points / 15),
        'Thyro': 1.0 * np.exp(-time_points / 50),
        'T_eff': 1500.0 * (1 + 0.5 * np.sin(time_points / 3))
    })


@pytest.fixture
def sample_ode_solution():
    """Create sample ODE solution for testing."""
    time_points = np.linspace(0, 30, 31)
    n_states = 7
    solution_data = np.random.random((n_states, len(time_points)))
    
    # Create mock solution object
    class MockSolution:
        def __init__(self, t, y, success=True):
            self.t = t
            self.y = y
            self.success = success
            self.message = "Test solution"
    
    return MockSolution(time_points, solution_data)


@pytest.fixture
def config_manager():
    """Create a configuration manager instance for testing."""
    return ConfigurationManager()


@pytest.fixture
def drug_types():
    """List of supported drug types for testing."""
    return ['nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab']


@pytest.fixture
def sample_config_file(temp_directory, sample_model_parameters):
    """Create a sample configuration file for testing."""
    config_file = temp_directory / "test_config.yaml"
    
    # Create a simple YAML config
    config_content = f"""
# Test configuration file
model_parameters:
  alpha: {sample_model_parameters.alpha}
  beta: {sample_model_parameters.beta}
  gamma: {sample_model_parameters.gamma}
  delta: {sample_model_parameters.delta}
  T_eff0: {sample_model_parameters.T_eff0}
  
  epsilon: {sample_model_parameters.epsilon}
  k_clear_IFN: {sample_model_parameters.k_clear_IFN}
  EC50_IFN_death: {sample_model_parameters.EC50_IFN_death}
  Hill_IFN: {sample_model_parameters.Hill_IFN}
  
  base_damage_threshold: {sample_model_parameters.base_damage_threshold}
  damage_threshold_growth_rate: {sample_model_parameters.damage_threshold_growth_rate}
  damage_accumulation_rate: {sample_model_parameters.damage_accumulation_rate}
  damage_decay_rate: {sample_model_parameters.damage_decay_rate}
  cytokine_threshold_pg_ml: {sample_model_parameters.cytokine_threshold_pg_ml}
  
  minimum_exposure_days: {sample_model_parameters.minimum_exposure_days}
  damage_ramp_time: {sample_model_parameters.damage_ramp_time}
  
  k_death: {sample_model_parameters.k_death}
  k_regen: {sample_model_parameters.k_regen}
  initial_regeneration_capacity: {sample_model_parameters.initial_regeneration_capacity}
  regeneration_decline_rate: {sample_model_parameters.regeneration_decline_rate}
  min_regeneration_capacity: {sample_model_parameters.min_regeneration_capacity}
  
  k_syn_T3: {sample_model_parameters.k_syn_T3}
  k_syn_T4: {sample_model_parameters.k_syn_T4}
  k_deg_T3: {sample_model_parameters.k_deg_T3}
  k_deg_T4: {sample_model_parameters.k_deg_T4}
  
  TSH_set: {sample_model_parameters.TSH_set}
  T3_set: {sample_model_parameters.T3_set}
  T4_set: {sample_model_parameters.T4_set}
  theta: {sample_model_parameters.theta}
  k_metab_TSH: {sample_model_parameters.k_metab_TSH}
  
  Thyro_max: {sample_model_parameters.Thyro_max}
  immune_memory_factor: {sample_model_parameters.immune_memory_factor}
  memory_accumulation_rate: {sample_model_parameters.memory_accumulation_rate}
  
  sex_factor: {sample_model_parameters.sex_factor}
  age_factor: {sample_model_parameters.age_factor}
  HLA_factor: {sample_model_parameters.HLA_factor}
  TPO_Ab_titer: {sample_model_parameters.TPO_Ab_titer}
  
  drug_clearance: {sample_model_parameters.drug_clearance}
  drug_volume: {sample_model_parameters.drug_volume}
  dosing_interval: {sample_model_parameters.dosing_interval}

metadata:
  version: "1.0.0"
  created_for: "testing"
  description: "Test configuration file"
"""
    
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_ode_solver():
    """Create a mock ODE solver for testing."""
    class MockODESolver:
        def __init__(self):
            self.solve_call_count = 0
            self.last_args = None
            self.last_kwargs = None
        
        def __call__(self, fun, t_span, y0, t_eval=None, method='LSODA', 
                     rtol=1e-6, atol=1e-9, max_step=1.0):
            self.solve_call_count += 1
            self.last_args = (fun, t_span, y0)
            self.last_kwargs = {
                't_eval': t_eval, 'method': method, 'rtol': rtol,
                'atol': atol, 'max_step': max_step
            }
            
            # Return mock solution
            t = np.linspace(t_span[0], t_span[1], len(t_eval) if t_eval is not None else 100)
            y = np.random.random((len(y0), len(t)))
            
            class MockSolution:
                def __init__(self, t, y):
                    self.t = t
                    self.y = y
                    self.success = True
                    self.message = "Mock solution"
            
            return MockSolution(t, y)
    
    return MockODESolver()


@pytest.fixture
def performance_data():
    """Sample performance data for benchmarking."""
    return {
        "single_simulation_times": [0.5, 0.6, 0.4, 0.7, 0.5],
        "population_simulation_times": [5.2, 6.1, 5.8, 6.5, 5.9],
        "memory_usage_mb": [50, 55, 48, 52, 51],
        "ode_solver_steps": [1000, 1200, 950, 1100, 1050]
    }


# Test markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as a smoke test"
    )
    config.addinivalue_line(
        "markers", "regression: mark test as a regression test"
    )
    config.addinivalue_line(
        "markers", "scientific: mark test as validating scientific accuracy"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on file location
        if "unit/" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to performance tests
        if "performance/" in str(item.fspath):
            item.add_marker(pytest.mark.slow)
        
        # Add smoke marker to basic functionality tests
        if "test_basic" in item.name or "test_init" in item.name:
            item.add_marker(pytest.mark.smoke)