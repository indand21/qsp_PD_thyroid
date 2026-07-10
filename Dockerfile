# QSP_PD_Thyroid_Final Docker Container
# Multi-stage build for optimized production and development images

# Base stage - Python environment
FROM python:3.9-slim as base

# Set environment variables for reproducibility
ENV PYTHONHASHSEED=0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV QSP_REPRODUCIBLE_MODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libffi-dev \
    libhdf5-dev \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt .
COPY requirements-dev.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Development stage - Includes development tools
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install pre-commit hooks
RUN pre-commit install

# Copy source code
COPY . .

# Install the project in development mode
RUN pip install -e .

# Set up directories for experiments and data
RUN mkdir -p /app/experiments /app/data /app/reports /app/logs

# Expose Jupyter port
EXPOSE 8888

# Default command for development
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]

# Production stage - Optimized for production use
FROM base as production

# Copy only necessary files for production
COPY setup.py .
COPY README.md .
COPY config/ ./config/
COPY data/ ./data/
COPY utils/ ./utils/
COPY performance/ ./performance/
COPY qsp_expanded/ ./qsp_expanded/
COPY scripts/ ./scripts/

# Install the project
RUN pip install -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash qsp_user && \
    chown -R qsp_user:qsp_user /app
USER qsp_user

# Set up directories
RUN mkdir -p /app/experiments /app/data /app/reports /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import qsp_expanded; print('OK')" || exit 1

# Default command for production
CMD ["python", "-c", "print('QSP_PD_Thyroid_Final container is ready')"]

# Testing stage - For automated testing
FROM development as testing

# Copy test files
COPY tests/ ./tests/
COPY pytest.ini .

# Run tests
RUN pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Documentation stage - For building documentation
FROM development as documentation

# Copy documentation files
COPY docs/ ./docs/
COPY docs/conf.py .

# Install documentation dependencies
RUN pip install --no-cache-dir sphinx-rtd-theme myst-parser

# Build documentation
RUN cd docs && make html

# Expose documentation port
EXPOSE 8000

# Serve documentation
CMD ["python", "-m", "http.server", "8000", "--directory", "docs/_build/html"]