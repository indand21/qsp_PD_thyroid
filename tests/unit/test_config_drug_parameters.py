"""
Unit tests for drug parameters module.

This module tests the drug-specific parameter classes and factory functions.
"""

import pytest
from typing import Dict, Any

from config.drug_parameters import (
    NivolumabParameters,
    PembrolizumabParameters,
    AtezolizumabParameters,
    DurvalumabParameters,
    create_drug_parameters,
    DRUG_PARAMETER_CLASSES
)


class TestNivolumabParameters:
    """Test cases for NivolumabParameters class."""
    
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = NivolumabParameters()
        
        assert params.drug_type == "nivolumab"
        assert params.Kd == 2.6
        assert params.CL == 0.2
        assert params.V == 6.0
        assert params.dose_mg_kg == 3
        assert params.potency == 1.0
        assert params.susceptibility_rate == 0.25
        assert params.activation_threshold == 8000.0
        
        # Check that Kd_nivo_PD1 is set correctly
        assert params.Kd_nivo_PD1 == 2.6
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        params = NivolumabParameters(
            Kd=3.0,
            CL=0.25,
            potency=0.9,
            susceptibility_rate=0.30
        )
        
        assert params.Kd == 3.0
        assert params.CL == 0.25
        assert params.potency == 0.9
        assert params.susceptibility_rate == 0.30
        assert params.Kd_nivo_PD1 == 3.0  # Should be set from Kd
    
    def test_direct_kd_nivo_setting(self):
        """Test setting Kd_nivo_PD1 directly."""
        params = NivolumabParameters(Kd_nivo_PD1=4.0)
        
        assert params.Kd_nivo_PD1 == 4.0
        assert params.Kd == 2.6  # Should remain default
    
    def test_get_parameter_definitions(self):
        """Test parameter definitions retrieval."""
        params = NivolumabParameters()
        definitions = params.get_parameter_definitions()
        
        # Test that nivolumab-specific parameters are included
        nivolumab_specific = ['Kd', 'CL', 'V', 'dose_mg_kg', 'potency', 
                             'susceptibility_rate', 'activation_threshold']
        
        for param in nivolumab_specific:
            assert param in definitions
            assert 'type' in definitions[param]
            assert 'description' in definitions[param]
            assert 'units' in definitions[param]
        
        # Test specific parameter definition
        kd_def = definitions['Kd']
        assert kd_def['type'] == float
        assert kd_def['min'] == 0.1
        assert kd_def['max'] == 10.0
        assert 'nivolumab-PD1 binding' in kd_def['description']
        assert kd_def['units'] == 'nM'


class TestPembrolizumabParameters:
    """Test cases for PembrolizumabParameters class."""
    
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = PembrolizumabParameters()
        
        assert params.drug_type == "pembrolizumab"
        assert params.Kd == 3.2
        assert params.CL == 0.22
        assert params.V == 6.0
        assert params.dose_mg_kg == 2
        assert params.potency == 0.85
        assert params.susceptibility_rate == 0.30
        assert params.activation_threshold == 6000.0
        
        # Check that Kd_pembro_PD1 is set correctly
        assert params.Kd_pembro_PD1 == 3.2
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        params = PembrolizumabParameters(
            Kd=3.5,
            CL=0.24,
            potency=0.9,
            susceptibility_rate=0.35
        )
        
        assert params.Kd == 3.5
        assert params.CL == 0.24
        assert params.potency == 0.9
        assert params.susceptibility_rate == 0.35
        assert params.Kd_pembro_PD1 == 3.5  # Should be set from Kd
    
    def test_get_parameter_definitions(self):
        """Test parameter definitions retrieval."""
        params = PembrolizumabParameters()
        definitions = params.get_parameter_definitions()
        
        # Test that pembrolizumab-specific parameters are included
        pembrolizumab_specific = ['Kd', 'CL', 'V', 'dose_mg_kg', 'potency', 
                                 'susceptibility_rate', 'activation_threshold']
        
        for param in pembrolizumab_specific:
            assert param in definitions
        
        # Test specific parameter definition
        potency_def = definitions['potency']
        assert potency_def['type'] == float
        assert potency_def['min'] == 0.1
        assert potency_def['max'] == 2.0
        assert 'immune activation potency' in potency_def['description']


