"""
Unit tests for error handler utilities.

This module tests the ErrorHandler class and related error handling functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from utils.exceptions import (
    QSPModelError,
    ParameterError,
    SimulationError,
    ValidationError
)
from utils.error_handler import (
    ErrorHandler,
    get_global_error_handler,
    handle_errors,
    error_context,
    safe_execute,
    format_error_message,
    create_error_report
)


class TestErrorHandler:
    """Test cases for ErrorHandler class."""
    
    def test_initialization(self):
        """Test ErrorHandler initialization."""
        handler = ErrorHandler("TestComponent")
        
        assert handler.component_name == "TestComponent"
        assert handler.logger is not None
        assert handler.error_counts == {}
        assert handler.error_history == []
    
    def test_handle_qsp_model_error(self):
        """Test handling QSP model errors."""
        handler = ErrorHandler("TestComponent")
        
        error = ParameterError("Invalid alpha value", parameter_name="alpha", parameter_value=-0.1)
        context = {"function": "test_function", "line": 10}
        
        # Test with reraise=True (default)
        with pytest.raises(ParameterError):
            handler.handle_error(error, context, reraise=True)
        
        # Check that error was recorded
        assert len(handler.error_history) == 1
        assert "ParameterError" in handler.error_counts
        assert handler.error_counts["ParameterError"] == 1
        
        error_record = handler.error_history[0]
        assert error_record['error_type'] == "ParameterError"
        assert error_record['error_message'] == "Invalid alpha value"
        assert error_record['component'] == "TestComponent"
        assert error_record['context'] == context
    
    def test_handle_standard_error(self):
        """Test handling standard Python errors."""
        handler = ErrorHandler("TestComponent")
        
        error = ValueError("Standard error")
        context = {"function": "test_function"}
        
        # Test with reraise=False
        error_record = handler.handle_error(error, context, reraise=False)
        
        assert error_record is not None
        assert error_record['error_type'] == "ValueError"
        assert error_record['error_message'] == "Standard error"
        assert error_record['component'] == "TestComponent"
        
        # Check that error was recorded
        assert len(handler.error_history) == 1
        assert "ValueError" in handler.error_counts
    
    def test_multiple_error_handling(self):
        """Test handling multiple errors."""
        handler = ErrorHandler("TestComponent")
        
        errors = [
            ParameterError("Error 1"),
            SimulationError("Error 2"),
            ValidationError("Error 3"),
            ParameterError("Error 4")  # Duplicate type
        ]
        
        for error in errors:
            handler.handle_error(error, reraise=False)
        
        # Check error counts
        assert handler.error_counts["ParameterError"] == 2
        assert handler.error_counts["SimulationError"] == 1
        assert handler.error_counts["ValidationError"] == 1
        
        # Check error history
        assert len(handler.error_history) == 4
        
        # Check total errors
        summary = handler.get_error_summary()
        assert summary['total_errors'] == 4
    
    def test_get_error_summary(self):
        """Test error summary generation."""
        handler = ErrorHandler("TestComponent")
        
        # Add some errors
        handler.handle_error(ParameterError("Error 1"), reraise=False)
        handler.handle_error(SimulationError("Error 2"), reraise=False)
        handler.handle_error(ParameterError("Error 3"), reraise=False)
        
        summary = handler.get_error_summary()
        
        assert summary['component'] == "TestComponent"
        assert summary['total_errors'] == 3
        assert summary['error_counts']['ParameterError'] == 2
        assert summary['error_counts']['SimulationError'] == 1
        assert len(summary['recent_errors']) == 3
        
        # Check recent errors
        recent_errors = summary['recent_errors']
        assert recent_errors[0]['error_type'] == "ParameterError"
        assert recent_errors[1]['error_type'] == "SimulationError"
        assert recent_errors[2]['error_type'] == "ParameterError"
    
    def test_clear_error_history(self):
        """Test clearing error history."""
        handler = ErrorHandler("TestComponent")
        
        # Add some errors
        handler.handle_error(ParameterError("Error 1"), reraise=False)
        handler.handle_error(SimulationError("Error 2"), reraise=False)
        
        assert len(handler.error_history) == 2
        assert len(handler.error_counts) == 2
        
        # Clear history
        handler.clear_error_history()
        
        assert len(handler.error_history) == 0
        assert len(handler.error_counts) == 0
    
    @patch('utils.error_handler.get_logger')
    def test_error_logging(self, mock_get_logger):
        """Test that errors are logged correctly."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        handler = ErrorHandler("TestComponent")
        
        # Test QSP model error
        qsp_error = ParameterError("Test error", parameter_name="alpha")
        handler.handle_error(qsp_error, reraise=False)
        
        mock_logger.error.assert_called()
        error_call_args = mock_logger.error.call_args[0][0]
        assert "QSP Model Error" in error_call_args
        assert "TestComponent" in error_call_args
        
        # Test standard error
        mock_logger.reset_mock()
        standard_error = ValueError("Standard error")
        handler.handle_error(standard_error, reraise=False)
        
        mock_logger.error.assert_called()
        error_call_args = mock_logger.error.call_args[0][0]
        assert "Unexpected error" in error_call_args
        assert "TestComponent" in error_call_args


