"""
Input Validation Utilities for QSP Thyroid Model

This module provides validation functions for common scientific data types
used in the QSP thyroid model.
"""

import numpy as np
import pandas as pd
from typing import Any, Union, List, Tuple, Optional, Dict
import inspect

from .exceptions import ValidationError


def validate_positive_number(value: Any, name: str = "value", 
                           allow_zero: bool = False,
                           max_value: Optional[float] = None) -> float:
    """
    Validate that a value is a positive number.
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        allow_zero: Whether to allow zero values
        max_value: Maximum allowed value
        
    Returns:
        Validated float value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be a number, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="numeric_type"
        )
    
    if float_value < 0:
        raise ValidationError(
            f"{name} must be positive, got {float_value}",
            input_name=name,
            input_value=float_value,
            validation_rule="positive_value"
        )
    
    if not allow_zero and float_value == 0:
        raise ValidationError(
            f"{name} must be greater than zero, got {float_value}",
            input_name=name,
            input_value=float_value,
            validation_rule="non_zero_value"
        )
    
    if max_value is not None and float_value > max_value:
        raise ValidationError(
            f"{name} must be <= {max_value}, got {float_value}",
            input_name=name,
            input_value=float_value,
            validation_rule=f"max_value_{max_value}"
        )
    
    return float_value


def validate_probability(value: Any, name: str = "probability") -> float:
    """
    Validate that a value is a valid probability (0-1).
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        
    Returns:
        Validated probability value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be a number, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="numeric_type"
        )
    
    if not 0.0 <= float_value <= 1.0:
        raise ValidationError(
            f"{name} must be between 0 and 1, got {float_value}",
            input_name=name,
            input_value=float_value,
            validation_rule="probability_range"
        )
    
    return float_value


def validate_time_series(value: Any, name: str = "time_series",
                        min_length: int = 1,
                        max_length: Optional[int] = None,
                        time_column: Optional[str] = None,
                        require_monotonic_time: bool = True) -> pd.DataFrame:
    """
    Validate time series data.
    
    Args:
        value: Time series data (DataFrame, dict, or array-like)
        name: Name of the parameter for error messages
        min_length: Minimum required length
        max_length: Maximum allowed length
        time_column: Name of time column if DataFrame
        require_monotonic_time: Whether time values must be monotonic increasing
        
    Returns:
        Validated DataFrame
        
    Raises:
        ValidationError: If validation fails
    """
    # Convert to DataFrame
    if isinstance(value, pd.DataFrame):
        df = value.copy()
    elif isinstance(value, pd.Series):
        df = value.to_frame()
    elif isinstance(value, dict):
        df = pd.DataFrame(value)
    elif isinstance(value, (list, np.ndarray)):
        arr = np.asarray(value)
        if arr.ndim == 1:
            df = pd.DataFrame({'value': arr})
        else:
            df = pd.DataFrame(value)
    else:
        raise ValidationError(
            f"{name} must be DataFrame, Series, dict, or array-like, got {type(value).__name__}",
            input_name=name,
            input_value=value,
            validation_rule="time_series_type"
        )
    
    # Check length
    if len(df) < min_length:
        raise ValidationError(
            f"{name} must have at least {min_length} points, got {len(df)}",
            input_name=name,
            input_value=len(df),
            validation_rule=f"min_length_{min_length}"
        )
    
    if max_length is not None and len(df) > max_length:
        raise ValidationError(
            f"{name} must have at most {max_length} points, got {len(df)}",
            input_name=name,
            input_value=len(df),
            validation_rule=f"max_length_{max_length}"
        )
    
    # Check for NaN values
    if df.isnull().any().any():
        nan_cols = df.columns[df.isnull().any()].tolist()
        raise ValidationError(
            f"{name} contains NaN values in columns: {nan_cols}",
            input_name=name,
            input_value=nan_cols,
            validation_rule="no_nan_values"
        )
    
    # Check time column if specified
    if time_column is not None:
        if time_column not in df.columns:
            raise ValidationError(
                f"{name} must have time column '{time_column}'",
                input_name=name,
                input_value=list(df.columns),
                validation_rule=f"required_time_column_{time_column}"
            )
        
        time_values = df[time_column].values
        
        # Check for monotonic time
        if require_monotonic_time:
            if not np.all(np.diff(time_values) > 0):
                raise ValidationError(
                    f"{name} time values must be strictly increasing",
                    input_name=name,
                    input_value=time_values,
                    validation_rule="monotonic_time"
                )
    
    return df


