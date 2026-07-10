"""
Mock classes for QSP_PD_Thyroid testing framework.

This module provides mock implementations of external dependencies for testing.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
from unittest.mock import Mock, MagicMock
import time


class MockODESolver:
    """Mock ODE solver for testing."""
    
    def __init__(self, 
                 success: bool = True,
                 solution_time: float = 0.1,
                 error_message: Optional[str] = None,
                 return_nan: bool = False,
                 return_inf: bool = False):
        """
        Initialize mock ODE solver.
        
        Args:
            success: Whether the solver should succeed
            solution_time: Time to simulate solving
            error_message: Error message if solver fails
            return_nan: Whether to return NaN values
            return_inf: Whether to return infinite values
        """
        self.success = success
        self.solution_time = solution_time
        self.error_message = error_message or "Mock solver failed"
        self.return_nan = return_nan
        self.return_inf = return_inf
        self.call_count = 0
        self.last_args = None
        self.last_kwargs = None
        
    def __call__(self, fun, t_span, y0, t_eval=None, method='LSODA', 
                 rtol=1e-6, atol=1e-9, max_step=1.0):
        """Mock ODE solver call."""
        self.call_count += 1
        self.last_args = (fun, t_span, y0)
        self.last_kwargs = {
            't_eval': t_eval, 'method': method, 'rtol': rtol,
            'atol': atol, 'max_step': max_step
        }
        
        # Simulate solution time
        time.sleep(self.solution_time)
        
        if not self.success:
            class FailedSolution:
                def __init__(self, message):
                    self.success = False
                    self.message = message
                    self.t = np.array([])
                    self.y = np.array([])
            
            return FailedSolution(self.error_message)
        
        # Generate mock solution
        if t_eval is not None:
            t = np.array(t_eval)
        else:
            t = np.linspace(t_span[0], t_span[1], 100)
        
        n_states = len(y0)
        y_shape = (n_states, len(t))
        
        if self.return_nan:
            y = np.full(y_shape, np.nan)
        elif self.return_inf:
            y = np.full(y_shape, np.inf)
        else:
            # Generate realistic mock solution
            y = np.zeros(y_shape)
            for i in range(n_states):
                if i == 0:  # R (checkpoint binding)
                    y[i] = 0.5 * (1 - np.exp(-t / 10))
                elif i == 1:  # T_eff (T-cells)
                    y[i] = y0[i] * (1 + 0.3 * np.sin(t / 5))
                elif i == 2:  # IFN (cytokines)
                    y[i] = 20 * np.exp(-t / 20) * (1 + 0.2 * np.sin(t / 3))
                elif i == 3:  # Thyro (thyrocytes)
                    y[i] = y0[i] * np.exp(-0.001 * t)
                elif i == 4:  # T3 (hormone)
                    y[i] = 4.8 * (1 - 0.1 * (1 - np.exp(-t / 60)))
                elif i == 5:  # TSH (hormone)
                    y[i] = 1.5 * (1 + 0.2 * (1 - np.exp(-t / 50)))
                elif i == 6:  # cumulative_damage
                    y[i] = 0.001 * t * (1 + 0.5 * np.exp(-t / 40))
                else:
                    y[i] = y0[i] * (1 + 0.1 * np.random.random(len(t)))
        
        class MockSolution:
            def __init__(self, t, y):
                self.t = t
                self.y = y
                self.success = True
                self.message = "Mock solution completed successfully"
        
        return MockSolution(t, y)


class MockConfigurationManager:
    """Mock configuration manager for testing."""
    
    def __init__(self, 
                 load_success: bool = True,
                 save_success: bool = True,
                 validation_success: bool = True,
                 error_message: Optional[str] = None):
        """
        Initialize mock configuration manager.
        
        Args:
            load_success: Whether loading should succeed
            save_success: Whether saving should succeed
            validation_success: Whether validation should succeed
            error_message: Error message for failures
        """
        self.load_success = load_success
        self.save_success = save_success
        self.validation_success = validation_success
        self.error_message = error_message or "Mock configuration error"
        self.load_call_count = 0
        self.save_call_count = 0
        self.validate_call_count = 0
        
    def load_from_file(self, file_path):
        """Mock loading configuration from file."""
        self.load_call_count += 1
        
        if not self.load_success:
            raise Exception(self.error_message)
        
        # Return mock parameters
        from config import ModelParameters
        return ModelParameters()
    
    def save_to_file(self, params, file_path):
        """Mock saving configuration to file."""
        self.save_call_count += 1
        
        if not self.save_success:
            raise Exception(self.error_message)
        
        return True
    
    def validate_parameters(self, params):
        """Mock parameter validation."""
        self.validate_call_count += 1
        
        if not self.validation_success:
            raise Exception(self.error_message)
        
        return True


class MockLogger:
    """Mock logger for testing."""
    
    def __init__(self, capture_logs: bool = True):
        """
        Initialize mock logger.
        
        Args:
            capture_logs: Whether to capture log messages
        """
        self.capture_logs = capture_logs
        self.logs = []
        self.debug_calls = []
        self.info_calls = []
        self.warning_calls = []
        self.error_calls = []
        self.critical_calls = []
    
    def _log(self, level, message, *args, **kwargs):
        """Internal logging method."""
        if self.capture_logs:
            log_entry = {
                'level': level,
                'message': message,
                'args': args,
                'kwargs': kwargs,
                'timestamp': time.time()
            }
            self.logs.append(log_entry)
            
            # Add to level-specific lists
            if level == 'debug':
                self.debug_calls.append(log_entry)
            elif level == 'info':
                self.info_calls.append(log_entry)
            elif level == 'warning':
                self.warning_calls.append(log_entry)
            elif level == 'error':
                self.error_calls.append(log_entry)
            elif level == 'critical':
                self.critical_calls.append(log_entry)
    
    def debug(self, message, *args, **kwargs):
        """Mock debug logging."""
        self._log('debug', message, *args, **kwargs)
    
    def info(self, message, *args, **kwargs):
        """Mock info logging."""
        self._log('info', message, *args, **kwargs)
    
    def warning(self, message, *args, **kwargs):
        """Mock warning logging."""
        self._log('warning', message, *args, **kwargs)
    
    def error(self, message, *args, **kwargs):
        """Mock error logging."""
        self._log('error', message, *args, **kwargs)
    
    def critical(self, message, *args, **kwargs):
        """Mock critical logging."""
        self._log('critical', message, *args, **kwargs)
    
    def clear(self):
        """Clear all captured logs."""
        self.logs.clear()
        self.debug_calls.clear()
        self.info_calls.clear()
        self.warning_calls.clear()
        self.error_calls.clear()
        self.critical_calls.clear()
    
    def has_message(self, level: str, message_substring: str) -> bool:
        """Check if a log message contains a specific substring."""
        level_calls = getattr(self, f"{level}_calls", [])
        return any(message_substring in call['message'] for call in level_calls)


class MockFileSystem:
    """Mock file system operations for testing."""
    
    def __init__(self):
        """Initialize mock file system."""
        self.files = {}
        self.directories = set()
        self.read_call_count = 0
        self.write_call_count = 0
        self.exists_call_count = 0
        
    def write_file(self, path: str, content: str):
        """Mock writing a file."""
        self.write_call_count += 1
        self.files[path] = content
        
        # Add parent directories
        parts = path.split('/')
        for i in range(1, len(parts)):
            parent_dir = '/'.join(parts[:i])
            self.directories.add(parent_dir)
    
    def read_file(self, path: str) -> str:
        """Mock reading a file."""
        self.read_call_count += 1
        
        if path not in self.files:
            raise FileNotFoundError(f"File not found: {path}")
        
        return self.files[path]
    
    def exists(self, path: str) -> bool:
        """Mock checking if file exists."""
        self.exists_call_count += 1
        return path in self.files or path in self.directories
    
    def mkdir(self, path: str):
        """Mock creating a directory."""
        self.directories.add(path)
    
    def listdir(self, path: str) -> List[str]:
        """Mock listing directory contents."""
        files_in_dir = []
        dirs_in_dir = []
        
        for file_path in self.files:
            if file_path.startswith(path + '/'):
                relative_path = file_path[len(path) + 1:]
                if '/' not in relative_path:
                    files_in_dir.append(relative_path)
        
        for dir_path in self.directories:
            if dir_path.startswith(path + '/'):
                relative_path = dir_path[len(path) + 1:]
                if '/' not in relative_path:
                    dirs_in_dir.append(relative_path)
        
        return files_in_dir + dirs_in_dir
    
    def clear(self):
        """Clear all files and directories."""
        self.files.clear()
        self.directories.clear()


class MockPerformanceMonitor:
    """Mock performance monitor for testing."""
    
    def __init__(self):
        """Initialize mock performance monitor."""
        self.measurements = []
        self.start_times = {}
        self.current_measurement = None
        
    def start_measurement(self, name: str):
        """Start a performance measurement."""
        self.start_times[name] = time.time()
        self.current_measurement = name
    
    def end_measurement(self, name: str) -> float:
        """End a performance measurement and return duration."""
        if name not in self.start_times:
            return 0.0
        
        duration = time.time() - self.start_times[name]
        del self.start_times[name]
        
        self.measurements.append({
            'name': name,
            'duration': duration,
            'timestamp': time.time()
        })
        
        if self.current_measurement == name:
            self.current_measurement = None
        
        return duration
    
    def get_measurement(self, name: str) -> Optional[Dict[str, Any]]:
        """Get measurement by name."""
        for measurement in reversed(self.measurements):
            if measurement['name'] == name:
                return measurement
        return None
    
    def get_all_measurements(self) -> List[Dict[str, Any]]:
        """Get all measurements."""
        return self.measurements.copy()
    
    def clear(self):
        """Clear all measurements."""
        self.measurements.clear()
        self.start_times.clear()
        self.current_measurement = None


class MockDatabase:
    """Mock database for testing."""
    
    def __init__(self):
        """Initialize mock database."""
        self.tables = {}
        self.query_count = 0
        self.insert_count = 0
        self.update_count = 0
        self.delete_count = 0
        
    def create_table(self, table_name: str, schema: Dict[str, str]):
        """Create a table with schema."""
        self.tables[table_name] = {
            'schema': schema,
            'data': []
        }
    
    def insert(self, table_name: str, data: Dict[str, Any]):
        """Insert data into table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        self.insert_count += 1
        self.tables[table_name]['data'].append(data)
    
    def query(self, table_name: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Query data from table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        self.query_count += 1
        data = self.tables[table_name]['data']
        
        if filters:
            filtered_data = []
            for row in data:
                match = True
                for key, value in filters.items():
                    if key not in row or row[key] != value:
                        match = False
                        break
                if match:
                    filtered_data.append(row)
            return filtered_data
        
        return data.copy()
    
    def update(self, table_name: str, filters: Dict[str, Any], updates: Dict[str, Any]):
        """Update data in table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        self.update_count += 1
        data = self.tables[table_name]['data']
        
        for row in data:
            match = True
            for key, value in filters.items():
                if key not in row or row[key] != value:
                    match = False
                    break
            
            if match:
                row.update(updates)
    
    def delete(self, table_name: str, filters: Dict[str, Any]):
        """Delete data from table."""
        if table_name not in self.tables:
            raise ValueError(f"Table {table_name} does not exist")
        
        self.delete_count += 1
        data = self.tables[table_name]['data']
        
        self.tables[table_name]['data'] = [
            row for row in data
            if not all(key in row and row[key] == value for key, value in filters.items())
        ]
    
    def clear(self):
        """Clear all tables."""
        self.tables.clear()
        self.query_count = 0
        self.insert_count = 0
        self.update_count = 0
        self.delete_count = 0


class MockExternalAPI:
    """Mock external API for testing."""
    
    def __init__(self, 
                 response_delay: float = 0.0,
                 success_rate: float = 1.0,
                 error_message: Optional[str] = None):
        """
        Initialize mock external API.
        
        Args:
            response_delay: Delay before responding
            success_rate: Rate of successful responses (0-1)
            error_message: Error message for failures
        """
        self.response_delay = response_delay
        self.success_rate = success_rate
        self.error_message = error_message or "Mock API error"
        self.request_count = 0
        self.requests = []
        
    def request(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Mock API request."""
        self.request_count += 1
        
        request_info = {
            'endpoint': endpoint,
            'data': data,
            'timestamp': time.time()
        }
        self.requests.append(request_info)
        
        # Simulate response delay
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # Simulate success/failure
        if np.random.random() > self.success_rate:
            return {
                'success': False,
                'error': self.error_message,
                'status_code': 500
            }
        
        # Mock successful response
        return {
            'success': True,
            'data': {
                'endpoint': endpoint,
                'processed_data': data,
                'result': 'mock_result'
            },
            'status_code': 200
        }
    
    def clear(self):
        """Clear request history."""
        self.requests.clear()
        self.request_count = 0