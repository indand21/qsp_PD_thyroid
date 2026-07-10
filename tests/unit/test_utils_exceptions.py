"""
Unit tests for custom exception classes.

This module tests the custom exception classes in the utils.exceptions module.
"""

import pytest
from utils.exceptions import (
    QSPModelError,
    ParameterError,
    SimulationError,
    DataError,
    ValidationError,
    ConfigurationError,
    FileOperationError,
    ConvergenceError,
    NumericalInstabilityError
)


class TestQSPModelError:
    """Test cases for QSPModelError base class."""
    
    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = QSPModelError("Test error message")
        
        assert error.message == "Test error message"
        assert error.error_code == "QSP_ERROR"
        assert error.details == {}
        assert str(error) == "Test error message (Error Code: QSP_ERROR)"
    
    def test_initialization_with_error_code(self):
        """Test initialization with custom error code."""
        error = QSPModelError("Test error", error_code="CUSTOM_ERROR")
        
        assert error.message == "Test error"
        assert error.error_code == "CUSTOM_ERROR"
        assert str(error) == "Test error (Error Code: CUSTOM_ERROR)"
    
    def test_initialization_with_details(self):
        """Test initialization with details."""
        details = {"param": "alpha", "value": 0.5}
        error = QSPModelError("Test error", details=details)
        
        assert error.details == details
        assert "Details: {'param': 'alpha', 'value': 0.5}" in str(error)
    
    def test_to_dict(self):
        """Test exception to dictionary conversion."""
        details = {"param": "alpha", "value": 0.5}
        error = QSPModelError("Test error", error_code="TEST_ERROR", details=details)
        
        error_dict = error.to_dict()
        
        assert error_dict['error_type'] == "QSPModelError"
        assert error_dict['message'] == "Test error"
        assert error_dict['error_code'] == "TEST_ERROR"
        assert error_dict['details'] == details
    
    def test_inheritance(self):
        """Test that QSPModelError inherits from Exception."""
        error = QSPModelError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, BaseException)


