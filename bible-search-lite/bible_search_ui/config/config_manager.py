"""
Configuration management for Bible Search application.

This module handles all configuration file operations including:
- Loading configuration from JSON files
- Saving configuration to JSON files
- Default configuration values
- Configuration validation

Author: Andrew Hopkins
"""

import json
import os
from typing import Dict, Any, Optional


class ConfigManager:
    """
    Manages application configuration stored in JSON files.
    
    Handles loading, saving, and providing default values for all
    application settings including window geometry, splitter sizes,
    translation selections, checkbox states, and font settings.
    
    Features:
    - Automatic default values if config file doesn't exist
    - Safe JSON parsing with error handling
    - Type-safe configuration access
    - Validation of loaded configuration
    
    Example:
        >>> config_mgr = ConfigManager("bible_search_lite_config.json")
        >>> 
        >>> # Load existing configuration
        >>> config = config_mgr.load()
        >>> if config:
        ...     window_geom = config['window_geometry']
        ...     print(f"Window size: {window_geom['width']}x{window_geom['height']}")
        >>> 
        >>> # Save new configuration
        >>> new_config = {
        ...     'window_geometry': {'x': 100, 'y': 100, 'width': 1200, 'height': 900},
        ...     'selected_translations': ['KJV', 'NIV']
        ... }
        >>> config_mgr.save(new_config)
    """
    
    def __init__(self, config_file: str = "bible_search_lite_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_file (str): Path to the JSON configuration file.
                Default is "bible_search_lite_config.json" in current directory.
                
        Side Effects:
            - Stores config file path
            - Does NOT create file (call save() to create)
        """
        self.config_file = config_file
        
    def get_default_config(self) -> Dict[str, Any]:
        """
        Return the default configuration structure.
        
        Provides sensible defaults for all configuration settings:
        - Window geometry: 1200x900 at position (100, 100)
        - Splitter sizes: Equal distribution [200, 250, 250, 200, 100]
        - Selected translations: ['KJV'] only
        - Checkboxes: case_sensitive=False, unique_verse=False, abbreviate_results=True
        - Font settings: title_font_size=0 (11px), verse_font_size=0 (9px)
        
        Returns:
            dict: Default configuration dictionary with all required keys.
            
        Note:
            Font size indices map to actual pixel sizes:
            - title: [11, 12, 13, 14, 15]
            - verse: [9, 10, 11, 12, 13]
        """
        return {
            'window_geometry': {
                'x': 100,
                'y': 100,
                'width': 1200,
                'height': 900
            },
            'splitter_sizes': [200, 250, 250, 200, 100],
            'selected_translations': ['KJV'],
            'checkboxes': {
                'case_sensitive': False,
                'unique_verse': False,
                'abbreviate_results': True
            },
            'font_settings': {
                'title_font_size': 0,
                'verse_font_size': 0
            },
            'search_history': []
        }
        
    def load(self) -> Optional[Dict[str, Any]]:
        """
        Load configuration from JSON file.
        
        Attempts to read and parse the configuration file. If the file
        doesn't exist or contains invalid JSON, returns default configuration.
        
        Returns:
            dict: Configuration dictionary with all settings, or None if
                  loading failed and no defaults should be used.
                  
        Side Effects:
            - Reads from file system
            - Prints status messages to console
            
        Example:
            >>> config_mgr = ConfigManager()
            >>> config = config_mgr.load()
            >>> if config:
            ...     print(f"Loaded config for {len(config['selected_translations'])} translations")
            ... else:
            ...     print("Using default configuration")
        """
        try:
            if not os.path.exists(self.config_file):
                print(f"No configuration file found at {self.config_file}")
                print("Using default configuration")
                return self.get_default_config()

            with open(self.config_file, 'r') as f:
                config = json.load(f)
                
            # Merge with defaults to ensure all keys exist
            default_config = self.get_default_config()
            merged_config = self._merge_configs(default_config, config)
            
            print(f"Configuration loaded from {self.config_file}")
            return merged_config

        except json.JSONDecodeError as e:
            print(f"Error parsing configuration file: {e}")
            print("Using default configuration")
            return self.get_default_config()
            
        except Exception as e:
            print(f"Error loading configuration: {e}")
            print("Using default configuration")
            return self.get_default_config()
            
    def save(self, config: Dict[str, Any]) -> bool:
        """
        Save configuration to JSON file.
        
        Writes the configuration dictionary to the JSON file with proper
        formatting (2-space indentation for readability).
        
        Args:
            config (dict): Configuration dictionary to save. Should contain:
                - window_geometry: Window position and size
                - splitter_sizes: List of splitter section heights
                - selected_translations: List of translation abbreviations
                - checkboxes: Dictionary of checkbox states
                - font_settings: Dictionary of font size indices
                
        Returns:
            bool: True if save successful, False if error occurred.
            
        Side Effects:
            - Writes to file system
            - Creates file if it doesn't exist
            - Prints status messages to console
            
        Example:
            >>> config_mgr = ConfigManager()
            >>> config = {
            ...     'window_geometry': {'x': 0, 'y': 0, 'width': 1024, 'height': 768},
            ...     'selected_translations': ['KJV', 'NIV', 'ESV']
            ... }
            >>> if config_mgr.save(config):
            ...     print("Configuration saved successfully")
        """
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
            
    def _merge_configs(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge loaded config with defaults to ensure all keys exist.
        
        Recursively merges two configuration dictionaries, with loaded values
        taking precedence over defaults. Ensures that if loaded config is
        missing keys, they are filled in from defaults.
        
        Args:
            default (dict): Default configuration with all required keys
            loaded (dict): Loaded configuration (may be incomplete)
            
        Returns:
            dict: Merged configuration with all keys from default,
                  but values from loaded where they exist.
                  
        Note:
            This is a helper method for internal use. Handles nested
            dictionaries (like 'window_geometry' and 'checkboxes').
        """
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Use loaded value
                result[key] = value
                
        return result
        
    def config_exists(self) -> bool:
        """
        Check if configuration file exists.
        
        Returns:
            bool: True if config file exists, False otherwise.
            
        Example:
            >>> config_mgr = ConfigManager()
            >>> if not config_mgr.config_exists():
            ...     print("First run - will use defaults")
        """
        return os.path.exists(self.config_file)
        
    def delete_config(self) -> bool:
        """
        Delete the configuration file.
        
        Useful for resetting to defaults or cleaning up during uninstall.
        
        Returns:
            bool: True if deletion successful or file didn't exist,
                  False if error occurred.
                  
        Side Effects:
            - Removes file from file system
            - Prints status messages to console
            
        Example:
            >>> config_mgr = ConfigManager()
            >>> if config_mgr.delete_config():
            ...     print("Configuration reset to defaults")
        """
        try:
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
                print(f"Configuration file {self.config_file} deleted")
                return True
            else:
                print(f"Configuration file {self.config_file} does not exist")
                return True
                
        except Exception as e:
            print(f"Error deleting configuration file: {e}")
            return False
