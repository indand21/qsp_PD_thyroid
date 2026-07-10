"""
QSP_PD_Thyroid Utility Package

This package provides error handling, input validation, logging, and recovery utilities
for the QSP thyroid model.
"""

from .exceptions import (
    QSPModelError,
    ParameterError,
    SimulationError,
    DataError,
    ValidationError,
    NumericalInstabilityError,
    FileOperationError
)

from .error_handler import ErrorHandler, handle_errors, create_error_report
from .validators import (
    validate_positive_number,
    validate_probability,
    validate_time_series,
    validate_parameter_range,
    validate_array_dimensions,
    validate_array_type,
    validate_drug_type,
    validate_patient_id,
    validate_file_path
)
from .decorators import (
    validate_inputs,
    validate_outputs,
    retry_on_failure
)
from .logger import (
    get_logger, setup_logging, get_context_logger,
    log_function_entry, log_function_exit, log_simulation_start,
    log_simulation_complete, log_validation_error, log_parameter_update,
    log_data_load, create_performance_logger, get_log_statistics,
    cleanup_old_logs
)
from .recovery import (
    RecoveryStrategy, ParameterAdjustmentStrategy, FallbackMethodStrategy,
    DataRepairStrategy, ErrorRecoveryManager, recover_from_error,
    can_recover_from_error, recovery_manager
)

__all__ = [
    # Exceptions
    'QSPModelError',
    'ParameterError',
    'SimulationError',
    'DataError',
    'ValidationError',
    'NumericalInstabilityError',
    'FileOperationError',
    
    # Error handling
    'ErrorHandler',
    'handle_errors',
    'create_error_report',
    
    # Validators
    'validate_positive_number',
    'validate_probability',
    'validate_time_series',
    'validate_parameter_range',
    'validate_array_dimensions',
    'validate_array_type',
    'validate_drug_type',
    'validate_patient_id',
    'validate_file_path',
    
    # Decorators
    'validate_inputs',
    'validate_outputs',
    'retry_on_failure',
    
    # Logging
    'get_logger',
    'setup_logging',
    'get_context_logger',
    'log_function_entry',
    'log_function_exit',
    'log_simulation_start',
    'log_simulation_complete',
    'log_validation_error',
    'log_parameter_update',
    'log_data_load',
    'create_performance_logger',
    'get_log_statistics',
    'cleanup_old_logs',
    
    # Recovery
    'RecoveryStrategy',
    'ParameterAdjustmentStrategy',
    'FallbackMethodStrategy',
    'DataRepairStrategy',
    'ErrorRecoveryManager',
    'recover_from_error',
    'can_recover_from_error',
    'recovery_manager'
]

__version__ = '1.1.0'