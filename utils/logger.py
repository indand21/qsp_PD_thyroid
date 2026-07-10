"""
Comprehensive Logging Framework for QSP Thyroid Model

This module provides a centralized logging system with different log levels,
formatters, and output options for the QSP thyroid model.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, Union
from datetime import datetime
import json
import traceback

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}
_configured = False


def setup_logging(log_level: str = "INFO",
                 log_file: Optional[str] = None,
                 console_output: bool = True,
                 file_output: bool = True,
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 backup_count: int = 5,
                 log_format: Optional[str] = None,
                 json_format: bool = False,
                 component_logs: bool = True) -> None:
    """
    Set up the logging configuration for the QSP model.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Base name for log files (default: qsp_model.log)
        console_output: Whether to output to console
        file_output: Whether to output to file
        max_file_size: Maximum file size in bytes before rotation
        backup_count: Number of backup files to keep
        log_format: Custom log format string
        json_format: Whether to use JSON format for logs
        component_logs: Whether to create separate log files for components
    """
    global _configured
    
    if _configured:
        return
    
    # Set default log file
    if log_file is None:
        log_file = "qsp_model.log"
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Define default format
    if log_format is None:
        if json_format:
            log_format = None  # Will use JSON formatter
        else:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(log_format)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if file_output:
        main_log_file = log_dir / log_file
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create component-specific loggers if requested
    if component_logs and file_output:
        components = ["QSP_Model", "Simulation", "Validation", "Configuration", "Data"]
        for component in components:
            component_log_file = log_dir / f"{component.lower()}.log"
            component_handler = logging.handlers.RotatingFileHandler(
                component_log_file,
                maxBytes=max_file_size // 2,  # Smaller files for components
                backupCount=backup_count
            )
            component_handler.setLevel(numeric_level)
            component_handler.setFormatter(formatter)
            
            component_logger = logging.getLogger(component)
            component_logger.addHandler(component_handler)
            component_logger.setLevel(numeric_level)
            component_logger.propagate = False  # Don't propagate to root logger
    
    _configured = True
    
    # Log initialization
    logger = logging.getLogger("Logging")
    logger.info(f"Logging initialized with level: {log_level}")
    logger.info(f"Log file: {log_dir / log_file}")
    logger.info(f"Console output: {console_output}, File output: {file_output}")


def get_logger(name: str = "QSP_Model") -> logging.Logger:
    """
    Get a logger instance for a specific component.
    
    Args:
        name: Name of the component/logger
        
    Returns:
        Logger instance
    """
    global _loggers
    
    if name not in _loggers:
        # Ensure logging is configured
        if not _configured:
            setup_logging()
        
        _loggers[name] = logging.getLogger(name)
    
    return _loggers[name]


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'lineno', 
                          'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process',
                          'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class ContextLogger:
    """
    Logger that automatically adds context information to log messages.
    """
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        """
        Initialize context logger.
        
        Args:
            logger: Base logger instance
            context: Context information to add to all log messages
        """
        self.logger = logger
        self.context = context
    
    def _log_with_context(self, level: int, message: str, *args, **kwargs):
        """Log message with added context."""
        # Create a LogRecord with extra context
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        kwargs['extra'].update(self.context)
        
        self.logger.log(level, message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception message with context."""
        kwargs['exc_info'] = True
        self._log_with_context(logging.ERROR, message, *args, **kwargs)


def get_context_logger(name: str = "QSP_Model", 
                      context: Optional[Dict[str, Any]] = None) -> ContextLogger:
    """
    Get a context logger for a specific component.
    
    Args:
        name: Name of the component/logger
        context: Context information to add to all log messages
        
    Returns:
        ContextLogger instance
    """
    logger = get_logger(name)
    context = context or {}
    return ContextLogger(logger, context)


def log_function_entry(logger: logging.Logger, func_name: str, 
                      args: tuple = (), kwargs: dict = None):
    """
    Log function entry with arguments.
    
    Args:
        logger: Logger instance
        func_name: Name of the function
        args: Function arguments
        kwargs: Function keyword arguments
    """
    kwargs = kwargs or {}
    
    # Create safe argument representations (limit length)
    safe_args = [str(arg)[:100] for arg in args]
    safe_kwargs = {k: str(v)[:100] for k, v in kwargs.items()}
    
    logger.debug(f"Entering {func_name} with args={safe_args}, kwargs={safe_kwargs}")


