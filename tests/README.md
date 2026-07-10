# QSP Thyroid Model Testing Framework

This directory contains the comprehensive testing framework for the QSP Thyroid Model. The framework is designed to ensure the reliability, performance, and correctness of the model through various types of tests.

## Directory Structure

```
tests/
├── __init__.py                 # Package initialization
├── conftest.py                 # Pytest configuration and fixtures
├── README.md                   # This file
├── fixtures/                   # Test fixtures and data generators
│   ├── __init__.py
│   └── data_generators.py      # Functions to generate test data
├── unit/                       # Unit tests
│   ├── __init__.py
│   ├── test_config_base_parameters.py
│   ├── test_config_drug_parameters.py
│   ├── test_config_manager.py
│   ├── test_config_model_parameters.py
│   ├── test_qsp_model_final.py
│   ├── test_utils_error_handler.py
│   ├── test_utils_exceptions.py
│   └── test_utils_validators.py
├── integration/                # Integration tests
│   ├── __init__.py
│   ├── test_config_model_integration.py
│   ├── test_end_to_end_workflows.py
│   └── test_error_handling_integration.py
├── performance/                # Performance tests
│   ├── __init__.py
│   ├── test_config_performance.py
│   └── test_simulation_performance.py
└── utils/                      # Test utilities
    ├── __init__.py
    ├── assertion_helpers.py    # Custom assertion functions
    └── mock_classes.py         # Mock classes for testing
```

## Test Types

### Unit Tests

Unit tests focus on testing individual components in isolation. They are located in the `unit/` directory and cover:

- Configuration system (base parameters, model parameters, drug parameters, config manager)
- Error handling system (exceptions, error handlers, validators)
- Core model functions (FinalQSPModel, simulation functions)

### Integration Tests

Integration tests verify that different components work together correctly. They are located in the `integration/` directory and cover:

- Configuration and model integration
- Error handling throughout the system
- End-to-end workflows

### Performance Tests

Performance tests ensure that the system meets performance requirements. They are located in the `performance/` directory and cover:

- Simulation performance
- Configuration system performance
- Memory efficiency
- Scalability

## Running Tests

### Running All Tests

To run all tests:

```bash
pytest tests/
```

### Running Specific Test Types

To run only unit tests:

```bash
pytest tests/unit/
```

To run only integration tests:

```bash
pytest tests/integration/
```

To run only performance tests:

```bash
pytest tests/performance/ -m performance
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest tests/ --cov=utils --cov=config --cov-report=html --cov-report=term-missing
```

### Running Tests in Parallel

To run tests in parallel for faster execution:

```bash
pytest tests/ -n auto
```

### Running Performance Tests

To run performance tests with benchmarking:

```bash
pytest tests/performance/ -m performance --benchmark-only
```

## Test Configuration

The test configuration is defined in `conftest.py` and includes:

- Fixtures for common test data
- Configuration for test execution
- Markers for different test types

### Test Markers

- `@pytest.mark.unit`: Marks unit tests
- `@pytest.mark.integration`: Marks integration tests
- `@pytest.mark.performance`: Marks performance tests
- `@pytest.mark.slow`: Marks tests that take a long time to run

### Test Fixtures

Common fixtures include:

- `qsp_model`: Creates a standard QSP model for testing
- `sample_model_parameters`: Creates sample model parameters
- `temp_directory`: Creates a temporary directory for file operations
- `test_config`: Provides test configuration values

## Test Data Generation

The `fixtures/data_generators.py` module provides functions to generate test data:

- `generate_patient_data()`: Generates patient data for population simulations
- `generate_time_series_data()`: Generates time series data for testing
- `generate_config_variations()`: Generates parameter variations for testing
- `generate_population_simulation_results()`: Generates mock simulation results

## Test Utilities

The `utils/` directory contains utility classes and functions for testing:

- `assertion_helpers.py`: Custom assertion functions for complex validations
- `mock_classes.py`: Mock classes for external dependencies

## Continuous Integration

The testing framework is integrated with GitHub Actions for continuous integration:

