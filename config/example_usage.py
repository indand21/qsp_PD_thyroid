#!/usr/bin/env python3
"""
Configuration System Example Usage
=================================

This script demonstrates how to use the QSP_PD_Thyroid configuration management system.
It shows loading, modifying, validating, and saving parameters, as well as versioning
and change logging functionality.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add the parent directory to the path to import config modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    ModelParameters, 
    NivolumabParameters, 
    PembrolizumabParameters,
    ConfigurationManager,
    ParameterVersion,
    ParameterChangeLog,
    ChangeType
)


def main():
    """Main example function."""
    print("QSP_PD_Thyroid Configuration Management System Example")
    print("=" * 60)
    
    # Example 1: Basic parameter creation and validation
    print("\n1. Basic Parameter Creation and Validation")
    print("-" * 40)
    
    # Create model parameters
    params = ModelParameters()
    print(f"Created ModelParameters with {len(params.__fields__)} fields")
    
    # Validate parameters
    errors = params.validate_parameters()
    if errors:
        print(f"Validation errors: {errors}")
    else:
        print("All parameters are valid!")
    
    # Example 2: Drug-specific parameters
    print("\n2. Drug-Specific Parameters")
    print("-" * 40)
    
    # Create nivolumab parameters
    nivo_params = NivolumabParameters()
    print(f"Nivolumab Kd: {nivo_params.Kd} nM")
    print(f"Nivolumab potency: {nivo_params.potency}")
    print(f"Nivolumab susceptibility rate: {nivo_params.susceptibility_rate}")
    
    # Create pembrolizumab parameters
    pembro_params = PembrolizumabParameters()
    print(f"Pembrolizumab Kd: {pembro_params.Kd} nM")
    print(f"Pembrolizumab potency: {pembro_params.potency}")
    print(f"Pembrolizumab susceptibility rate: {pembro_params.susceptibility_rate}")
    
    # Example 3: Configuration Manager
    print("\n3. Configuration Manager")
    print("-" * 40)
    
    # Create configuration manager
    config_manager = ConfigurationManager(
        config_dir="config",
        auto_backup=True,
        enable_change_log=True,
        enable_versioning=True
    )
    
    # Load nivolumab configuration
    try:
        loaded_nivo_params = config_manager.load_from_file(
            "config/nivolumab_config.yaml",
            author="Example User"
        )
        print(f"Loaded nivolumab configuration: {loaded_nivo_params.__class__.__name__}")
        print(f"Nivolumab Kd from file: {loaded_nivo_params.Kd_nivo_PD1} nM")
    except Exception as e:
        print(f"Error loading configuration: {e}")
    
    # Example 4: Parameter Modification and Validation
    print("\n4. Parameter Modification and Validation")
    print("-" * 40)
    
    # Modify some parameters
    original_alpha = params.alpha
    params.alpha = 0.0005
    params.beta = 0.13
    
    print(f"Changed alpha from {original_alpha} to {params.alpha}")
    print(f"Changed beta to {params.beta}")
    
    # Validate modified parameters
    errors = params.validate_parameters()
    if errors:
        print(f"Validation errors after modification: {errors}")
    else:
        print("Modified parameters are still valid!")
    
    # Example 5: Parameter Comparison
    print("\n5. Parameter Comparison")
    print("-" * 40)
    
    # Compare original and modified parameters
    original_params = ModelParameters()
    differences = params.compare_parameters(original_params)
    
    print(f"Number of different parameters: {len(differences)}")
    for param_name, (old_val, new_val) in differences.items():
        print(f"  {param_name}: {old_val} -> {new_val}")
    
    # Example 6: Version Management
    print("\n6. Version Management")
    print("-" * 40)
    
    # Create versions
    version1 = config_manager.create_version(
        parameters=original_params,
        version="v1.0.0",
        author="Example User",
        description="Original parameters",
        tags=["baseline"]
    )
    
    version2 = config_manager.create_version(
        parameters=params,
        version="v1.1.0",
        author="Example User",
        description="Modified T-cell dynamics",
        tags=["modified", "optimization"],
        parent_version="v1.0.0"
    )
    
    print(f"Created versions: v1.0.0 and v1.1.0")
    
    # Compare versions
    comparison = config_manager.compare_versions("v1.0.0", "v1.1.0")
    print(f"Version similarity score: {comparison['similarity_score']:.2f}")
    print(f"Different parameters: {comparison['different_parameters']}")
    
    # Example 7: Change Logging
    print("\n7. Change Logging")
    print("-" * 40)
    
    # Log some manual changes
    config_manager.change_log.log_parameter_update(
        parameter_name="gamma",
        old_value=original_params.gamma,
        new_value=1.1,
        parameter_type="ModelParameters",
        author="Example User",
        reason="Testing change logging"
    )
    
    # Generate change report
    report = config_manager.change_log.generate_report()
    print(f"Total changes logged: {report['total_changes']}")
    print(f"Changes by type: {report['changes_by_type']}")
    
    # Example 8: Saving Configurations
    print("\n8. Saving Configurations")
    print("-" * 40)
    
    # Save modified parameters
    output_file = "config/example_modified_config.yaml"
    config_manager.save_to_file(
        parameters=params,
        filepath=output_file,
        author="Example User",
        description="Example modified configuration"
    )
    print(f"Saved modified configuration to {output_file}")
    
    # Example 9: Parameter Information
    print("\n9. Parameter Information")
    print("-" * 40)
    
    # Get information about specific parameters
    alpha_info = params.get_parameter_info("alpha")
    print(f"Alpha parameter info: {alpha_info}")
    
    # Get drug-specific parameters
    nivo_drug_params = nivo_params.get_drug_parameters("nivolumab")
    print(f"Nivolumab drug parameters: {nivo_drug_params}")
    
    # Example 10: Configuration Conversion
    print("\n10. Configuration Conversion")
    print("-" * 40)
    
    # Convert between parameter types
    converted_params = config_manager.convert_parameters(
        parameters=nivo_params,
        target_type="ModelParameters"
    )
    print(f"Converted {nivo_params.__class__.__name__} to {converted_params.__class__.__name__}")
    
    # Example 11: Configuration Report
    print("\n11. Configuration Report")
    print("-" * 40)
    
    # Generate comprehensive report
    report = config_manager.generate_report()
    print(f"Configuration directory: {report['config_directory']}")
    print(f"Configuration files: {len(report['configuration_files'])}")
    print(f"Auto backup enabled: {report['auto_backup']}")
    print(f"Change log enabled: {report['change_log_enabled']}")
    print(f"Versioning enabled: {report['versioning_enabled']}")
    
    if 'version_history' in report:
        print(f"Total versions: {report['version_history']['total_versions']}")
        print(f"Latest version: {report['version_history']['latest_version']}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("Check the 'config' directory for generated files.")


if __name__ == "__main__":
    main()