class TestParameterError:
    """Test cases for ParameterError class."""
    
    def test_basic_initialization(self):
        """Test basic parameter error initialization."""
        error = ParameterError("Invalid parameter")
        
        assert error.message == "Invalid parameter"
        assert error.parameter_name is None
        assert error.parameter_value is None
        assert error.expected_range is None
        assert error.error_code == "PARAM_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with parameter attributes."""
        error = ParameterError(
            "Invalid alpha value",
            parameter_name="alpha",
            parameter_value=-0.1,
            expected_range="> 0"
        )
        
        assert error.parameter_name == "alpha"
        assert error.parameter_value == -0.1
        assert error.expected_range == "> 0"
        
        # Check details
        assert error.details['parameter_name'] == "alpha"
        assert error.details['parameter_value'] == -0.1
        assert error.details['expected_range'] == "> 0"
    
    def test_custom_error_code(self):
        """Test custom error code."""
        error = ParameterError("Invalid parameter", error_code="ALPHA_ERROR")
        assert error.error_code == "ALPHA_ERROR"
    
    def test_inheritance(self):
        """Test that ParameterError inherits from QSPModelError."""
        error = ParameterError("Test error")
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestSimulationError:
    """Test cases for SimulationError class."""
    
    def test_basic_initialization(self):
        """Test basic simulation error initialization."""
        error = SimulationError("Simulation failed")
        
        assert error.message == "Simulation failed"
        assert error.simulation_type is None
        assert error.time_point is None
        assert error.solver_message is None
        assert error.error_code == "SIM_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with simulation attributes."""
        error = SimulationError(
            "ODE solver failed",
            simulation_type="patient_simulation",
            time_point=45.5,
            solver_message="Step size too small"
        )
        
        assert error.simulation_type == "patient_simulation"
        assert error.time_point == 45.5
        assert error.solver_message == "Step size too small"
        
        # Check details
        assert error.details['simulation_type'] == "patient_simulation"
        assert error.details['time_point'] == 45.5
        assert error.details['solver_message'] == "Step size too small"
    
    def test_inheritance(self):
        """Test that SimulationError inherits from QSPModelError."""
        error = SimulationError("Test error")
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestDataError:
    """Test cases for DataError class."""
    
    def test_basic_initialization(self):
        """Test basic data error initialization."""
        error = DataError("Data loading failed")
        
        assert error.message == "Data loading failed"
        assert error.data_source is None
        assert error.data_type is None
        assert error.invalid_records is None
        assert error.error_code == "DATA_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with data attributes."""
        error = DataError(
            "Invalid time series data",
            data_source="patient_data.csv",
            data_type="time_series",
            invalid_records=5
        )
        
        assert error.data_source == "patient_data.csv"
        assert error.data_type == "time_series"
        assert error.invalid_records == 5
        
        # Check details
        assert error.details['data_source'] == "patient_data.csv"
        assert error.details['data_type'] == "time_series"
        assert error.details['invalid_records'] == 5
    
    def test_inheritance(self):
        """Test that DataError inherits from QSPModelError."""
        error = DataError("Test error")
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestValidationError:
    """Test cases for ValidationError class."""
    
    def test_basic_initialization(self):
        """Test basic validation error initialization."""
        error = ValidationError("Validation failed")
        
        assert error.message == "Validation failed"
        assert error.input_name is None
        assert error.input_value is None
        assert error.validation_rule is None
        assert error.error_code == "VALIDATION_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with validation attributes."""
        error = ValidationError(
            "Invalid parameter value",
            input_name="alpha",
            input_value=-0.1,
            validation_rule="positive_value"
        )
        
        assert error.input_name == "alpha"
        assert error.input_value == -0.1
        assert error.validation_rule == "positive_value"
        
        # Check details
        assert error.details['input_name'] == "alpha"
        assert error.details['input_value'] == -0.1
        assert error.details['validation_rule'] == "positive_value"
    
    def test_inheritance(self):
        """Test that ValidationError inherits from QSPModelError."""
        error = ValidationError("Test error")
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestConfigurationError:
    """Test cases for ConfigurationError class."""
    
    def test_basic_initialization(self):
        """Test basic configuration error initialization."""
        error = ConfigurationError("Configuration loading failed")
        
        assert error.message == "Configuration loading failed"
        assert error.config_file is None
        assert error.config_section is None
        assert error.missing_keys == []
        assert error.error_code == "CONFIG_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with configuration attributes."""
        error = ConfigurationError(
            "Missing required parameters",
            config_file="config.yaml",
            config_section="model_parameters",
            missing_keys=["alpha", "beta"]
        )
        
        assert error.config_file == "config.yaml"
        assert error.config_section == "model_parameters"
        assert error.missing_keys == ["alpha", "beta"]
        
        # Check details
        assert error.details['config_file'] == "config.yaml"
        assert error.details['config_section'] == "model_parameters"
        assert error.details['missing_keys'] == ["alpha", "beta"]
    
    def test_inheritance(self):
        """Test that ConfigurationError inherits from QSPModelError."""
        error = ConfigurationError("Test error")
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestFileOperationError:
    """Test cases for FileOperationError class."""
    
    def test_basic_initialization(self):
        """Test basic file operation error initialization."""
        error = FileOperationError("File operation failed")
        
        assert error.message == "File operation failed"
        assert error.file_path is None
        assert error.operation is None
        assert error.original_error is None
        assert error.error_code == "FILE_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with file operation attributes."""
        original_error = IOError("Permission denied")
        error = FileOperationError(
            "Cannot read file",
            file_path="/path/to/file.txt",
            operation="read",
            original_error=original_error
        )
        
        assert error.file_path == "/path/to/file.txt"
        assert error.operation == "read"
        assert error.original_error == original_error
        
        # Check details
        assert error.details['file_path'] == "/path/to/file.txt"
        assert error.details['operation'] == "read"
        assert error.details['original_error'] == "Permission denied"
    
    def test_inheritance(self):
        """Test that FileOperationError inherits from QSPModelError."""
        error = FileOperationError("Test error")
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestConvergenceError:
    """Test cases for ConvergenceError class."""
    
    def test_basic_initialization(self):
        """Test basic convergence error initialization."""
        error = ConvergenceError("Method failed to converge")
        
        assert error.message == "Method failed to converge"
        assert error.method is None
        assert error.max_iterations is None
        assert error.residual_norm is None
        assert error.simulation_type == "convergence"
        assert error.error_code == "CONVERGENCE_ERROR"
    
    def test_initialization_with_attributes(self):
        """Test initialization with convergence attributes."""
        error = ConvergenceError(
            "Newton method failed",
            method="newton",
            max_iterations=100,
            residual_norm=1e-3
        )
        
        assert error.method == "newton"
        assert error.max_iterations == 100
        assert error.residual_norm == 1e-3
        
        # Check details
        assert error.details['method'] == "newton"
        assert error.details['max_iterations'] == 100
        assert error.details['residual_norm'] == 1e-3
    
    def test_inheritance(self):
        """Test that ConvergenceError inherits from SimulationError."""
        error = ConvergenceError("Test error")
        assert isinstance(error, SimulationError)
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestNumericalInstabilityError:
    """Test cases for NumericalInstabilityError class."""
    
    def test_basic_initialization(self):
        """Test basic numerical instability error initialization."""
        error = NumericalInstabilityError("Numerical instability detected")
        
        assert error.message == "Numerical instability detected"
        assert error.variable_name is None
        assert error.value is None
        assert error.threshold is None
        assert error.simulation_type == "numerical_instability"
        assert error.error_code == "NUMERICAL_INSTABILITY"
    
    def test_initialization_with_attributes(self):
        """Test initialization with instability attributes."""
        error = NumericalInstabilityError(
            "TSH value exploded",
            variable_name="TSH",
            time_point=50.5,
            value=1e6,
            threshold=1000.0
        )
        
        assert error.variable_name == "TSH"
        assert error.time_point == 50.5
        assert error.value == 1e6
        assert error.threshold == 1000.0
        
        # Check details
        assert error.details['variable_name'] == "TSH"
        assert error.details['value'] == 1e6
        assert error.details['threshold'] == 1000.0
    
    def test_inheritance(self):
        """Test that NumericalInstabilityError inherits from SimulationError."""
        error = NumericalInstabilityError("Test error")
        assert isinstance(error, SimulationError)
        assert isinstance(error, QSPModelError)
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Test cases for exception hierarchy and relationships."""
    
    def test_all_exceptions_inherit_from_qsp_model_error(self):
        """Test that all custom exceptions inherit from QSPModelError."""
        exceptions = [
            ParameterError,
            SimulationError,
            DataError,
            ValidationError,
            ConfigurationError,
            FileOperationError,
            ConvergenceError,
            NumericalInstabilityError
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, QSPModelError)
    
    def test_specialized_exceptions_inherit_from_base_types(self):
        """Test that specialized exceptions inherit from correct base types."""
        assert issubclass(ConvergenceError, SimulationError)
        assert issubclass(NumericalInstabilityError, SimulationError)
    
    def test_exception_catching(self):
        """Test that exceptions can be caught correctly."""
        # Test catching base exception
        try:
            raise ParameterError("Test error")
        except QSPModelError as e:
            assert isinstance(e, ParameterError)
            assert str(e) == "Test error (Error Code: PARAM_ERROR)"
        
        # Test catching specific exception
        try:
            raise SimulationError("Test error")
        except SimulationError as e:
            assert isinstance(e, SimulationError)
            assert str(e) == "Test error (Error Code: SIM_ERROR)"
    
    def test_exception_chaining(self):
        """Test exception chaining functionality."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as original_error:
                raise ParameterError("Parameter error") from original_error
        except ParameterError as e:
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"