- `ci.yml`: Main CI workflow that runs on every push and pull request
- `performance.yml`: Performance testing workflow that runs on a schedule

### CI Workflow

The main CI workflow:

1. Sets up the Python environment
2. Installs dependencies
3. Runs linting with flake8
4. Runs unit tests with coverage
5. Runs integration tests
6. Runs performance tests
7. Uploads coverage to Codecov
8. Uploads benchmark results

### Performance Workflow

The performance workflow:

1. Runs performance benchmarks
2. Profiles memory usage
3. Tests scalability with different population sizes
4. Checks for performance regressions
5. Notifies on performance test results

## Writing Tests

### Unit Test Example

```python
import pytest
from config.model_parameters import ModelParameters

class TestModelParameters:
    def test_default_initialization(self):
        """Test default parameter initialization."""
        params = ModelParameters()
        
        assert params.alpha == 4e-4
        assert params.beta == 0.12
        assert params.epsilon == 2.0
```

### Integration Test Example

```python
import pytest
from qsp_model_final import FinalQSPModel, final_simulate_patient

class TestConfigModelIntegration:
    def test_model_with_custom_config(self):
        """Test model with custom configuration."""
        custom_params = ModelParameters(alpha=5e-4, beta=0.15)
        model = FinalQSPModel(parameters=custom_params)
        
        assert model.params.alpha == 5e-4
        assert model.params.beta == 0.15
```

### Performance Test Example

```python
import pytest
import time
from qsp_model_final import FinalQSPModel, final_simulate_patient

@pytest.mark.performance
class TestSimulationPerformance:
    def test_single_simulation_performance(self, qsp_model):
        """Test performance of single patient simulation."""
        t_span = (0, 180)
        
        start_time = time.time()
        results = final_simulate_patient(qsp_model, t_span=t_span, drug_type='nivolumab')
        end_time = time.time()
        
        run_time = end_time - start_time
        assert run_time < 5.0, f"Simulation took {run_time:.2f}s, threshold is 5.0s"
```

## Test Coverage

The testing framework aims for high test coverage across all components. Current coverage targets:

- Configuration system: >90%
- Error handling system: >90%
- Core model functions: >85%
- Overall: >80%

Coverage reports are generated during CI runs and can be viewed locally:

```bash
pytest tests/ --cov=utils --cov=config --cov-report=html
# Open htmlcov/index.html in a browser
```

## Debugging Tests

### Running Tests in Debug Mode

To run tests with verbose output and stop on first failure:

```bash
pytest tests/ -v -x
```

### Running a Specific Test

To run a specific test:

```bash
pytest tests/unit/test_config_model_parameters.py::TestModelParameters::test_default_initialization -v
```

### Debugging with pdb

To run tests with the Python debugger:

```bash
pytest tests/ --pdb
```

## Best Practices

### Test Organization

- Group related tests in classes
- Use descriptive test names
- Keep tests focused on a single behavior
- Use fixtures for common setup

### Test Data

- Use fixtures for consistent test data
- Generate data programmatically when possible
- Avoid hardcoding specific values in tests

### Assertions

- Use specific assertions for clarity
- Include helpful error messages
- Test both positive and negative cases

### Performance Tests

- Set appropriate performance thresholds
- Measure multiple runs for consistency
- Test with different input sizes

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the package is installed in development mode (`pip install -e .`)
2. **Fixture Not Found**: Check that fixtures are defined in `conftest.py`
3. **Test Timeouts**: Increase timeout values for slow tests
4. **Memory Issues**: Reduce test data size or add garbage collection

### Getting Help

If you encounter issues with the testing framework:

1. Check the pytest documentation: https://docs.pytest.org/
2. Review existing tests for examples
3. Ask for help in project discussions or issues

## Contributing

When contributing new code:

1. Write tests for new functionality
2. Ensure all tests pass
3. Maintain or improve test coverage
4. Add performance tests for critical paths
5. Update documentation as needed

## Future Enhancements

Potential improvements to the testing framework:

1. Property-based testing with hypothesis
2. Visual regression testing for plots
3. Automated test data generation
4. More comprehensive performance monitoring
5. Integration with external testing services