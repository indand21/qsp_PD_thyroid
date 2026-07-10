"""
Parameter Versioning Module
===========================

This module provides the ParameterVersion class for tracking parameter versions
and comparing different parameter configurations.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import json
import hashlib
from dataclasses import dataclass, field
from .base_parameters import BaseParameters


@dataclass
class ParameterVersion:
    """
    Class for tracking parameter versions and changes.
    
    This class provides functionality to:
    - Track parameter versions with metadata
    - Compare different parameter configurations
    - Generate version hashes
    - Maintain version history
    """
    
    version: str
    parameters: BaseParameters
    timestamp: datetime = field(default_factory=datetime.now)
    author: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    parent_version: Optional[str] = None
    changes: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Calculate parameter hash
        self.parameter_hash = self.parameters.calculate_hash()
        
        # Generate full version hash
        self.version_hash = self._calculate_version_hash()
    
    def _calculate_version_hash(self) -> str:
        """
        Calculate a hash of the version information.
        
        Returns:
            SHA-256 hash of the version information
        """
        version_data = {
            'version': self.version,
            'parameter_hash': self.parameter_hash,
            'timestamp': self.timestamp.isoformat(),
            'author': self.author,
            'description': self.description,
            'tags': sorted(self.tags),
            'parent_version': self.parent_version
        }
        
        json_str = json.dumps(version_data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def compare_with(self, other: 'ParameterVersion') -> Dict[str, Any]:
        """
        Compare this version with another version.
        
        Args:
            other: Another ParameterVersion instance
            
        Returns:
            Dictionary containing comparison results
        """
        # Compare parameters
        param_differences = self.parameters.compare_parameters(other.parameters)
        
        # Compare metadata
        metadata_differences = {}
        if self.author != other.author:
            metadata_differences['author'] = (self.author, other.author)
        if self.description != other.description:
            metadata_differences['description'] = (self.description, other.description)
        if sorted(self.tags) != sorted(other.tags):
            metadata_differences['tags'] = (self.tags, other.tags)
        
        # Calculate similarity score
        total_params = len(self.parameters.__fields__)
        different_params = len(param_differences)
        similarity_score = 1.0 - (different_params / total_params) if total_params > 0 else 1.0
        
        return {
            'parameter_differences': param_differences,
            'metadata_differences': metadata_differences,
            'similarity_score': similarity_score,
            'total_parameters': total_params,
            'different_parameters': different_params,
            'time_difference': abs((self.timestamp - other.timestamp).total_seconds())
        }
    
    def is_compatible_with(self, other: 'ParameterVersion') -> bool:
        """
        Check if this version is compatible with another version.
        
        Args:
            other: Another ParameterVersion instance
            
        Returns:
            True if versions are compatible, False otherwise
        """
        # Check if they have the same parameter class
        if type(self.parameters) != type(other.parameters):
            return False
        
        # Check similarity score
        comparison = self.compare_with(other)
        if comparison['similarity_score'] < 0.8:  # 80% similarity threshold
            return False
        
        # Check for critical parameter differences
        critical_params = ['Kd_nivo_PD1', 'Kd_pembro_PD1', 'Kd_atezo_PDL1', 'Kd_durva_PDL1']
        for param in critical_params:
            if param in comparison['parameter_differences']:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert version information to dictionary.
        
        Returns:
            Dictionary representation of the version
        """
        return {
            'version': self.version,
            'parameter_hash': self.parameter_hash,
            'version_hash': self.version_hash,
            'timestamp': self.timestamp.isoformat(),
            'author': self.author,
            'description': self.description,
            'tags': self.tags,
            'parent_version': self.parent_version,
            'changes': self.changes,
            'parameters': self.parameters.to_dict(),
            'parameter_type': self.parameters.__class__.__name__
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterVersion':
        """
        Create version from dictionary.
        
        Args:
            data: Dictionary containing version information
            
        Returns:
            ParameterVersion instance
        """
        # Extract parameter data
        param_data = data.get('parameters', {})
        param_type_name = data.get('parameter_type', 'ModelParameters')
        
        # Import parameter classes dynamically
        from .model_parameters import ModelParameters
        from .drug_parameters import (
            NivolumabParameters,
            PembrolizumabParameters,
            AtezolizumabParameters,
            DurvalumabParameters
        )
        
        param_classes = {
            'ModelParameters': ModelParameters,
            'NivolumabParameters': NivolumabParameters,
            'PembrolizumabParameters': PembrolizumabParameters,
            'AtezolizumabParameters': AtezolizumabParameters,
            'DurvalumabParameters': DurvalumabParameters
        }
        
        param_class = param_classes.get(param_type_name, ModelParameters)
        parameters = param_class.from_dict(param_data)
        
        # Create version
        version = cls(
            version=data['version'],
            parameters=parameters,
            timestamp=datetime.fromisoformat(data['timestamp']),
            author=data.get('author'),
            description=data.get('description'),
            tags=data.get('tags', []),
            parent_version=data.get('parent_version'),
            changes=data.get('changes', {})
        )
        
        return version
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert version to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string representation of the version
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ParameterVersion':
        """
        Create version from JSON string.
        
        Args:
            json_str: JSON string containing version information
            
        Returns:
            ParameterVersion instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class VersionHistory:
    """
    Class for managing parameter version history.
    
    This class provides functionality to:
    - Maintain a history of parameter versions
    - Track version lineage
    - Find versions by criteria
    - Generate version reports
    """
    
    def __init__(self):
        """Initialize version history."""
        self.versions: Dict[str, ParameterVersion] = {}
        self.lineage: Dict[str, List[str]] = {}  # parent -> [children]
    
    def add_version(self, version: ParameterVersion) -> None:
        """
        Add a version to the history.
        
        Args:
            version: ParameterVersion to add
        """
        # Add to versions
        self.versions[version.version] = version
        
        # Update lineage
        if version.parent_version:
            if version.parent_version not in self.lineage:
                self.lineage[version.parent_version] = []
            self.lineage[version.parent_version].append(version.version)
    
    def get_version(self, version: str) -> Optional[ParameterVersion]:
        """
        Get a version by identifier.
        
        Args:
            version: Version identifier
            
        Returns:
            ParameterVersion instance or None if not found
        """
        return self.versions.get(version)
    
    def get_latest_version(self, parameter_type: Optional[str] = None) -> Optional[ParameterVersion]:
        """
        Get the latest version.
        
        Args:
            parameter_type: Optional parameter type filter
            
        Returns:
            Latest ParameterVersion or None if no versions
        """
        if not self.versions:
            return None
        
        versions = list(self.versions.values())
        if parameter_type:
            versions = [v for v in versions if v.parameters.__class__.__name__ == parameter_type]
        
        if not versions:
            return None
        
        return max(versions, key=lambda v: v.timestamp)
    
    def find_versions_by_tag(self, tag: str) -> List[ParameterVersion]:
        """
        Find versions with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of ParameterVersion instances with the tag
        """
        return [v for v in self.versions.values() if tag in v.tags]
    
    def find_versions_by_author(self, author: str) -> List[ParameterVersion]:
        """
        Find versions by author.
        
        Args:
            author: Author name to search for
            
        Returns:
            List of ParameterVersion instances by the author
        """
        return [v for v in self.versions.values() if v.author == author]
    
    def get_version_lineage(self, version: str) -> List[ParameterVersion]:
        """
        Get the full lineage of a version.
        
        Args:
            version: Version identifier
            
        Returns:
            List of ParameterVersion instances in chronological order
        """
        if version not in self.versions:
            return []
        
        # Build lineage by tracing back to root
        lineage = []
        current_version = version
        
        while current_version:
            if current_version in self.versions:
                lineage.append(self.versions[current_version])
            
            # Find parent
            parent = self.versions[current_version].parent_version
            current_version = parent
        
        # Reverse to get chronological order
        lineage.reverse()
        return lineage
    
    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Compare two versions.
        
        Args:
            version1: First version identifier
            version2: Second version identifier
            
        Returns:
            Comparison result dictionary
        """
        v1 = self.versions.get(version1)
        v2 = self.versions.get(version2)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        return v1.compare_with(v2)
    
    def generate_report(self, version: str) -> Dict[str, Any]:
        """
        Generate a detailed report for a version.
        
        Args:
            version: Version identifier
            
        Returns:
            Dictionary containing version report
        """
        if version not in self.versions:
            raise ValueError(f"Version {version} not found")
        
        v = self.versions[version]
        lineage = self.get_version_lineage(version)
        
        # Find changes from parent
        parent_changes = {}
        if v.parent_version and v.parent_version in self.versions:
            parent = self.versions[v.parent_version]
            parent_changes = v.compare_with(parent)['parameter_differences']
        
        return {
            'version': v.version,
            'timestamp': v.timestamp.isoformat(),
            'author': v.author,
            'description': v.description,
            'tags': v.tags,
            'parent_version': v.parent_version,
            'lineage_length': len(lineage),
            'parameter_type': v.parameters.__class__.__name__,
            'parameter_hash': v.parameter_hash,
            'version_hash': v.version_hash,
            'changes_from_parent': parent_changes,
            'total_parameters': len(v.parameters.__fields__),
            'validation_errors': v.parameters.validate_parameters()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert version history to dictionary.
        
        Returns:
            Dictionary representation of the version history
        """
        return {
            'versions': {v: version.to_dict() for v, version in self.versions.items()},
            'lineage': self.lineage
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert version history to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string representation of the version history
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'VersionHistory':
        """
        Create version history from JSON string.
        
        Args:
            json_str: JSON string containing version history
            
        Returns:
            VersionHistory instance
        """
        data = json.loads(json_str)
        history = cls()
        
        # Load versions
        versions_data = data.get('versions', {})
        for version_id, version_data in versions_data.items():
            version = ParameterVersion.from_dict(version_data)
            history.versions[version_id] = version
        
        # Load lineage
        history.lineage = data.get('lineage', {})
        
        return history