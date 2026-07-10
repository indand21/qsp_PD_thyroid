"""
QSP_PD_Thyroid Testing Framework
=================================

This package contains comprehensive unit tests, integration tests, and performance tests
for the QSP_PD_Thyroid_Final project.

Test Categories:
    - Unit tests for individual components
    - Integration tests for system interactions
    - Performance tests for benchmarking
    - Fixtures and utilities for test support

Running Tests:
    pytest tests/                    # Run all tests
    pytest tests/unit/              # Run unit tests only
    pytest tests/integration/       # Run integration tests only
    pytest tests/performance/       # Run performance tests only
    pytest -m "not slow"            # Skip slow tests
    pytest -m "unit"                # Run only unit tests
    pytest -m "integration"         # Run only integration tests
    pytest -m "performance"         # Run only performance tests
"""

import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure test environment
os.environ["QSP_TEST_MODE"] = "true"
os.environ["QSP_LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests

__version__ = "1.0.0"