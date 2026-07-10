"""
Unit tests for configuration manager module.

This module tests the ConfigurationManager class and its functionality.
"""

import pytest
import yaml
import json
from pathlib import Path
from typing import Dict, Any
from unittest.mock import patch, mock_open

from config.config_manager import ConfigurationManager
from config.model_parameters import ModelParameters
from config.drug_parameters import NivolumabParameters, PembrolizumabParameters


class TestConfigurationManager:
    """Test cases for ConfigurationManager class."""
    
    def test_initialization(self):
        """Test ConfigurationManager initialization."""
        manager = ConfigurationManager()
        
        assert manager is not None
        assert hasattr(manager, 'load_from_file')
        assert hasattr(manager, 'save_to_file')
        assert hasattr(manager, 'validate_config')
        assert hasattr(manager, 'merge_configs')
    
    def test_load_from_yaml_file(self, temp_directory):
        """Test loading configuration from YAML file."""
        # Create test YAML file
        config_data = {
            'model_parameters': {
                'alpha': 5e-4,
                'beta': 0.15,
                'gamma': 1.2,
                'T_eff0': 2000.0,
                'Kd_nivo_PD1': 3.0,
                'Kd_pembro_PD1': 3.5
            },
            'metadata': {
                'version': '1.0.0',
                'description': 'Test configuration'
            }
        }
        
        config_file = temp_directory / "test_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configuration
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert isinstance(params, ModelParameters)
        assert params.alpha == 5e-4
        assert params.beta == 0.15
        assert params.gamma == 1.2
        assert params.T_eff0 == 2000.0
        assert params.Kd_nivo_PD1 == 3.0
        assert params.Kd_pembro_PD1 == 3.5
    
    def test_load_from_json_file(self, temp_directory):
        """Test loading configuration from JSON file."""
        # Create test JSON file
        config_data = {
            'model_parameters': {
                'alpha': 6e-4,
                'beta': 0.18,
                'epsilon': 2.5,
                'k_clear_IFN': 1.5,
                'drug_susceptibility_rates': {
                    'nivolumab': 0.30,
                    'pembrolizumab': 0.35
                }
            },
            'metadata': {
                'version': '2.0.0',
                'author': 'Test Author'
            }
        }
        
        config_file = temp_directory / "test_config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Load configuration
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert isinstance(params, ModelParameters)
        assert params.alpha == 6e-4
        assert params.beta == 0.18
        assert params.epsilon == 2.5
        assert params.k_clear_IFN == 1.5
        assert params.drug_susceptibility_rates['nivolumab'] == 0.30
        assert params.drug_susceptibility_rates['pembrolizumab'] == 0.35
    
    def test_load_drug_specific_config(self, temp_directory):
        """Test loading drug-specific configuration."""
        # Create nivolumab-specific config
        config_data = {
            'model_parameters': {
                'Kd_nivo_PD1': 2.8,
                'drug_susceptibility_rates': {
                    'nivolumab': 0.28
                },
                'drug_activation_thresholds': {
                    'nivolumab': 8500.0
                }
            },
            'drug_type': 'nivolumab',
            'metadata': {
                'version': '1.0.0',
                'description': 'Nivolumab-specific configuration'
            }
        }
        
        config_file = temp_directory / "nivolumab_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load configuration
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert isinstance(params, ModelParameters)
        assert params.Kd_nivo_PD1 == 2.8
        assert params.drug_susceptibility_rates['nivolumab'] == 0.28
        assert params.drug_activation_thresholds['nivolumab'] == 8500.0
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file."""
        manager = ConfigurationManager()
        
        with pytest.raises(FileNotFoundError):
            manager.load_from_file("nonexistent_file.yaml")
    
    def test_load_invalid_yaml(self, temp_directory):
        """Test loading from invalid YAML file."""
        # Create invalid YAML file
        config_file = temp_directory / "invalid_config.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        manager = ConfigurationManager()
        
        with pytest.raises(yaml.YAMLError):
            manager.load_from_file(str(config_file))
    
    def test_load_invalid_json(self, temp_directory):
        """Test loading from invalid JSON file."""
        # Create invalid JSON file
        config_file = temp_directory / "invalid_config.json"
        with open(config_file, 'w') as f:
            f.write('{"invalid": json content}')
        
        manager = ConfigurationManager()
        
        with pytest.raises(json.JSONDecodeError):
            manager.load_from_file(str(config_file))
    
    def test_load_missing_model_parameters(self, temp_directory):
        """Test loading config with missing model_parameters section."""
        config_data = {
            'metadata': {
                'version': '1.0.0'
            }
        }
        
        config_file = temp_directory / "missing_params.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager()
        
        with pytest.raises(ValueError, match="Missing 'model_parameters' section"):
            manager.load_from_file(str(config_file))
    
    def test_save_to_yaml_file(self, temp_directory, sample_model_parameters):
        """Test saving configuration to YAML file."""
        config_file = temp_directory / "save_test.yaml"
        
        manager = ConfigurationManager()
        success = manager.save_to_file(sample_model_parameters, str(config_file))
        
        assert success
        assert config_file.exists()
        
        # Verify saved content
        with open(config_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert 'model_parameters' in saved_data
        assert 'metadata' in saved_data
        assert saved_data['model_parameters']['alpha'] == sample_model_parameters.alpha
        assert saved_data['model_parameters']['beta'] == sample_model_parameters.beta
    
    def test_save_to_json_file(self, temp_directory, sample_model_parameters):
        """Test saving configuration to JSON file."""
        config_file = temp_directory / "save_test.json"
        
        manager = ConfigurationManager()
        success = manager.save_to_file(sample_model_parameters, str(config_file))
        
        assert success
        assert config_file.exists()
        
        # Verify saved content
        with open(config_file, 'r') as f:
            saved_data = json.load(f)
        
        assert 'model_parameters' in saved_data
        assert 'metadata' in saved_data
        assert saved_data['model_parameters']['alpha'] == sample_model_parameters.alpha
        assert saved_data['model_parameters']['beta'] == sample_model_parameters.beta
    
    def test_save_with_metadata(self, temp_directory, sample_model_parameters):
        """Test saving configuration with custom metadata."""
        config_file = temp_directory / "save_with_metadata.yaml"
        
        metadata = {
            'version': '2.0.0',
            'author': 'Test Author',
            'description': 'Test configuration with custom metadata',
            'tags': ['test', 'validation']
        }
        
        manager = ConfigurationManager()
        success = manager.save_to_file(
            sample_model_parameters, 
            str(config_file), 
            metadata=metadata
        )
        
        assert success
        
        # Verify saved metadata
        with open(config_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data['metadata']['version'] == '2.0.0'
        assert saved_data['metadata']['author'] == 'Test Author'
        assert saved_data['metadata']['description'] == 'Test configuration with custom metadata'
        assert saved_data['metadata']['tags'] == ['test', 'validation']
    
    def test_save_to_nonexistent_directory(self, sample_model_parameters):
        """Test saving to nonexistent directory."""
        config_file = "nonexistent_dir/config.yaml"
        
        manager = ConfigurationManager()
        
        with pytest.raises(FileNotFoundError):
            manager.save_to_file(sample_model_parameters, config_file)
    
    def test_validate_config(self, sample_model_parameters):
        """Test configuration validation."""
        manager = ConfigurationManager()
        
        # Valid configuration
        is_valid, errors = manager.validate_config(sample_model_parameters)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid configuration
        sample_model_parameters.alpha = -0.001  # Invalid value
        sample_model_parameters.beta = 2.0      # Invalid value
        
        is_valid, errors = manager.validate_config(sample_model_parameters)
        assert not is_valid
        assert len(errors) > 0
        assert any('alpha' in error for error in errors)
        assert any('beta' in error for error in errors)
    
    def test_merge_configs(self, sample_model_parameters):
        """Test configuration merging."""
        manager = ConfigurationManager()
        
        # Create second configuration
        base_params = ModelParameters(
            alpha=5e-4,
            beta=0.15,
            gamma=1.2
        )
        
        # Merge configurations
        merged_params = manager.merge_configs(base_params, sample_model_parameters)
        
        assert isinstance(merged_params, ModelParameters)
        # Sample parameters should take precedence
        assert merged_params.alpha == sample_model_parameters.alpha
        assert merged_params.beta == sample_model_parameters.beta
        assert merged_params.gamma == sample_model_parameters.gamma
    
    def test_merge_with_overrides(self, sample_model_parameters):
        """Test configuration merging with explicit overrides."""
        manager = ConfigurationManager()
        
        base_params = ModelParameters(
            alpha=5e-4,
            beta=0.15,
            gamma=1.2
        )
        
        overrides = {
            'alpha': 7e-4,
            'epsilon': 3.0,
            'Kd_nivo_PD1': 3.5
        }
        
        merged_params = manager.merge_configs(
            base_params, 
            sample_model_parameters, 
            overrides=overrides
        )
        
        # Overrides should take precedence
        assert merged_params.alpha == 7e-4
        assert merged_params.epsilon == 3.0
        assert merged_params.Kd_nivo_PD1 == 3.5
        
        # Non-overridden parameters should come from sample_params
        assert merged_params.beta == sample_model_parameters.beta
        assert merged_params.gamma == sample_model_parameters.gamma
    
    def test_load_drug_parameters_from_config(self, temp_directory):
        """Test loading drug-specific parameters from config."""
        config_data = {
            'drug_type': 'nivolumab',
            'model_parameters': {
                'Kd_nivo_PD1': 2.8,
                'CL': 0.22,
                'V': 6.5,
                'potency': 0.9,
                'susceptibility_rate': 0.28,
                'activation_threshold': 8500.0,
                'alpha': 5e-4,
                'beta': 0.15
            },
            'metadata': {
                'version': '1.0.0',
                'description': 'Nivolumab configuration'
            }
        }
        
        config_file = temp_directory / "nivolumab_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert isinstance(params, ModelParameters)
        assert params.Kd_nivo_PD1 == 2.8
        assert params.alpha == 5e-4
        assert params.beta == 0.15
    
    def test_config_file_format_detection(self, temp_directory):
        """Test automatic detection of config file format."""
        # Test YAML file
        config_data = {'model_parameters': {'alpha': 5e-4}}
        yaml_file = temp_directory / "config.yaml"
        with open(yaml_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager()
        params = manager.load_from_file(str(yaml_file))
        assert params.alpha == 5e-4
        
        # Test JSON file
        json_file = temp_directory / "config.json"
        with open(json_file, 'w') as f:
            json.dump(config_data, f)
        
        params = manager.load_from_file(str(json_file))
        assert params.alpha == 5e-4
    
    def test_config_with_comments(self, temp_directory):
        """Test loading YAML config with comments."""
        yaml_content = """
