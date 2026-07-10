"""
QSP_PD_Thyroid Configuration Management System
==============================================

This package provides a comprehensive configuration management system for the
QSP_PD_Thyroid_Final project, including:

- Parameter validation with pydantic
- Drug-specific parameter classes
- YAML configuration file support
- Parameter versioning and change tracking
- Backward compatibility with existing code

Classes:
    BaseParameters: Base class with common functionality
    ModelParameters: Main model parameters class
    NivolumabParameters: Nivolumab-specific parameters
    PembrolizumabParameters: Pembrolizumab-specific parameters
    AtezolizumabParameters: Atezolizumab-specific parameters
    DurvalumabParameters: Durvalumab-specific parameters
    ConfigurationManager: Configuration file management
    ParameterVersion: Parameter version tracking
    ParameterChangeLog: Change log system

Usage:
    from config import ModelParameters, ConfigurationManager
    
    # Load configuration from file
    config_manager = ConfigurationManager()
    params = config_manager.load_from_file("nivolumab_config.yaml")
    
    # Create parameters programmatically
    params = ModelParameters()
    nivo_params = NivolumabParameters()
"""

from .base_parameters import BaseParameters
from .model_parameters import ModelParameters
from .drug_parameters import (
    NivolumabParameters,
    PembrolizumabParameters,
    AtezolizumabParameters,
    DurvalumabParameters
)
from .config_manager import ConfigurationManager
from .parameter_version import ParameterVersion
from .change_log import ParameterChangeLog

def create_drug_parameters(drug_type: str):
    """
    Factory function to create drug-specific parameter objects.

    Args:
        drug_type: Type of drug ('nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab')

    Returns:
        Drug-specific parameter object

    Raises:
        ValueError: If drug_type is not recognized
    """
    drug_type_lower = drug_type.lower()

    if drug_type_lower == 'nivolumab':
        return NivolumabParameters()
    elif drug_type_lower == 'pembrolizumab':
        return PembrolizumabParameters()
    elif drug_type_lower == 'atezolizumab':
        return AtezolizumabParameters()
    elif drug_type_lower == 'durvalumab':
        return DurvalumabParameters()
    else:
        raise ValueError(f"Unknown drug type: {drug_type}. Must be one of: nivolumab, pembrolizumab, atezolizumab, durvalumab")

__all__ = [
    "BaseParameters",
    "ModelParameters",
    "NivolumabParameters",
    "PembrolizumabParameters",
    "AtezolizumabParameters",
    "DurvalumabParameters",
    "ConfigurationManager",
    "ParameterVersion",
    "ParameterChangeLog",
    "create_drug_parameters"
]

# Version of the configuration system
__version__ = "1.0.0"