def validate_parameter_range(value: Any, name: str, 
                           min_value: Optional[float] = None,
                           max_value: Optional[float] = None,
                           default_value: Optional[float] = None) -> float:
    """
    Validate that a parameter is within a specified range.
    
    Args:
        value: Value to validate
        name: Name of the parameter
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        default_value: Default value if value is None
        
    Returns:
        Validated float value
        
    Raises:
        ValidationError: If validation fails
    """
    # Substitute the default for a missing value, then validate it against the
    # same range constraints (an out-of-range default must not slip through).
    if value is None and default_value is not None:
        value = default_value

    try:
        float_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be a number, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="numeric_type"
        )
    
    if min_value is not None and float_value < min_value:
        raise ValidationError(
            f"{name} must be >= {min_value}, got {float_value}",
            input_name=name,
            input_value=float_value,
            validation_rule=f"min_value_{min_value}"
        )
    
    if max_value is not None and float_value > max_value:
        raise ValidationError(
            f"{name} must be <= {max_value}, got {float_value}",
            input_name=name,
            input_value=float_value,
            validation_rule=f"max_value_{max_value}"
        )
    
    return float_value


def validate_array_dimensions(value: Any, name: str = "array",
                            expected_dims: Optional[int] = None,
                            expected_shape: Optional[Tuple[int, ...]] = None,
                            min_length: Optional[int] = None,
                            max_length: Optional[int] = None) -> np.ndarray:
    """
    Validate array dimensions and shape.
    
    Args:
        value: Array to validate
        name: Name of the parameter for error messages
        expected_dims: Expected number of dimensions
        expected_shape: Expected shape tuple
        min_length: Minimum length for 1D arrays
        max_length: Maximum length for 1D arrays
        
    Returns:
        Validated numpy array

    Raises:
        ValidationError: If validation fails
    """
    # np.asarray() silently wraps scalars/strings/None into 0-d arrays, so reject
    # non-array-like inputs explicitly before conversion.
    if value is None or np.isscalar(value):
        raise ValidationError(
            f"{name} must be array-like, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="array_type"
        )

    try:
        array = np.asarray(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be array-like, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="array_type"
        )

    # Check dimensions
    if expected_dims is not None and array.ndim != expected_dims:
        raise ValidationError(
            f"{name} must have {expected_dims} dimensions, got {array.ndim}",
            input_name=name,
            input_value=array.shape,
            validation_rule=f"expected_dims_{expected_dims}"
        )
    
    # Check shape
    if expected_shape is not None and array.shape != expected_shape:
        raise ValidationError(
            f"{name} must have shape {expected_shape}, got {array.shape}",
            input_name=name,
            input_value=array.shape,
            validation_rule=f"expected_shape_{expected_shape}"
        )
    
    # Check length for 1D arrays
    if array.ndim == 1:
        if min_length is not None and len(array) < min_length:
            raise ValidationError(
                f"{name} must have at least {min_length} elements, got {len(array)}",
                input_name=name,
                input_value=len(array),
                validation_rule=f"min_length_{min_length}"
            )
        
        if max_length is not None and len(array) > max_length:
            raise ValidationError(
                f"{name} must have at most {max_length} elements, got {len(array)}",
                input_name=name,
                input_value=len(array),
                validation_rule=f"max_length_{max_length}"
            )
    
    # Check for NaN values (only for numeric arrays)
    if array.dtype.kind in 'fc':  # float or complex types
        if np.isnan(array).any():
            raise ValidationError(
                f"{name} contains NaN values",
                input_name=name,
                input_value=array,
                validation_rule="no_nan_values"
            )

        # Check for infinite values (only for numeric arrays)
        if np.isinf(array).any():
            raise ValidationError(
                f"{name} contains infinite values",
                input_name=name,
                input_value=array,
                validation_rule="no_infinite_values"
            )
    
    return array