# Model configuration for testing
model_parameters:
  # T-cell dynamics
  alpha: 5e-4  # APC-driven T-cell expansion rate
  beta: 0.15   # T-cell death rate
  
  # Drug binding
  Kd_nivo_PD1: 3.0  # Nivolumab binding constant

metadata:
  version: "1.0.0"
  description: "Test configuration with comments"
"""
        
        config_file = temp_directory / "commented_config.yaml"
        with open(config_file, 'w') as f:
            f.write(yaml_content)
        
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert params.alpha == 5e-4
        assert params.beta == 0.15
        assert params.Kd_nivo_PD1 == 3.0
    
    def test_config_with_references(self, temp_directory):
        """Test loading config with references/anchors."""
        yaml_content = """
defaults: &defaults
  alpha: 5e-4
  beta: 0.15
  gamma: 1.0

model_parameters:
  <<: *defaults
  Kd_nivo_PD1: 3.0
  epsilon: 2.5

metadata:
  version: "1.0.0"
"""
        
        config_file = temp_directory / "reference_config.yaml"
        with open(config_file, 'w') as f:
            f.write(yaml_content)
        
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert params.alpha == 5e-4
        assert params.beta == 0.15
        assert params.gamma == 1.0
        assert params.Kd_nivo_PD1 == 3.0
        assert params.epsilon == 2.5
    
    @patch('builtins.open', new_callable=mock_open)
    def test_file_read_error_handling(self, mock_file):
        """Test handling of file read errors."""
        mock_file.side_effect = IOError("Permission denied")
        
        manager = ConfigurationManager()
        
        with pytest.raises(IOError, match="Permission denied"):
            manager.load_from_file("test_config.yaml")
    
    @patch('builtins.open', new_callable=mock_open)
    def test_file_write_error_handling(self, mock_file, sample_model_parameters):
        """Test handling of file write errors."""
        mock_file.side_effect = IOError("Disk full")
        
        manager = ConfigurationManager()
        
        with pytest.raises(IOError, match="Disk full"):
            manager.save_to_file(sample_model_parameters, "test_config.yaml")
    
    def test_round_trip_serialization(self, temp_directory, sample_model_parameters):
        """Test round-trip serialization (save then load)."""
        config_file = temp_directory / "round_trip.yaml"
        
        manager = ConfigurationManager()
        
        # Save configuration
        save_success = manager.save_to_file(sample_model_parameters, str(config_file))
        assert save_success
        
        # Load configuration
        loaded_params = manager.load_from_file(str(config_file))
        
        # Compare parameters
        assert loaded_params.alpha == sample_model_parameters.alpha
        assert loaded_params.beta == sample_model_parameters.beta
        assert loaded_params.gamma == sample_model_parameters.gamma
        assert loaded_params.Kd_nivo_PD1 == sample_model_parameters.Kd_nivo_PD1
        assert loaded_params.drug_susceptibility_rates == sample_model_parameters.drug_susceptibility_rates
    
    def test_config_with_nested_structures(self, temp_directory):
        """Test loading config with nested parameter structures."""
        config_data = {
            'model_parameters': {
                'alpha': 5e-4,
                'beta': 0.15,
                'drug_susceptibility_rates': {
                    'nivolumab': 0.25,
                    'pembrolizumab': 0.30,
                    'atezolizumab': 0.20,
                    'durvalumab': 0.18
                },
                'drug_activation_thresholds': {
                    'nivolumab': 8000.0,
                    'pembrolizumab': 6000.0,
                    'atezolizumab': 45000.0,
                    'durvalumab': 35000.0
                }
            },
            'metadata': {
                'version': '1.0.0',
                'tags': ['test', 'nested'],
                'author': {
                    'name': 'Test Author',
                    'email': 'test@example.com'
                }
            }
        }
        
        config_file = temp_directory / "nested_config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigurationManager()
        params = manager.load_from_file(str(config_file))
        
        assert params.drug_susceptibility_rates['nivolumab'] == 0.25
        assert params.drug_susceptibility_rates['pembrolizumab'] == 0.30
        assert params.drug_activation_thresholds['nivolumab'] == 8000.0
        assert params.drug_activation_thresholds['pembrolizumab'] == 6000.0