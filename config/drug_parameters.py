"""
Drug-Specific Parameters Module
================================

This module provides drug-specific parameter classes that inherit from
ModelParameters and contain drug-configured values for each checkpoint inhibitor.
"""

from typing import Dict, Any, Optional
from pydantic import Field, validator
from .model_parameters import ModelParameters


class NivolumabParameters(ModelParameters):
    """
    Nivolumab-specific parameters with pre-configured values optimized for
    nivolumab-induced hypothyroidism modeling.
    """
    
    drug_type: str = Field(default="nivolumab", description="Drug type identifier")
    
    # Nivolumab-specific binding parameters
    Kd: float = Field(default=2.6, description="Dissociation constant for nivolumab-PD1 binding (nM)")
    
    # Nivolumab-specific PK parameters
    CL: float = Field(default=0.2, description="Nivolumab clearance rate (L/day)")
    V: float = Field(default=6.0, description="Nivolumab volume of distribution (L)")
    dose_mg_kg: float = Field(default=3.0, description="Nivolumab dose (mg/kg)")
    
    # Nivolumab-specific immune parameters
    potency: float = Field(default=1.0, description="Relative immune activation potency")
    susceptibility_rate: float = Field(default=0.25, description="Immune susceptibility rate for nivolumab")
    activation_threshold: float = Field(default=8000.0, description="Activation threshold for nivolumab")
    
    def __init__(self, **data):
        """Initialize nivolumab parameters with drug-specific values."""
        # Set drug-specific values before validation
        if 'Kd_nivo_PD1' not in data:
            data['Kd_nivo_PD1'] = data.get('Kd', 2.6)
        
        super().__init__(**data)
    
    def get_parameter_definitions(self) -> Dict[str, Any]:
        """Get nivolumab-specific parameter definitions."""
        base_defs = super().get_parameter_definitions()
        
        # Add nivolumab-specific parameters
        nivolumab_defs = {
            "Kd": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for nivolumab-PD1 binding",
                "units": "nM"
            },
            "CL": {
                "type": float,
                "min": 0.1,
                "max": 0.5,
                "description": "Nivolumab clearance rate",
                "units": "L/day"
            },
            "V": {
                "type": float,
                "min": 4.0,
                "max": 8.0,
                "description": "Nivolumab volume of distribution",
                "units": "L"
            },
            "dose_mg_kg": {
                "type": float,
                "min": 1,
                "max": 10,
                "description": "Nivolumab dose",
                "units": "mg/kg"
            },
            "potency": {
                "type": float,
                "min": 0.1,
                "max": 2.0,
                "description": "Relative immune activation potency",
                "units": "dimensionless"
            },
            "susceptibility_rate": {
                "type": float,
                "min": 0.0,
                "max": 1.0,
                "description": "Immune susceptibility rate for nivolumab",
                "units": "dimensionless"
            },
            "activation_threshold": {
                "type": float,
                "min": 1000,
                "max": 20000,
                "description": "Activation threshold for nivolumab",
                "units": "concentration units"
            }
        }
        
        return {**base_defs, **nivolumab_defs}


