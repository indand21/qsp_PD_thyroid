"""
Unit tests for input validation utilities.

This module tests the validation functions in the utils.validators module.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

from utils.validators import (
    validate_positive_number,
    validate_probability,
    validate_time_series,
    validate_parameter_range,
    validate_array_dimensions,
    validate_array_type,
    validate_string_choice,
    validate_file_path,
    validate_drug_type,
    validate_patient_id
)
from utils.exceptions import ValidationError


class TestValidatePositiveNumber:
    """Test cases for validate_positive_number function."""
    
    def test_valid_positive_numbers(self):
        """Test validation of valid positive numbers."""
        # Valid positive floats
        assert validate_positive_number(1.5) == 1.5
        assert validate_positive_number(0.1) == 0.1
        assert validate_positive_number(100.0) == 100.0
        
        # Valid positive integers
        assert validate_positive_number(5) == 5.0
        assert validate_positive_number(10) == 10.0
        
        # Valid string numbers
        assert validate_positive_number("2.5") == 2.5
        assert validate_positive_number("10") == 10.0
    
    def test_zero_value(self):
        """Test validation of zero values."""
        # Zero not allowed by default
        with pytest.raises(ValidationError, match="must be greater than zero"):
            validate_positive_number(0)
        
        # Zero allowed when specified
        assert validate_positive_number(0, allow_zero=True) == 0.0
    
    def test_negative_values(self):
        """Test validation of negative values."""
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_number(-1.0)
        
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_number(-5)
        
        with pytest.raises(ValidationError, match="must be positive"):
            validate_positive_number("-2.5")
    
    def test_max_value_constraint(self):
        """Test validation with maximum value constraint."""
        # Valid values
        assert validate_positive_number(5.0, max_value=10.0) == 5.0
        assert validate_positive_number(10.0, max_value=10.0) == 10.0
        
        # Invalid values
        with pytest.raises(ValidationError, match="must be <= 10.0"):
            validate_positive_number(15.0, max_value=10.0)
    
    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_positive_number("not_a_number")
        
        with pytest.raises(ValidationError, match="must be a number"):
            validate_positive_number([1, 2, 3])
        
        with pytest.raises(ValidationError, match="must be a number"):
            validate_positive_number(None)
        
        with pytest.raises(ValidationError, match="must be a number"):
            validate_positive_number({"value": 1.0})
    
    def test_custom_parameter_name(self):
        """Test validation with custom parameter name."""
        with pytest.raises(ValidationError, match="alpha must be positive"):
            validate_positive_number(-1.0, name="alpha")
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Very small positive number
        assert validate_positive_number(1e-10) == 1e-10
        
        # Very large positive number
        assert validate_positive_number(1e10) == 1e10
        
        # Scientific notation strings
        assert validate_positive_number("1e-5") == 1e-5
        assert validate_positive_number("1E5") == 100000.0


class TestValidateProbability:
    """Test cases for validate_probability function."""
    
    def test_valid_probabilities(self):
        """Test validation of valid probabilities."""
        # Valid probability values
        assert validate_probability(0.0) == 0.0
        assert validate_probability(0.5) == 0.5
        assert validate_probability(1.0) == 1.0
        assert validate_probability(0.25) == 0.25
        assert validate_probability(0.75) == 0.75
        
        # Valid string probabilities
        assert validate_probability("0.5") == 0.5
        assert validate_probability("0.0") == 0.0
        assert validate_probability("1.0") == 1.0
    
    def test_invalid_probabilities(self):
        """Test validation of invalid probabilities."""
        # Values below 0
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            validate_probability(-0.1)
        
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            validate_probability(-1.0)
        
        # Values above 1
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            validate_probability(1.1)
        
        with pytest.raises(ValidationError, match="must be between 0 and 1"):
            validate_probability(2.0)
    
    def test_edge_cases(self):
        """Test edge cases."""
        # Very small positive probability
        assert validate_probability(1e-10) == 1e-10
        
        # Very close to 1
        assert validate_probability(0.999999999) == 0.999999999
        
        # Scientific notation
        assert validate_probability("1e-6") == 1e-6
    
    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_probability("not_a_number")
        
        with pytest.raises(ValidationError, match="must be a number"):
            validate_probability([0.5])
        
        with pytest.raises(ValidationError, match="must be a number"):
            validate_probability(None)


class TestValidateTimeSeries:
    """Test cases for validate_time_series function."""
    
    def test_valid_dataframe(self):
        """Test validation of valid DataFrame."""
        df = pd.DataFrame({
            'time': [0, 1, 2, 3, 4],
            'value': [1.0, 2.0, 3.0, 4.0, 5.0]
        })
        
        result = validate_time_series(df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5
        assert list(result.columns) == ['time', 'value']
    
    def test_valid_dict(self):
        """Test validation of valid dictionary."""
        data = {
            'time': [0, 1, 2, 3],
            'TSH': [1.0, 1.5, 2.0, 2.5]
        }
        
        result = validate_time_series(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert list(result.columns) == ['time', 'TSH']
    
    def test_valid_list(self):
        """Test validation of valid list."""
        data = [1.0, 2.0, 3.0, 4.0]
        
        result = validate_time_series(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert list(result.columns) == ['value']
    
    def test_valid_numpy_array(self):
        """Test validation of valid numpy array."""
        data = np.array([1.0, 2.0, 3.0, 4.0])
        
        result = validate_time_series(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert list(result.columns) == ['value']
    
    def test_multidimensional_numpy_array(self):
        """Test validation of multidimensional numpy array."""
        data = np.array([[1, 2], [3, 4]])
        
        result = validate_time_series(data)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == [0, 1]
    
    def test_length_constraints(self):
        """Test length constraints."""
        df = pd.DataFrame({'value': [1, 2, 3]})
        
        # Minimum length
        result = validate_time_series(df, min_length=3)
        assert len(result) == 3
        
        with pytest.raises(ValidationError, match="must have at least 5 points"):
            validate_time_series(df, min_length=5)
        
        # Maximum length
        result = validate_time_series(df, max_length=5)
        assert len(result) == 3
        
        with pytest.raises(ValidationError, match="must have at most 2 points"):
            validate_time_series(df, max_length=2)
    
    def test_time_column_validation(self):
        """Test time column validation."""
        df = pd.DataFrame({
            'time': [0, 1, 2, 3],
            'value': [1, 2, 3, 4]
        })
        
        # Valid time column
        result = validate_time_series(df, time_column='time')
        assert 'time' in result.columns
        
        # Missing time column
        with pytest.raises(ValidationError, match="must have time column 'timestamp'"):
            validate_time_series(df, time_column='timestamp')
        
        # Non-monotonic time
        df_non_monotonic = pd.DataFrame({
            'time': [0, 2, 1, 3],
            'value': [1, 2, 3, 4]
        })
        
        with pytest.raises(ValidationError, match="time values must be strictly increasing"):
            validate_time_series(df_non_monotonic, time_column='time')
        
        # Non-monotonic check disabled
        result = validate_time_series(
            df_non_monotonic, 
            time_column='time', 
            require_monotonic_time=False
        )
        assert len(result) == 4
    
    def test_nan_values(self):
        """Test NaN value validation."""
        # DataFrame with NaN
        df_with_nan = pd.DataFrame({
            'time': [0, 1, 2, np.nan],
            'value': [1, 2, 3, 4]
        })
        
        with pytest.raises(ValidationError, match="contains NaN values"):
            validate_time_series(df_with_nan)
        
        df_with_nan2 = pd.DataFrame({
            'time': [0, 1, 2, 3],
            'value': [1, np.nan, 3, 4]
        })
        
        with pytest.raises(ValidationError, match="contains NaN values"):
            validate_time_series(df_with_nan2)
    
    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(ValidationError, match="must be DataFrame, Series, dict, or array-like"):
            validate_time_series("not_valid")
        
        with pytest.raises(ValidationError, match="must be DataFrame, Series, dict, or array-like"):
            validate_time_series(123)
        
        with pytest.raises(ValidationError, match="must be DataFrame, Series, dict, or array-like"):
            validate_time_series(None)


class TestValidateParameterRange:
    """Test cases for validate_parameter_range function."""
    
    def test_valid_range(self):
        """Test validation within valid range."""
        assert validate_parameter_range(5.0, "param", min_value=0.0, max_value=10.0) == 5.0
        assert validate_parameter_range(0.0, "param", min_value=0.0, max_value=10.0) == 0.0
        assert validate_parameter_range(10.0, "param", min_value=0.0, max_value=10.0) == 10.0
    
    def test_min_value_constraint(self):
        """Test minimum value constraint."""
        assert validate_parameter_range(5.0, "param", min_value=3.0) == 5.0
        
        with pytest.raises(ValidationError, match="must be >= 3.0"):
            validate_parameter_range(2.0, "param", min_value=3.0)
    
    def test_max_value_constraint(self):
        """Test maximum value constraint."""
        assert validate_parameter_range(5.0, "param", max_value=10.0) == 5.0
        
        with pytest.raises(ValidationError, match="must be <= 8.0"):
            validate_parameter_range(9.0, "param", max_value=8.0)
    
    def test_both_constraints(self):
        """Test both minimum and maximum constraints."""
        assert validate_parameter_range(5.0, "param", min_value=3.0, max_value=8.0) == 5.0
        
        with pytest.raises(ValidationError, match="must be >= 3.0"):
            validate_parameter_range(2.0, "param", min_value=3.0, max_value=8.0)
        
        with pytest.raises(ValidationError, match="must be <= 8.0"):
            validate_parameter_range(9.0, "param", min_value=3.0, max_value=8.0)
    
    def test_default_value(self):
        """Test default value functionality."""
        assert validate_parameter_range(None, "param", default_value=5.0) == 5.0
        
        # Default value should be used when value is None
        result = validate_parameter_range(None, "param", min_value=3.0, max_value=8.0, default_value=5.0)
        assert result == 5.0
        
        # Default value should be validated against constraints
        with pytest.raises(ValidationError, match="must be >= 3.0"):
            validate_parameter_range(None, "param", min_value=3.0, max_value=8.0, default_value=2.0)
    
    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(ValidationError, match="must be a number"):
            validate_parameter_range("not_a_number", "param")
        
        with pytest.raises(ValidationError, match="must be a number"):
            validate_parameter_range([1, 2, 3], "param")


class TestValidateArrayDimensions:
    """Test cases for validate_array_dimensions function."""
    
    def test_valid_arrays(self):
        """Test validation of valid arrays."""
        # 1D array
        arr_1d = np.array([1, 2, 3, 4])
        result = validate_array_dimensions(arr_1d, expected_dims=1)
        assert result.ndim == 1
        assert len(result) == 4
        
        # 2D array
        arr_2d = np.array([[1, 2], [3, 4]])
        result = validate_array_dimensions(arr_2d, expected_dims=2)
        assert result.ndim == 2
        assert result.shape == (2, 2)
        
        # Specific shape
        result = validate_array_dimensions(arr_2d, expected_shape=(2, 2))
        assert result.shape == (2, 2)
    
    def test_dimension_constraints(self):
        """Test dimension constraints."""
        arr_1d = np.array([1, 2, 3])
        arr_2d = np.array([[1, 2, 3]])
        
        # Correct dimensions
        result = validate_array_dimensions(arr_1d, expected_dims=1)
        assert result.ndim == 1
        
        # Incorrect dimensions
        with pytest.raises(ValidationError, match="must have 2 dimensions"):
            validate_array_dimensions(arr_1d, expected_dims=2)
        
        with pytest.raises(ValidationError, match="must have 1 dimensions"):
            validate_array_dimensions(arr_2d, expected_dims=1)
    
    def test_shape_constraints(self):
        """Test shape constraints."""
        arr = np.array([[1, 2], [3, 4]])
        
        # Correct shape
        result = validate_array_dimensions(arr, expected_shape=(2, 2))
        assert result.shape == (2, 2)
        
        # Incorrect shape
        with pytest.raises(ValidationError, match="must have shape \\(3, 2\\)"):
            validate_array_dimensions(arr, expected_shape=(3, 2))
    
    def test_length_constraints_1d(self):
        """Test length constraints for 1D arrays."""
        arr = np.array([1, 2, 3, 4, 5])
        
        # Minimum length
        result = validate_array_dimensions(arr, min_length=3)
        assert len(result) == 5
        
        with pytest.raises(ValidationError, match="must have at least 10 elements"):
            validate_array_dimensions(arr, min_length=10)
        
        # Maximum length
        result = validate_array_dimensions(arr, max_length=10)
        assert len(result) == 5
        
        with pytest.raises(ValidationError, match="must have at most 3 elements"):
            validate_array_dimensions(arr, max_length=3)
    
    def test_nan_and_inf_validation(self):
        """Test NaN and infinite value validation."""
        # Array with NaN
        arr_nan = np.array([1, 2, np.nan, 4])
        with pytest.raises(ValidationError, match="contains NaN values"):
            validate_array_dimensions(arr_nan)
        
        # Array with inf
        arr_inf = np.array([1, 2, np.inf, 4])
        with pytest.raises(ValidationError, match="contains infinite values"):
            validate_array_dimensions(arr_inf)
        
        # Array with -inf
        arr_neg_inf = np.array([1, 2, -np.inf, 4])
        with pytest.raises(ValidationError, match="contains infinite values"):
            validate_array_dimensions(arr_neg_inf)
    
    def test_type_conversion(self):
        """Test type conversion to numpy array."""
        # List conversion
        result = validate_array_dimensions([1, 2, 3, 4])
        assert isinstance(result, np.ndarray)
        assert result.ndim == 1
        
        # Tuple conversion
        result = validate_array_dimensions((1, 2, 3, 4))
        assert isinstance(result, np.ndarray)
        
        # Nested list conversion
        result = validate_array_dimensions([[1, 2], [3, 4]])
        assert isinstance(result, np.ndarray)
        assert result.ndim == 2
    
    def test_invalid_types(self):
        """Test validation with invalid types."""
        with pytest.raises(ValidationError, match="must be array-like"):
            validate_array_dimensions("not_an_array")
        
        with pytest.raises(ValidationError, match="must be array-like"):
            validate_array_dimensions(None)
        
        with pytest.raises(ValidationError, match="must be array-like"):
            validate_array_dimensions(123)


class TestValidateArrayType:
    """Test cases for validate_array_type function."""
    
    def test_type_conversion(self):
        """Test array type conversion."""
        arr = [1, 2, 3, 4]
        
        # Convert to float64
        result = validate_array_type(arr, expected_type=np.float64)
        assert result.dtype == np.float64
        
        # Convert to int32
        result = validate_array_type(arr, expected_type=np.int32)
        assert result.dtype == np.int32
    
    def test_invalid_conversion(self):
        """Test invalid type conversion."""
        arr = ["not", "numbers", "here"]
        
        with pytest.raises(ValidationError, match="cannot be converted to"):
            validate_array_type(arr, expected_type=np.float64)
    
    def test_allow_none(self):
        """Test allowing None values."""
        # Allow None
        result = validate_array_type(None, allow_none=True)
        assert result is None
        
        # Don't allow None
        with pytest.raises(ValidationError, match="must be array-like"):
            validate_array_type(None, allow_none=False)
    
    def test_no_type_constraint(self):
        """Test validation without type constraint."""
        arr = [1, 2, 3, 4]
        result = validate_array_type(arr)
        assert isinstance(result, np.ndarray)
        # Should preserve original type if possible
        assert np.issubdtype(result.dtype, np.integer)


class TestValidateStringChoice:
    """Test cases for validate_string_choice function."""
    
    def test_valid_choices(self):
        """Test validation of valid choices."""
        choices = ["option1", "option2", "option3"]
        
        assert validate_string_choice("option1", "param", choices) == "option1"
        assert validate_string_choice("option2", "param", choices) == "option2"
        assert validate_string_choice("option3", "param", choices) == "option3"
    
    def test_case_sensitive(self):
        """Test case-sensitive validation."""
        choices = ["Option1", "Option2", "Option3"]
        
        # Valid exact match
        assert validate_string_choice("Option1", "param", choices) == "Option1"
        
        # Invalid case
        with pytest.raises(ValidationError, match="must be one of"):
            validate_string_choice("option1", "param", choices)
    
    def test_case_insensitive(self):
        """Test case-insensitive validation."""
        choices = ["Option1", "Option2", "Option3"]
        
        # Valid with different case
        assert validate_string_choice("option1", "param", choices, case_sensitive=False) == "Option1"
        assert validate_string_choice("OPTION1", "param", choices, case_sensitive=False) == "Option1"
        assert validate_string_choice("Option2", "param", choices, case_sensitive=False) == "Option2"
    
    def test_invalid_choice(self):
        """Test validation of invalid choice."""
        choices = ["option1", "option2", "option3"]
        
        with pytest.raises(ValidationError, match="must be one of"):
            validate_string_choice("invalid_option", "param", choices)
    
    def test_non_string_input(self):
        """Test validation with non-string input."""
        choices = ["option1", "option2", "option3"]
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string_choice(123, "param", choices)
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string_choice(["option1"], "param", choices)
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_string_choice(None, "param", choices)


class TestValidateFilePath:
    """Test cases for validate_file_path function."""
    
    def test_valid_path(self):
        """Test validation of valid file path."""
        valid_path = "/path/to/file.txt"
        result = validate_file_path(valid_path)
        assert result == valid_path
    
    def test_empty_path(self):
        """Test validation of empty path."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_file_path("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_file_path("   ")
    
    def test_non_string_input(self):
        """Test validation with non-string input."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_file_path(123)
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_file_path(["path", "to", "file"])
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_file_path(None)
    
    def test_file_existence(self):
        """Test file existence validation."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # File exists - should pass
            result = validate_file_path(temp_path, must_exist=True)
            assert result == temp_path
            
            # File doesn't exist - should fail
            non_existent = temp_path + "_nonexistent"
            with pytest.raises(ValidationError, match="does not exist"):
                validate_file_path(non_existent, must_exist=True)
        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_file_extension_validation(self):
        """Test file extension validation."""
        valid_extensions = [".txt", ".csv", ".yaml"]
        
        # Valid extensions
        assert validate_file_path("file.txt", allowed_extensions=valid_extensions) == "file.txt"
        assert validate_file_path("file.csv", allowed_extensions=valid_extensions) == "file.csv"
        assert validate_file_path("file.yaml", allowed_extensions=valid_extensions) == "file.yaml"
        
        # Invalid extension
        with pytest.raises(ValidationError, match="must have one of these extensions"):
            validate_file_path("file.json", allowed_extensions=valid_extensions)
        
        # Case insensitive
        assert validate_file_path("file.TXT", allowed_extensions=valid_extensions) == "file.TXT"
        assert validate_file_path("file.CSV", allowed_extensions=valid_extensions) == "file.CSV"