def log_function_exit(logger: logging.Logger, func_name: str, 
                     result: Any = None, execution_time: Optional[float] = None):
    """
    Log function exit with result and execution time.
    
    Args:
        logger: Logger instance
        func_name: Name of the function
        result: Function result
        execution_time: Execution time in seconds
    """
    safe_result = str(result)[:100] if result is not None else None
    time_str = f" ({execution_time:.3f}s)" if execution_time is not None else ""
    
    logger.debug(f"Exiting {func_name} with result={safe_result}{time_str}")


def log_simulation_start(logger: logging.Logger, patient_id: str, 
                        drug_type: str, simulation_time: float):
    """
    Log the start of a simulation.
    
    Args:
        logger: Logger instance
        patient_id: Patient identifier
        drug_type: Type of drug being simulated
        simulation_time: Simulation time horizon
    """
    logger.info(f"Starting simulation for patient {patient_id} "
               f"with {drug_type} (time horizon: {simulation_time} days)")


def log_simulation_complete(logger: logging.Logger, patient_id: str,
                           success: bool, error_message: Optional[str] = None,
                           execution_time: Optional[float] = None):
    """
    Log the completion of a simulation.
    
    Args:
        logger: Logger instance
        patient_id: Patient identifier
        success: Whether simulation was successful
        error_message: Error message if simulation failed
        execution_time: Execution time in seconds
    """
    if success:
        time_str = f" ({execution_time:.3f}s)" if execution_time is not None else ""
        logger.info(f"Simulation completed successfully for patient {patient_id}{time_str}")
    else:
        logger.error(f"Simulation failed for patient {patient_id}: {error_message}")


def log_validation_error(logger: logging.Logger, error_type: str,
                        input_name: str, input_value: Any, 
                        validation_rule: str):
    """
    Log a validation error.
    
    Args:
        logger: Logger instance
        error_type: Type of validation error
        input_name: Name of the invalid input
        input_value: The invalid value
        validation_rule: Rule that was violated
    """
    logger.warning(f"Validation failed for {input_name}: {error_type} "
                  f"(value: {input_value}, rule: {validation_rule})")


def log_parameter_update(logger: logging.Logger, parameter_name: str,
                        old_value: Any, new_value: Any):
    """
    Log a parameter update.
    
    Args:
        logger: Logger instance
        parameter_name: Name of the parameter
        old_value: Previous parameter value
        new_value: New parameter value
    """
    logger.info(f"Parameter updated: {parameter_name} changed from {old_value} to {new_value}")


def log_data_load(logger: logging.Logger, data_source: str, 
                 record_count: int, success: bool,
                 error_message: Optional[str] = None):
    """
    Log data loading operation.
    
    Args:
        logger: Logger instance
        data_source: Source of the data
        record_count: Number of records loaded
        success: Whether loading was successful
        error_message: Error message if loading failed
    """
    if success:
        logger.info(f"Successfully loaded {record_count} records from {data_source}")
    else:
        logger.error(f"Failed to load data from {data_source}: {error_message}")


def create_performance_logger(logger: logging.Logger) -> callable:
    """
    Create a performance logging decorator.
    
    Args:
        logger: Logger instance to use for performance logging
        
    Returns:
        Decorator function
    """
    def performance_logger(func):
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                
                if success:
                    logger.info(f"Performance: {func.__name__} completed in {execution_time:.3f}s")
                else:
                    logger.error(f"Performance: {func.__name__} failed after {execution_time:.3f}s: {error}")
            
            return result
        return wrapper
    return performance_logger


def get_log_statistics() -> Dict[str, Any]:
    """
    Get statistics about log files.
    
    Returns:
        Dictionary with log file statistics
    """
    log_dir = Path("logs")
    
    if not log_dir.exists():
        return {'total_files': 0, 'total_size': 0, 'files': []}
    
    files = []
    total_size = 0
    
    for log_file in log_dir.glob("*.log*"):
        try:
            file_size = log_file.stat().st_size
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            
            files.append({
                'name': log_file.name,
                'size': file_size,
                'modified': file_mtime.isoformat()
            })
            
            total_size += file_size
        except OSError:
            continue
    
    return {
        'total_files': len(files),
        'total_size': total_size,
        'files': sorted(files, key=lambda x: x['name'])
    }


def cleanup_old_logs(days_to_keep: int = 30) -> int:
    """
    Clean up old log files.
    
    Args:
        days_to_keep: Number of days to keep log files
        
    Returns:
        Number of files deleted
    """
    log_dir = Path("logs")
    
    if not log_dir.exists():
        return 0
    
    cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
    deleted_count = 0
    
    for log_file in log_dir.glob("*.log*"):
        try:
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                deleted_count += 1
        except OSError:
            continue
    
    logger = get_logger("Logging")
    logger.info(f"Cleaned up {deleted_count} old log files (older than {days_to_keep} days)")
    
    return deleted_count