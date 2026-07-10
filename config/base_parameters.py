"""
Base Parameters Module
======================

This module provides the BaseParameters class that contains common functionality
for all parameter classes in the configuration management system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import json
import hashlib
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)


class BaseParameters(BaseModel, ABC):
    """
    Abstract base class for all parameter classes.
    
    Provides common functionality including:
    - Parameter validation
    - Serialization/deserialization
    - Hash calculation for versioning
    - Metadata tracking
    """
    
    # Metadata fields
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="1.0.0")
    description: Optional[str] = Field(default=None)
    author: Optional[str] = Field(default=None)
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        use_enum_values = True
        extra = "ignore"  # Changed from "forbid" to allow extra fields like parameter_type in YAML
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def __init__(self, **data):
        """Initialize parameters with validation."""
        super().__init__(**data)
        self._post_init_processing()
    
    def _post_init_processing(self):
        """Post-initialization processing."""
        # Calculate initial hash
        self._hash = self.calculate_hash()
    
    @abstractmethod
    def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get parameter definitions for validation and documentation.
        
        Returns:
            Dictionary mapping parameter names to their definitions
            including type, range, description, etc.
        """
        pass
    
    def calculate_hash(self) -> str:
        """
        Calculate a hash of the current parameter values.
        
        Returns:
            SHA-256 hash of the parameter values
        """
        # Get all fields except metadata
        param_fields = {}
        for field_name, field_value in self.dict(exclude={'created_at', 'updated_at', 'version', 'description', 'author'}).items():
            if isinstance(field_value, (int, float, str, bool, type(None))):
                param_fields[field_name] = field_value
            elif isinstance(field_value, dict):
                # Sort dictionary keys for consistent hashing
                param_fields[field_name] = dict(sorted(field_value.items()))
        
        # Create JSON string with sorted keys
        json_str = json.dumps(param_fields, sort_keys=True, default=str)
        
        # Calculate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def has_changed(self) -> bool:
        """
        Check if parameters have changed since initialization.
        
        Returns:
            True if parameters have changed, False otherwise
        """
        current_hash = self.calculate_hash()
        return current_hash != self._hash
    
    def update_timestamp(self):
        """Update the timestamp when parameters are modified."""
        self.updated_at = datetime.now()
        self._hash = self.calculate_hash()
    
    def to_dict(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Convert parameters to dictionary.
        
        Args:
            include_metadata: Whether to include metadata fields
            
        Returns:
            Dictionary representation of parameters
        """
        if include_metadata:
            return self.dict()
        else:
            return self.dict(exclude={'created_at', 'updated_at', 'version', 'description', 'author'})
    
    def to_json(self, include_metadata: bool = True, indent: int = 2) -> str:
        """
        Convert parameters to JSON string.
        
        Args:
            include_metadata: Whether to include metadata fields
            indent: JSON indentation level
            
        Returns:
            JSON string representation of parameters
        """
        return json.dumps(self.to_dict(include_metadata), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseParameters':
        """
        Create parameters from dictionary.
        
        Args:
            data: Dictionary containing parameter values
            
        Returns:
            BaseParameters instance
        """
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'BaseParameters':
        """
        Create parameters from JSON string.
        
        Args:
            json_str: JSON string containing parameter values
            
        Returns:
            BaseParameters instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate_parameters(self) -> List[str]:
        """
        Validate parameters against their definitions.
        
        Returns:
            List of validation error messages
        """
        errors = []
        definitions = self.get_parameter_definitions()
        
        for param_name, param_def in definitions.items():
            if not hasattr(self, param_name):
                continue
                
            value = getattr(self, param_name)
            
            # Type validation
            expected_type = param_def.get('type')
            if expected_type and not isinstance(value, expected_type):
                errors.append(f"Parameter '{param_name}' should be of type {expected_type.__name__}, got {type(value).__name__}")
                continue
            
            # Range validation
            if isinstance(value, (int, float)):
                min_val = param_def.get('min')
                max_val = param_def.get('max')
                
                if min_val is not None and value < min_val:
                    errors.append(f"Parameter '{param_name}' value {value} is below minimum {min_val}")
                
                if max_val is not None and value > max_val:
                    errors.append(f"Parameter '{param_name}' value {value} is above maximum {max_val}")
            
            # Choice validation
            choices = param_def.get('choices')
            if choices and value not in choices:
                errors.append(f"Parameter '{param_name}' value {value} is not in allowed choices: {choices}")
        
        return errors
    
    def get_parameter_info(self, param_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific parameter.
        
        Args:
            param_name: Name of the parameter
            
        Returns:
            Parameter definition dictionary or None if not found
        """
        definitions = self.get_parameter_definitions()
        return definitions.get(param_name)
    
    def compare_parameters(self, other: 'BaseParameters') -> Dict[str, Tuple[Any, Any]]:
        """
        Compare parameters with another instance.
        
        Args:
            other: Another BaseParameters instance
            
        Returns:
            Dictionary mapping parameter names to tuples of (self_value, other_value)
            for parameters that differ
        """
        differences = {}
        
        # Get all field names from both instances
        all_fields = set(self.__fields__.keys()) | set(other.__fields__.keys())
        
        for field_name in all_fields:
            if field_name in {'created_at', 'updated_at', 'version', 'description', 'author'}:
                continue
                
            self_value = getattr(self, field_name, None)
            other_value = getattr(other, field_name, None)
            
            if self_value != other_value:
                differences[field_name] = (self_value, other_value)
        
        return differences
    
    def __setattr__(self, name, value):
        """Override setattr to update timestamp when parameters are modified."""
        super().__setattr__(name, value)
        
        # Update timestamp if this is a parameter field (not metadata)
        if name not in {'created_at', 'updated_at', 'version', 'description', 'author', '_hash'}:
            self.update_timestamp()
    
    def __repr__(self) -> str:
        """String representation of parameters."""
        return f"{self.__class__.__name__}(version={self.version}, updated_at={self.updated_at.isoformat()})"