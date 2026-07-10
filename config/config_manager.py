"""
Configuration Manager Module
============================

This module provides the ConfigurationManager class for handling
configuration file operations including loading, saving, and validation.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Type
from datetime import datetime
import logging

from .base_parameters import BaseParameters
from .model_parameters import ModelParameters
from .drug_parameters import (
    NivolumabParameters,
    PembrolizumabParameters,
    AtezolizumabParameters,
    DurvalumabParameters,
    DRUG_PARAMETER_CLASSES
)
from .parameter_version import ParameterVersion, VersionHistory
from .change_log import ParameterChangeLog, ChangeType

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """
    Configuration manager for handling parameter files and operations.
    
    This class provides functionality to:
    - Load and save configuration files (YAML and JSON)
    - Validate parameters
    - Track parameter versions and changes
    - Manage configuration history
    - Convert between different parameter formats
    """
    
    def __init__(self, 
                 config_dir: Optional[str] = None,
                 auto_backup: bool = True,
                 enable_change_log: bool = True,
                 enable_versioning: bool = True):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory to store configuration files
            auto_backup: Whether to automatically backup configurations
            enable_change_log: Whether to enable change logging
            enable_versioning: Whether to enable version tracking
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        self.auto_backup = auto_backup
        self.enable_change_log = enable_change_log
        self.enable_versioning = enable_versioning
        
        # Initialize change log and version history
        self.change_log = ParameterChangeLog() if enable_change_log else None
        self.version_history = VersionHistory() if enable_versioning else None
        
        # Parameter class mapping
        self.parameter_classes = {
            'ModelParameters': ModelParameters,
            'NivolumabParameters': NivolumabParameters,
            'PembrolizumabParameters': PembrolizumabParameters,
            'AtezolizumabParameters': AtezolizumabParameters,
            'DurvalumabParameters': DurvalumabParameters
        }
        
        # Supported file formats
        self.supported_formats = {'.yaml', '.yml', '.json'}
        
        logger.info(f"Configuration manager initialized with config directory: {self.config_dir}")
    
    def load_from_file(self, 
                      filepath: Union[str, Path],
                      validate: bool = True,
                      author: Optional[str] = None) -> BaseParameters:
        """
        Load parameters from a configuration file.
        
        Args:
            filepath: Path to the configuration file
            validate: Whether to validate parameters after loading
            author: Author name for change logging
            
        Returns:
            Loaded BaseParameters instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
            ValidationError: If validation fails
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        if filepath.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {filepath.suffix}. "
                           f"Supported formats: {self.supported_formats}")
        
        # Read file content
        with open(filepath, 'r') as f:
            if filepath.suffix.lower() in {'.yaml', '.yml'}:
                data = yaml.safe_load(f)
            else:  # JSON
                data = json.load(f)
        
        # Determine parameter class
        param_type = data.get('parameter_type', 'ModelParameters')
        if param_type not in self.parameter_classes:
            raise ValueError(f"Unknown parameter type: {param_type}")
        
        param_class = self.parameter_classes[param_type]
        
        # Create parameters instance
        parameters = param_class.from_dict(data)
        
        # Validate if requested
        if validate:
            validation_errors = parameters.validate_parameters()
            if validation_errors:
                raise ValueError(f"Parameter validation failed: {validation_errors}")
        
        # Log change
        if self.change_log:
            self.change_log.log_import(
                source=str(filepath),
                parameter_count=len(parameters.__fields__),
                author=author
            )
        
        logger.info(f"Loaded {param_type} from {filepath}")
        return parameters
    
    def save_to_file(self,
                    parameters: BaseParameters,
                    filepath: Union[str, Path],
                    format: Optional[str] = None,
                    backup: Optional[bool] = None,
                    author: Optional[str] = None,
                    description: Optional[str] = None) -> None:
        """
        Save parameters to a configuration file.
        
        Args:
            parameters: Parameters to save
            filepath: Path to save the configuration file
            format: File format ('yaml', 'yml', or 'json'). If None, inferred from extension
            backup: Whether to create backup. If None, uses instance default
            author: Author name for change logging
            description: Description for change logging
        """
        filepath = Path(filepath)
        
        # Determine format
        if format is None:
            format = filepath.suffix.lower()
        
        if format not in {'.yaml', '.yml', '.json', 'yaml', 'yml', 'json'}:
            raise ValueError(f"Unsupported format: {format}")
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup if needed
        if (backup if backup is not None else self.auto_backup) and filepath.exists():
            backup_path = filepath.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}{filepath.suffix}")
            filepath.rename(backup_path)
            logger.info(f"Created backup: {backup_path}")
        
        # Prepare data
        data = parameters.to_dict()
        data['parameter_type'] = parameters.__class__.__name__
        data['saved_at'] = datetime.now().isoformat()
        data['saved_by'] = author
        
        # Write file
        with open(filepath, 'w') as f:
            if format in {'.yaml', '.yml', 'yaml', 'yml'}:
                yaml.dump(data, f, default_flow_style=False, indent=2)
            else:  # JSON
                json.dump(data, f, indent=2, default=str)
        
        # Log change
        if self.change_log:
            self.change_log.log_export(
                destination=str(filepath),
                parameter_count=len(parameters.__fields__),
                author=author,
                reason=description
            )
        
        logger.info(f"Saved {parameters.__class__.__name__} to {filepath}")
    
    def create_version(self,
                      parameters: BaseParameters,
                      version: str,
                      author: Optional[str] = None,
                      description: Optional[str] = None,
                      tags: Optional[List[str]] = None,
                      parent_version: Optional[str] = None) -> ParameterVersion:
        """
        Create a new parameter version.
        
        Args:
            parameters: Parameters to version
            version: Version identifier
            author: Author name
            description: Version description
            tags: List of tags
            parent_version: Parent version identifier
            
        Returns:
            Created ParameterVersion instance
        """
        if not self.version_history:
            raise RuntimeError("Versioning is not enabled")
        
        # Create version
        param_version = ParameterVersion(
            version=version,
            parameters=parameters,
            author=author,
            description=description,
            tags=tags or [],
            parent_version=parent_version
        )
        
        # Add to history
        self.version_history.add_version(param_version)
        
        # Log change
        if self.change_log:
            self.change_log.log_change(
                change_type=ChangeType.CREATE,
                parameter_name=None,
                new_value=version,
                parameter_type=parameters.__class__.__name__,
                author=author,
                description=f"Created version {version}",
                reason=description,
                context={'version': version, 'tags': tags}
            )
        
        logger.info(f"Created version {version} of {parameters.__class__.__name__}")
        return param_version
    
    def load_version(self, version: str) -> Optional[BaseParameters]:
        """
        Load parameters from a specific version.
        
        Args:
            version: Version identifier
            
        Returns:
            BaseParameters instance or None if version not found
        """
        if not self.version_history:
            raise RuntimeError("Versioning is not enabled")
        
        param_version = self.version_history.get_version(version)
        if not param_version:
            return None
        
        return param_version.parameters
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two parameter versions.
        
        Args:
            version1: First version identifier
            version2: Second version identifier
            
        Returns:
            Comparison result dictionary
        """
        if not self.version_history:
            raise RuntimeError("Versioning is not enabled")
        
        return self.version_history.compare_versions(version1, version2)
    
    def get_version_history(self, parameter_type: Optional[str] = None) -> List[ParameterVersion]:
        """
        Get version history.
        
        Args:
            parameter_type: Optional parameter type filter
            
        Returns:
            List of ParameterVersion instances
        """
        if not self.version_history:
            raise RuntimeError("Versioning is not enabled")
        
        if parameter_type:
            return [v for v in self.version_history.versions.values() 
                   if v.parameters.__class__.__name__ == parameter_type]
        
        return list(self.version_history.versions.values())
    
    def validate_parameters(self, parameters: BaseParameters) -> List[str]:
        """
        Validate parameters and log the validation.
        
        Args:
            parameters: Parameters to validate
            
        Returns:
            List of validation error messages
        """
        errors = parameters.validate_parameters()
        
        # Log validation
        if self.change_log:
            for param_name in parameters.__fields__:
                param_errors = [e for e in errors if param_name in e]
                self.change_log.log_validation(
                    parameter_name=param_name,
                    value=getattr(parameters, param_name),
                    parameter_type=parameters.__class__.__name__,
                    validation_result=len(param_errors) == 0,
                    errors=param_errors
                )
        
        return errors
    
    def convert_parameters(self,
                          parameters: BaseParameters,
                          target_type: str,
                          **kwargs) -> BaseParameters:
        """
        Convert parameters to a different type.
        
        Args:
            parameters: Source parameters
            target_type: Target parameter type
            **kwargs: Additional parameters for target type
            
        Returns:
            Converted BaseParameters instance
        """
        if target_type not in self.parameter_classes:
            raise ValueError(f"Unknown target parameter type: {target_type}")
        
        target_class = self.parameter_classes[target_type]
        
        # Get parameter data
        param_data = parameters.to_dict(include_metadata=False)
        
        # Add additional parameters
        param_data.update(kwargs)
        
        # Create new parameters
        target_params = target_class(**param_data)
        
        # Log change
        if self.change_log:
            self.change_log.log_change(
                change_type=ChangeType.UPDATE,
                parameter_name=None,
                old_value=parameters.__class__.__name__,
                new_value=target_type,
                parameter_type=target_type,
                description=f"Converted from {parameters.__class__.__name__} to {target_type}"
            )
        
        logger.info(f"Converted {parameters.__class__.__name__} to {target_type}")
        return target_params
    
    def list_configurations(self, pattern: str = "*") -> List[Path]:
        """
        List configuration files in the config directory.
        
        Args:
            pattern: Glob pattern to match files
            
        Returns:
            List of configuration file paths
        """
        config_files = []
        
        for ext in self.supported_formats:
            config_files.extend(self.config_dir.glob(f"{pattern}{ext}"))
        
        return sorted(config_files)
    
    def delete_configuration(self, 
                           filepath: Union[str, Path],
                           author: Optional[str] = None,
                           reason: Optional[str] = None) -> None:
        """
        Delete a configuration file.
        
        Args:
            filepath: Path to the configuration file
            author: Author name for change logging
            reason: Reason for deletion
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        
        # Load parameters before deletion for logging
        try:
            parameters = self.load_from_file(filepath, validate=False)
            param_type = parameters.__class__.__name__
        except Exception:
            param_type = "Unknown"
        
        # Delete file
        filepath.unlink()
        
        # Log change
        if self.change_log:
            self.change_log.log_change(
                change_type=ChangeType.DELETE,
                parameter_name=None,
                old_value=str(filepath),
                new_value=None,
                parameter_type=param_type,
                author=author,
                description=f"Deleted configuration file {filepath.name}",
                reason=reason
            )
        
        logger.info(f"Deleted configuration file: {filepath}")
    
    def export_change_log(self, filepath: Union[str, Path]) -> None:
        """
        Export change log to file.
        
        Args:
            filepath: Path to export the change log
        """
        if not self.change_log:
            raise RuntimeError("Change logging is not enabled")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        self.change_log.save_to_file(str(filepath))
        logger.info(f"Exported change log to {filepath}")
    
    def import_change_log(self, filepath: Union[str, Path]) -> None:
        """
        Import change log from file.
        
        Args:
            filepath: Path to the change log file
        """
        if not self.change_log:
            raise RuntimeError("Change logging is not enabled")
        
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Change log file not found: {filepath}")
        
        # Load change log
        imported_log = ParameterChangeLog.load_from_file(str(filepath))
        
        # Merge with existing log
        self.change_log.entries.extend(imported_log.entries)
        
        logger.info(f"Imported change log from {filepath}")
    
    def export_version_history(self, filepath: Union[str, Path]) -> None:
        """
        Export version history to file.
        
        Args:
            filepath: Path to export the version history
        """
        if not self.version_history:
            raise RuntimeError("Versioning is not enabled")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(self.version_history.to_json())
        
        logger.info(f"Exported version history to {filepath}")
    
    def import_version_history(self, filepath: Union[str, Path]) -> None:
        """
        Import version history from file.
        
        Args:
            filepath: Path to the version history file
        """
        if not self.version_history:
            raise RuntimeError("Versioning is not enabled")
        
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Version history file not found: {filepath}")
        
        # Load version history
        with open(filepath, 'r') as f:
            json_str = f.read()
        
        imported_history = VersionHistory.from_json(json_str)
        
        # Merge with existing history
        for version_id, version in imported_history.versions.items():
            self.version_history.add_version(version)
        
        logger.info(f"Imported version history from {filepath}")
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive configuration management report.
        
        Returns:
            Dictionary containing the report
        """
        report = {
            'config_directory': str(self.config_dir),
            'configuration_files': [str(f) for f in self.list_configurations()],
            'auto_backup': self.auto_backup,
            'change_log_enabled': self.enable_change_log,
            'versioning_enabled': self.enable_versioning
        }
        
        # Add change log statistics
        if self.change_log:
            report['change_log'] = self.change_log.generate_report()
        
        # Add version history statistics
        if self.version_history:
            report['version_history'] = {
                'total_versions': len(self.version_history.versions),
                'latest_version': self.version_history.get_latest_version().version if self.version_history.get_latest_version() else None
            }
        
        return report