"""
Performance tests for configuration system.

This module tests the performance characteristics of the configuration system.
"""

import pytest
import time
import numpy as np
import pandas as pd
import psutil
import os
from typing import Dict, List, Tuple
import gc
import tracemalloc
import tempfile
import yaml
import json

from config import (
    ModelParameters,
    NivolumabParameters,
    create_drug_parameters,
    ConfigurationManager
)
from tests.fixtures.data_generators import generate_config_variations


class TestConfigPerformance:
    """Test cases for configuration system performance."""
    
    @pytest.mark.performance
    def test_parameter_creation_performance(self, test_config):
        """Test performance of parameter object creation."""
        # Test creating many parameter objects
        n_objects = 1000
        
        # Measure performance
        tracemalloc.start()
        start_time = time.time()
        
        params_list = []
        for i in range(n_objects):
            params = ModelParameters(
                alpha=4e-4 * (1 + 0.001 * i),  # Small variation
                beta=0.12 * (1 + 0.001 * i)    # Small variation
            )
            params_list.append(params)
        
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        creation_time = end_time - start_time
        avg_time_per_object = creation_time / n_objects
        peak_memory = peak / 1024 / 1024  # MB
        
        # Performance assertions
        assert avg_time_per_object < 0.001, \
            f"Parameter creation too slow: {avg_time_per_object:.6f}s per object"
        assert creation_time < 5.0, \
            f"Batch parameter creation too slow: {creation_time:.2f}s for {n_objects} objects"
        assert peak_memory < 100, \
            f"Parameter creation used too much memory: {peak_memory:.2f}MB"
        
        # Verify objects are valid
        assert len(params_list) == n_objects
        for params in params_list:
            assert isinstance(params, ModelParameters)
            assert params.alpha > 0
            assert params.beta > 0
    
    @pytest.mark.performance
    def test_parameter_serialization_performance(self, test_config):
        """Test performance of parameter serialization."""
        # Create test parameters
        params = ModelParameters(
            alpha=5e-4,
            beta=0.15,
            epsilon=2.5,
            drug_susceptibility_rates={
                'nivolumab': 0.30,
                'pembrolizumab': 0.35
            }
        )
        
        # Test multiple serialization cycles
        n_cycles = 100
        
        # Measure to_dict performance
        start_time = time.time()
        for _ in range(n_cycles):
            params_dict = params.to_dict()
        end_time = time.time()
        to_dict_time = end_time - start_time
        avg_to_dict_time = to_dict_time / n_cycles
        
        assert avg_to_dict_time < 0.001, \
            f"Parameter to_dict too slow: {avg_to_dict_time:.6f}s per call"
        
        # Measure to_json performance
        start_time = time.time()
        for _ in range(n_cycles):
            params_json = params.to_json()
        end_time = time.time()
        to_json_time = end_time - start_time
        avg_to_json_time = to_json_time / n_cycles
        
        assert avg_to_json_time < 0.002, \
            f"Parameter to_json too slow: {avg_to_json_time:.6f}s per call"
        
        # Measure from_dict performance
        params_dict = params.to_dict()
        start_time = time.time()
        for _ in range(n_cycles):
            restored_params = ModelParameters.from_dict(params_dict)
        end_time = time.time()
        from_dict_time = end_time - start_time
        avg_from_dict_time = from_dict_time / n_cycles
        
        assert avg_from_dict_time < 0.001, \
            f"Parameter from_dict too slow: {avg_from_dict_time:.6f}s per call"
        
        # Measure from_json performance
        params_json = params.to_json()
        start_time = time.time()
        for _ in range(n_cycles):
            restored_params = ModelParameters.from_json(params_json)
        end_time = time.time()
        from_json_time = end_time - start_time
        avg_from_json_time = from_json_time / n_cycles
        
        assert avg_from_json_time < 0.002, \
            f"Parameter from_json too slow: {avg_from_json_time:.6f}s per call"
        
        # Verify round-trip integrity
        restored_params = ModelParameters.from_dict(params_dict)
        assert restored_params.alpha == params.alpha
        assert restored_params.beta == params.beta
        assert restored_params.drug_susceptibility_rates == params.drug_susceptibility_rates
    
    @pytest.mark.performance
    def test_config_file_io_performance(self, test_config, temp_directory):
        """Test performance of configuration file I/O."""
        # Create test configuration
        config_data = {
            'model_parameters': {
                'alpha': 5e-4,
                'beta': 0.15,
                'epsilon': 2.5,
                'k_death': 0.01,
                'drug_susceptibility_rates': {
                    'nivolumab': 0.30,
                    'pembrolizumab': 0.35,
                    'atezolizumab': 0.25,
                    'durvalumab': 0.20
                }
            },
            'metadata': {
                'version': '1.0.0',
                'description': 'Performance test configuration',
                'author': 'Test Suite',
                'created_at': '2023-01-01T00:00:00Z'
            }
        }
        
        # Test YAML I/O performance
        n_cycles = 50
        
        # Measure YAML write performance
        yaml_file = temp_directory / "perf_test.yaml"
        start_time = time.time()
        for _ in range(n_cycles):
            with open(yaml_file, 'w') as f:
                yaml.dump(config_data, f)
        end_time = time.time()
        yaml_write_time = end_time - start_time
        avg_yaml_write_time = yaml_write_time / n_cycles
        
        assert avg_yaml_write_time < 0.01, \
            f"YAML write too slow: {avg_yaml_write_time:.6f}s per write"
        
        # Measure YAML read performance
        start_time = time.time()
        for _ in range(n_cycles):
            with open(yaml_file, 'r') as f:
                loaded_data = yaml.safe_load(f)
        end_time = time.time()
        yaml_read_time = end_time - start_time
        avg_yaml_read_time = yaml_read_time / n_cycles
        
        assert avg_yaml_read_time < 0.01, \
            f"YAML read too slow: {avg_yaml_read_time:.6f}s per read"
        
        # Test JSON I/O performance
        json_file = temp_directory / "perf_test.json"
        
        # Measure JSON write performance
        start_time = time.time()
        for _ in range(n_cycles):
            with open(json_file, 'w') as f:
                json.dump(config_data, f)
        end_time = time.time()
        json_write_time = end_time - start_time
        avg_json_write_time = json_write_time / n_cycles
        
        assert avg_json_write_time < 0.005, \
            f"JSON write too slow: {avg_json_write_time:.6f}s per write"
        
        # Measure JSON read performance
        start_time = time.time()
        for _ in range(n_cycles):
            with open(json_file, 'r') as f:
                loaded_data = json.load(f)
        end_time = time.time()
        json_read_time = end_time - start_time
        avg_json_read_time = json_read_time / n_cycles
        
        assert avg_json_read_time < 0.005, \
            f"JSON read too slow: {avg_json_read_time:.6f}s per read"
        
        # JSON should generally be faster than YAML
        assert avg_json_read_time < avg_yaml_read_time, \
            "JSON read should be faster than YAML read"
        assert avg_json_write_time < avg_yaml_write_time, \
            "JSON write should be faster than YAML write"
    
    @pytest.mark.performance
    def test_config_manager_performance(self, test_config, temp_directory):
        """Test performance of configuration manager."""
        # Create test configuration file
        config_data = {
            'model_parameters': {
                'alpha': 5e-4,
                'beta': 0.15,
                'epsilon': 2.5
            }
        }
        
        config_file = temp_directory / "manager_test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test configuration manager performance
        n_operations = 100
        config_manager = ConfigurationManager()
        
        # Measure load performance
        start_time = time.time()
        for _ in range(n_operations):
            params = config_manager.load_from_file(str(config_file))
        end_time = time.time()
        load_time = end_time - start_time
        avg_load_time = load_time / n_operations
        
        assert avg_load_time < 0.01, \
            f"Config manager load too slow: {avg_load_time:.6f}s per load"
        
        # Test save performance
        params = config_manager.load_from_file(str(config_file))
        save_file = temp_directory / "manager_save_test.yaml"
        
        start_time = time.time()
        for _ in range(n_operations):
            config_manager.save_to_file(params, str(save_file))
        end_time = time.time()
        save_time = end_time - start_time
        avg_save_time = save_time / n_operations
        
        assert avg_save_time < 0.01, \
            f"Config manager save too slow: {avg_save_time:.6f}s per save"
        
        # Test validation performance
        start_time = time.time()
        for _ in range(n_operations):
            is_valid, errors = config_manager.validate_config(params)
        end_time = time.time()
        validation_time = end_time - start_time
        avg_validation_time = validation_time / n_operations
        
        assert avg_validation_time < 0.001, \
            f"Config validation too slow: {avg_validation_time:.6f}s per validation"
    
    @pytest.mark.performance
    def test_drug_parameter_factory_performance(self, test_config):
        """Test performance of drug parameter factory."""
        drugs = ['nivolumab', 'pembrolizumab', 'atezolizumab', 'durvalumab']
        n_creations = 200
        
        # Measure factory performance
        start_time = time.time()
        params_list = []
        
        for i in range(n_creations):
            drug = drugs[i % len(drugs)]
            params = create_drug_parameters(
                drug,
                alpha=4e-4 * (1 + 0.001 * i),
                beta=0.12 * (1 + 0.001 * i)
            )
            params_list.append(params)
        
        end_time = time.time()
        creation_time = end_time - start_time
        avg_creation_time = creation_time / n_creations
        
        assert avg_creation_time < 0.002, \
            f"Drug parameter factory too slow: {avg_creation_time:.6f}s per creation"
        
        # Verify results
        assert len(params_list) == n_creations
        for params in params_list:
            assert isinstance(params, ModelParameters)
            assert params.alpha > 0
            assert params.beta > 0
    
    @pytest.mark.performance
    def test_parameter_validation_performance(self, test_config):
        """Test performance of parameter validation."""
        # Create test parameters
        params = ModelParameters()
        
        # Test validation performance
        n_validations = 1000
        
        start_time = time.time()
        for _ in range(n_validations):
            errors = params.validate_parameters()
        end_time = time.time()
        validation_time = end_time - start_time
        avg_validation_time = validation_time / n_validations
        
        assert avg_validation_time < 0.001, \
            f"Parameter validation too slow: {avg_validation_time:.6f}s per validation"
        
        # Test validation with invalid parameters
        invalid_params = ModelParameters(
            alpha=-0.001,  # Invalid
            beta=2.0,      # Invalid
            k_death=-0.01   # Invalid
        )
        
        start_time = time.time()
        for _ in range(n_validations):
            errors = invalid_params.validate_parameters()
        end_time = time.time()
        invalid_validation_time = end_time - start_time
        avg_invalid_validation_time = invalid_validation_time / n_validations
        
        assert avg_invalid_validation_time < 0.001, \
            f"Invalid parameter validation too slow: {avg_invalid_validation_time:.6f}s per validation"
        
        # Should detect errors
        errors = invalid_params.validate_parameters()
        assert len(errors) > 0
    
    @pytest.mark.performance
    def test_config_merge_performance(self, test_config):
        """Test performance of configuration merging."""
        # Create base parameters
        base_params = ModelParameters(
            alpha=4e-4,
            beta=0.12,
            gamma=1.0
        )
        
        # Create override parameters
        override_params = ModelParameters(
            alpha=5e-4,  # Override
            epsilon=2.5  # New parameter
        )
        
        # Test merge performance
        n_merges = 500
        config_manager = ConfigurationManager()
        
        start_time = time.time()
        for _ in range(n_merges):
            merged_params = config_manager.merge_configs(base_params, override_params)
        end_time = time.time()
        merge_time = end_time - start_time
        avg_merge_time = merge_time / n_merges
        
        assert avg_merge_time < 0.001, \
            f"Config merge too slow: {avg_merge_time:.6f}s per merge"
        
        # Verify merge result
        merged_params = config_manager.merge_configs(base_params, override_params)
        assert merged_params.alpha == 5e-4  # Should be overridden
        assert merged_params.beta == 0.12  # Should be preserved
        assert merged_params.epsilon == 2.5  # Should be added
    
    @pytest.mark.performance
    def test_large_config_performance(self, test_config, temp_directory):
        """Test performance with large configurations."""
        # Create large configuration
        large_config_data = {
            'model_parameters': {},
            'metadata': {
                'version': '1.0.0',
                'description': 'Large configuration for performance testing'
            }
        }
        
        # Add many parameters
        for i in range(100):
            large_config_data['model_parameters'][f'param_{i}'] = i * 0.01
        
        # Add large metadata
        large_config_data['metadata']['large_list'] = list(range(1000))
        large_config_data['metadata']['large_dict'] = {f'key_{i}': f'value_{i}' for i in range(500)}
        
        # Test file I/O performance
        config_file = temp_directory / "large_config.yaml"
        
        # Measure write performance
        start_time = time.time()
        with open(config_file, 'w') as f:
            yaml.dump(large_config_data, f)
        end_time = time.time()
        write_time = end_time - start_time
        
        assert write_time < 1.0, \
            f"Large config write too slow: {write_time:.2f}s"
        
        # Measure read performance
        start_time = time.time()
        with open(config_file, 'r') as f:
            loaded_data = yaml.safe_load(f)
        end_time = time.time()
        read_time = end_time - start_time
        
        assert read_time < 1.0, \
            f"Large config read too slow: {read_time:.2f}s"
        
        # Verify data integrity
        assert len(loaded_data['model_parameters']) == 100
        assert len(loaded_data['metadata']['large_list']) == 1000
        assert len(loaded_data['metadata']['large_dict']) == 500
    
    @pytest.mark.performance
    def test_concurrent_config_access(self, test_config, temp_directory):
        """Test performance of concurrent configuration access."""
        import threading
        import queue
        
        # Create test configuration file
        config_data = {
            'model_parameters': {
                'alpha': 5e-4,
                'beta': 0.15
            }
        }
        
        config_file = temp_directory / "concurrent_test.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Test concurrent access
        n_threads = 4
        n_operations_per_thread = 50
        results_queue = queue.Queue()
        
        def worker():
            config_manager = ConfigurationManager()
            thread_results = []
            
            for i in range(n_operations_per_thread):
                start_time = time.time()
                params = config_manager.load_from_file(str(config_file))
                end_time = time.time()
                
                thread_results.append({
                    'operation': i,
                    'time': end_time - start_time,
                    'alpha': params.alpha,
                    'beta': params.beta
                })
            
            results_queue.put(thread_results)
        
        # Start threads
        threads = []
        start_time = time.time()
        
        for _ in range(n_threads):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Collect results
        all_results = []
        while not results_queue.empty():
            all_results.extend(results_queue.get())
        
        # Verify results
        assert len(all_results) == n_threads * n_operations_per_thread
        
        # Check performance
        operation_times = [r['time'] for r in all_results]
        avg_operation_time = np.mean(operation_times)
        
        assert avg_operation_time < 0.01, \
            f"Concurrent config access too slow: {avg_operation_time:.6f}s per operation"
        
        # Check that all operations returned correct values
        for result in all_results:
            assert result['alpha'] == 5e-4
            assert result['beta'] == 0.15
    
    @pytest.mark.performance
    def test_config_memory_efficiency(self, test_config):
        """Test memory efficiency of configuration operations."""
        # Measure memory usage
        process = psutil.Process(os.getpid())
        
        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many parameter objects
        n_objects = 500
        params_list = []
        
        tracemalloc.start()
        
        for i in range(n_objects):
            params = ModelParameters(
                alpha=4e-4 * (1 + 0.001 * i),
                beta=0.12 * (1 + 0.001 * i),
                drug_susceptibility_rates={
                    'nivolumab': 0.25 + 0.001 * i,
                    'pembrolizumab': 0.30 + 0.001 * i
                }
            )
            params_list.append(params)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = current_memory - baseline_memory
        peak_memory = peak / 1024 / 1024  # MB
        
        # Memory assertions
        assert memory_used < 50, \
            f"Config objects used too much memory: {memory_used:.2f}MB for {n_objects} objects"
        assert peak_memory < 100, \
            f"Peak memory too high: {peak_memory:.2f}MB"
        
        # Test memory cleanup
        del params_list
        gc.collect()
        
        cleanup_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_retained = cleanup_memory - baseline_memory
        
        assert memory_retained < 10, \
            f"Too much memory retained after cleanup: {memory_retained:.2f}MB"
    
    @pytest.mark.performance
    def test_config_hash_calculation_performance(self, test_config):
        """Test performance of parameter hash calculation."""
        # Create test parameters
        params = ModelParameters(
            alpha=5e-4,
            beta=0.15,
            epsilon=2.5,
            drug_susceptibility_rates={
                'nivolumab': 0.30,
                'pembrolizumab': 0.35
            }
        )
        
        # Test hash calculation performance
        n_hashes = 1000
        
        start_time = time.time()
        for _ in range(n_hashes):
            hash_value = params.calculate_hash()
        end_time = time.time()
        hash_time = end_time - start_time
        avg_hash_time = hash_time / n_hashes
        
        assert avg_hash_time < 0.001, \
            f"Parameter hash calculation too slow: {avg_hash_time:.6f}s per hash"
        
        # Verify hash is consistent
        hash1 = params.calculate_hash()
        hash2 = params.calculate_hash()
        assert hash1 == hash2, "Hash should be consistent"
        
        # Verify hash changes when parameters change
        original_hash = params.calculate_hash()
        params.alpha = 6e-4
        new_hash = params.calculate_hash()
        assert original_hash != new_hash, "Hash should change when parameters change"
    
    @pytest.mark.performance
    def test_config_comparison_performance(self, test_config):
        """Test performance of parameter comparison."""
        # Create test parameters
        params1 = ModelParameters(alpha=5e-4, beta=0.15)
        params2 = ModelParameters(alpha=6e-4, beta=0.15)  # Different alpha
        params3 = ModelParameters(alpha=5e-4, beta=0.15)  # Same as params1
        
        # Test comparison performance
        n_comparisons = 1000
        
        # Compare different parameters
        start_time = time.time()
        for _ in range(n_comparisons):
            differences = params1.compare_parameters(params2)
        end_time = time.time()
        comparison_time = end_time - start_time
        avg_comparison_time = comparison_time / n_comparisons
        
        assert avg_comparison_time < 0.001, \
            f"Parameter comparison too slow: {avg_comparison_time:.6f}s per comparison"
        
        # Verify comparison results
        differences = params1.compare_parameters(params2)
        assert 'alpha' in differences
        assert differences['alpha'] == (5e-4, 6e-4)
        
        # Compare identical parameters
        differences = params1.compare_parameters(params3)
        assert len(differences) == 0