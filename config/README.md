# QSP_PD_Thyroid Configuration Management System

## Overview

This configuration management system provides a comprehensive framework for managing parameters in the QSP_PD_Thyroid_Final project. It replaces hard-coded parameters with a flexible, validated, and version-controlled configuration system.

## Features

- **Parameter Validation**: Uses Pydantic for type checking and range validation
- **Drug-Specific Parameters**: Pre-configured parameter sets for nivolumab, pembrolizumab, atezolizumab, and durvalumab
- **Configuration File Support**: Load and save parameters in YAML or JSON format
- **Parameter Versioning**: Track parameter changes and maintain version history
- **Change Logging**: Comprehensive audit trail of all parameter modifications
- **Backward Compatibility**: Maintains compatibility with existing `FinalModelParameters` class

## Quick Start

### Basic Usage

```python
from config import ModelParameters, ConfigurationManager

# Create configuration manager
config_manager = ConfigurationManager()

# Load drug-specific configuration
nivolumab_params = config_manager.load_from_file("config/nivolumab_config.yaml")

# Create parameters programmatically
params = ModelParameters()
params.alpha = 0.0005  # Modify T-cell expansion rate

# Save configuration
config_manager.save_to_file(params, "my_config.yaml", author="Researcher")
```

### Drug-Specific Parameters

```python
from config import NivolumabParameters, PembrolizumabParameters

# Create nivolumab-specific parameters
nivo_params = NivolumabParameters()
print(f"Nivolumab Kd: {nivo_params.Kd} nM")
print(f"Susceptibility rate: {nivo_params.susceptibility_rate}")

# Create pembrolizumab-specific parameters
pembro_params = PembrolizumabParameters()
print(f"Pembrolizumab potency: {pembro_params.potency}")
```

### Parameter Validation

```python
# Validate parameters
errors = params.validate_parameters()
if errors:
    print("Validation errors:", errors)
else:
    print("Parameters are valid")

# Get parameter information
param_info = params.get_parameter_info("alpha")
print(f"Parameter info: {param_info}")
```

## Configuration File Format

### YAML Structure

```yaml
parameter_type: NivolumabParameters
version: "1.0.0"
description: "Nivolumab parameters for hypothyroidism modeling"
author: "QSP Team"

# Drug-specific parameters
Kd_nivo_PD1: 2.6
potency: 1.0
susceptibility_rate: 0.25

# Model parameters
alpha: 0.0004
beta: 0.12
# ... other parameters
```

### JSON Structure

```json
{
  "parameter_type": "NivolumabParameters",
  "version": "1.0.0",
  "description": "Nivolumab parameters for hypothyroidism modeling",
  "author": "QSP Team",
  "Kd_nivo_PD1": 2.6,
  "potency": 1.0,
  "susceptibility_rate": 0.25,
  "alpha": 0.0004,
  "beta": 0.12
}
```

## Parameter Classes

### BaseParameters

Abstract base class providing common functionality:
- Parameter validation
- Serialization/deserialization
- Hash calculation for versioning
- Metadata tracking

### ModelParameters

Main model parameters class containing all QSP model parameters extracted from the original `FinalModelParameters` class.

### Drug-Specific Classes

- `NivolumabParameters`: Nivolumab-specific parameters
- `PembrolizumabParameters`: Pembrolizumab-specific parameters
- `AtezolizumabParameters`: Atezolizumab-specific parameters
- `DurvalumabParameters`: Durvalumab-specific parameters

## Parameter Versioning

### Creating Versions

```python
from config import ParameterVersion

# Create a new version
version = config_manager.create_version(
    parameters=nivolumab_params,
    version="v1.1.0",
    author="Researcher",
    description="Updated T-cell dynamics",
    tags=["optimization", "validation"]
)
```

### Comparing Versions

```python
# Compare two versions
comparison = config_manager.compare_versions("v1.0.0", "v1.1.0")
print(f"Similarity score: {comparison['similarity_score']}")
print(f"Different parameters: {comparison['different_parameters']}")
```

### Version History

