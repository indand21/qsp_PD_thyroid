"""
Error Handling Utilities for QSP Thyroid Model

This module provides utilities for handling errors in a consistent way
throughout the QSP thyroid model.
"""

import traceback
import sys
from typing import Callable, Any, Optional, Dict, List, Union
from functools import wraps
from contextlib import contextmanager

from .exceptions import QSPModelError
from .logger import get_logger


class ErrorHandler:
    """
    Centralized error handler for the QSP model.
    
    Provides methods for consistent error handling, logging, and recovery.
    """
    
    def __init__(self, component_name: str = "QSP_Model"):
        """
        Initialize error handler.
        
        Args:
            component_name: Name of the component for logging
        """
        self.component_name = component_name
        self.logger = get_logger(component_name)
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None,
                    reraise: bool = True) -> Optional[Dict[str, Any]]:
        """
        Handle an error in a consistent way.
        
        Args:
            error: The exception to handle
            context: Additional context information
            reraise: Whether to reraise the exception
            
        Returns:
            Error information dictionary if reraise=False
        """
        context = context or {}
        error_type = type(error).__name__
        error_message = str(error)
        
        # Count errors by type
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Create error record
        error_record = {
            'error_type': error_type,
            'error_message': error_message,
            'component': self.component_name,
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        # Add to history
        self.error_history.append(error_record)
        
        # Log the error
        if isinstance(error, QSPModelError):
            self.logger.error(f"QSP Model Error in {self.component_name}: {error}")
            if error.details:
                self.logger.debug(f"Error details: {error.details}")
        else:
            self.logger.error(f"Unexpected error in {self.component_name}: {error}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Add context to log
        if context:
            self.logger.debug(f"Error context: {context}")
        
        # Reraise if requested
        if reraise:
            raise error
        
        return error_record
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all errors encountered.
        
        Returns:
            Dictionary with error statistics
        """
        return {
            'component': self.component_name,
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'recent_errors': self.error_history[-10:] if self.error_history else []
        }
    
    def clear_error_history(self):
        """Clear error history and counts."""
        self.error_counts.clear()
        self.error_history.clear()
        self.logger.info(f"Error history cleared for {self.component_name}")


# Global error handler instance
_global_error_handler = None


def get_global_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler("Global")
    return _global_error_handler


def handle_errors(error_types: Optional[List[type]] = None,
                 fallback_value: Any = None,
                 log_errors: bool = True,
                 reraise: bool = True,
                 context: Optional[Dict[str, Any]] = None):
    """
    Decorator for handling errors in functions.
    
    Args:
        error_types: List of exception types to catch (None for all)
        fallback_value: Value to return if error occurs and reraise=False
        log_errors: Whether to log errors
        reraise: Whether to reraise exceptions
        context: Additional context for error reporting
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_global_error_handler()
            
            # Prepare context
            func_context = {
                'function': func.__name__,
                'module': func.__module__,
                'args': str(args)[:200],  # Limit length
                'kwargs': str(kwargs)[:200]  # Limit length
            }
            if context:
                func_context.update(context)
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we should handle this error type
                if error_types is not None and not any(isinstance(e, et) for et in error_types):
                    raise
                
                # Handle the error
                error_record = handler.handle_error(e, func_context, reraise=False)
                
                if log_errors:
                    handler.logger.error(f"Error in {func.__name__}: {e}")
                
                if reraise:
                    raise
                
                return fallback_value
        
        return wrapper
    return decorator


@contextmanager
def error_context(context: Dict[str, Any], 
                 error_types: Optional[List[type]] = None,
                 reraise: bool = True):
    """
    Context manager for error handling.
    
    Args:
        context: Context information for error reporting
        error_types: List of exception types to catch
        reraise: Whether to reraise exceptions
    """
    handler = get_global_error_handler()
    
    try:
        yield
    except Exception as e:
        # Check if we should handle this error type
        if error_types is not None and not any(isinstance(e, et) for et in error_types):
            raise
        
        # Handle the error
        handler.handle_error(e, context, reraise)
        
        if not reraise:
            return  # Suppress the error


def safe_execute(func: Callable, *args, 
                fallback_value: Any = None,
                error_types: Optional[List[type]] = None,
                context: Optional[Dict[str, Any]] = None,
                **kwargs) -> Any:
    """
    Safely execute a function with error handling.
    
    Args:
        func: Function to execute
        *args: Function arguments
        fallback_value: Value to return if error occurs
        error_types: List of exception types to catch
        context: Additional context for error reporting
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or fallback value
    """
    handler = get_global_error_handler()
    
    # Prepare context
    func_context = {
        'function': func.__name__ if hasattr(func, '__name__') else str(func),
        'module': func.__module__ if hasattr(func, '__module__') else 'unknown',
        'args': str(args)[:200],
        'kwargs': str(kwargs)[:200]
    }
    if context:
        func_context.update(context)
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # Check if we should handle this error type
        if error_types is not None and not any(isinstance(e, et) for et in error_types):
            raise
        
        # Handle the error
        handler.handle_error(e, func_context, reraise=False)
        return fallback_value


def format_error_message(error: Exception, include_traceback: bool = False) -> str:
    """
    Format an error message for display.
    
    Args:
        error: Exception to format
        include_traceback: Whether to include traceback
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if isinstance(error, QSPModelError):
        formatted = f"{error_type}: {error_msg}"
        if error.error_code:
            formatted += f" (Code: {error.error_code})"
        if error.details:
            details_str = ", ".join(f"{k}: {v}" for k, v in error.details.items())
            formatted += f" | Details: {details_str}"
    else:
        formatted = f"{error_type}: {error_msg}"
    
    if include_traceback:
        formatted += f"\nTraceback:\n{traceback.format_exc()}"
    
    return formatted


def create_error_report(component_name: Optional[str] = None) -> str:
    """
    Create a comprehensive error report.
    
    Args:
        component_name: Component to report on (None for all)
        
    Returns:
        Formatted error report
    """
    handler = get_global_error_handler()
    
    if component_name and component_name != handler.component_name:
        # For now, just return global handler report
        # In a more complex implementation, we could maintain multiple handlers
        pass
    
    summary = handler.get_error_summary()
    
    report = f"Error Report for {summary['component']}\n"
    report += "=" * 50 + "\n"
    report += f"Total Errors: {summary['total_errors']}\n\n"
    
    if summary['error_counts']:
        report += "Error Counts by Type:\n"
        for error_type, count in summary['error_counts'].items():
            report += f"  {error_type}: {count}\n"
        report += "\n"
    
    if summary['recent_errors']:
        report += "Recent Errors (last 10):\n"
        for i, error in enumerate(summary['recent_errors'], 1):
            report += f"  {i}. {error['error_type']}: {error['error_message']}\n"
            if error['context']:
                report += f"     Context: {error['context']}\n"
        report += "\n"
    
    return report