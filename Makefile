# QSP_PD_Thyroid_Final Makefile
# Provides convenient commands for testing and development

.PHONY: help install install-dev test test-cov lint format build docker deploy clean

# Default target
help:
	@echo "QSP_PD_Thyroid_Final - Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  install      Install the package and dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test         Run tests"
	@echo "  test-cov     Run tests with coverage"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo ""
	@echo "Build and Deploy:"
	@echo "  build        Build the package"
	@echo "  docker       Build Docker image"
	@echo "  deploy       Deploy to production"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        Clean all build artifacts"

# Installation
install:
	pip install -e .

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .
	pre-commit install

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

test-integration:
	pytest tests/integration/ -v

test-performance:
	pytest tests/performance/ -v

# Code quality
lint:
	flake8 config/ utils/
	mypy config/ utils/ --ignore-missing-imports
	pydocstyle config/ utils/

format:
	black config/ utils/
	isort config/ utils/

# Build
build:
	python setup.py sdist bdist_wheel

build-docker:
	docker build -t qsp-thyroid-model .

build-docker-dev:
	docker build --target development -t qsp-thyroid-model:dev .

build-docker-prod:
	docker build --target production -t qsp-thyroid-model:latest .

# Development
dev-server:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

# Data and experiments
run-examples:
	python -m examples.basic_usage
	python -m examples.population_analysis
	python -m examples.drug_comparison

# Performance
benchmark:
	python -m pytest tests/performance/ --benchmark-only

# Deployment
deploy-pypi:
	python -m twine upload dist/*

deploy-docker:
	docker push qsp-thyroid-model:latest

# Maintenance
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf logs/

clean-all: clean
	docker system prune -f

# Validation
validate-env:
	python -c "
import sys
import importlib
required_packages = ['numpy', 'pandas', 'scipy', 'matplotlib', 'seaborn']
missing = []
for pkg in required_packages:
    try:
        importlib.import_module(pkg)
    except ImportError:
        missing.append(pkg)
if missing:
    print(f'Missing packages: {missing}')
    sys.exit(1)
else:
    print('All required packages are installed')
"

validate-model:
	python -c "
from qsp_expanded import simulate_expanded_patient
df = simulate_expanded_patient('nivolumab')
print(f'Model validation passed: {len(df)} time points')
"

# Quick development cycle
dev: install-dev format lint test-cov

# Full validation pipeline
validate: validate-env validate-model test lint
	@echo "All validation checks passed!"

# Release preparation
release-prep: clean format lint test-cov build
	@echo "Release preparation completed!"

# Docker development
docker-dev:
	docker run --rm -it -v $(PWD):/workspace -p 8888:8888 qsp-thyroid-model:dev

docker-prod:
	docker run --rm -v $(PWD):/workspace qsp-thyroid-model:latest

# Performance monitoring
monitor-resources:
	python -c "
import psutil
import time
while True:
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    print(f'CPU: {cpu:.1f}%, Memory: {memory:.1f}%')
    time.sleep(5)
"
