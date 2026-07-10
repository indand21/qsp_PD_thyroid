"""
Unit tests for base parameters module.

This module tests the BaseParameters class and its functionality.
"""

import pytest
import json
import hashlib
from datetime import datetime
from typing import Dict, Any

from config.base_parameters import BaseParameters


class TestBaseParameters:
    """Test cases for BaseParameters class."""
    
    def test_abstract_class(self):
        """Test that BaseParameters is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseParameters()
    
    def test_concrete_implementation(self):
        """Test concrete implementation of BaseParameters."""
        
        class ConcreteParameters(BaseParameters):
            """Concrete implementation for testing."""
            
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {
                    "param1": {
                        "type": float,
                        "min": 0.0,
                        "max": 10.0,
                        "description": "Test parameter 1"
                    },
                    "param2": {
                        "type": str,
                        "choices": ["test", "other"],
                        "description": "Test parameter 2"
                    }
                }
        
        # Test instantiation
        params = ConcreteParameters()
        assert params.param1 == 1.0
        assert params.param2 == "test"
        
        # Test metadata
        assert isinstance(params.created_at, datetime)
        assert isinstance(params.updated_at, datetime)
        assert params.version == "1.0.0"
        assert params.description is None
        assert params.author is None
    
    def test_initialization_with_data(self):
        """Test initialization with provided data."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters(
            param1=2.5,
            param2="custom",
            version="2.0.0",
            description="Custom description",
            author="Test Author"
        )
        
        assert params.param1 == 2.5
        assert params.param2 == "custom"
        assert params.version == "2.0.0"
        assert params.description == "Custom description"
        assert params.author == "Test Author"
    
    def test_hash_calculation(self):
        """Test hash calculation functionality."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params1 = ConcreteParameters(param1=1.0, param2="test")
        params2 = ConcreteParameters(param1=1.0, param2="test")
        params3 = ConcreteParameters(param1=2.0, param2="test")
        
        # Same parameters should have same hash
        hash1 = params1.calculate_hash()
        hash2 = params2.calculate_hash()
        hash3 = params3.calculate_hash()
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA-256 hex length
    
    def test_has_changed(self):
        """Test change detection functionality."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters(param1=1.0)
        initial_hash = params._hash
        
        # Initially unchanged
        assert not params.has_changed()
        
        # Change parameter
        params.param1 = 2.0
        
        # Should detect change
        assert params.has_changed()
        assert params._hash != initial_hash
    
    def test_update_timestamp(self):
        """Test timestamp update functionality."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters(param1=1.0)
        initial_updated_at = params.updated_at
        
        # Wait a bit to ensure different timestamp
        import time
        time.sleep(0.01)
        
        # Update parameter
        params.param1 = 2.0
        
        # Timestamp should be updated
        assert params.updated_at > initial_updated_at
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters(
            param1=2.5,
            param2="custom",
            version="2.0.0",
            description="Custom description"
        )
        
        # Test with metadata
        dict_with_meta = params.to_dict(include_metadata=True)
        assert 'param1' in dict_with_meta
        assert 'param2' in dict_with_meta
        assert 'version' in dict_with_meta
        assert 'description' in dict_with_meta
        assert 'created_at' in dict_with_meta
        assert 'updated_at' in dict_with_meta
        
        # Test without metadata
        dict_without_meta = params.to_dict(include_metadata=False)
        assert 'param1' in dict_without_meta
        assert 'param2' in dict_without_meta
        assert 'version' not in dict_without_meta
        assert 'description' not in dict_without_meta
        assert 'created_at' not in dict_without_meta
        assert 'updated_at' not in dict_without_meta
    
    def test_to_json(self):
        """Test JSON conversion."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters(param1=2.5, param2="custom")
        
        json_str = params.to_json()
        parsed = json.loads(json_str)
        
        assert parsed['param1'] == 2.5
        assert parsed['param2'] == "custom"
        assert 'version' in parsed
        assert 'created_at' in parsed
        assert 'updated_at' in parsed
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        data = {
            'param1': 3.5,
            'param2': 'from_dict',
            'version': '3.0.0',
            'description': 'Created from dict'
        }
        
        params = ConcreteParameters.from_dict(data)
        
        assert params.param1 == 3.5
        assert params.param2 == 'from_dict'
        assert params.version == '3.0.0'
        assert params.description == 'Created from dict'
    
    def test_from_json(self):
        """Test creation from JSON string."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        json_str = json.dumps({
            'param1': 4.5,
            'param2': 'from_json',
            'version': '4.0.0'
        })
        
        params = ConcreteParameters.from_json(json_str)
        
        assert params.param1 == 4.5
        assert params.param2 == 'from_json'
        assert params.version == '4.0.0'
    
    def test_validate_parameters(self):
        """Test parameter validation."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            param3: int = 5
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {
                    "param1": {
                        "type": float,
                        "min": 0.0,
                        "max": 10.0
                    },
                    "param2": {
                        "type": str,
                        "choices": ["test", "other"]
                    },
                    "param3": {
                        "type": int,
                        "min": 1,
                        "max": 10
                    }
                }
        
        # Valid parameters
        params = ConcreteParameters(param1=5.0, param2="test", param3=7)
        errors = params.validate_parameters()
        assert len(errors) == 0
        
        # Invalid parameters
        params = ConcreteParameters(param1=15.0, param2="invalid", param3=0)
        errors = params.validate_parameters()
        assert len(errors) == 3
        assert any("param1" in error and "above maximum" in error for error in errors)
        assert any("param2" in error and "not in allowed choices" in error for error in errors)
        assert any("param3" in error and "below minimum" in error for error in errors)
    
    def test_get_parameter_info(self):
        """Test getting parameter information."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {
                    "param1": {
                        "type": float,
                        "min": 0.0,
                        "max": 10.0,
                        "description": "Test parameter"
                    }
                }
        
        params = ConcreteParameters()
        
        info = params.get_parameter_info("param1")
        assert info is not None
        assert info['type'] == float
        assert info['min'] == 0.0
        assert info['max'] == 10.0
        assert info['description'] == "Test parameter"
        
        # Non-existent parameter
        info = params.get_parameter_info("non_existent")
        assert info is None
    
    def test_compare_parameters(self):
        """Test parameter comparison."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params1 = ConcreteParameters(param1=1.0, param2="test")
        params2 = ConcreteParameters(param1=1.0, param2="test")
        params3 = ConcreteParameters(param1=2.0, param2="test")
        params4 = ConcreteParameters(param1=1.0, param2="other")
        
        # Identical parameters
        differences = params1.compare_parameters(params2)
        assert len(differences) == 0
        
        # Different param1
        differences = params1.compare_parameters(params3)
        assert len(differences) == 1
        assert 'param1' in differences
        assert differences['param1'] == (1.0, 2.0)
        
        # Different param2
        differences = params1.compare_parameters(params4)
        assert len(differences) == 1
        assert 'param2' in differences
        assert differences['param2'] == ("test", "other")
        
        # Multiple differences
        differences = params3.compare_parameters(params4)
        assert len(differences) == 2
        assert 'param1' in differences
        assert 'param2' in differences
    
    def test_repr(self):
        """Test string representation."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters(version="2.0.0")
        repr_str = repr(params)
        
        assert "ConcreteParameters" in repr_str
        assert "version=2.0.0" in repr_str
        assert "updated_at=" in repr_str
    
    def test_parameter_modification_tracking(self):
        """Test that parameter modifications are properly tracked."""
        
        class ConcreteParameters(BaseParameters):
            param1: float = 1.0
            param2: str = "test"
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params = ConcreteParameters()
        initial_updated_at = params.updated_at
        initial_hash = params._hash
        
        # Wait a bit to ensure different timestamp
        import time
        time.sleep(0.01)
        
        # Modify parameter
        params.param1 = 2.0
        
        # Check that timestamp and hash were updated
        assert params.updated_at > initial_updated_at
        assert params._hash != initial_hash
        assert params.has_changed() is False  # Should be False after hash update
    
    def test_complex_parameter_hashing(self):
        """Test hashing with complex parameter types."""
        
        class ConcreteParameters(BaseParameters):
            param_dict: Dict[str, float] = {"a": 1.0, "b": 2.0}
            param_list: list = []
            
            def get_parameter_definitions(self) -> Dict[str, Dict[str, Any]]:
                return {}
        
        params1 = ConcreteParameters(param_dict={"a": 1.0, "b": 2.0})
        params2 = ConcreteParameters(param_dict={"b": 2.0, "a": 1.0})  # Different order
        
        # Hashes should be the same regardless of dict key order
        hash1 = params1.calculate_hash()
        hash2 = params2.calculate_hash()
        assert hash1 == hash2