class PembrolizumabParameters(ModelParameters):
    """
    Pembrolizumab-specific parameters with pre-configured values optimized for
    pembrolizumab-induced hypothyroidism modeling.
    """
    
    drug_type: str = Field(default="pembrolizumab", description="Drug type identifier")
    
    # Pembrolizumab-specific binding parameters
    Kd: float = Field(default=3.2, description="Dissociation constant for pembrolizumab-PD1 binding (nM)")
    
    # Pembrolizumab-specific PK parameters
    CL: float = Field(default=0.22, description="Pembrolizumab clearance rate (L/day)")
    V: float = Field(default=6.0, description="Pembrolizumab volume of distribution (L)")
    dose_mg_kg: float = Field(default=2.0, description="Pembrolizumab dose (mg/kg)")
    
    # Pembrolizumab-specific immune parameters
    potency: float = Field(default=0.85, description="Relative immune activation potency")
    susceptibility_rate: float = Field(default=0.30, description="Immune susceptibility rate for pembrolizumab")
    activation_threshold: float = Field(default=6000.0, description="Activation threshold for pembrolizumab")
    
    def __init__(self, **data):
        """Initialize pembrolizumab parameters with drug-specific values."""
        # Set drug-specific values before validation
        if 'Kd_pembro_PD1' not in data:
            data['Kd_pembro_PD1'] = data.get('Kd', 3.2)
        
        super().__init__(**data)
    
    def get_parameter_definitions(self) -> Dict[str, Any]:
        """Get pembrolizumab-specific parameter definitions."""
        base_defs = super().get_parameter_definitions()
        
        # Add pembrolizumab-specific parameters
        pembrolizumab_defs = {
            "Kd": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for pembrolizumab-PD1 binding",
                "units": "nM"
            },
            "CL": {
                "type": float,
                "min": 0.1,
                "max": 0.5,
                "description": "Pembrolizumab clearance rate",
                "units": "L/day"
            },
            "V": {
                "type": float,
                "min": 4.0,
                "max": 8.0,
                "description": "Pembrolizumab volume of distribution",
                "units": "L"
            },
            "dose_mg_kg": {
                "type": float,
                "min": 1,
                "max": 10,
                "description": "Pembrolizumab dose",
                "units": "mg/kg"
            },
            "potency": {
                "type": float,
                "min": 0.1,
                "max": 2.0,
                "description": "Relative immune activation potency",
                "units": "dimensionless"
            },
            "susceptibility_rate": {
                "type": float,
                "min": 0.0,
                "max": 1.0,
                "description": "Immune susceptibility rate for pembrolizumab",
                "units": "dimensionless"
            },
            "activation_threshold": {
                "type": float,
                "min": 1000,
                "max": 20000,
                "description": "Activation threshold for pembrolizumab",
                "units": "concentration units"
            }
        }
        
        return {**base_defs, **pembrolizumab_defs}


class AtezolizumabParameters(ModelParameters):
    """
    Atezolizumab-specific parameters with pre-configured values optimized for
    atezolizumab-induced hypothyroidism modeling.
    """
    
    drug_type: str = Field(default="atezolizumab", description="Drug type identifier")
    
    # Atezolizumab-specific binding parameters
    Kd: float = Field(default=0.8, description="Dissociation constant for atezolizumab-PDL1 binding (nM)")
    
    # Atezolizumab-specific PK parameters
    CL: float = Field(default=0.25, description="Atezolizumab clearance rate (L/day)")
    V: float = Field(default=6.5, description="Atezolizumab volume of distribution (L)")
    dose_mg_kg: float = Field(default=15.0, description="Atezolizumab dose (mg/kg)")
    
    # Atezolizumab-specific immune parameters
    potency: float = Field(default=0.25, description="Relative immune activation potency")
    susceptibility_rate: float = Field(default=0.20, description="Immune susceptibility rate for atezolizumab")
    activation_threshold: float = Field(default=45000.0, description="Activation threshold for atezolizumab")
    
    def __init__(self, **data):
        """Initialize atezolizumab parameters with drug-specific values."""
        # Set drug-specific values before validation
        if 'Kd_atezo_PDL1' not in data:
            data['Kd_atezo_PDL1'] = data.get('Kd', 0.8)
        
        super().__init__(**data)
    
    def get_parameter_definitions(self) -> Dict[str, Any]:
        """Get atezolizumab-specific parameter definitions."""
        base_defs = super().get_parameter_definitions()
        
        # Add atezolizumab-specific parameters
        atezolizumab_defs = {
            "Kd": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for atezolizumab-PDL1 binding",
                "units": "nM"
            },
            "CL": {
                "type": float,
                "min": 0.1,
                "max": 0.5,
                "description": "Atezolizumab clearance rate",
                "units": "L/day"
            },
            "V": {
                "type": float,
                "min": 4.0,
                "max": 10.0,
                "description": "Atezolizumab volume of distribution",
                "units": "L"
            },
            "dose_mg_kg": {
                "type": float,
                "min": 5,
                "max": 20,
                "description": "Atezolizumab dose",
                "units": "mg/kg"
            },
            "potency": {
                "type": float,
                "min": 0.1,
                "max": 2.0,
                "description": "Relative immune activation potency",
                "units": "dimensionless"
            },
            "susceptibility_rate": {
                "type": float,
                "min": 0.0,
                "max": 1.0,
                "description": "Immune susceptibility rate for atezolizumab",
                "units": "dimensionless"
            },
            "activation_threshold": {
                "type": float,
                "min": 10000,
                "max": 100000,
                "description": "Activation threshold for atezolizumab",
                "units": "concentration units"
            }
        }
        
        return {**base_defs, **atezolizumab_defs}


