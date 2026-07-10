"""
Custom Exception Classes for QSP Thyroid Model

This module defines custom exception classes for different types of errors
that can occur in the QSP thyroid model.
"""

from typing import Optional, Dict, Any


class QSPModelError(Exception):
    """
    Base exception class for all QSP model errors.
    
    Attributes:
        message (str): Error message
        error_code (str): Unique error code for tracking
        details (Dict[str, Any]): Additional error details
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or "QSP_ERROR"
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Error Code: {self.error_code}, Details: {self.details})"
        return f"{self.message} (Error Code: {self.error_code})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ParameterError(QSPModelError):
    """
    Exception raised for parameter-related errors.
    
    Attributes:
        parameter_name (str): Name of the problematic parameter
        parameter_value (Any): The problematic value
        expected_range (Optional[str]): Expected range or format
    """
    
    def __init__(self, message: str, parameter_name: Optional[str] = None,
                 parameter_value: Any = None, expected_range: Optional[str] = None,
                 error_code: Optional[str] = None):
        self.parameter_name = parameter_name
        self.parameter_value = parameter_value
        self.expected_range = expected_range
        
        details = {
            'parameter_name': parameter_name,
            'parameter_value': parameter_value,
            'expected_range': expected_range
        }
        
        super().__init__(message, error_code or "PARAM_ERROR", details)


class SimulationError(QSPModelError):
    """
    Exception raised for simulation-related errors.
    
    Attributes:
        simulation_type (str): Type of simulation that failed
        time_point (Optional[float]): Time point where error occurred
        solver_message (Optional[str]): Message from ODE solver
    """
    
    def __init__(self, message: str, simulation_type: Optional[str] = None,
                 time_point: Optional[float] = None, solver_message: Optional[str] = None,
                 error_code: Optional[str] = None):
        self.simulation_type = simulation_type
        self.time_point = time_point
        self.solver_message = solver_message
        
        details = {
            'simulation_type': simulation_type,
            'time_point': time_point,
            'solver_message': solver_message
        }
        
        super().__init__(message, error_code or "SIM_ERROR", details)


class DataError(QSPModelError):
    """
    Exception raised for data handling errors.
    
    Attributes:
        data_source (str): Source of the problematic data
        data_type (str): Type of data (e.g., 'time_series', 'parameters')
        invalid_records (Optional[int]): Number of invalid records found
    """
    
    def __init__(self, message: str, data_source: Optional[str] = None,
                 data_type: Optional[str] = None, invalid_records: Optional[int] = None,
                 error_code: Optional[str] = None):
        self.data_source = data_source
        self.data_type = data_type
        self.invalid_records = invalid_records
        
        details = {
            'data_source': data_source,
            'data_type': data_type,
            'invalid_records': invalid_records
        }
        
        super().__init__(message, error_code or "DATA_ERROR", details)


class ValidationError(QSPModelError):
    """
    Exception raised for input validation errors.
    
    Attributes:
        input_name (str): Name of the invalid input
        input_value (Any): The invalid value
        validation_rule (str): Rule that was violated
    """
    
    def __init__(self, message: str, input_name: Optional[str] = None,
                 input_value: Any = None, validation_rule: Optional[str] = None,
                 error_code: Optional[str] = None):
        self.input_name = input_name
        self.input_value = input_value
        self.validation_rule = validation_rule
        
        details = {
            'input_name': input_name,
            'input_value': input_value,
            'validation_rule': validation_rule
        }
        
        super().__init__(message, error_code or "VALIDATION_ERROR", details)


class ConfigurationError(QSPModelError):
    """
    Exception raised for configuration-related errors.
    
    Attributes:
        config_file (str): Configuration file path
        config_section (str): Section with the problem
        missing_keys (Optional[list]): List of missing configuration keys
    """
    
    def __init__(self, message: str, config_file: Optional[str] = None,
                 config_section: Optional[str] = None, missing_keys: Optional[list] = None,
                 error_code: Optional[str] = None):
        self.config_file = config_file
        self.config_section = config_section
        self.missing_keys = missing_keys or []
        
        details = {
            'config_file': config_file,
            'config_section': config_section,
            'missing_keys': missing_keys
        }
        
        super().__init__(message, error_code or "CONFIG_ERROR", details)


class FileOperationError(QSPModelError):
    """
    Exception raised for file operation errors.
    
    Attributes:
        file_path (str): Path to the problematic file
        operation (str): Type of operation (read, write, etc.)
        original_error (Optional[Exception]): Original exception if applicable
    """
    
    def __init__(self, message: str, file_path: Optional[str] = None,
                 operation: Optional[str] = None, original_error: Optional[Exception] = None,
                 error_code: Optional[str] = None):
        self.file_path = file_path
        self.operation = operation
        self.original_error = original_error
        
        details = {
            'file_path': file_path,
            'operation': operation,
            'original_error': str(original_error) if original_error else None
        }
        
        super().__init__(message, error_code or "FILE_ERROR", details)


class ConvergenceError(SimulationError):
    """
    Exception raised when numerical methods fail to converge.
    
    Attributes:
        method (str): Numerical method that failed
        max_iterations (Optional[int]): Maximum iterations allowed
        residual_norm (Optional[float]): Final residual norm
    """
    
    def __init__(self, message: str, method: Optional[str] = None,
                 max_iterations: Optional[int] = None, residual_norm: Optional[float] = None,
                 error_code: Optional[str] = None):
        self.method = method
        self.max_iterations = max_iterations
        self.residual_norm = residual_norm
        
        details = {
            'method': method,
            'max_iterations': max_iterations,
            'residual_norm': residual_norm
        }
        
        super().__init__(message, "convergence", None, None, error_code or "CONVERGENCE_ERROR")
        self.details.update(details)


class NumericalInstabilityError(SimulationError):
    """
    Exception raised when numerical instability is detected.
    
    Attributes:
        variable_name (str): Name of unstable variable
        time_point (float): Time point where instability detected
        value (float): Problematic value
        threshold (float): Stability threshold
    """
    
    def __init__(self, message: str, variable_name: Optional[str] = None,
                 time_point: Optional[float] = None, value: Optional[float] = None,
                 threshold: Optional[float] = None, error_code: Optional[str] = None):
        self.variable_name = variable_name
        self.value = value
        self.threshold = threshold
        
        details = {
            'variable_name': variable_name,
            'value': value,
            'threshold': threshold
        }
        
        super().__init__(message, "numerical_instability", time_point, None, error_code or "NUMERICAL_INSTABILITY")
        self.details.update(details)