class TestValidateDrugType:
    """Test cases for validate_drug_type function."""
    
    def test_valid_drug_types(self):
        """Test validation of valid drug types."""
        valid_drugs = ["nivolumab", "pembrolizumab", "atezolizumab", "durvalumab"]
        
        for drug in valid_drugs:
            result = validate_drug_type(drug)
            assert result == drug
    
    def test_case_insensitive_drug_types(self):
        """Test case-insensitive drug type validation."""
        assert validate_drug_type("NIVOLUMAB") == "nivolumab"
        assert validate_drug_type("Pembrolizumab") == "pembrolizumab"
        assert validate_drug_type("ATEZOLIZUMAB") == "atezolizumab"
        assert validate_drug_type("Durvalumab") == "durvalumab"
    
    def test_invalid_drug_types(self):
        """Test validation of invalid drug types."""
        invalid_drugs = ["invalid_drug", "drug1", "medicine", ""]
        
        for drug in invalid_drugs:
            with pytest.raises(ValidationError, match="must be one of"):
                validate_drug_type(drug)
    
    def test_non_string_drug_types(self):
        """Test validation with non-string drug types."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_drug_type(123)
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_drug_type(["nivolumab"])
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_drug_type(None)


class TestValidatePatientId:
    """Test cases for validate_patient_id function."""
    
    def test_valid_patient_ids(self):
        """Test validation of valid patient IDs."""
        valid_ids = ["PATIENT001", "VP0001", "TEST_123", "patient-456", "ID123"]
        
        for patient_id in valid_ids:
            result = validate_patient_id(patient_id)
            assert result == patient_id
    
    def test_empty_patient_id(self):
        """Test validation of empty patient ID."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_patient_id("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_patient_id("   ")
    
    def test_long_patient_id(self):
        """Test validation of overly long patient ID."""
        long_id = "A" * 51  # 51 characters
        with pytest.raises(ValidationError, match="cannot exceed 50 characters"):
            validate_patient_id(long_id)
    
    def test_max_length_boundary(self):
        """Test validation at maximum length boundary."""
        max_length_id = "A" * 50  # Exactly 50 characters
        result = validate_patient_id(max_length_id)
        assert result == max_length_id
    
    def test_non_string_patient_id(self):
        """Test validation with non-string patient ID."""
        with pytest.raises(ValidationError, match="must be a string"):
            validate_patient_id(123)
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_patient_id(["PATIENT001"])
        
        with pytest.raises(ValidationError, match="must be a string"):
            validate_patient_id(None)
    
    def test_whitespace_handling(self):
        """Test whitespace handling in patient ID."""
        # Should be stripped
        assert validate_patient_id("  PATIENT001  ") == "PATIENT001"
        assert validate_patient_id("\tVP0001\n") == "VP0001"
    
    def test_special_characters(self):
        """Test patient IDs with special characters."""
        # Valid special characters
        valid_special = ["PATIENT-001", "PATIENT_001", "PATIENT.001", "PATIENT/001"]
        
        for patient_id in valid_special:
            result = validate_patient_id(patient_id)
            assert result == patient_id


