"""
Error Recovery Mechanisms for QSP Thyroid Model

This module provides automated recovery strategies for common errors
that may occur during model execution, including parameter adjustments,
fallback methods, and alternative computation paths.
"""

import numpy as np
import pandas as pd
import time
import traceback
from typing import Any, Dict, List, Optional, Union, Callable, Tuple
from pathlib import Path
import json

from .exceptions import (
    QSPModelError, ParameterError, SimulationError, DataError, ValidationError,
    NumericalInstabilityError
)
from .logger import get_logger


class RecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def __init__(self, name: str):
        """
        Initialize recovery strategy.
        
        Args:
            name: Name of the recovery strategy
        """
        self.name = name
        self.logger = get_logger(f"Recovery_{name}")
        self.attempts = 0
        self.max_attempts = 3
        self.successful = False
    
    def can_recover(self, error: Exception) -> bool:
        """
        Check if this strategy can recover from the given error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if this strategy can recover from the error
        """
        raise NotImplementedError("Subclasses must implement can_recover")
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Attempt to recover from the error.
        
        Args:
            error: The error that occurred
            context: Context information about the error
            
        Returns:
            Result of the recovery attempt
            
        Raises:
            Exception: If recovery fails
        """
        self.attempts += 1
        self.logger.info(f"Attempting recovery {self.attempts}/{self.max_attempts} for {type(error).__name__}")
        
        if self.attempts > self.max_attempts:
            raise error  # Re-raise original error if max attempts exceeded
        
        try:
            result = self._recover(error, context)
            self.successful = True
            self.logger.info(f"Recovery successful for {type(error).__name__}")
            return result
        except Exception as e:
            self.logger.warning(f"Recovery attempt {self.attempts} failed: {e}")
            if self.attempts >= self.max_attempts:
                self.logger.error(f"All recovery attempts failed for {type(error).__name__}")
                raise error  # Re-raise original error
            else:
                # Try again with same strategy
                return self.recover(error, context)
    
    def _recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Implement the actual recovery logic.
        
        Args:
            error: The error that occurred
            context: Context information about the error
            
        Returns:
            Result of the recovery attempt
        """
        raise NotImplementedError("Subclasses must implement _recover")


