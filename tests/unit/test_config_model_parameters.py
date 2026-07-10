"""
Unit tests for model parameters module.

This module tests the ModelParameters class and its functionality.
"""

import pytest
from typing import Dict, Any

from config.model_parameters import ModelParameters


class TestModelParameters:
    """Test cases for ModelParameters class."""
    
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = ModelParameters()
        
        # Test drug binding parameters
        assert params.Kd_nivo_PD1 == 2.6
        assert params.Kd_pembro_PD1 == 3.2
        assert params.Kd_atezo_PDL1 == 0.8
        assert params.Kd_durva_PDL1 == 1.0
        
        # Test drug susceptibility rates
        assert params.drug_susceptibility_rates['nivolumab'] == 0.25
        assert params.drug_susceptibility_rates['pembrolizumab'] == 0.30
        assert params.drug_susceptibility_rates['atezolizumab'] == 0.20
        assert params.drug_susceptibility_rates['durvalumab'] == 0.18
        
        # Test drug activation thresholds
        assert params.drug_activation_thresholds['nivolumab'] == 8000.0
        assert params.drug_activation_thresholds['pembrolizumab'] == 6000.0
        assert params.drug_activation_thresholds['atezolizumab'] == 45000.0
        assert params.drug_activation_thresholds['durvalumab'] == 35000.0
        
        # Test T-cell dynamics
        assert params.alpha == 4e-4
        assert params.beta == 0.12
        assert params.gamma == 1.0
        assert params.delta == 0.005
        assert params.T_eff0 == 1.5e3
        
        # Test cytokine parameters
        assert params.epsilon == 2.0
        assert params.k_clear_IFN == 1.2
        assert params.EC50_IFN_death == 85
        assert params.Hill_IFN == 1.2
        
        # Test damage accumulation
        assert params.base_damage_threshold == 0.025
        assert params.damage_threshold_growth_rate == 0.00005
        assert params.damage_accumulation_rate == 800000.0
        assert params.damage_decay_rate == 0.0005
        assert params.cytokine_threshold_pg_ml == 120.0
        
        # Test time-dependent damage gating
        assert params.minimum_exposure_days == 45.0
        assert params.damage_ramp_time == 30.0
        
        # Test thyrocyte dynamics
        assert params.k_death == 0.008
        assert params.k_regen == 0.055
        assert params.initial_regeneration_capacity == 0.055
        assert params.regeneration_decline_rate == 0.0004
        assert params.min_regeneration_capacity == 0.020
        
        # Test thyroid hormone synthesis
        assert params.k_syn_T3 == 3.0
        assert params.k_syn_T4 == 14.0
        assert params.k_deg_T3 == 0.693
        assert params.k_deg_T4 == 0.099
        
        # Test HPT axis parameters
        assert params.TSH_set == 1.5
        assert params.T3_set == 4.8
        assert params.T4_set == 12.0
        assert params.theta == 0.10
        assert params.k_metab_TSH == 0.05
        
        # Test other parameters
        assert params.Thyro_max == 1.0
        assert params.immune_memory_factor == 1.1
        assert params.memory_accumulation_rate == 0.0005
        
        # Test patient covariates
        assert params.sex_factor == 1.0
        assert params.age_factor == 1.0
        assert params.HLA_factor == 1.0
        assert params.TPO_Ab_titer == 0.0
        
        # Test drug PK parameters
        assert params.drug_clearance == 0.2
        assert params.drug_volume == 6.0
        assert params.dosing_interval == 14
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        custom_params = {
            'alpha': 5e-4,
            'beta': 0.15,
            'Kd_nivo_PD1': 3.0,
            'drug_susceptibility_rates': {
                'nivolumab': 0.30,
                'pembrolizumab': 0.35,
                'atezolizumab': 0.25,
                'durvalumab': 0.20
            }
        }
        
        params = ModelParameters(**custom_params)
        
        assert params.alpha == 5e-4
        assert params.beta == 0.15
        assert params.Kd_nivo_PD1 == 3.0
        assert params.drug_susceptibility_rates['nivolumab'] == 0.30
        assert params.drug_susceptibility_rates['pembrolizumab'] == 0.35
    
    def test_get_parameter_definitions(self):
        """Test parameter definitions retrieval."""
        params = ModelParameters()
        definitions = params.get_parameter_definitions()
        
        # Test that all expected parameters are defined
        expected_params = [
            'Kd_nivo_PD1', 'Kd_pembro_PD1', 'Kd_atezo_PDL1', 'Kd_durva_PDL1',
            'alpha', 'beta', 'gamma', 'delta', 'T_eff0',
            'epsilon', 'k_clear_IFN', 'EC50_IFN_death', 'Hill_IFN',
            'base_damage_threshold', 'damage_threshold_growth_rate',
            'damage_accumulation_rate', 'damage_decay_rate', 'cytokine_threshold_pg_ml',
            'minimum_exposure_days', 'damage_ramp_time',
            'k_death', 'k_regen', 'initial_regeneration_capacity',
            'regeneration_decline_rate', 'min_regeneration_capacity',
            'k_syn_T3', 'k_syn_T4', 'k_deg_T3', 'k_deg_T4',
            'TSH_set', 'T3_set', 'T4_set', 'theta', 'k_metab_TSH',
            'Thyro_max', 'immune_memory_factor', 'memory_accumulation_rate',
            'sex_factor', 'age_factor', 'HLA_factor', 'TPO_Ab_titer',
            'drug_clearance', 'drug_volume', 'dosing_interval'
        ]
        
        for param in expected_params:
            assert param in definitions
            assert 'type' in definitions[param]
            assert 'description' in definitions[param]
            assert 'units' in definitions[param]
        
        # Test specific parameter definition
        alpha_def = definitions['alpha']
        assert alpha_def['type'] == float
        assert alpha_def['min'] == 1e-6
        assert alpha_def['max'] == 1e-2
        assert 'APC-driven T-cell expansion rate' in alpha_def['description']
        assert alpha_def['units'] == '1/day'
    
    def test_validate_drug_susceptibility_rates(self):
        """Test validation of drug susceptibility rates."""
        # Valid rates
        valid_rates = {
            'nivolumab': 0.25,
            'pembrolizumab': 0.30,
            'atezolizumab': 0.20,
            'durvalumab': 0.18
        }
        params = ModelParameters(drug_susceptibility_rates=valid_rates)
        assert params.drug_susceptibility_rates == valid_rates
        
        # Invalid drug name
        with pytest.raises(ValueError, match="Invalid drug name"):
            ModelParameters(drug_susceptibility_rates={
                'nivolumab': 0.25,
                'invalid_drug': 0.30,
                'atezolizumab': 0.20,
                'durvalumab': 0.18
            })
        
        # Invalid rate (negative)
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            ModelParameters(drug_susceptibility_rates={
                'nivolumab': -0.1,
                'pembrolizumab': 0.30,
                'atezolizumab': 0.20,
                'durvalumab': 0.18
            })
        
        # Invalid rate (greater than 1)
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            ModelParameters(drug_susceptibility_rates={
                'nivolumab': 1.5,
                'pembrolizumab': 0.30,
                'atezolizumab': 0.20,
                'durvalumab': 0.18
            })
    
    def test_validate_drug_activation_thresholds(self):
        """Test validation of drug activation thresholds."""
        # Valid thresholds
        valid_thresholds = {
            'nivolumab': 8000.0,
            'pembrolizumab': 6000.0,
            'atezolizumab': 45000.0,
            'durvalumab': 35000.0
        }
        params = ModelParameters(drug_activation_thresholds=valid_thresholds)
        assert params.drug_activation_thresholds == valid_thresholds
        
        # Invalid drug name
        with pytest.raises(ValueError, match="Invalid drug name"):
            ModelParameters(drug_activation_thresholds={
                'nivolumab': 8000.0,
                'invalid_drug': 6000.0,
                'atezolizumab': 45000.0,
                'durvalumab': 35000.0
            })
        
        # Invalid threshold (zero)
        with pytest.raises(ValueError, match="must be positive"):
            ModelParameters(drug_activation_thresholds={
                'nivolumab': 0.0,
                'pembrolizumab': 6000.0,
                'atezolizumab': 45000.0,
                'durvalumab': 35000.0
            })
        
        # Invalid threshold (negative)
        with pytest.raises(ValueError, match="must be positive"):
            ModelParameters(drug_activation_thresholds={
                'nivolumab': -1000.0,
                'pembrolizumab': 6000.0,
                'atezolizumab': 45000.0,
                'durvalumab': 35000.0
            })
    
    def test_get_drug_parameters(self):
        """Test getting drug-specific parameters."""
        params = ModelParameters()
        
        # Test nivolumab parameters
        nivo_params = params.get_drug_parameters('nivolumab')
        assert nivo_params['susceptibility_rate'] == 0.25
        assert nivo_params['activation_threshold'] == 8000.0
        assert nivo_params['Kd'] == 2.6
        
        # Test pembrolizumab parameters
        pembro_params = params.get_drug_parameters('pembrolizumab')
        assert pembro_params['susceptibility_rate'] == 0.30
        assert pembro_params['activation_threshold'] == 6000.0
        assert pembro_params['Kd'] == 3.2
        
        # Test atezolizumab parameters
        atezo_params = params.get_drug_parameters('atezolizumab')
        assert atezo_params['susceptibility_rate'] == 0.20
        assert atezo_params['activation_threshold'] == 45000.0
        assert atezo_params['Kd'] == 0.8
        
        # Test durvalumab parameters
        durva_params = params.get_drug_parameters('durvalumab')
        assert durva_params['susceptibility_rate'] == 0.18
        assert durva_params['activation_threshold'] == 35000.0
        assert durva_params['Kd'] == 1.0
        
        # Test invalid drug type
        with pytest.raises(ValueError, match="Unknown drug type"):
            params.get_drug_parameters('invalid_drug')
    
    def test_update_drug_parameters(self):
        """Test updating drug-specific parameters."""
        params = ModelParameters()
        
        # Update nivolumab parameters
        params.update_drug_parameters(
            'nivolumab',
            susceptibility_rate=0.35,
            activation_threshold=9000.0,
            Kd=3.0
        )
        
        assert params.drug_susceptibility_rates['nivolumab'] == 0.35
        assert params.drug_activation_thresholds['nivolumab'] == 9000.0
        assert params.Kd_nivo_PD1 == 3.0
        
        # Update partial parameters
        params.update_drug_parameters(
            'pembrolizumab',
            susceptibility_rate=0.40
        )
        
        assert params.drug_susceptibility_rates['pembrolizumab'] == 0.40
        assert params.drug_activation_thresholds['pembrolizumab'] == 6000.0  # Unchanged
        assert params.Kd_pembro_PD1 == 3.2  # Unchanged
        
        # Test invalid drug type
        with pytest.raises(ValueError, match="Unknown drug type"):
            params.update_drug_parameters('invalid_drug', susceptibility_rate=0.5)
    
    def test_parameter_validation(self):
        """Test parameter validation functionality."""
        params = ModelParameters()
        
        # Test valid parameters
        errors = params.validate_parameters()
        assert len(errors) == 0
        
        # Test invalid parameters
        params.alpha = -0.001  # Below minimum
        params.beta = 2.0      # Above maximum
        params.k_death = 0.2   # Above maximum
        
        errors = params.validate_parameters()
        assert len(errors) >= 3
        
        error_messages = ' '.join(errors)
        assert 'alpha' in error_messages
        assert 'beta' in error_messages
        assert 'k_death' in error_messages
    
    def test_serialization(self):
        """Test parameter serialization and deserialization."""
        # Create custom parameters
        original_params = ModelParameters(
            alpha=5e-4,
            beta=0.15,
            Kd_nivo_PD1=3.0,
            version="2.0.0",
            description="Custom parameters for testing"
        )
        
        # Convert to dict and back
        params_dict = original_params.to_dict()
        restored_params = ModelParameters.from_dict(params_dict)
        
        # Check that parameters are restored correctly
        assert restored_params.alpha == 5e-4
        assert restored_params.beta == 0.15
        assert restored_params.Kd_nivo_PD1 == 3.0
        assert restored_params.version == "2.0.0"
        assert restored_params.description == "Custom parameters for testing"
        
        # Convert to JSON and back
        json_str = original_params.to_json()
        restored_from_json = ModelParameters.from_json(json_str)
        
        # Check that parameters are restored correctly
        assert restored_from_json.alpha == 5e-4
        assert restored_from_json.beta == 0.15
        assert restored_from_json.Kd_nivo_PD1 == 3.0
    
    def test_parameter_comparison(self):
        """Test parameter comparison functionality."""
        params1 = ModelParameters(alpha=4e-4, beta=0.12)
        params2 = ModelParameters(alpha=4e-4, beta=0.12)
        params3 = ModelParameters(alpha=5e-4, beta=0.12)
        
        # Identical parameters
        differences = params1.compare_parameters(params2)
        assert len(differences) == 0
        
        # Different alpha
        differences = params1.compare_parameters(params3)
        assert len(differences) == 1
        assert 'alpha' in differences
        assert differences['alpha'] == (4e-4, 5e-4)
    
    def test_change_tracking(self):
        """Test change tracking functionality."""
        params = ModelParameters(alpha=4e-4)
        
        # Initially unchanged
        assert not params.has_changed()
        
        # Modify parameter
        params.alpha = 5e-4
        
        # Should detect change
        assert params.has_changed()
        
        # Update hash should reset change detection
        params.update_timestamp()
        assert not params.has_changed()
    
    def test_parameter_ranges(self):
        """Test that all parameters are within defined ranges."""
        params = ModelParameters()
        definitions = params.get_parameter_definitions()
        
        for param_name, param_def in definitions.items():
            if 'min' in param_def or 'max' in param_def:
                value = getattr(params, param_name)
                
                if 'min' in param_def:
                    assert value >= param_def['min'], f"{param_name} {value} < {param_def['min']}"
                
                if 'max' in param_def:
                    assert value <= param_def['max'], f"{param_name} {value} > {param_def['max']}"
    
    def test_edge_case_parameters(self):
        """Test edge case parameter values."""
        # Test minimum values
        min_params = ModelParameters(
            alpha=1e-6,  # Minimum
            beta=0.01,   # Minimum
            gamma=0.1,   # Minimum
            delta=1e-4,  # Minimum
            T_eff0=100,  # Minimum
            k_death=1e-4,  # Minimum
            k_regen=0.001,  # Minimum
            sex_factor=0.5,  # Minimum
            age_factor=0.5,  # Minimum
            HLA_factor=0.5,  # Minimum
            TPO_Ab_titer=0.0  # Minimum
        )
        
        errors = min_params.validate_parameters()
        assert len(errors) == 0
        
        # Test maximum values
        max_params = ModelParameters(
            alpha=1e-2,   # Maximum
            beta=1.0,     # Maximum
            gamma=10.0,   # Maximum
            delta=0.1,    # Maximum
            T_eff0=10000, # Maximum
            k_death=0.1,  # Maximum
            k_regen=0.2,  # Maximum
            sex_factor=2.0,  # Maximum
            age_factor=2.0,  # Maximum
            HLA_factor=2.0,  # Maximum
            TPO_Ab_titer=1000.0  # Maximum
        )
        
        errors = max_params.validate_parameters()
        assert len(errors) == 0