class TestValidatorIntegration:
    """Test cases for validator integration scenarios."""
    
    def test_nested_validation(self):
        """Test nested validation scenarios."""
        # Validate a complex structure
        patient_data = {
            'patient_id': 'TEST001',
            'drug_type': 'nivolumab',
            'parameters': {
                'alpha': 0.001,
                'beta': 0.1,
                'probability': 0.5
            },
            'time_series': {
                'time': [0, 1, 2, 3],
                'TSH': [1.0, 1.5, 2.0, 2.5]
            }
        }
        
        # Validate patient ID
        patient_id = validate_patient_id(patient_data['patient_id'])
        assert patient_id == 'TEST001'
        
        # Validate drug type
        drug_type = validate_drug_type(patient_data['drug_type'])
        assert drug_type == 'nivolumab'
        
        # Validate parameters
        alpha = validate_positive_number(patient_data['parameters']['alpha'], name='alpha')
        beta = validate_parameter_range(patient_data['parameters']['beta'], 'beta', min_value=0.0, max_value=1.0)
        probability = validate_probability(patient_data['parameters']['probability'])
        
        assert alpha == 0.001
        assert beta == 0.1
        assert probability == 0.5
        
        # Validate time series
        ts_df = validate_time_series(patient_data['time_series'], time_column='time')
        assert isinstance(ts_df, pd.DataFrame)
        assert len(ts_df) == 4
    
    def test_validation_error_attributes(self):
        """Test that validation errors have proper attributes."""
        with pytest.raises(ValidationError) as exc_info:
            validate_positive_number(-1.0, name="test_param")
        
        error = exc_info.value
        assert error.input_name == "test_param"
        assert error.input_value == -1.0
        assert error.validation_rule == "positive_value"
    
    def test_chained_validation(self):
        """Test chained validation with multiple checks."""
        def validate_complex_parameter(value, name):
            """Complex validation with multiple checks."""
            # First check: positive number
            result = validate_positive_number(value, name)
            
            # Second check: within range
            result = validate_parameter_range(result, name, min_value=0.001, max_value=0.1)
            
            # Third check: not too close to boundaries
            if result < 0.002:
                raise ValidationError(
                    f"{name} is too close to minimum boundary",
                    input_name=name,
                    input_value=result,
                    validation_rule="boundary_buffer"
                )
            
            return result
        
        # Valid value
        result = validate_complex_parameter(0.005, "alpha")
        assert result == 0.005
        
        # Invalid: negative
        with pytest.raises(ValidationError, match="must be positive"):
            validate_complex_parameter(-0.001, "alpha")
        
        # Invalid: too close to boundary
        with pytest.raises(ValidationError, match="too close to minimum boundary"):
            validate_complex_parameter(0.0015, "alpha")