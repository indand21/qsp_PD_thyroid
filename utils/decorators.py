"""
Decorators for Input Validation and Error Handling

This module provides decorators for automatic input validation,
output validation, and retry mechanisms.
"""

import time
import functools
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from inspect import signature, Parameter

from .validators import (
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
from .exceptions import ValidationError, SimulationError
from .logger import get_logger


def validate_inputs(**validators):
    """
    Decorator for validating function inputs.
    
    Args:
        **validators: Mapping of parameter names to validator functions
        
    Example:
        @validate_inputs(
            concentration=validate_positive_number,
            drug_type=validate_drug_type,
            time_span=lambda x: validate_parameter_range(x, "time_span", min_value=0)
        )
        def simulate(concentration, drug_type, time_span):
            pass
    """
    def decorator(func: Callable) -> Callable:
        sig = signature(func)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Bind arguments to function signature
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each parameter that has a validator
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    
                    # Handle special case where validator is a tuple (validator, args, kwargs)
                    if isinstance(validator, tuple) and len(validator) == 3:
                        validator_func, validator_args, validator_kwargs = validator
                        validated_value = validator_func(value, *validator_args, **validator_kwargs)
                    else:
                        validated_value = validator(value)
                    
                    # Update the bound arguments with validated value
                    bound_args.arguments[param_name] = validated_value
            
            # Call the function with validated arguments
            return func(**bound_args.arguments)
        
        return wrapper
    return decorator


def validate_outputs(**validators):
    """
    Decorator for validating function outputs.
    
    Args:
        **validators: Mapping of output indices/names to validator functions
        
    Example:
        @validate_outputs(
            result=validate_array_dimensions,
            time_points=lambda x: validate_parameter_range(x, "time_points", min_value=0)
        )
        def simulate():
            return result, time_points
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Call the function
            result = func(*args, **kwargs)
            
            # Handle different return types
            if isinstance(result, tuple):
                # Multiple return values
                validated_results = []
                for i, value in enumerate(result):
                    validator_key = str(i) if str(i) in validators else i
                    if validator_key in validators:
                        validator = validators[validator_key]
                        if isinstance(validator, tuple) and len(validator) == 3:
                            validator_func, validator_args, validator_kwargs = validator
                            validated_value = validator_func(value, *validator_args, **validator_kwargs)
                        else:
                            validated_value = validator(value)
                        validated_results.append(validated_value)
                    else:
                        validated_results.append(value)
                return tuple(validated_results)
            else:
                # Single return value
                if 'result' in validators:
                    validator = validators['result']
                    if isinstance(validator, tuple) and len(validator) == 3:
                        validator_func, validator_args, validator_kwargs = validator
                        return validator_func(result, *validator_args, **validator_kwargs)
                    else:
                        return validator(result)
                return result
        
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3,
                    delay: float = 1.0,
                    backoff_factor: float = 2.0,
                    exceptions: Tuple = (Exception,),
                    on_retry: Optional[Callable] = None):
    """
    Decorator for retrying functions on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each attempt
        exceptions: Tuple of exception types to catch and retry on
        on_retry: Optional callback function called on each retry
        
    Example:
        @retry_on_failure(max_attempts=3, delay=0.5, exceptions=(SimulationError,))
        def unstable_simulation():
            pass
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed, raise the exception
                        logger.error(f"Function {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}")
                    logger.info(f"Retrying in {current_delay:.1f} seconds...")
                    
                    # Call retry callback if provided
                    if on_retry is not None:
                        try:
                            on_retry(attempt + 1, e, *args, **kwargs)
                        except Exception as callback_error:
                            logger.error(f"Retry callback failed: {callback_error}")
                    
                    # Wait before retry
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def validate_model_parameters(func: Callable) -> Callable:
    """
    Specialized decorator for validating QSP model parameters.
    
    This decorator automatically validates common model parameters
    based on their names and expected types.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get function signature
        sig = signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        
        # Define parameter validators based on common patterns
        param_validators = {
            # Patient parameters
            'patient_id': validate_patient_id,
            'damage_susceptibility': lambda x: validate_parameter_range(x, "damage_susceptibility", 0.5, 2.0),
            
            # Drug parameters
            'drug_type': validate_drug_type,
            'drug_concentration': validate_positive_number,
            'dose': validate_positive_number,
            
            # Time parameters
            'time': validate_positive_number,
            'time_span': lambda x: validate_parameter_range(x, "time_span", min_value=0),
            't_span': lambda x: validate_parameter_range(x, "t_span", min_value=0),
            't_eval': validate_time_series,
            
            # Biological parameters
            'probability': validate_probability,
            'rate': validate_positive_number,
            'threshold': validate_positive_number,
            
            # Array parameters
            'initial_conditions': validate_array_dimensions,
            'parameters': validate_array_type,
            
            # File parameters
            'file_path': validate_file_path,
            'config_file': lambda x: validate_file_path(x, must_exist=True),
        }
        
        # Validate parameters
        for param_name, value in bound_args.arguments.items():
            # Check for exact match
            if param_name in param_validators:
                validator = param_validators[param_name]
                try:
                    validated_value = validator(value)
                    bound_args.arguments[param_name] = validated_value
                except ValidationError as e:
                    # Re-raise with more context
                    raise ValidationError(
                        f"Parameter validation failed for {param_name}: {e.message}",
                        input_name=param_name,
                        input_value=value,
                        validation_rule=e.validation_rule
                    )
            
            # Check for partial matches (e.g., parameters ending with '_rate')
            elif param_name.endswith('_rate'):
                try:
                    validated_value = validate_positive_number(value, param_name)
                    bound_args.arguments[param_name] = validated_value
                except ValidationError:
                    pass  # Allow custom validation for special cases
            
            elif param_name.endswith('_threshold'):
                try:
                    validated_value = validate_positive_number(value, param_name)
                    bound_args.arguments[param_name] = validated_value
                except ValidationError:
                    pass  # Allow custom validation for special cases
        
        # Call the function with validated arguments
        return func(**bound_args.arguments)
    
    return wrapper


def log_function_calls(log_level: str = "INFO",
                      log_args: bool = False,
                      log_result: bool = False,
                      log_exceptions: bool = True):
    """
    Decorator for logging function calls.
    
    Args:
        log_level: Logging level to use
        log_args: Whether to log function arguments
        log_result: Whether to log function result
        log_exceptions: Whether to log exceptions
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            
            # Log function entry
            if log_args:
                logger.log(
                    getattr(logger, log_level.lower()),
                    f"Calling {func_name} with args={args}, kwargs={kwargs}"
                )
            else:
                logger.log(
                    getattr(logger, log_level.lower()),
                    f"Calling {func_name}"
                )
            
            try:
                # Call the function
                result = func(*args, **kwargs)
                
                # Log successful completion
                if log_result:
                    logger.log(
                        getattr(logger, log_level.lower()),
                        f"{func_name} completed successfully with result={result}"
                    )
                else:
                    logger.log(
                        getattr(logger, log_level.lower()),
                        f"{func_name} completed successfully"
                    )
                
                return result
                
            except Exception as e:
                # Log exception
                if log_exceptions:
                    logger.error(f"{func_name} failed with error: {e}")
                raise
        
        return wrapper
    return decorator


def measure_performance(log_level: str = "DEBUG"):
    """
    Decorator for measuring and logging function performance.
    
    Args:
        log_level: Logging level to use for performance metrics
    """
    def decorator(func: Callable) -> Callable:
        logger = get_logger(func.__module__)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                result = e
                success = False
                raise
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                
                logger.log(
                    getattr(logger, log_level.lower()),
                    f"Performance: {func.__module__}.{func.__name__} "
                    f"took {execution_time:.3f}s (success: {success})"
                )
            
            return result
        
        return wrapper
    return decorator


def cache_result(max_size: int = 128, ttl: Optional[float] = None):
    """
    Simple caching decorator for function results.
    
    Args:
        max_size: Maximum number of cached results
        ttl: Time to live for cached results in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_times = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            cache_key = str(args) + str(sorted(kwargs.items()))
            current_time = time.time()
            
            # Check if result is cached and not expired
            if cache_key in cache:
                if ttl is None or (current_time - cache_times[cache_key]) < ttl:
                    return cache[cache_key]
                else:
                    # Remove expired entry
                    del cache[cache_key]
                    del cache_times[cache_key]
            
            # Compute result
            result = func(*args, **kwargs)
            
            # Add to cache (with size management)
            if len(cache) >= max_size:
                # Remove oldest entry
                oldest_key = min(cache_times.keys(), key=cache_times.get)
                del cache[oldest_key]
                del cache_times[oldest_key]
            
            cache[cache_key] = result
            cache_times[cache_key] = current_time
            
            return result
        
        return wrapper
    return decorator