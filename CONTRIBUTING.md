# Contributing to QSP_PD_Thyroid_Final

Thank you for your interest in contributing to the QSP_PD_Thyroid_Final project! This guide provides information on how to contribute to this quantitative systems pharmacology model for thyroid dysfunction.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Contributing Guidelines](#contributing-guidelines)
- [Documentation](#documentation)
- [Testing](#testing)
- [Code Review Process](#code-review-process)
- [Community](#community)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html). Please read and follow these guidelines to ensure a welcoming and inclusive environment for all contributors.

## Getting Started

### Prerequisites

- Python 3.8 or later
- Git
- Basic knowledge of Python, scientific computing, and pharmacology

### Setup Instructions

1. **Fork the Repository**
   ```bash
   # Fork the repository on GitHub, then clone your fork
   git clone https://github.com/your-username/QSP_PD_Thyroid_Final.git
   cd QSP_PD_Thyroid_Final
   ```

2. **Set Up Development Environment**
   ```bash
   # Create conda environment
   conda env create -f environment.yml
   conda activate qsp_thyroid
   
   # Or use pip
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. **Set Up Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Verify Installation**
   ```bash
   make validate-quickstart
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Follow the coding standards outlined below
- Write tests for new functionality
- Update documentation as needed
- Keep commits small and focused

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run linting
make lint

# Format code
make format
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new drug model for pembrolizumab"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub with a clear description of your changes.

## Contributing Guidelines

### Types of Contributions

#### Bug Fixes
- Check existing issues for related bug reports
- Create a new issue if none exists
- Include steps to reproduce the bug
- Add tests that verify the fix

#### New Features
- Discuss major changes in an issue first
- Follow the existing code patterns and architecture
- Include comprehensive tests and documentation
- Consider backward compatibility

#### Documentation
- Improve existing documentation
- Add examples and tutorials
- Fix typos and clarify explanations
- Ensure all public APIs are documented

#### Performance Improvements
- Benchmark before and after changes
- Include performance tests
- Document any trade-offs

### Code Standards

#### Python Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://isort.readthedocs.io/) for import sorting
- Maximum line length: 88 characters

#### Type Hints
- Include type hints for all public functions and methods
- Use `typing` module for type annotations
- Document complex types with docstrings

#### Docstrings
- Use Google-style docstrings
- Include parameter types, return types, and descriptions
- Add examples for complex functions
- Document all public classes and methods

Example:
```python
def simulate_patient(
    model: FinalQSPModel,
    drug_type: str,
    t_span: Tuple[float, float],
    evaluation_times: Optional[np.ndarray] = None
) -> pd.DataFrame:
    """Simulate thyroid dynamics for a single patient.
    
    Args:
        model: QSP model instance with patient parameters
        drug_type: Type of immune checkpoint inhibitor
        t_span: Simulation time span (start, end) in days
        evaluation_times: Optional specific time points for evaluation
        
    Returns:
        DataFrame containing simulation results with time series data
        
    Raises:
        ValueError: If drug_type is not supported
        SimulationError: If simulation fails to converge
        
    Example:
        >>> model = FinalQSPModel(patient_id="001", drug_type="nivolumab")
        >>> results = simulate_patient(model, "nivolumab", (0, 180))
        >>> print(results.head())
    """
```

#### Naming Conventions
- **Classes**: `PascalCase` (e.g., `FinalQSPModel`)
- **Functions**: `snake_case` (e.g., `simulate_patient`)
- **Variables**: `snake_case` (e.g., `patient_id`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIME_SPAN`)
- **Private methods**: `_snake_case` (e.g., `_validate_parameters`)

#### Error Handling
- Use specific exception types
- Include informative error messages
- Handle expected errors gracefully
- Log errors with appropriate levels

#### Logging
- Use the `utils.logger` module
- Include context in log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Avoid logging sensitive information

### Project Structure

```
QSP_PD_Thyroid_Final/
├── model/                    # Core model components
│   ├── __init__.py
│   ├── final_model.py        # Main model implementation
│   ├── pk_model.py           # Pharmacokinetic models
│   ├── pd_model.py           # Pharmacodynamic models
│   └── thyroid_model.py      # Thyroid-specific models
├── config/                   # Configuration management
├── data/                     # Data handling and storage
├── utils/                    # Utility functions
├── performance/              # Performance optimization
├── tests/                    # Test suite
├── docs/                     # Documentation
├── examples/                 # Example scripts and notebooks
└── reproducibility/          # Reproducibility tools
```

## Documentation

### Documentation Types

#### API Documentation
- Automatically generated from docstrings
- Include in `docs/api/` section
- Follow existing documentation patterns

#### User Documentation
- Installation and setup guides
- Tutorials and examples
- Troubleshooting guides
- Located in `docs/user_guide/`

#### Scientific Documentation
- Model descriptions and assumptions
- Mathematical formulations
- Validation studies
- Located in `docs/scientific/`

#### Developer Documentation
- Architecture overview
- Contributing guidelines
- Code style guide
- Located in `docs/developer/`

### Writing Documentation

#### Sphinx Documentation
- Use reStructuredText (.rst) format
- Follow existing style and structure
- Include cross-references and citations
- Test documentation builds locally

#### Code Examples
- Include in docstrings and separate example files
- Test all examples automatically
- Use realistic but simple data
- Explain each step clearly

#### Mathematical Content
- Use LaTeX for mathematical expressions
- Define all variables and parameters
- Include units and ranges
- Reference relevant literature

## Testing

### Test Structure

```
tests/
├── unit/                     # Unit tests
├── integration/              # Integration tests
├── performance/              # Performance tests
├── fixtures/                 # Test data and utilities
└── conftest.py              # Pytest configuration
```

### Writing Tests

#### Unit Tests
- Test individual functions and classes
- Use descriptive test names
- Test edge cases and error conditions
- Mock external dependencies

Example:
```python
def test_simulate_patient_with_valid_input():
    """Test patient simulation with valid parameters."""
    model = FinalQSPModel(patient_id="test", drug_type="nivolumab")
    results = simulate_patient(model, "nivolumab", (0, 10))
    
    assert isinstance(results, pd.DataFrame)
    assert len(results) > 0
    assert "TSH" in results.columns
    assert "time" in results.columns
```

#### Integration Tests
- Test component interactions
- Use real data when appropriate
- Test complete workflows
- Verify end-to-end functionality

#### Performance Tests
- Benchmark critical functions
- Test with realistic data sizes
- Monitor memory usage
- Compare against baseline performance

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-performance

# Run with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_model.py -v
```

### Test Coverage

- Aim for >80% code coverage
- Focus on critical paths
- Review uncovered code
- Add tests for missing coverage

## Code Review Process

### Pull Request Guidelines

#### Before Submitting
- Ensure all tests pass
- Update documentation
- Follow code style guidelines
- Include tests for new functionality

#### Pull Request Template
```markdown
## Description
Brief description of changes and motivation.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

#### Review Process
1. **Automated Checks**: CI/CD pipeline runs tests and linting
2. **Peer Review**: At least one maintainer reviews the changes
3. **Feedback**: Address reviewer comments and suggestions
4. **Approval**: Merge after approval and all checks pass

### Review Guidelines for Reviewers

- Focus on code quality, logic, and design
- Provide constructive feedback
- Check for test coverage
- Verify documentation updates
- Consider performance implications

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Email**: Direct contact for maintainers

### Getting Help

- Check existing documentation and issues
- Search for similar problems
- Provide minimal reproducible examples
- Include environment details

### Release Process

1. **Preparation**: Update version, changelog, and documentation
2. **Testing**: Complete testing on multiple platforms
3. **Review**: Final code review and approval
4. **Release**: Create GitHub release and publish to PyPI
5. **Announcement**: Notify community of new release

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Documentation acknowledgments
- GitHub contributor statistics

Thank you for contributing to the QSP_PD_Thyroid_Final project!

---

## Additional Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [Scientific Python Development](https://scientific-python.org/)
- [Open Source Guides](https://opensource.guide/)
- [Contributor Covenant](https://www.contributor-covenant.org/)

For questions about contributing, please open an issue or contact the maintainers.