class ParameterAdjustmentStrategy(RecoveryStrategy):
    """Recovery strategy that adjusts model parameters to fix errors."""
    
    def __init__(self):
        """Initialize parameter adjustment strategy."""
        super().__init__("ParameterAdjustment")
        self.adjustment_factors = {
            'stiffness': 0.5,  # Reduce stiffness for ODE solver
            'threshold': 0.8,  # Reduce thresholds for numerical stability
            'scale': 1.2,      # Scale parameters to avoid extreme values
            'noise': 0.01      # Add small noise to avoid singularities
        }
    
    def can_recover(self, error: Exception) -> bool:
        """
        Check if this strategy can recover from the given error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if this strategy can recover from the error
        """
        return isinstance(error, (NumericalInstabilityError, SimulationError, ParameterError))
    
    def _recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Attempt to recover by adjusting parameters.
        
        Args:
            error: The error that occurred
            context: Context information about the error
            
        Returns:
            Adjusted parameters or model
        """
        if 'model' in context:
            model = context['model']
            
            # Adjust model parameters based on error type
            if isinstance(error, NumericalInstabilityError):
                # Reduce stiffness for numerical stability
                if hasattr(model, 'params'):
                    # Adjust parameters that might cause stiffness
                    if hasattr(model.params, 'alpha'):
                        model.params.alpha *= self.adjustment_factors['stiffness']
                    if hasattr(model.params, 'beta'):
                        model.params.beta *= self.adjustment_factors['stiffness']
                    if hasattr(model.params, 'epsilon'):
                        model.params.epsilon *= self.adjustment_factors['stiffness']
                    
                    self.logger.info("Adjusted model parameters to reduce stiffness")
            
            elif isinstance(error, SimulationError):
                # Adjust thresholds and scales
                if hasattr(model, 'params'):
                    if hasattr(model.params, 'damage_threshold'):
                        model.params.damage_threshold *= self.adjustment_factors['threshold']
                    if hasattr(model.params, 'cytokine_threshold'):
                        model.params.cytokine_threshold *= self.adjustment_factors['threshold']
                    
                    self.logger.info("Adjusted model thresholds for simulation stability")
            
            return model
        
        elif 'parameters' in context:
            parameters = context['parameters']
            
            # Add small noise to avoid singularities
            if isinstance(parameters, dict):
                for key, value in parameters.items():
                    if isinstance(value, (int, float)) and value == 0:
                        parameters[key] = self.adjustment_factors['noise']
                        self.logger.info(f"Added noise to parameter {key} to avoid singularity")
            
            return parameters
        
        return None


class FallbackMethodStrategy(RecoveryStrategy):
    """Recovery strategy that uses alternative methods when primary methods fail."""
    
    def __init__(self):
        """Initialize fallback method strategy."""
        super().__init__("FallbackMethod")
        self.fallback_methods = {
            'ode_solver': ['RK45', 'BDF', 'Radau', 'LSODA'],
            'interpolation': ['linear', 'cubic', 'nearest'],
            'integration': ['trapezoidal', 'simpson', 'romberg']
        }
    
    def can_recover(self, error: Exception) -> bool:
        """
        Check if this strategy can recover from the given error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if this strategy can recover from the error
        """
        return isinstance(error, (SimulationError, NumericalInstabilityError))
    
    def _recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Attempt to recover by using fallback methods.
        
        Args:
            error: The error that occurred
            context: Context information about the error
            
        Returns:
            Result using fallback method
        """
        # Check for ODE solver errors
        if 'solver' in context and 'method' in context:
            current_method = context['method']
            available_methods = self.fallback_methods['ode_solver']
            
            if current_method in available_methods:
                current_index = available_methods.index(current_method)
                
                # Try next available method
                if current_index + 1 < len(available_methods):
                    fallback_method = available_methods[current_index + 1]
                    self.logger.info(f"Switching ODE solver from {current_method} to {fallback_method}")
                    return {'method': fallback_method, 'solver': context['solver']}
        
        # Check for interpolation errors
        if 'interpolation_method' in context:
            current_method = context['interpolation_method']
            available_methods = self.fallback_methods['interpolation']
            
            if current_method in available_methods:
                current_index = available_methods.index(current_method)
                
                # Try next available method
                if current_index + 1 < len(available_methods):
                    fallback_method = available_methods[current_index + 1]
                    self.logger.info(f"Switching interpolation from {current_method} to {fallback_method}")
                    return {'interpolation_method': fallback_method}
        
        # Check for integration errors
        if 'integration_method' in context:
            current_method = context['integration_method']
            available_methods = self.fallback_methods['integration']
            
            if current_method in available_methods:
                current_index = available_methods.index(current_method)
                
                # Try next available method
                if current_index + 1 < len(available_methods):
                    fallback_method = available_methods[current_index + 1]
                    self.logger.info(f"Switching integration from {current_method} to {fallback_method}")
                    return {'integration_method': fallback_method}
        
        # Default fallback: reduce time step or increase tolerance
        if 'time_step' in context:
            new_time_step = context['time_step'] * 0.5
            self.logger.info(f"Reducing time step from {context['time_step']} to {new_time_step}")
            return {'time_step': new_time_step}
        
        if 'tolerance' in context:
            new_tolerance = context['tolerance'] * 10.0
            self.logger.info(f"Increasing tolerance from {context['tolerance']} to {new_tolerance}")
            return {'tolerance': new_tolerance}
        
        return None


