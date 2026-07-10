"""
Assertion helpers for QSP_PD_Thyroid testing framework.

This module provides specialized assertion functions for scientific data validation.
"""

import numpy as np
import pandas as pd
from typing import Union, Dict, List, Tuple, Optional, Any
import math


def assert_array_close(
    actual: np.ndarray,
    expected: np.ndarray,
    rtol: float = 1e-5,
    atol: float = 1e-8,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that two arrays are close within tolerances.
    
    Args:
        actual: Actual array
        expected: Expected array
        rtol: Relative tolerance
        atol: Absolute tolerance
        err_msg: Optional error message
        
    Raises:
        AssertionError: If arrays are not close
    """
    if actual.shape != expected.shape:
        raise AssertionError(
            f"Array shapes differ: {actual.shape} vs {expected.shape}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    if not np.allclose(actual, expected, rtol=rtol, atol=atol):
        diff = np.abs(actual - expected)
        max_diff = np.max(diff)
        max_idx = np.unravel_index(np.argmax(diff), diff.shape)
        
        raise AssertionError(
            f"Arrays not close within tolerances (rtol={rtol}, atol={atol})\n"
            f"Max difference: {max_diff} at index {max_idx}\n"
            f"Actual value: {actual[max_idx]} vs Expected: {expected[max_idx]}\n"
            f"{f' - {err_msg}' if err_msg else ''}"
        )


def assert_series_close(
    actual: pd.Series,
    expected: pd.Series,
    rtol: float = 1e-5,
    atol: float = 1e-8,
    check_index: bool = True,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that two Series are close within tolerances.
    
    Args:
        actual: Actual Series
        expected: Expected Series
        rtol: Relative tolerance
        atol: Absolute tolerance
        check_index: Whether to check index equality
        err_msg: Optional error message
        
    Raises:
        AssertionError: If Series are not close
    """
    if check_index and not actual.index.equals(expected.index):
        raise AssertionError(
            f"Series indices differ:\n"
            f"Actual: {actual.index}\n"
            f"Expected: {expected.index}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    if not actual.index.equals(expected.index):
        # Realign for comparison
        expected = expected.reindex(actual.index)
    
    assert_array_close(
        actual.values, expected.values, rtol, atol, err_msg
    )


def assert_dataframe_close(
    actual: pd.DataFrame,
    expected: pd.DataFrame,
    rtol: float = 1e-5,
    atol: float = 1e-8,
    check_index: bool = True,
    check_columns: bool = True,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that two DataFrames are close within tolerances.
    
    Args:
        actual: Actual DataFrame
        expected: Expected DataFrame
        rtol: Relative tolerance
        atol: Absolute tolerance
        check_index: Whether to check index equality
        check_columns: Whether to check column equality
        err_msg: Optional error message
        
    Raises:
        AssertionError: If DataFrames are not close
    """
    if check_columns and not actual.columns.equals(expected.columns):
        raise AssertionError(
            f"DataFrame columns differ:\n"
            f"Actual: {list(actual.columns)}\n"
            f"Expected: {list(expected.columns)}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    if check_index and not actual.index.equals(expected.index):
        raise AssertionError(
            f"DataFrame indices differ:\n"
            f"Actual: {actual.index}\n"
            f"Expected: {expected.index}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    # Realign for comparison
    if not actual.index.equals(expected.index):
        expected = expected.reindex(actual.index)
    
    for col in actual.columns:
        if col in expected.columns:
            assert_series_close(
                actual[col], expected[col], rtol, atol, 
                check_index=False,  # Already checked
                err_msg=f"Column '{col}'{f' - {err_msg}' if err_msg else ''}"
            )


def assert_physical_bounds(
    data: Union[pd.Series, np.ndarray, Dict[str, Any]],
    bounds: Dict[str, Tuple[float, float]],
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that data values are within physical bounds.
    
    Args:
        data: Data to check (Series, array, or dict of arrays)
        bounds: Dictionary mapping variable names to (min, max) bounds
        err_msg: Optional error message
        
    Raises:
        AssertionError: If values are outside bounds
    """
    if isinstance(data, dict):
        for var_name, values in data.items():
            if var_name in bounds:
                min_val, max_val = bounds[var_name]
                if isinstance(values, (pd.Series, np.ndarray)):
                    violations = (values < min_val) | (values > max_val)
                    if violations.any():
                        viol_count = violations.sum()
                        viol_indices = np.where(violations)[0][:5]  # First 5
                        raise AssertionError(
                            f"Variable '{var_name}' has {viol_count} values outside bounds "
                            f"[{min_val}, {max_val}]. Example violations at indices: {viol_indices}"
                            f"{f' - {err_msg}' if err_msg else ''}"
                        )
    else:
        # Single array/Series
        if len(bounds) != 1:
            raise ValueError("Single data requires exactly one bound")
        
        var_name, (min_val, max_val) = next(iter(bounds.items()))
        violations = (data < min_val) | (data > max_val)
        if isinstance(violations, (pd.Series, np.ndarray)):
            if violations.any():
                viol_count = violations.sum()
                viol_indices = np.where(violations)[0][:5]  # First 5
                raise AssertionError(
                    f"Data has {viol_count} values outside bounds "
                    f"[{min_val}, {max_val}]. Example violations at indices: {viol_indices}"
                    f"{f' - {err_msg}' if err_msg else ''}"
                )
        else:
            if violations:
                raise AssertionError(
                    f"Value {data} outside bounds [{min_val}, {max_val}]"
                    f"{f' - {err_msg}' if err_msg else ''}"
                )


def assert_monotonic(
    data: Union[pd.Series, np.ndarray],
    increasing: bool = True,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that data is monotonic (increasing or decreasing).
    
    Args:
        data: Data to check
        increasing: True for increasing, False for decreasing
        err_msg: Optional error message
        
    Raises:
        AssertionError: If data is not monotonic
    """
    if isinstance(data, pd.Series):
        values = data.values
    else:
        values = np.asarray(data)
    
    if len(values) < 2:
        return  # Trivial case
    
    diffs = np.diff(values)
    
    if increasing:
        violations = diffs < 0
    else:
        violations = diffs > 0
    
    if violations.any():
        viol_count = violations.sum()
        viol_indices = np.where(violations)[0][:5]  # First 5
        direction = "increasing" if increasing else "decreasing"
        raise AssertionError(
            f"Data is not {direction}. Found {viol_count} violations. "
            f"Example violations at indices: {viol_indices}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )


def assert_no_nan_inf(
    data: Union[pd.Series, np.ndarray, pd.DataFrame, Dict[str, Any]],
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that data contains no NaN or infinite values.
    
    Args:
        data: Data to check
        err_msg: Optional error message
        
    Raises:
        AssertionError: If NaN or infinite values are found
    """
    if isinstance(data, dict):
        for key, values in data.items():
            if isinstance(values, (pd.Series, np.ndarray, pd.DataFrame)):
                if isinstance(values, pd.DataFrame):
                    if values.isnull().any().any():
                        nan_cols = values.columns[values.isnull().any()].tolist()
                        raise AssertionError(
                            f"DataFrame for key '{key}' contains NaN values in columns: {nan_cols}"
                            f"{f' - {err_msg}' if err_msg else ''}"
                        )
                    if np.isinf(values.values).any():
                        raise AssertionError(
                            f"DataFrame for key '{key}' contains infinite values"
                            f"{f' - {err_msg}' if err_msg else ''}"
                        )
                else:
                    if isinstance(values, pd.Series):
                        if values.isnull().any():
                            nan_count = values.isnull().sum()
                            raise AssertionError(
                                f"Series for key '{key}' contains {nan_count} NaN values"
                                f"{f' - {err_msg}' if err_msg else ''}"
                            )
                        if np.isinf(values.values).any():
                            raise AssertionError(
                                f"Series for key '{key}' contains infinite values"
                                f"{f' - {err_msg}' if err_msg else ''}"
                            )
                    else:  # numpy array
                        if np.isnan(values).any():
                            nan_count = np.isnan(values).sum()
                            raise AssertionError(
                                f"Array for key '{key}' contains {nan_count} NaN values"
                                f"{f' - {err_msg}' if err_msg else ''}"
                            )
                        if np.isinf(values).any():
                            raise AssertionError(
                                f"Array for key '{key}' contains infinite values"
                                f"{f' - {err_msg}' if err_msg else ''}"
                            )
    elif isinstance(data, pd.DataFrame):
        if data.isnull().any().any():
            nan_cols = data.columns[data.isnull().any()].tolist()
            raise AssertionError(
                f"DataFrame contains NaN values in columns: {nan_cols}"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
        if np.isinf(data.values).any():
            raise AssertionError(
                f"DataFrame contains infinite values"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    elif isinstance(data, pd.Series):
        if data.isnull().any():
            nan_count = data.isnull().sum()
            raise AssertionError(
                f"Series contains {nan_count} NaN values"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
        if np.isinf(data.values).any():
            raise AssertionError(
                f"Series contains infinite values"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    else:  # numpy array or scalar
        arr = np.asarray(data)
        if np.isnan(arr).any():
            nan_count = np.isnan(arr).sum()
            raise AssertionError(
                f"Array contains {nan_count} NaN values"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
        if np.isinf(arr).any():
            raise AssertionError(
                f"Array contains infinite values"
                f"{f' - {err_msg}' if err_msg else ''}"
            )


def assert_conservation_law(
    data: Dict[str, Union[pd.Series, np.ndarray]],
    conservation_eq: str,
    tolerance: float = 1e-10,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that a conservation law is satisfied within tolerance.
    
    Args:
        data: Dictionary of variables
        conservation_eq: String representing conservation equation
        tolerance: Tolerance for conservation check
        err_msg: Optional error message
        
    Raises:
        AssertionError: If conservation law is violated
    """
    try:
        # Create safe namespace for evaluation
        namespace = {}
        for key, value in data.items():
            if isinstance(value, pd.Series):
                namespace[key] = value.values
            else:
                namespace[key] = np.asarray(value)
        
        # Evaluate conservation equation
        result = eval(conservation_eq, {"__builtins__": {}}, namespace)
        
        if isinstance(result, (pd.Series, np.ndarray)):
            violations = np.abs(result) > tolerance
            if violations.any():
                max_violation = np.max(np.abs(result))
                viol_count = violations.sum()
                raise AssertionError(
                    f"Conservation law '{conservation_eq}' violated. "
                    f"Max violation: {max_violation:.2e}, Count: {viol_count}"
                    f"{f' - {err_msg}' if err_msg else ''}"
                )
        else:
            if abs(result) > tolerance:
                raise AssertionError(
                    f"Conservation law '{conservation_eq}' violated. "
                    f"Value: {result:.2e} (tolerance: {tolerance:.2e})"
                    f"{f' - {err_msg}' if err_msg else ''}"
                )
                
    except Exception as e:
        if isinstance(e, AssertionError):
            raise
        raise ValueError(f"Error evaluating conservation equation '{conservation_eq}': {e}")


def assert_steady_state(
    data: Union[pd.Series, np.ndarray],
    window_size: int = 10,
    tolerance: float = 1e-3,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that data reaches steady state within tolerance.
    
    Args:
        data: Time series data
        window_size: Size of rolling window for steady state check
        tolerance: Tolerance for steady state variation
        err_msg: Optional error message
        
    Raises:
        AssertionError: If steady state is not reached
    """
    if isinstance(data, pd.Series):
        values = data.values
    else:
        values = np.asarray(data)
    
    if len(values) < window_size * 2:
        raise AssertionError(
            f"Insufficient data points for steady state check. "
            f"Need at least {window_size * 2}, got {len(values)}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    # Check rolling standard deviation in the final window
    final_window = values[-window_size:]
    variation = np.std(final_window)
    
    if variation > tolerance:
        raise AssertionError(
            f"Data does not reach steady state. Final window variation: {variation:.2e} "
            f"(tolerance: {tolerance:.2e})"
            f"{f' - {err_msg}' if err_msg else ''}"
        )


def assert_hypothyroidism_classification(
    TSH: Union[pd.Series, np.ndarray],
    T3: Union[pd.Series, np.ndarray],
    grades: Union[pd.Series, np.ndarray],
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that hypothyroidism classification is correct.
    
    Args:
        TSH: TSH values
        T3: T3 values
        grades: Hypothyroidism grades
        err_msg: Optional error message
        
    Raises:
        AssertionError: If classification is incorrect
    """
    # Convert to arrays if needed
    if isinstance(TSH, pd.Series):
        TSH = TSH.values
    if isinstance(T3, pd.Series):
        T3 = T3.values
    if isinstance(grades, pd.Series):
        grades = grades.values
    
    # Check grade boundaries
    grade_0_mask = grades == 0
    grade_1_mask = grades == 1
    grade_2_mask = grades == 2
    grade_3_mask = grades == 3
    grade_4_mask = grades == 4
    
    # Grade 0: Normal
    if grade_0_mask.any():
        if np.any(TSH[grade_0_mask] > 4.5):
            raise AssertionError(
                f"Grade 0 classification has TSH > 4.5"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    
    # Grade 1: Mild
    if grade_1_mask.any():
        if np.any((TSH[grade_1_mask] <= 4.5) | (TSH[grade_1_mask] > 10.0) | (T3[grade_1_mask] < 3.1)):
            raise AssertionError(
                f"Grade 1 classification violates criteria (TSH: 4.5-10.0, T3 >= 3.1)"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    
    # Grade 2: Moderate
    if grade_2_mask.any():
        if np.any((TSH[grade_2_mask] <= 10.0) & (T3[grade_2_mask] >= 3.1)):
            raise AssertionError(
                f"Grade 2 classification violates criteria (TSH > 10.0 or T3 < 3.1)"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    
    # Grade 3: Severe
    if grade_3_mask.any():
        if np.any((TSH[grade_3_mask] <= 20.0) & (T3[grade_3_mask] >= 2.5)):
            raise AssertionError(
                f"Grade 3 classification violates criteria (TSH > 20.0 or T3 < 2.5)"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    
    # Grade 4: Life-threatening
    if grade_4_mask.any():
        if np.any((TSH[grade_4_mask] <= 50.0) & (T3[grade_4_mask] >= 2.0)):
            raise AssertionError(
                f"Grade 4 classification violates criteria (TSH > 50.0 or T3 < 2.0)"
                f"{f' - {err_msg}' if err_msg else ''}"
            )


def assert_ode_solution_quality(
    solution: Any,
    min_time_points: int = 10,
    max_step_size: float = 5.0,
    err_msg: Optional[str] = None
) -> None:
    """
    Assert that ODE solution meets quality criteria.
    
    Args:
        solution: ODE solution object
        min_time_points: Minimum number of time points
        max_step_size: Maximum allowed step size
        err_msg: Optional error message
        
    Raises:
        AssertionError: If solution quality is insufficient
    """
    # Check solution success
    if not solution.success:
        raise AssertionError(
            f"ODE solution failed: {solution.message}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    # Check number of time points
    if len(solution.t) < min_time_points:
        raise AssertionError(
            f"Insufficient time points: {len(solution.t)} < {min_time_points}"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    # Check step sizes
    if len(solution.t) > 1:
        step_sizes = np.diff(solution.t)
        max_step = np.max(step_sizes)
        if max_step > max_step_size:
            raise AssertionError(
                f"Maximum step size too large: {max_step:.2f} > {max_step_size}"
                f"{f' - {err_msg}' if err_msg else ''}"
            )
    
    # Check for NaN or infinite values
    if np.isnan(solution.y).any():
        raise AssertionError(
            f"ODE solution contains NaN values"
            f"{f' - {err_msg}' if err_msg else ''}"
        )
    
    if np.isinf(solution.y).any():
        raise AssertionError(
            f"ODE solution contains infinite values"
            f"{f' - {err_msg}' if err_msg else ''}"
        )