class TestAtezolizumabParameters:
    """Test cases for AtezolizumabParameters class."""
    
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = AtezolizumabParameters()
        
        assert params.drug_type == "atezolizumab"
        assert params.Kd == 0.8
        assert params.CL == 0.25
        assert params.V == 6.5
        assert params.dose_mg_kg == 15
        assert params.potency == 0.25
        assert params.susceptibility_rate == 0.20
        assert params.activation_threshold == 45000.0
        
        # Check that Kd_atezo_PDL1 is set correctly
        assert params.Kd_atezo_PDL1 == 0.8
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        params = AtezolizumabParameters(
            Kd=1.0,
            CL=0.27,
            potency=0.3,
            susceptibility_rate=0.25
        )
        
        assert params.Kd == 1.0
        assert params.CL == 0.27
        assert params.potency == 0.3
        assert params.susceptibility_rate == 0.25
        assert params.Kd_atezo_PDL1 == 1.0  # Should be set from Kd
    
    def test_get_parameter_definitions(self):
        """Test parameter definitions retrieval."""
        params = AtezolizumabParameters()
        definitions = params.get_parameter_definitions()
        
        # Test that atezolizumab-specific parameters are included
        atezolizumab_specific = ['Kd', 'CL', 'V', 'dose_mg_kg', 'potency', 
                                'susceptibility_rate', 'activation_threshold']
        
        for param in atezolizumab_specific:
            assert param in definitions
        
        # Test specific parameter definition
        activation_def = definitions['activation_threshold']
        assert activation_def['type'] == float
        assert activation_def['min'] == 10000
        assert activation_def['max'] == 100000
        assert 'atezolizumab' in activation_def['description']


class TestDurvalumabParameters:
    """Test cases for DurvalumabParameters class."""
    
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = DurvalumabParameters()
        
        assert params.drug_type == "durvalumab"
        assert params.Kd == 1.0
        assert params.CL == 0.24
        assert params.V == 6.2
        assert params.dose_mg_kg == 10
        assert params.potency == 0.30
        assert params.susceptibility_rate == 0.18
        assert params.activation_threshold == 35000.0
        
        # Check that Kd_durva_PDL1 is set correctly
        assert params.Kd_durva_PDL1 == 1.0
    
    def test_custom_initialization(self):
        """Test initialization with custom parameters."""
        params = DurvalumabParameters(
            Kd=1.2,
            CL=0.26,
            potency=0.35,
            susceptibility_rate=0.22
        )
        
        assert params.Kd == 1.2
        assert params.CL == 0.26
        assert params.potency == 0.35
        assert params.susceptibility_rate == 0.22
        assert params.Kd_durva_PDL1 == 1.2  # Should be set from Kd
    
    def test_get_parameter_definitions(self):
        """Test parameter definitions retrieval."""
        params = DurvalumabParameters()
        definitions = params.get_parameter_definitions()
        
        # Test that durvalumab-specific parameters are included
        durvalumab_specific = ['Kd', 'CL', 'V', 'dose_mg_kg', 'potency', 
                              'susceptibility_rate', 'activation_threshold']
        
        for param in durvalumab_specific:
            assert param in definitions
        
        # Test specific parameter definition
        dose_def = definitions['dose_mg_kg']
        assert dose_def['type'] == float
        assert dose_def['min'] == 5
        assert dose_def['max'] == 20
        assert 'durvalumab dose' in dose_def['description']