```python
# Get version history
history = config_manager.get_version_history("NivolumabParameters")
for version in history:
    print(f"Version {version.version}: {version.description}")
```

## Change Logging

### Automatic Logging

```python
# Enable automatic change logging
config_manager.change_log.set_auto_logging(True)

# Modify parameters (automatically logged)
params.alpha = 0.0005
params.beta = 0.13
```

### Manual Logging

```python
# Log manual changes
config_manager.change_log.log_parameter_update(
    parameter_name="alpha",
    old_value=0.0004,
    new_value=0.0005,
    parameter_type="ModelParameters",
    author="Researcher",
    reason="Optimization for better fit"
)
```

### Change Reports

```python
# Generate change report
report = config_manager.change_log.generate_report()
print(f"Total changes: {report['total_changes']}")
print(f"Changes by type: {report['changes_by_type']}")
```

## Configuration Management

### Loading Configurations

```python
# Load from file
params = config_manager.load_from_file("config/nivolumab_config.yaml")

# Load with validation
params = config_manager.load_from_file(
    "config/nivolumab_config.yaml",
    validate=True,
    author="Researcher"
)
```

### Saving Configurations

```python
# Save to file
config_manager.save_to_file(
    params,
    "config/my_nivolumab_config.yaml",
    author="Researcher",
    description="Custom nivolumab configuration"
)

# Save with backup
config_manager.save_to_file(
    params,
    "config/nivolumab_config.yaml",
    backup=True
)
```

### Converting Parameters

```python
# Convert between parameter types
nivolumab_params = NivolumabParameters()
model_params = config_manager.convert_parameters(
    nivolumab_params,
    "ModelParameters"
)
```

## Integration with Existing Code

### Backward Compatibility

The configuration system maintains backward compatibility with the existing `FinalModelParameters` class:

```python
# Use with existing model
from qsp_model_final import FinalQSPModel

# Load configuration
config_manager = ConfigurationManager()
params = config_manager.load_from_file("config/nivolumab_config.yaml")

# Create model with configuration
model = FinalQSPModel()
model.params = params  # Replace with new parameters
```

### Migration Guide

1. Replace hard-coded parameters with configuration loading
2. Update parameter access to use new parameter classes
3. Add validation checks where needed
4. Implement change logging for parameter modifications

## Best Practices

1. **Always validate parameters** before using them in simulations
2. **Use versioning** when making significant parameter changes
3. **Document changes** with descriptive reasons
4. **Back up configurations** before making modifications
5. **Use drug-specific parameter classes** when working with specific drugs
6. **Regularly export change logs** for audit purposes

## Troubleshooting

### Common Issues

1. **Validation Errors**: Check parameter ranges and types
2. **File Loading Errors**: Verify file format and path
3. **Version Conflicts**: Ensure version compatibility
4. **Import Errors**: Check package installation

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
config_manager = ConfigurationManager()
```

## API Reference

### ConfigurationManager

- `load_from_file(filepath, validate=True)`: Load parameters from file
- `save_to_file(parameters, filepath, backup=True)`: Save parameters to file
- `create_version(parameters, version, author=None)`: Create parameter version
- `compare_versions(version1, version2)`: Compare two versions
- `validate_parameters(parameters)`: Validate parameters

### BaseParameters

- `validate_parameters()`: Validate parameter values
- `calculate_hash()`: Calculate parameter hash
- `compare_parameters(other)`: Compare with another parameter set
- `to_dict(include_metadata=True)`: Convert to dictionary
- `from_dict(data)`: Create from dictionary

### ParameterVersion

- `compare_with(other)`: Compare with another version
- `is_compatible_with(other)`: Check compatibility
- `to_dict()`: Convert to dictionary
- `from_dict(data)`: Create from dictionary

### ParameterChangeLog

- `log_parameter_update(...)`: Log parameter update
- `get_changes_by_parameter(name)`: Get changes for parameter
- `generate_report(...)`: Generate change report
- `save_to_file(filepath)`: Save to file
- `load_from_file(filepath)`: Load from file