class DurvalumabParameters(ModelParameters):
    """
    Durvalumab-specific parameters with pre-configured values optimized for
    durvalumab-induced hypothyroidism modeling.
    """
    
    drug_type: str = Field(default="durvalumab", description="Drug type identifier")
    
    # Durvalumab-specific binding parameters
    Kd: float = Field(default=1.0, description="Dissociation constant for durvalumab-PDL1 binding (nM)")
    
    # Durvalumab-specific PK parameters
    CL: float = Field(default=0.24, description="Durvalumab clearance rate (L/day)")
    V: float = Field(default=6.2, description="Durvalumab volume of distribution (L)")
    dose_mg_kg: float = Field(default=10.0, description="Durvalumab dose (mg/kg)")
    
    # Durvalumab-specific immune parameters
    potency: float = Field(default=0.30, description="Relative immune activation potency")
    susceptibility_rate: float = Field(default=0.18, description="Immune susceptibility rate for durvalumab")
    activation_threshold: float = Field(default=35000.0, description="Activation threshold for durvalumab")
    
    def __init__(self, **data):
        """Initialize durvalumab parameters with drug-specific values."""
        # Set drug-specific values before validation
        if 'Kd_durva_PDL1' not in data:
            data['Kd_durva_PDL1'] = data.get('Kd', 1.0)
        
        super().__init__(**data)
    
    def get_parameter_definitions(self) -> Dict[str, Any]:
        """Get durvalumab-specific parameter definitions."""
        base_defs = super().get_parameter_definitions()
        
        # Add durvalumab-specific parameters
        durvalumab_defs = {
            "Kd": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for durvalumab-PDL1 binding",
                "units": "nM"
            },
            "CL": {
                "type": float,
                "min": 0.1,
                "max": 0.5,
                "description": "Durvalumab clearance rate",
                "units": "L/day"
            },
            "V": {
                "type": float,
                "min": 4.0,
                "max": 10.0,
                "description": "Durvalumab volume of distribution",
                "units": "L"
            },
            "dose_mg_kg": {
                "type": float,
                "min": 5,
                "max": 20,
                "description": "Durvalumab dose",
                "units": "mg/kg"
            },
            "potency": {
                "type": float,
                "min": 0.1,
                "max": 2.0,
                "description": "Relative immune activation potency",
                "units": "dimensionless"
            },
            "susceptibility_rate": {
                "type": float,
                "min": 0.0,
                "max": 1.0,
                "description": "Immune susceptibility rate for durvalumab",
                "units": "dimensionless"
            },
            "activation_threshold": {
                "type": float,
                "min": 10000,
                "max": 100000,
                "description": "Activation threshold for durvalumab",
                "units": "concentration units"
            }
        }
        
        return {**base_defs, **durvalumab_defs}


# Factory function to create drug-specific parameters
def create_drug_parameters(drug_type: str, **kwargs) -> ModelParameters:
    """
    Factory function to create drug-specific parameters.
    
    Args:
        drug_type: Type of drug (nivolumab, pembrolizumab, atezolizumab, durvalumab)
        **kwargs: Additional parameters to override defaults
        
    Returns:
        Drug-specific parameter instance
        
    Raises:
        ValueError: If drug_type is not recognized
    """
    drug_classes = {
        'nivolumab': NivolumabParameters,
        'pembrolizumab': PembrolizumabParameters,
        'atezolizumab': AtezolizumabParameters,
        'durvalumab': DurvalumabParameters
    }
    
    if drug_type not in drug_classes:
        raise ValueError(f"Unknown drug type: {drug_type}. "
                        f"Supported types: {list(drug_classes.keys())}")
    
    return drug_classes[drug_type](**kwargs)


# Dictionary of all drug parameter classes for easy access
DRUG_PARAMETER_CLASSES = {
    'nivolumab': NivolumabParameters,
    'pembrolizumab': PembrolizumabParameters,
    'atezolizumab': AtezolizumabParameters,
    'durvalumab': DurvalumabParameters
}