class TestCreateDrugParameters:
    """Test cases for create_drug_parameters factory function."""
    
    def test_create_nivolumab_parameters(self):
        """Test creating nivolumab parameters."""
        params = create_drug_parameters('nivolumab')
        
        assert isinstance(params, NivolumabParameters)
        assert params.drug_type == "nivolumab"
        assert params.Kd == 2.6
        assert params.susceptibility_rate == 0.25
    
    def test_create_pembrolizumab_parameters(self):
        """Test creating pembrolizumab parameters."""
        params = create_drug_parameters('pembrolizumab')
        
        assert isinstance(params, PembrolizumabParameters)
        assert params.drug_type == "pembrolizumab"
        assert params.Kd == 3.2
        assert params.susceptibility_rate == 0.30
    
    def test_create_atezolizumab_parameters(self):
        """Test creating atezolizumab parameters."""
        params = create_drug_parameters('atezolizumab')
        
        assert isinstance(params, AtezolizumabParameters)
        assert params.drug_type == "atezolizumab"
        assert params.Kd == 0.8
        assert params.susceptibility_rate == 0.20
    
    def test_create_durvalumab_parameters(self):
        """Test creating durvalumab parameters."""
        params = create_drug_parameters('durvalumab')
        
        assert isinstance(params, DurvalumabParameters)
        assert params.drug_type == "durvalumab"
        assert params.Kd == 1.0
        assert params.susceptibility_rate == 0.18
    
    def test_create_with_custom_parameters(self):
        """Test creating parameters with custom values."""
        params = create_drug_parameters(
            'nivolumab',
            Kd=3.0,
            potency=0.9,
            susceptibility_rate=0.35
        )
        
        assert isinstance(params, NivolumabParameters)
        assert params.Kd == 3.0
        assert params.potency == 0.9
        assert params.susceptibility_rate == 0.35
    
    def test_create_invalid_drug_type(self):
        """Test creating parameters for invalid drug type."""
        with pytest.raises(ValueError, match="Unknown drug type"):
            create_drug_parameters('invalid_drug')
        
        with pytest.raises(ValueError, match="Supported types"):
            create_drug_parameters('invalid_drug')


class TestDrugParameterClasses:
    """Test cases for DRUG_PARAMETER_CLASSES dictionary."""
    
    def test_dictionary_completeness(self):
        """Test that all expected drug types are in the dictionary."""
        expected_drugs = ['nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab']
        
        for drug in expected_drugs:
            assert drug in DRUG_PARAMETER_CLASSES
            assert callable(DRUG_PARAMETER_CLASSES[drug])
    
    def test_dictionary_classes(self):
        """Test that dictionary contains correct classes."""
        assert DRUG_PARAMETER_CLASSES['nivolumab'] == NivolumabParameters
        assert DRUG_PARAMETER_CLASSES['pembrolizumab'] == PembrolizumabParameters
        assert DRUG_PARAMETER_CLASSES['atezolizumab'] == AtezolizumabParameters
        assert DRUG_PARAMETER_CLASSES['durvalumab'] == DurvalumabParameters


class TestDrugParameterValidation:
    """Test cases for drug parameter validation."""
    
    def test_nivolumab_validation(self):
        """Test nivolumab parameter validation."""
        # Valid parameters
        params = NivolumabParameters()
        errors = params.validate_parameters()
        assert len(errors) == 0
        
        # Invalid parameters
        params = NivolumabParameters(
            Kd=20.0,  # Above maximum
            CL=1.0,   # Above maximum
            potency=5.0  # Above maximum
        )
        
        errors = params.validate_parameters()
        assert len(errors) >= 3
        
        error_messages = ' '.join(errors)
        assert 'Kd' in error_messages
        assert 'CL' in error_messages
        assert 'potency' in error_messages
    
    def test_pembrolizumab_validation(self):
        """Test pembrolizumab parameter validation."""
        # Valid parameters
        params = PembrolizumabParameters()
        errors = params.validate_parameters()
        assert len(errors) == 0
        
        # Invalid parameters
        params = PembrolizumabParameters(
            Kd=0.05,  # Below minimum
            V=2.0,    # Below minimum
            dose_mg_kg=20  # Above maximum
        )
        
        errors = params.validate_parameters()
        assert len(errors) >= 3
    
    def test_atezolizumab_validation(self):
        """Test atezolizumab parameter validation."""
        # Valid parameters
        params = AtezolizumabParameters()
        errors = params.validate_parameters()
        assert len(errors) == 0
        
        # Invalid parameters
        params = AtezolizumabParameters(
            activation_threshold=5000.0,  # Below minimum
            dose_mg_kg=3.0,               # Below minimum
            susceptibility_rate=1.5        # Above maximum
        )
        
        errors = params.validate_parameters()
        assert len(errors) >= 3
    
    def test_durvalumab_validation(self):
        """Test durvalumab parameter validation."""
        # Valid parameters
        params = DurvalumabParameters()
        errors = params.validate_parameters()
        assert len(errors) == 0
        
        # Invalid parameters
        params = DurvalumabParameters(
            activation_threshold=5000.0,  # Below minimum
            V=3.0,                        # Below minimum
            potency=5.0                    # Above maximum
        )
        
        errors = params.validate_parameters()
        assert len(errors) >= 3