class TestGlobalErrorHandler:
    """Test cases for global error handler functions."""
    
    def test_get_global_error_handler(self):
        """Test getting global error handler."""
        handler1 = get_global_error_handler()
        handler2 = get_global_error_handler()
        
        # Should return the same instance
        assert handler1 is handler2
        assert handler1.component_name == "Global"
    
    def test_global_error_handler_state(self):
        """Test that global error handler maintains state."""
        handler = get_global_error_handler()
        
        # Clear any existing state
        handler.clear_error_history()
        
        # Add an error
        handler.handle_error(ValueError("Test error"), reraise=False)
        
        # Get handler again and check state
        handler2 = get_global_error_handler()
        summary = handler2.get_error_summary()
        
        assert summary['total_errors'] == 1


class TestHandleErrorsDecorator:
    """Test cases for handle_errors decorator."""
    
    def test_successful_execution(self):
        """Test decorator with successful function execution."""
        @handle_errors()
        def test_function(x, y):
            return x + y
        
        result = test_function(2, 3)
        assert result == 5
    
    def test_error_handling_with_reraise(self):
        """Test decorator with reraise=True (default)."""
        @handle_errors(reraise=True)
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_function()
    
    def test_error_handling_without_reraise(self):
        """Test decorator with reraise=False."""
        @handle_errors(reraise=False, fallback_value="fallback")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result == "fallback"
    
    def test_error_with_specific_types(self):
        """Test decorator with specific error types."""
        @handle_errors(error_types=[ValueError], reraise=False, fallback_value="caught")
        def test_function():
            raise ValueError("Test error")
        
        result = test_function()
        assert result == "caught"
    
    def test_error_type_not_caught(self):
        """Test decorator when error type is not in catch list."""
        @handle_errors(error_types=[ValueError], reraise=True)  # Default
        def test_function():
            raise TypeError("Test error")
        
        with pytest.raises(TypeError, match="Test error"):
            test_function()
    
    def test_context_logging(self):
        """Test that context is logged with errors."""
        @handle_errors(reraise=False, fallback_value=None)
        def test_function(x, y):
            raise ValueError(f"Error with {x}, {y}")
        
        with patch('utils.error_handler.get_global_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_get_handler.return_value = mock_handler
            
            test_function(1, 2)
            
            # Check that handle_error was called with context
            mock_handler.handle_error.assert_called_once()
            call_args = mock_handler.handle_error.call_args
            context = call_args[0][1]  # Second argument (context)
            
            assert context['function'] == 'test_function'
            assert '1' in context['args']
            assert '2' in context['args']
    
    def test_custom_context(self):
        """Test decorator with custom context."""
        custom_context = {"component": "test", "operation": "validation"}
        
        @handle_errors(reraise=False, fallback_value=None, context=custom_context)
        def test_function():
            raise ValueError("Test error")
        
        with patch('utils.error_handler.get_global_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_get_handler.return_value = mock_handler
            
            test_function()
            
            # Check that custom context was included
            call_args = mock_handler.handle_error.call_args
            context = call_args[0][1]
            
            assert context['component'] == "test"
            assert context['operation'] == "validation"


class TestErrorContext:
    """Test cases for error_context context manager."""
    
    def test_successful_context(self):
        """Test context manager with successful execution."""
        context = {"operation": "test_operation"}
        
        with error_context(context):
            result = 2 + 2
            assert result == 4
    
    def test_error_context_with_reraise(self):
        """Test context manager with reraise=True."""
        context = {"operation": "test_operation"}
        
        with pytest.raises(ValueError, match="Test error"):
            with error_context(context, reraise=True):
                raise ValueError("Test error")
    
    def test_error_context_without_reraise(self):
        """Test context manager with reraise=False."""
        context = {"operation": "test_operation"}
        
        # Should not raise exception
        with error_context(context, reraise=False):
            raise ValueError("Test error")
    
    def test_error_context_with_error_types(self):
        """Test context manager with specific error types."""
        context = {"operation": "test_operation"}
        
        # Should catch ValueError but not TypeError
        with error_context(context, error_types=[ValueError], reraise=False):
            raise ValueError("Test error")
        
        # Should raise TypeError
        with pytest.raises(TypeError):
            with error_context(context, error_types=[ValueError], reraise=True):
                raise TypeError("Test error")
    
    @patch('utils.error_handler.get_global_error_handler')
    def test_error_context_logging(self, mock_get_handler):
        """Test that context manager logs errors correctly."""
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler
        
        context = {"operation": "test_operation"}
        
        with error_context(context, reraise=False):
            raise ValueError("Test error")
        
        # Check that handle_error was called
        mock_handler.handle_error.assert_called_once()
        call_args = mock_handler.handle_error.call_args
        
        # Check that context was passed
        passed_context = call_args[0][1]
        assert passed_context == context


class TestSafeExecute:
    """Test cases for safe_execute function."""
    
    def test_successful_execution(self):
        """Test safe_execute with successful function."""
        def test_func(x, y):
            return x * y
        
        result = safe_execute(test_func, 3, 4)
        assert result == 12
    
    def test_error_handling(self):
        """Test safe_execute with error."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(test_func, fallback_value="fallback")
        assert result == "fallback"
    
    def test_error_with_types(self):
        """Test safe_execute with specific error types."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(
            test_func, 
            error_types=[ValueError], 
            fallback_value="caught"
        )
        assert result == "caught"
    
    def test_error_type_not_caught(self):
        """Test safe_execute when error type is not in catch list."""
        def test_func():
            raise TypeError("Test error")
        
        with pytest.raises(TypeError, match="Test error"):
            safe_execute(test_func, error_types=[ValueError])
    
    def test_with_context(self):
        """Test safe_execute with context."""
        def test_func():
            raise ValueError("Test error")
        
        context = {"operation": "test"}
        
        with patch('utils.error_handler.get_global_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_get_handler.return_value = mock_handler
            
            safe_execute(test_func, context=context, fallback_value=None)
            
            # Check that context was passed
            call_args = mock_handler.handle_error.call_args
            passed_context = call_args[0][1]
            assert passed_context['operation'] == "test"


class TestFormatErrorMessage:
    """Test cases for format_error_message function."""
    
    def test_format_standard_error(self):
        """Test formatting standard Python error."""
        error = ValueError("Test error message")
        
        formatted = format_error_message(error)
        
        assert "ValueError: Test error message" in formatted
        assert "Traceback:" not in formatted
    
    def test_format_qsp_model_error(self):
        """Test formatting QSP model error."""
        error = ParameterError(
            "Invalid parameter",
            parameter_name="alpha",
            parameter_value=-0.1
        )
        
        formatted = format_error_message(error)
        
        assert "ParameterError: Invalid parameter" in formatted
        assert "Code: PARAM_ERROR" in formatted
        assert "Details:" in formatted
        assert "parameter_name: alpha" in formatted
        assert "parameter_value: -0.1" in formatted
    
    def test_format_with_traceback(self):
        """Test formatting error with traceback."""
        error = ValueError("Test error")
        
        formatted = format_error_message(error, include_traceback=True)
        
        assert "ValueError: Test error" in formatted
        assert "Traceback:" in formatted
    
    def test_format_error_without_details(self):
        """Test formatting QSP error without details."""
        error = QSPModelError("Simple error")
        
        formatted = format_error_message(error)
        
        assert "QSPModelError: Simple error" in formatted
        assert "Code: QSP_ERROR" in formatted
        assert "Details:" not in formatted


class TestCreateErrorReport:
    """Test cases for create_error_report function."""
    
    def test_create_empty_report(self):
        """Test creating report with no errors."""
        with patch('utils.error_handler.get_global_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.get_error_summary.return_value = {
                'component': 'TestComponent',
                'total_errors': 0,
                'error_counts': {},
                'recent_errors': []
            }
            mock_get_handler.return_value = mock_handler
            
            report = create_error_report()
            
            assert "Error Report for TestComponent" in report
            assert "Total Errors: 0" in report
            assert "Error Counts by Type:" not in report
            assert "Recent Errors:" not in report
    
    def test_create_report_with_errors(self):
        """Test creating report with errors."""
        with patch('utils.error_handler.get_global_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.get_error_summary.return_value = {
                'component': 'TestComponent',
                'total_errors': 3,
                'error_counts': {
                    'ParameterError': 2,
                    'SimulationError': 1
                },
                'recent_errors': [
                    {
                        'error_type': 'ParameterError',
                        'error_message': 'Invalid alpha',
                        'context': {'function': 'test_func'}
                    },
                    {
                        'error_type': 'SimulationError',
                        'error_message': 'Solver failed',
                        'context': None
                    }
                ]
            }
            mock_get_handler.return_value = mock_handler
            
            report = create_error_report()
            
            assert "Error Report for TestComponent" in report
            assert "Total Errors: 3" in report
            assert "Error Counts by Type:" in report
            assert "ParameterError: 2" in report
            assert "SimulationError: 1" in report
            assert "Recent Errors:" in report
            assert "1. ParameterError: Invalid alpha" in report
            assert "2. SimulationError: Solver failed" in report
    
    def test_create_report_for_component(self):
        """Test creating report for specific component."""
        with patch('utils.error_handler.get_global_error_handler') as mock_get_handler:
            mock_handler = Mock()
            mock_handler.component_name = "TestComponent"
            mock_handler.get_error_summary.return_value = {
                'component': 'TestComponent',
                'total_errors': 1,
                'error_counts': {'ValueError': 1},
                'recent_errors': []
            }
            mock_get_handler.return_value = mock_handler
            
            # Should still work (implementation falls back to global handler)
            report = create_error_report("DifferentComponent")
            
            assert "Error Report for TestComponent" in report


class TestErrorIntegration:
    """Test cases for error handling integration."""
    
    def test_decorator_and_context_manager_interaction(self):
        """Test interaction between decorator and context manager."""
        handler = ErrorHandler("TestComponent")
        
        @handle_errors(reraise=False)
        def test_function():
            with error_context({"operation": "nested"}):
                raise ValueError("Nested error")
        
        result = test_function()
        assert result is None
        
        # Check that error was recorded
        summary = handler.get_error_summary()
        assert summary['total_errors'] >= 1
    
    def test_error_recovery_workflow(self):
        """Test complete error recovery workflow."""
        handler = ErrorHandler("TestComponent")
        handler.clear_error_history()
        
        # Function that might fail
        @handle_errors(reraise=False, fallback_value=None)
        def risky_operation(should_fail):
            if should_fail:
                raise ParameterError("Operation failed", parameter_name="alpha")
            return "success"
        
        # First call fails
        result1 = risky_operation(True)
        assert result1 is None
        
        # Second call succeeds
        result2 = risky_operation(False)
        assert result2 == "success"
        
        # Check error summary
        summary = handler.get_error_summary()
        assert summary['total_errors'] == 1
        assert summary['error_counts']['ParameterError'] == 1
    
    def test_nested_error_handling(self):
        """Test nested error handling scenarios."""
        handler = ErrorHandler("TestComponent")
        handler.clear_error_history()
        
        @handle_errors(reraise=False, fallback_value="outer_fallback")
        def outer_function():
            @handle_errors(reraise=False, fallback_value="inner_fallback")
            def inner_function():
                raise ValueError("Inner error")
            
            return inner_function()
        
        result = outer_function()
        assert result == "inner_fallback"
        
        # Both errors should be recorded
        summary = handler.get_error_summary()
        assert summary['total_errors'] == 2