def validate_array_type(value: Any, name: str = "array",
                       expected_type: Optional[type] = None,
                       allow_none: bool = False) -> np.ndarray:
    """
    Validate array data type.
    
    Args:
        value: Array to validate
        name: Name of the parameter for error messages
        expected_type: Expected data type (e.g., np.float64)
        allow_none: Whether to allow None values
        
    Returns:
        Validated numpy array
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        if allow_none:
            return None
        raise ValidationError(
            f"{name} must be array-like, got None",
            input_name=name,
            input_value=value,
            validation_rule="array_type"
        )

    try:
        array = np.asarray(value)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be array-like, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="array_type"
        )

    if expected_type is not None:
        try:
            array = array.astype(expected_type)
        except (ValueError, TypeError):
            raise ValidationError(
                f"{name} cannot be converted to {expected_type}",
                input_name=name,
                input_value=array.dtype,
                validation_rule=f"convertible_to_{expected_type}"
            )
    
    return array


def validate_string_choice(value: Any, name: str, 
                          valid_choices: List[str],
                          case_sensitive: bool = True) -> str:
    """
    Validate that a string value is one of the valid choices.
    
    Args:
        value: Value to validate
        name: Name of the parameter for error messages
        valid_choices: List of valid choices
        case_sensitive: Whether comparison is case sensitive
        
    Returns:
        Validated string value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{name} must be a string, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="string_type"
        )
    
    if not case_sensitive:
        value_lower = value.lower()
        valid_choices_lower = [c.lower() for c in valid_choices]
        if value_lower not in valid_choices_lower:
            raise ValidationError(
                f"{name} must be one of {valid_choices}, got '{value}'",
                input_name=name,
                input_value=value,
                validation_rule=f"valid_choice_{valid_choices}"
            )
        # Return original case version
        for choice in valid_choices:
            if choice.lower() == value_lower:
                return choice
    else:
        if value not in valid_choices:
            raise ValidationError(
                f"{name} must be one of {valid_choices}, got '{value}'",
                input_name=name,
                input_value=value,
                validation_rule=f"valid_choice_{valid_choices}"
            )
        return value


def validate_file_path(value: Any, name: str = "file_path",
                      must_exist: bool = False,
                      allowed_extensions: Optional[List[str]] = None) -> str:
    """
    Validate file path.
    
    Args:
        value: File path to validate
        name: Name of the parameter for error messages
        must_exist: Whether file must exist
        allowed_extensions: List of allowed file extensions
        
    Returns:
        Validated file path
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{name} must be a string, got {type(value).__name__}: {value}",
            input_name=name,
            input_value=value,
            validation_rule="string_type"
        )
    
    if not value.strip():
        raise ValidationError(
            f"{name} cannot be empty",
            input_name=name,
            input_value=value,
            validation_rule="non_empty_string"
        )
    
    # Check file existence
    if must_exist:
        from pathlib import Path
        if not Path(value).exists():
            raise ValidationError(
                f"{name} does not exist: {value}",
                input_name=name,
                input_value=value,
                validation_rule="file_exists"
            )
    
    # Check file extension
    if allowed_extensions is not None:
        from pathlib import Path
        ext = Path(value).suffix.lower()
        if ext not in [e.lower() for e in allowed_extensions]:
            raise ValidationError(
                f"{name} must have one of these extensions: {allowed_extensions}, got '{ext}'",
                input_name=name,
                input_value=value,
                validation_rule=f"allowed_extension_{allowed_extensions}"
            )
    
    return value


def validate_drug_type(value: Any) -> str:
    """
    Validate drug type parameter.
    
    Args:
        value: Drug type to validate
        
    Returns:
        Validated drug type
        
    Raises:
        ValidationError: If validation fails
    """
    valid_drugs = ['nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab']
    return validate_string_choice(value, "drug_type", valid_drugs, case_sensitive=False)


def validate_patient_id(value: Any) -> str:
    """
    Validate patient ID parameter.
    
    Args:
        value: Patient ID to validate
        
    Returns:
        Validated patient ID
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"patient_id must be a string, got {type(value).__name__}: {value}",
            input_name="patient_id",
            input_value=value,
            validation_rule="string_type"
        )
    
    if not value.strip():
        raise ValidationError(
            "patient_id cannot be empty",
            input_name="patient_id",
            input_value=value,
            validation_rule="non_empty_string"
        )
    
    # Check for reasonable length
    if len(value) > 50:
        raise ValidationError(
            "patient_id cannot exceed 50 characters",
            input_name="patient_id",
            input_value=len(value),
            validation_rule="max_length_50"
        )
    
    return value.strip()