class TestDrugParameterInheritance:
    """Test cases for drug parameter inheritance from ModelParameters."""
    
    def test_inheritance_hierarchy(self):
        """Test that drug parameter classes inherit from ModelParameters."""
        from config.model_parameters import ModelParameters
        
        assert issubclass(NivolumabParameters, ModelParameters)
        assert issubclass(PembrolizumabParameters, ModelParameters)
        assert issubclass(AtezolizumabParameters, ModelParameters)
        assert issubclass(DurvalumabParameters, ModelParameters)
    
    def test_inherited_parameters(self):
        """Test that inherited parameters are accessible."""
        params = NivolumabParameters()
        
        # Test that base model parameters are available
        assert hasattr(params, 'alpha')
        assert hasattr(params, 'beta')
        assert hasattr(params, 'gamma')
        assert hasattr(params, 'delta')
        assert hasattr(params, 'T_eff0')
        assert hasattr(params, 'epsilon')
        assert hasattr(params, 'k_clear_IFN')
        assert hasattr(params, 'EC50_IFN_death')
        assert hasattr(params, 'Hill_IFN')
        
        # Test that drug susceptibility rates are available
        assert hasattr(params, 'drug_susceptibility_rates')
        assert 'nivolumab' in params.drug_susceptibility_rates
        
        # Test that drug activation thresholds are available
        assert hasattr(params, 'drug_activation_thresholds')
        assert 'nivolumab' in params.drug_activation_thresholds
    
    def test_parameter_override(self):
        """Test that drug-specific parameters can be accessed through base methods."""
        nivo_params = NivolumabParameters()
        pembro_params = PembrolizumabParameters()
        
        # Test that get_drug_parameters works
        nivo_drug_params = nivo_params.get_drug_parameters('nivolumab')
        pembro_drug_params = pembro_params.get_drug_parameters('pembrolizumab')
        
        assert nivo_drug_params['Kd'] == 2.6
        assert pembro_drug_params['Kd'] == 3.2
        
        # Test that update_drug_parameters works
        nivo_params.update_drug_parameters('nivolumab', Kd=3.5)
        assert nivo_params.Kd == 3.5
        assert nivo_params.Kd_nivo_PD1 == 3.5


class TestDrugParameterSerialization:
    """Test cases for drug parameter serialization."""
    
    def test_serialization(self):
        """Test serialization and deserialization of drug parameters."""
        # Create custom nivolumab parameters
        original_params = NivolumabParameters(
            Kd=3.0,
            potency=0.9,
            susceptibility_rate=0.35,
            version="2.0.0",
            description="Custom nivolumab parameters"
        )
        
        # Convert to dict and back
        params_dict = original_params.to_dict()
        restored_params = NivolumabParameters.from_dict(params_dict)
        
        # Check that parameters are restored correctly
        assert restored_params.drug_type == "nivolumab"
        assert restored_params.Kd == 3.0
        assert restored_params.potency == 0.9
        assert restored_params.susceptibility_rate == 0.35
        assert restored_params.version == "2.0.0"
        assert restored_params.description == "Custom nivolumab parameters"
        
        # Convert to JSON and back
        json_str = original_params.to_json()
        restored_from_json = NivolumabParameters.from_json(json_str)
        
        # Check that parameters are restored correctly
        assert restored_from_json.Kd == 3.0
        assert restored_from_json.potency == 0.9
        assert restored_from_json.susceptibility_rate == 0.35
    
    def test_cross_drug_serialization(self):
        """Test that parameters can be serialized between drug types."""
        # Create nivolumab parameters
        nivo_params = NivolumabParameters(Kd=3.0, potency=0.9)
        
        # Convert to dict
        nivo_dict = nivo_params.to_dict()
        
        # Create pembrolizumab from same dict (should work for common parameters)
        pembro_params = PembrolizumabParameters.from_dict(nivo_dict)
        
        # Common parameters should be preserved
        assert pembro_params.alpha == nivo_params.alpha
        assert pembro_params.beta == nivo_params.beta
        assert pembro_params.gamma == nivo_params.gamma
        
        # Drug-specific parameters should be pembrolizumab defaults
        assert pembro_params.drug_type == "pembrolizumab"
        assert pembro_params.Kd == 3.2  # Pembrolizumab default, not nivolumab value