class DataRepairStrategy(RecoveryStrategy):
    """Recovery strategy that repairs corrupted or invalid data."""
    
    def __init__(self):
        """Initialize data repair strategy."""
        super().__init__("DataRepair")
        self.repair_methods = {
            'remove_nan': True,
            'remove_inf': True,
            'interpolate_missing': True,
            'clip_outliers': True,
            'smooth_data': False
        }
    
    def can_recover(self, error: Exception) -> bool:
        """
        Check if this strategy can recover from the given error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if this strategy can recover from the error
        """
        return isinstance(error, (DataError, ValidationError))
    
    def _recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Attempt to recover by repairing data.
        
        Args:
            error: The error that occurred
            context: Context information about the error
            
        Returns:
            Repaired data
        """
        if 'data' in context:
            data = context['data']
            
            # Handle pandas DataFrame
            if isinstance(data, pd.DataFrame):
                repaired_data = data.copy()
                
                # Remove NaN values
                if self.repair_methods['remove_nan']:
                    nan_count = repaired_data.isnull().sum().sum()
                    if nan_count > 0:
                        repaired_data = repaired_data.dropna()
                        self.logger.info(f"Removed {nan_count} NaN values from DataFrame")
                
                # Remove infinite values
                if self.repair_methods['remove_inf']:
                    inf_count = np.isinf(repaired_data.select_dtypes(include=[np.number])).sum().sum()
                    if inf_count > 0:
                        repaired_data = repaired_data.replace([np.inf, -np.inf], np.nan)
                        repaired_data = repaired_data.dropna()
                        self.logger.info(f"Removed {inf_count} infinite values from DataFrame")
                
                # Interpolate missing values
                if self.repair_methods['interpolate_missing'] and len(repaired_data) > 1:
                    repaired_data = repaired_data.interpolate()
                    self.logger.info("Interpolated missing values in DataFrame")
                
                # Clip outliers
                if self.repair_methods['clip_outliers']:
                    numeric_columns = repaired_data.select_dtypes(include=[np.number]).columns
                    for col in numeric_columns:
                        q1 = repaired_data[col].quantile(0.25)
                        q3 = repaired_data[col].quantile(0.75)
                        iqr = q3 - q1
                        lower_bound = q1 - 1.5 * iqr
                        upper_bound = q3 + 1.5 * iqr
                        
                        outlier_count = ((repaired_data[col] < lower_bound) | 
                                       (repaired_data[col] > upper_bound)).sum()
                        
                        if outlier_count > 0:
                            repaired_data[col] = repaired_data[col].clip(lower_bound, upper_bound)
                            self.logger.info(f"Clipped {outlier_count} outliers in column {col}")
                
                return repaired_data
            
            # Handle numpy array
            elif isinstance(data, np.ndarray):
                repaired_data = data.copy()
                
                # Remove NaN values
                if self.repair_methods['remove_nan']:
                    nan_mask = np.isnan(repaired_data)
                    nan_count = np.sum(nan_mask)
                    if nan_count > 0:
                        repaired_data = repaired_data[~nan_mask.any(axis=1)] if repaired_data.ndim > 1 else repaired_data[~nan_mask]
                        self.logger.info(f"Removed {nan_count} NaN values from array")
                
                # Remove infinite values
                if self.repair_methods['remove_inf']:
                    inf_mask = np.isinf(repaired_data)
                    inf_count = np.sum(inf_mask)
                    if inf_count > 0:
                        repaired_data = repaired_data[~inf_mask.any(axis=1)] if repaired_data.ndim > 1 else repaired_data[~inf_mask]
                        self.logger.info(f"Removed {inf_count} infinite values from array")
                
                return repaired_data
            
            # Handle dictionary
            elif isinstance(data, dict):
                repaired_data = {}
                
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        # Check for NaN or infinite values
                        if np.isnan(value) or np.isinf(value):
                            repaired_data[key] = 0.0  # Replace with default value
                            self.logger.info(f"Replaced invalid value for key {key} with 0.0")
                        else:
                            repaired_data[key] = value
                    else:
                        repaired_data[key] = value
                
                return repaired_data
        
        return None


class ErrorRecoveryManager:
    """
    Manager class that coordinates different recovery strategies.
    """
    
    def __init__(self):
        """Initialize error recovery manager."""
        self.logger = get_logger("ErrorRecoveryManager")
        self.strategies = [
            ParameterAdjustmentStrategy(),
            FallbackMethodStrategy(),
            DataRepairStrategy()
        ]
        self.recovery_history = []
    
    def can_recover(self, error: Exception) -> bool:
        """
        Check if any strategy can recover from the given error.
        
        Args:
            error: The error that occurred
            
        Returns:
            True if any strategy can recover from the error
        """
        for strategy in self.strategies:
            if strategy.can_recover(error):
                return True
        return False
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """
        Attempt to recover from the error using available strategies.
        
        Args:
            error: The error that occurred
            context: Context information about the error
            
        Returns:
            Result of the recovery attempt
            
        Raises:
            Exception: If recovery fails
        """
        self.logger.info(f"Attempting recovery for {type(error).__name__}: {error}")
        
        recovery_start_time = time.time()
        
        # Try each strategy in order
        for strategy in self.strategies:
            if strategy.can_recover(error):
                try:
                    result = strategy.recover(error, context)
                    
                    # Record successful recovery
                    recovery_time = time.time() - recovery_start_time
                    self.recovery_history.append({
                        'timestamp': time.time(),
                        'error_type': type(error).__name__,
                        'error_message': str(error),
                        'strategy': strategy.name,
                        'attempts': strategy.attempts,
                        'recovery_time': recovery_time,
                        'successful': strategy.successful
                    })
                    
                    self.logger.info(f"Recovery successful using {strategy.name} in {recovery_time:.2f}s")
                    return result
                    
                except Exception as e:
                    self.logger.warning(f"Recovery with {strategy.name} failed: {e}")
                    continue
        
        # If all strategies fail, re-raise the original error
        self.logger.error(f"All recovery strategies failed for {type(error).__name__}")
        raise error
    
    def get_recovery_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about recovery attempts.
        
        Returns:
            Dictionary with recovery statistics
        """
        if not self.recovery_history:
            return {
                'total_recoveries': 0,
                'successful_recoveries': 0,
                'success_rate': 0.0,
                'strategies_used': [],
                'common_errors': []
            }
        
        total_recoveries = len(self.recovery_history)
        successful_recoveries = sum(1 for r in self.recovery_history if r['successful'])
        success_rate = successful_recoveries / total_recoveries if total_recoveries > 0 else 0.0
        
        strategies_used = list(set(r['strategy'] for r in self.recovery_history))
        error_types = list(set(r['error_type'] for r in self.recovery_history))
        
        # Calculate average recovery time
        avg_recovery_time = sum(r['recovery_time'] for r in self.recovery_history) / total_recoveries
        
        return {
            'total_recoveries': total_recoveries,
            'successful_recoveries': successful_recoveries,
            'success_rate': success_rate,
            'strategies_used': strategies_used,
            'common_errors': error_types,
            'average_recovery_time': avg_recovery_time
        }
    
    def save_recovery_history(self, file_path: str = 'recovery_history.json') -> None:
        """
        Save recovery history to a file.
        
        Args:
            file_path: Path to save the recovery history
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(self.recovery_history, f, indent=2)
            self.logger.info(f"Recovery history saved to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save recovery history: {e}")


# Global recovery manager instance
recovery_manager = ErrorRecoveryManager()


def recover_from_error(error: Exception, context: Dict[str, Any]) -> Any:
    """
    Attempt to recover from an error using the global recovery manager.
    
    Args:
        error: The error that occurred
        context: Context information about the error
        
    Returns:
        Result of the recovery attempt
        
    Raises:
        Exception: If recovery fails
    """
    return recovery_manager.recover(error, context)


def can_recover_from_error(error: Exception) -> bool:
    """
    Check if the error can be recovered from.
    
    Args:
        error: The error that occurred
        
    Returns:
        True if the error can be recovered from
    """
    return recovery_manager.can_recover(error)