class TestExceptionSerialization:
    """Test cases for exception serialization and deserialization."""
    
    def test_all_exceptions_to_dict(self):
        """Test that all exceptions can be converted to dictionary."""
        exceptions = [
            QSPModelError("Test error"),
            ParameterError("Test error", parameter_name="alpha", parameter_value=0.5),
            SimulationError("Test error", simulation_type="test", time_point=10.0),
            DataError("Test error", data_source="test.csv", data_type="time_series"),
            ValidationError("Test error", input_name="alpha", validation_rule="positive"),
            ConfigurationError("Test error", config_file="config.yaml"),
            FileOperationError("Test error", file_path="test.txt", operation="read"),
            ConvergenceError("Test error", method="newton", max_iterations=100),
            NumericalInstabilityError("Test error", variable_name="TSH", value=1000.0)
        ]
        
        for exc in exceptions:
            error_dict = exc.to_dict()
            
            # Check required fields
            assert 'error_type' in error_dict
            assert 'message' in error_dict
            assert 'error_code' in error_dict
            assert 'details' in error_dict
            
            # Check that error_type matches class name
            assert error_dict['error_type'] == exc.__class__.__name__
            
            # Check that message matches
            assert error_dict['message'] == exc.message
            
            # Check that error_code matches
            assert error_dict['error_code'] == exc.error_code
    
    def test_exception_details_consistency(self):
        """Test that exception details are consistent with attributes."""
        # Test ParameterError
        param_error = ParameterError(
            "Invalid alpha",
            parameter_name="alpha",
            parameter_value=-0.1,
            expected_range="> 0"
        )
        
        assert param_error.details['parameter_name'] == param_error.parameter_name
        assert param_error.details['parameter_value'] == param_error.parameter_value
        assert param_error.details['expected_range'] == param_error.expected_range
        
        # Test SimulationError
        sim_error = SimulationError(
            "Solver failed",
            simulation_type="test",
            time_point=10.0,
            solver_message="Error message"
        )
        
        assert sim_error.details['simulation_type'] == sim_error.simulation_type
        assert sim_error.details['time_point'] == sim_error.time_point
        assert sim_error.details['solver_message'] == sim_error.solver_message
        
        # Test NumericalInstabilityError
        instab_error = NumericalInstabilityError(
            "Instability",
            variable_name="TSH",
            time_point=50.0,
            value=1000.0,
            threshold=100.0
        )
        
        assert instab_error.details['variable_name'] == instab_error.variable_name
        assert instab_error.details['value'] == instab_error.value
        assert instab_error.details['threshold'] == instab_error.threshold