"""
Change Log Module
=================

This module provides the ParameterChangeLog class for tracking parameter
modifications and maintaining a comprehensive change history.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
from dataclasses import dataclass, field
import pandas as pd
from .base_parameters import BaseParameters


class ChangeType(Enum):
    """Enumeration of parameter change types."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VALIDATE = "validate"
    IMPORT = "import"
    EXPORT = "export"


@dataclass
class ChangeEntry:
    """
    Class representing a single parameter change entry.
    
    This class captures information about parameter modifications including:
    - What changed
    - When it changed
    - Who made the change
    - Why it was changed
    """
    
    timestamp: datetime = field(default_factory=datetime.now)
    change_type: ChangeType = ChangeType.UPDATE
    parameter_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    parameter_type: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert change entry to dictionary.
        
        Returns:
            Dictionary representation of the change entry
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'change_type': self.change_type.value,
            'parameter_name': self.parameter_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'parameter_type': self.parameter_type,
            'author': self.author,
            'description': self.description,
            'reason': self.reason,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChangeEntry':
        """
        Create change entry from dictionary.
        
        Args:
            data: Dictionary containing change entry data
            
        Returns:
            ChangeEntry instance
        """
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            change_type=ChangeType(data['change_type']),
            parameter_name=data.get('parameter_name'),
            old_value=data.get('old_value'),
            new_value=data.get('new_value'),
            parameter_type=data.get('parameter_type'),
            author=data.get('author'),
            description=data.get('description'),
            reason=data.get('reason'),
            context=data.get('context', {})
        )
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert change entry to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string representation of the change entry
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ChangeEntry':
        """
        Create change entry from JSON string.
        
        Args:
            json_str: JSON string containing change entry data
            
        Returns:
            ChangeEntry instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class ParameterChangeLog:
    """
    Class for managing parameter change history.
    
    This class provides functionality to:
    - Track parameter changes over time
    - Filter changes by criteria
    - Generate change reports
    - Export/import change history
    """
    
    def __init__(self):
        """Initialize change log."""
        self.entries: List[ChangeEntry] = []
        self.auto_log: bool = True
    
    def set_auto_logging(self, enabled: bool) -> None:
        """
        Enable or disable automatic logging.
        
        Args:
            enabled: Whether to enable automatic logging
        """
        self.auto_log = enabled
    
    def log_change(self, 
                   change_type: ChangeType,
                   parameter_name: Optional[str] = None,
                   old_value: Optional[Any] = None,
                   new_value: Optional[Any] = None,
                   parameter_type: Optional[str] = None,
                   author: Optional[str] = None,
                   description: Optional[str] = None,
                   reason: Optional[str] = None,
                   context: Optional[Dict[str, Any]] = None) -> ChangeEntry:
        """
        Log a parameter change.
        
        Args:
            change_type: Type of change
            parameter_name: Name of the parameter that changed
            old_value: Previous value of the parameter
            new_value: New value of the parameter
            parameter_type: Type/class of the parameter
            author: Person who made the change
            description: Description of the change
            reason: Reason for the change
            context: Additional context information
            
        Returns:
            Created ChangeEntry
        """
        entry = ChangeEntry(
            change_type=change_type,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            parameter_type=parameter_type,
            author=author,
            description=description,
            reason=reason,
            context=context or {}
        )
        
        self.entries.append(entry)
        return entry
    
    def log_parameter_update(self,
                            parameter_name: str,
                            old_value: Any,
                            new_value: Any,
                            parameter_type: str,
                            author: Optional[str] = None,
                            reason: Optional[str] = None) -> ChangeEntry:
        """
        Log a parameter value update.
        
        Args:
            parameter_name: Name of the parameter
            old_value: Previous value
            new_value: New value
            parameter_type: Type of the parameter
            author: Person who made the change
            reason: Reason for the change
            
        Returns:
            Created ChangeEntry
        """
        if not self.auto_log:
            return None
        
        return self.log_change(
            change_type=ChangeType.UPDATE,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=new_value,
            parameter_type=parameter_type,
            author=author,
            reason=reason,
            description=f"Updated {parameter_name} from {old_value} to {new_value}"
        )
    
    def log_parameter_creation(self,
                              parameter_name: str,
                              value: Any,
                              parameter_type: str,
                              author: Optional[str] = None,
                              reason: Optional[str] = None) -> ChangeEntry:
        """
        Log a parameter creation.
        
        Args:
            parameter_name: Name of the parameter
            value: Initial value
            parameter_type: Type of the parameter
            author: Person who created the parameter
            reason: Reason for creation
            
        Returns:
            Created ChangeEntry
        """
        return self.log_change(
            change_type=ChangeType.CREATE,
            parameter_name=parameter_name,
            old_value=None,
            new_value=value,
            parameter_type=parameter_type,
            author=author,
            reason=reason,
            description=f"Created {parameter_name} with value {value}"
        )
    
    def log_parameter_deletion(self,
                              parameter_name: str,
                              old_value: Any,
                              parameter_type: str,
                              author: Optional[str] = None,
                              reason: Optional[str] = None) -> ChangeEntry:
        """
        Log a parameter deletion.
        
        Args:
            parameter_name: Name of the parameter
            old_value: Value before deletion
            parameter_type: Type of the parameter
            author: Person who deleted the parameter
            reason: Reason for deletion
            
        Returns:
            Created ChangeEntry
        """
        return self.log_change(
            change_type=ChangeType.DELETE,
            parameter_name=parameter_name,
            old_value=old_value,
            new_value=None,
            parameter_type=parameter_type,
            author=author,
            reason=reason,
            description=f"Deleted {parameter_name} (was {old_value})"
        )
    
    def log_validation(self,
                      parameter_name: str,
                      value: Any,
                      parameter_type: str,
                      validation_result: bool,
                      errors: List[str],
                      author: Optional[str] = None) -> ChangeEntry:
        """
        Log a parameter validation.
        
        Args:
            parameter_name: Name of the parameter
            value: Value that was validated
            parameter_type: Type of the parameter
            validation_result: Whether validation passed
            errors: List of validation errors
            author: Person who performed validation
            
        Returns:
            Created ChangeEntry
        """
        return self.log_change(
            change_type=ChangeType.VALIDATE,
            parameter_name=parameter_name,
            old_value=None,
            new_value=value,
            parameter_type=parameter_type,
            author=author,
            description=f"Validated {parameter_name}: {'PASSED' if validation_result else 'FAILED'}",
            context={'validation_result': validation_result, 'errors': errors}
        )
    
    def log_import(self,
                  source: str,
                  parameter_count: int,
                  author: Optional[str] = None,
                  reason: Optional[str] = None) -> ChangeEntry:
        """
        Log a parameter import operation.
        
        Args:
            source: Source of the import (file, API, etc.)
            parameter_count: Number of parameters imported
            author: Person who performed the import
            reason: Reason for import
            
        Returns:
            Created ChangeEntry
        """
        return self.log_change(
            change_type=ChangeType.IMPORT,
            parameter_name=None,
            old_value=None,
            new_value=parameter_count,
            parameter_type=None,
            author=author,
            reason=reason,
            description=f"Imported {parameter_count} parameters from {source}",
            context={'source': source, 'parameter_count': parameter_count}
        )
    
    def log_export(self,
                  destination: str,
                  parameter_count: int,
                  author: Optional[str] = None,
                  reason: Optional[str] = None) -> ChangeEntry:
        """
        Log a parameter export operation.
        
        Args:
            destination: Destination of the export (file, API, etc.)
            parameter_count: Number of parameters exported
            author: Person who performed the export
            reason: Reason for export
            
        Returns:
            Created ChangeEntry
        """
        return self.log_change(
            change_type=ChangeType.EXPORT,
            parameter_name=None,
            old_value=None,
            new_value=parameter_count,
            parameter_type=None,
            author=author,
            reason=reason,
            description=f"Exported {parameter_count} parameters to {destination}",
            context={'destination': destination, 'parameter_count': parameter_count}
        )
    
    def get_changes_by_parameter(self, parameter_name: str) -> List[ChangeEntry]:
        """
        Get all changes for a specific parameter.
        
        Args:
            parameter_name: Name of the parameter
            
        Returns:
            List of ChangeEntry instances for the parameter
        """
        return [entry for entry in self.entries if entry.parameter_name == parameter_name]
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[ChangeEntry]:
        """
        Get all changes of a specific type.
        
        Args:
            change_type: Type of change
            
        Returns:
            List of ChangeEntry instances of the specified type
        """
        return [entry for entry in self.entries if entry.change_type == change_type]
    
    def get_changes_by_author(self, author: str) -> List[ChangeEntry]:
        """
        Get all changes made by a specific author.
        
        Args:
            author: Author name
            
        Returns:
            List of ChangeEntry instances by the author
        """
        return [entry for entry in self.entries if entry.author == author]
    
    def get_changes_in_timerange(self, 
                                start_time: datetime, 
                                end_time: datetime) -> List[ChangeEntry]:
        """
        Get all changes within a time range.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of ChangeEntry instances within the time range
        """
        return [entry for entry in self.entries 
                if start_time <= entry.timestamp <= end_time]
    
    def get_recent_changes(self, hours: int = 24) -> List[ChangeEntry]:
        """
        Get recent changes within the specified number of hours.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent ChangeEntry instances
        """
        cutoff_time = datetime.now().replace(microsecond=0) - pd.Timedelta(hours=hours)
        return [entry for entry in self.entries if entry.timestamp >= cutoff_time]
    
    def generate_report(self, 
                       parameter_name: Optional[str] = None,
                       author: Optional[str] = None,
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate a change report.
        
        Args:
            parameter_name: Optional parameter name filter
            author: Optional author filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            
        Returns:
            Dictionary containing change report
        """
        # Filter entries
        filtered_entries = self.entries
        
        if parameter_name:
            filtered_entries = [e for e in filtered_entries if e.parameter_name == parameter_name]
        
        if author:
            filtered_entries = [e for e in filtered_entries if e.author == author]
        
        if start_time:
            filtered_entries = [e for e in filtered_entries if e.timestamp >= start_time]
        
        if end_time:
            filtered_entries = [e for e in filtered_entries if e.timestamp <= end_time]
        
        # Calculate statistics
        total_changes = len(filtered_entries)
        changes_by_type = {}
        changes_by_parameter = {}
        changes_by_author = {}
        
        for entry in filtered_entries:
            # Count by type
            change_type = entry.change_type.value
            changes_by_type[change_type] = changes_by_type.get(change_type, 0) + 1
            
            # Count by parameter
            if entry.parameter_name:
                param_name = entry.parameter_name
                changes_by_parameter[param_name] = changes_by_parameter.get(param_name, 0) + 1
            
            # Count by author
            if entry.author:
                auth = entry.author
                changes_by_author[auth] = changes_by_author.get(auth, 0) + 1
        
        # Get most recent changes
        recent_changes = sorted(filtered_entries, key=lambda e: e.timestamp, reverse=True)[:10]
        
        return {
            'total_changes': total_changes,
            'time_range': {
                'start': start_time.isoformat() if start_time else None,
                'end': end_time.isoformat() if end_time else None
            },
            'filters': {
                'parameter_name': parameter_name,
                'author': author
            },
            'changes_by_type': changes_by_type,
            'changes_by_parameter': changes_by_parameter,
            'changes_by_author': changes_by_author,
            'most_recent_changes': [e.to_dict() for e in recent_changes]
        }
    
    def clear(self) -> None:
        """Clear all change entries."""
        self.entries.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert change log to dictionary.
        
        Returns:
            Dictionary representation of the change log
        """
        return {
            'entries': [entry.to_dict() for entry in self.entries],
            'auto_log': self.auto_log
        }
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert change log to JSON string.
        
        Args:
            indent: JSON indentation level
            
        Returns:
            JSON string representation of the change log
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ParameterChangeLog':
        """
        Create change log from dictionary.
        
        Args:
            data: Dictionary containing change log data
            
        Returns:
            ParameterChangeLog instance
        """
        change_log = cls()
        change_log.auto_log = data.get('auto_log', True)
        
        for entry_data in data.get('entries', []):
            entry = ChangeEntry.from_dict(entry_data)
            change_log.entries.append(entry)
        
        return change_log
    
    @classmethod
    def from_json(cls, json_str: str) -> 'ParameterChangeLog':
        """
        Create change log from JSON string.
        
        Args:
            json_str: JSON string containing change log data
            
        Returns:
            ParameterChangeLog instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, filename: str) -> None:
        """
        Save change log to file.
        
        Args:
            filename: Path to save the change log
        """
        with open(filename, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def load_from_file(cls, filename: str) -> 'ParameterChangeLog':
        """
        Load change log from file.
        
        Args:
            filename: Path to the change log file
            
        Returns:
            ParameterChangeLog instance
        """
        with open(filename, 'r') as f:
            json_str = f.read()
        
        return cls.from_json(json_str)