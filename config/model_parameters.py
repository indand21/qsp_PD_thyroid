"""
Model Parameters Module
======================

This module provides the ModelParameters class that contains all the
parameters extracted from the existing FinalModelParameters class in qsp_model_final.py.
"""

from typing import Dict, Any, List, Optional
from pydantic import Field, validator
import numpy as np
from .base_parameters import BaseParameters


class ModelParameters(BaseParameters):
    """
    Main model parameters class containing all QSP model parameters.
    
    This class extracts and organizes all parameters from the existing
    FinalModelParameters class with proper validation and documentation.
    """
    
    # DRUG-SPECIFIC BINDING AND ACTIVATION - VALIDATED
    Kd_nivo_PD1: float = Field(default=2.6, description="Dissociation constant for nivolumab-PD1 binding (nM)")
    Kd_pembro_PD1: float = Field(default=3.2, description="Dissociation constant for pembrolizumab-PD1 binding (nM)")
    Kd_atezo_PDL1: float = Field(default=0.8, description="Dissociation constant for atezolizumab-PDL1 binding (nM)")
    Kd_durva_PDL1: float = Field(default=1.0, description="Dissociation constant for durvalumab-PDL1 binding (nM)")
    
    # IMMUNE SUSCEPTIBILITY POPULATION - VALIDATED FOR INCIDENCE
    drug_susceptibility_rates: Dict[str, float] = Field(
        default={
            'nivolumab': 0.25,
            'pembrolizumab': 0.30,  
            'atezolizumab': 0.20,
            'durvalumab': 0.18
        },
        description="Drug-specific immune susceptibility rates"
    )
    
    # DRUG-SPECIFIC ACTIVATION THRESHOLDS - VALIDATED FOR INCIDENCE
    drug_activation_thresholds: Dict[str, float] = Field(
        default={
            'nivolumab': 8000.0,
            'pembrolizumab': 6000.0,
            'atezolizumab': 45000.0,
            'durvalumab': 35000.0
        },
        description="Drug-specific activation thresholds"
    )
    
    # T-CELL DYNAMICS - BALANCED FOR SUSTAINED BUT SLOWER RESPONSE
    alpha: float = Field(default=4e-4, description="APC-driven T-cell expansion rate")
    beta: float = Field(default=0.12, description="T-cell death rate")
    gamma: float = Field(default=1.0, description="PD-1 mediated inhibition factor")
    delta: float = Field(default=0.005, description="IL-2 driven T-cell proliferation rate")
    T_eff0: float = Field(default=1.5e3, description="Baseline T-cell count")
    
    # CYTOKINE PARAMETERS - SIGNIFICANTLY SLOWED FOR 60-120 DAY TIMING
    epsilon: float = Field(default=2.0, description="IFN-γ secretion rate")
    k_clear_IFN: float = Field(default=1.2, description="IFN-γ clearance rate")
    EC50_IFN_death: float = Field(default=85.0, description="IFN-γ concentration for 50% thyrocyte death effect")
    Hill_IFN: float = Field(default=1.2, description="Hill coefficient for IFN-γ effect")
    
    # DAMAGE ACCUMULATION - MAJOR CORRECTION FOR REALISTIC TIMING
    base_damage_threshold: float = Field(default=0.025, description="Base threshold for damage accumulation")
    damage_threshold_growth_rate: float = Field(default=0.00005, description="Growth rate of damage threshold over time")
    damage_accumulation_rate: float = Field(default=800000.0, description="Rate of damage accumulation")
    damage_decay_rate: float = Field(default=0.0005, description="Rate of damage decay")
    cytokine_threshold_pg_ml: float = Field(default=120.0, description="Cytokine threshold for damage onset (pg/mL)")
    
    # TIME-DEPENDENT DAMAGE GATING - NEW MECHANISM FOR DELAYED ONSET
    minimum_exposure_days: float = Field(default=45.0, description="Minimum exposure time before damage can accumulate")
    damage_ramp_time: float = Field(default=30.0, description="Time over which damage accumulation ramps up")
    
    # THYROCYTE DYNAMICS - FINE-TUNED FOR SUSTAINED DAMAGE
    k_death: float = Field(default=0.008, description="Thyrocyte apoptosis rate")
    k_regen: float = Field(default=0.055, description="Thyrocyte regeneration rate")
    initial_regeneration_capacity: float = Field(default=0.055, description="Initial regeneration capacity")
    regeneration_decline_rate: float = Field(default=0.0004, description="Decline rate of regeneration capacity")
    min_regeneration_capacity: float = Field(default=0.020, description="Minimum regeneration capacity")
    
    # THYROID HORMONE SYNTHESIS - MAINTAINED FOR GRADE 2+ RATES
    k_syn_T3: float = Field(default=3.0, description="T3 synthesis rate")
    k_syn_T4: float = Field(default=14.0, description="T4 synthesis rate")
    k_deg_T3: float = Field(default=0.693, description="T3 degradation rate")
    k_deg_T4: float = Field(default=0.099, description="T4 degradation rate")
    
    # HPT AXIS PARAMETERS - STANDARD
    TSH_set: float = Field(default=1.5, description="TSH set point")
    T3_set: float = Field(default=4.8, description="T3 set point")
    T4_set: float = Field(default=12.0, description="T4 set point")
    theta: float = Field(default=0.10, description="HPT axis feedback sensitivity")
    k_metab_TSH: float = Field(default=0.05, description="TSH metabolism rate")
    
    # OTHER PARAMETERS
    Thyro_max: float = Field(default=1.0, description="Maximum thyroid mass")
    immune_memory_factor: float = Field(default=1.1, description="Immune memory amplification factor")
    memory_accumulation_rate: float = Field(default=0.0005, description="Rate of immune memory accumulation")
    
    # PATIENT COVARIATES
    sex_factor: float = Field(default=1.0, description="Sex-based risk factor")
    age_factor: float = Field(default=1.0, description="Age-based risk factor")
    HLA_factor: float = Field(default=1.0, description="HLA genotype risk factor")
    TPO_Ab_titer: float = Field(default=0.0, description="TPO antibody titer")
    
    # DRUG PK PARAMETERS
    drug_clearance: float = Field(default=0.2, description="Drug clearance rate")
    drug_volume: float = Field(default=6.0, description="Drug volume of distribution")
    dosing_interval: float = Field(default=14.0, description="Dosing interval in days")
    
    def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get parameter definitions for validation and documentation.
        
        Returns:
            Dictionary mapping parameter names to their definitions
        """
        return {
            # Drug binding parameters
            "Kd_nivo_PD1": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for nivolumab-PD1 binding (nM)",
                "units": "nM"
            },
            "Kd_pembro_PD1": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for pembrolizumab-PD1 binding (nM)",
                "units": "nM"
            },
            "Kd_atezo_PDL1": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for atezolizumab-PDL1 binding (nM)",
                "units": "nM"
            },
            "Kd_durva_PDL1": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "Dissociation constant for durvalumab-PDL1 binding (nM)",
                "units": "nM"
            },
            
            # T-cell dynamics
            "alpha": {
                "type": float,
                "min": 1e-6,
                "max": 1e-2,
                "description": "APC-driven T-cell expansion rate",
                "units": "1/day"
            },
            "beta": {
                "type": float,
                "min": 0.01,
                "max": 1.0,
                "description": "T-cell death rate",
                "units": "1/day"
            },
            "gamma": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "PD-1 mediated inhibition factor",
                "units": "dimensionless"
            },
            "delta": {
                "type": float,
                "min": 1e-4,
                "max": 0.1,
                "description": "IL-2 driven T-cell proliferation rate",
                "units": "1/day"
            },
            "T_eff0": {
                "type": float,
                "min": 100,
                "max": 10000,
                "description": "Baseline T-cell count",
                "units": "cells"
            },
            
            # Cytokine parameters
            "epsilon": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "IFN-γ secretion rate",
                "units": "pg/(cell·day)"
            },
            "k_clear_IFN": {
                "type": float,
                "min": 0.1,
                "max": 5.0,
                "description": "IFN-γ clearance rate",
                "units": "1/day"
            },
            "EC50_IFN_death": {
                "type": float,
                "min": 10,
                "max": 200,
                "description": "IFN-γ concentration for 50% thyrocyte death effect",
                "units": "pg/mL"
            },
            "Hill_IFN": {
                "type": float,
                "min": 0.5,
                "max": 5.0,
                "description": "Hill coefficient for IFN-γ effect",
                "units": "dimensionless"
            },
            
            # Damage accumulation
            "base_damage_threshold": {
                "type": float,
                "min": 0.001,
                "max": 0.1,
                "description": "Base threshold for damage accumulation",
                "units": "dimensionless"
            },
            "damage_threshold_growth_rate": {
                "type": float,
                "min": 1e-6,
                "max": 1e-3,
                "description": "Growth rate of damage threshold over time",
                "units": "1/day"
            },
            "damage_accumulation_rate": {
                "type": float,
                "min": 10000,
                "max": 10000000,
                "description": "Rate of damage accumulation",
                "units": "pg·day/damage"
            },
            "damage_decay_rate": {
                "type": float,
                "min": 1e-5,
                "max": 0.01,
                "description": "Rate of damage decay",
                "units": "1/day"
            },
            "cytokine_threshold_pg_ml": {
                "type": float,
                "min": 10,
                "max": 500,
                "description": "Cytokine threshold for damage onset",
                "units": "pg/mL"
            },
            
            # Time-dependent damage gating
            "minimum_exposure_days": {
                "type": float,
                "min": 1,
                "max": 120,
                "description": "Minimum exposure time before damage can accumulate",
                "units": "days"
            },
            "damage_ramp_time": {
                "type": float,
                "min": 1,
                "max": 90,
                "description": "Time over which damage accumulation ramps up",
                "units": "days"
            },
            
            # Thyrocyte dynamics
            "k_death": {
                "type": float,
                "min": 1e-4,
                "max": 0.1,
                "description": "Thyrocyte apoptosis rate",
                "units": "1/day"
            },
            "k_regen": {
                "type": float,
                "min": 0.001,
                "max": 0.2,
                "description": "Thyrocyte regeneration rate",
                "units": "1/day"
            },
            "initial_regeneration_capacity": {
                "type": float,
                "min": 0.001,
                "max": 0.2,
                "description": "Initial regeneration capacity",
                "units": "1/day"
            },
            "regeneration_decline_rate": {
                "type": float,
                "min": 1e-5,
                "max": 0.01,
                "description": "Decline rate of regeneration capacity",
                "units": "1/day"
            },
            "min_regeneration_capacity": {
                "type": float,
                "min": 0.001,
                "max": 0.1,
                "description": "Minimum regeneration capacity",
                "units": "1/day"
            },
            
            # Thyroid hormone synthesis
            "k_syn_T3": {
                "type": float,
                "min": 0.1,
                "max": 10.0,
                "description": "T3 synthesis rate",
                "units": "pmol/(thyrocyte·day)"
            },
            "k_syn_T4": {
                "type": float,
                "min": 1.0,
                "max": 50.0,
                "description": "T4 synthesis rate",
                "units": "pmol/(thyrocyte·day)"
            },
            "k_deg_T3": {
                "type": float,
                "min": 0.1,
                "max": 2.0,
                "description": "T3 degradation rate",
                "units": "1/day"
            },
            "k_deg_T4": {
                "type": float,
                "min": 0.01,
                "max": 0.5,
                "description": "T4 degradation rate",
                "units": "1/day"
            },
            
            # HPT axis parameters
            "TSH_set": {
                "type": float,
                "min": 0.5,
                "max": 5.0,
                "description": "TSH set point",
                "units": "mIU/L"
            },
            "T3_set": {
                "type": float,
                "min": 2.0,
                "max": 8.0,
                "description": "T3 set point",
                "units": "pmol/L"
            },
            "T4_set": {
                "type": float,
                "min": 5.0,
                "max": 25.0,
                "description": "T4 set point",
                "units": "pmol/L"
            },
            "theta": {
                "type": float,
                "min": 0.01,
                "max": 1.0,
                "description": "HPT axis feedback sensitivity",
                "units": "dimensionless"
            },
            "k_metab_TSH": {
                "type": float,
                "min": 0.01,
                "max": 0.5,
                "description": "TSH metabolism rate",
                "units": "1/day"
            },
            
            # Other parameters
            "Thyro_max": {
                "type": float,
                "min": 0.5,
                "max": 2.0,
                "description": "Maximum thyroid mass",
                "units": "dimensionless"
            },
            "immune_memory_factor": {
                "type": float,
                "min": 0.5,
                "max": 5.0,
                "description": "Immune memory amplification factor",
                "units": "dimensionless"
            },
            "memory_accumulation_rate": {
                "type": float,
                "min": 1e-5,
                "max": 0.01,
                "description": "Rate of immune memory accumulation",
                "units": "1/day"
            },
            
            # Patient covariates
            "sex_factor": {
                "type": float,
                "min": 0.5,
                "max": 2.0,
                "description": "Sex-based risk factor",
                "units": "dimensionless"
            },
            "age_factor": {
                "type": float,
                "min": 0.5,
                "max": 2.0,
                "description": "Age-based risk factor",
                "units": "dimensionless"
            },
            "HLA_factor": {
                "type": float,
                "min": 0.5,
                "max": 2.0,
                "description": "HLA genotype risk factor",
                "units": "dimensionless"
            },
            "TPO_Ab_titer": {
                "type": float,
                "min": 0.0,
                "max": 1000.0,
                "description": "TPO antibody titer",
                "units": "IU/mL"
            },
            
            # Drug PK parameters
            "drug_clearance": {
                "type": float,
                "min": 0.1,
                "max": 1.0,
                "description": "Drug clearance rate",
                "units": "L/day"
            },
            "drug_volume": {
                "type": float,
                "min": 3.0,
                "max": 10.0,
                "description": "Drug volume of distribution",
                "units": "L"
            },
            "dosing_interval": {
                "type": float,
                "min": 1,
                "max": 28,
                "description": "Dosing interval",
                "units": "days"
            }
        }
    
    @validator('drug_susceptibility_rates')
    def validate_drug_susceptibility_rates(cls, v):
        """Validate drug susceptibility rates."""
        valid_drugs = ['nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab']
        for drug, rate in v.items():
            if drug not in valid_drugs:
                raise ValueError(f"Invalid drug name: {drug}")
            if not 0 <= rate <= 1:
                raise ValueError(f"Drug susceptibility rate for {drug} must be between 0 and 1")
        return v
    
    @validator('drug_activation_thresholds')
    def validate_drug_activation_thresholds(cls, v):
        """Validate drug activation thresholds."""
        valid_drugs = ['nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab']
        for drug, threshold in v.items():
            if drug not in valid_drugs:
                raise ValueError(f"Invalid drug name: {drug}")
            if not threshold > 0:
                raise ValueError(f"Drug activation threshold for {drug} must be positive")
        return v
    
    def get_drug_parameters(self, drug_type: str) -> Dict[str, Any]:
        """
        Get drug-specific parameters.
        
        Args:
            drug_type: Type of drug (nivolumab, pembrolizumab, atezolizumab, durvalumab)
            
        Returns:
            Dictionary of drug-specific parameters
        """
        if drug_type not in self.drug_susceptibility_rates:
            raise ValueError(f"Unknown drug type: {drug_type}")
        
        return {
            'susceptibility_rate': self.drug_susceptibility_rates[drug_type],
            'activation_threshold': self.drug_activation_thresholds[drug_type],
            'Kd': getattr(self, f'Kd_{drug_type[:4]}_{"PD1" if drug_type in ["nivolumab", "pembrolizumab"] else "PDL1"}')
        }
    
    def update_drug_parameters(self, drug_type: str, **kwargs):
        """
        Update drug-specific parameters.
        
        Args:
            drug_type: Type of drug
            **kwargs: Parameters to update
        """
        if drug_type not in self.drug_susceptibility_rates:
            raise ValueError(f"Unknown drug type: {drug_type}")
        
        if 'susceptibility_rate' in kwargs:
            self.drug_susceptibility_rates[drug_type] = kwargs['susceptibility_rate']
        
        if 'activation_threshold' in kwargs:
            self.drug_activation_thresholds[drug_type] = kwargs['activation_threshold']
        
        # Update Kd if provided
        kd_param = f'Kd_{drug_type[:4]}_{"PD1" if drug_type in ["nivolumab", "pembrolizumab"] else "PDL1"}'
        if 'Kd' in kwargs:
            setattr(self, kd_param, kwargs['Kd'])