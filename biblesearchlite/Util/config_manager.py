#!/usr/bin/env python3
"""
Configuration Manager for Bible Search Application
Handles all configuration loading, saving, and validation
"""

import json
import os
import logging
from typing import Dict, Any, List, Optional


class ConfigManager:
    def __init__(self, config_path: str = "BibleSearchConfig.json"):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.default_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values"""
        return {
            'SearchHistory': [],
            'IgnoreCase': False,
            'UniqueOnly': False,
            'Abbreviate': False,
            'BibleScope': 'bible',
            'ProximityWindow': 5,
            'MainFontSize': 10,
            'OtherFontSize': 9,
            'Book': 'All',
            'Chapter': 0,
            'Translation': '',
            'SelectedTranslations': {
                'KJV': True,
                'ASV': False,
                'DRB': False,
                'DBT': False,
                'ERV': False,
                'WBT': False,
                'WEB': False,
                'YLT': False,
                'AKJV': False,
                'WNT': False
            },
            'TranslationOrder': {
                'KJV': 1,
                'ASV': 2,
                'DRB': 3,
                'DBT': 4,
                'ERV': 5,
                'WBT': 6,
                'WEB': 7,
                'YLT': 8,
                'AKJV': 9,
                'WNT': 10
            },
            'SearchHeight': 10,
            'VerseHeight': 15,
            'SubjectHeight': 10,
            'CommentsHeight': 5,
            'WindowGeometry': '800x600+100+100'
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        self.logger.info("Loading configuration...")
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults to ensure all keys are present
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                # Convert search history to new format if needed
                if 'SearchHistory' in merged_config:
                    merged_config['SearchHistory'] = self._convert_search_history(
                        merged_config['SearchHistory']
                    )
                
                # Handle legacy FontSize setting
                if 'FontSize' in config and 'MainFontSize' not in config:
                    merged_config['MainFontSize'] = config['FontSize']
                    merged_config['OtherFontSize'] = config['FontSize']
                
                # Validate configuration
                merged_config = self._validate_config(merged_config)
                
                self.logger.info("Configuration loaded successfully")
                return merged_config
            else:
                self.logger.info("Configuration file not found, using defaults")
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return self.default_config.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to JSON file"""
        self.logger.info("Saving configuration...")
        try:
            # Validate configuration before saving
            validated_config = self._validate_config(config)
            
            with open(self.config_path, 'w') as f:
                json.dump(validated_config, f, indent=2)
            
            self.logger.info("Configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def _convert_search_history(self, history: List[str]) -> List[str]:
        """Convert search history to new format with mode indicators"""
        converted_history = []
        for entry in history:
            if '|' not in entry:
                # Old format - auto-detect mode
                if self._is_verse_reference(entry):
                    converted_history.append(f"{entry}|verse")
                else:
                    converted_history.append(f"{entry}|word")
            else:
                # New format - use as is
                converted_history.append(entry)
        return converted_history
    
    def _is_verse_reference(self, text: str) -> bool:
        """Check if text looks like a verse reference"""
        import re
        verse_patterns = [
            r'\b\w+\s+\d+:\d+',  # Book Chapter:Verse
            r'\b\d+\s+\w+\s+\d+:\d+',  # Number Book Chapter:Verse
            r'\b\w+\s+\d+:\d+-\d+',  # Book Chapter:Verse-Verse
        ]
        
        for pattern in verse_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize configuration values"""
        validated = config.copy()
        
        # Validate search history length
        if 'SearchHistory' in validated and len(validated['SearchHistory']) > 50:
            validated['SearchHistory'] = validated['SearchHistory'][:50]
        
        # Validate boolean values
        bool_keys = ['IgnoreCase', 'UniqueOnly', 'Abbreviate']
        for key in bool_keys:
            if key in validated and not isinstance(validated[key], bool):
                validated[key] = bool(validated[key])
        
        # Validate integer values
        int_keys = {
            'ProximityWindow': (1, 100),
            'MainFontSize': (6, 72),
            'OtherFontSize': (6, 72),
            'Chapter': (0, 200),
            'SearchHeight': (5, 50),
            'VerseHeight': (5, 50),
            'SubjectHeight': (5, 50),
            'CommentsHeight': (3, 30)
        }
        
        for key, (min_val, max_val) in int_keys.items():
            if key in validated:
                try:
                    val = int(validated[key])
                    validated[key] = max(min_val, min(max_val, val))
                except (ValueError, TypeError):
                    validated[key] = self.default_config[key]
        
        # Validate string values
        valid_bible_scopes = ['bible', 'ot', 'nt']
        if 'BibleScope' in validated and validated['BibleScope'] not in valid_bible_scopes:
            validated['BibleScope'] = 'bible'
        
        # Validate SelectedTranslations structure
        if 'SelectedTranslations' in validated:
            if not isinstance(validated['SelectedTranslations'], dict):
                validated['SelectedTranslations'] = self.default_config['SelectedTranslations'].copy()
            else:
                # Ensure all translation codes are present
                for code in self.default_config['SelectedTranslations']:
                    if code not in validated['SelectedTranslations']:
                        validated['SelectedTranslations'][code] = False
        
        # Validate TranslationOrder structure
        if 'TranslationOrder' in validated:
            if not isinstance(validated['TranslationOrder'], dict):
                validated['TranslationOrder'] = self.default_config['TranslationOrder'].copy()
            else:
                # Ensure all translation codes are present with valid order numbers
                for code, default_order in self.default_config['TranslationOrder'].items():
                    if code not in validated['TranslationOrder']:
                        validated['TranslationOrder'][code] = default_order
                    else:
                        try:
                            order = int(validated['TranslationOrder'][code])
                            validated['TranslationOrder'][code] = max(1, min(100, order))
                        except (ValueError, TypeError):
                            validated['TranslationOrder'][code] = default_order
        
        # Validate WindowGeometry format
        if 'WindowGeometry' in validated:
            import re
            geometry_pattern = r'^\d+x\d+\+\d+\+\d+$'
            if not re.match(geometry_pattern, validated['WindowGeometry']):
                validated['WindowGeometry'] = self.default_config['WindowGeometry']
        
        return validated
    
    def update_search_history(self, current_history: List[str], new_term: str, 
                            search_mode: str) -> List[str]:
        """Update search history with new term and mode"""
        if not new_term:
            return current_history
        
        # Create history entry with mode
        history_entry = f"{new_term}|{search_mode}"
        
        # Remove existing entry if it exists
        updated_history = [entry for entry in current_history if entry != history_entry]
        
        # Add new entry at the beginning
        updated_history.insert(0, history_entry)
        
        # Limit to 50 entries
        return updated_history[:50]
    
    def get_search_history_terms(self, history: List[str]) -> List[str]:
        """Extract just the search terms from history entries"""
        terms = []
        for entry in history:
            if '|' in entry:
                term, _ = entry.split('|', 1)
                terms.append(term)
            else:
                terms.append(entry)
        return terms
    
    def get_config_value(self, config: Dict[str, Any], key: str, default=None):
        """Safely get a configuration value with fallback to default"""
        return config.get(key, self.default_config.get(key, default))
    
    def backup_config(self) -> bool:
        """Create a backup of the current configuration file"""
        if not os.path.exists(self.config_path):
            return True  # Nothing to backup
        
        try:
            import shutil
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.config_path}.backup_{timestamp}"
            
            shutil.copy2(self.config_path, backup_path)
            self.logger.info(f"Configuration backed up to: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating config backup: {e}")
            return False
    
    def restore_defaults(self) -> Dict[str, Any]:
        """Reset configuration to default values"""
        self.logger.info("Restoring default configuration")
        return self.default_config.copy()
    
    def export_config(self, export_path: str, config: Dict[str, Any]) -> bool:
        """Export configuration to a different file"""
        try:
            with open(export_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info(f"Configuration exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> Optional[Dict[str, Any]]:
        """Import configuration from a file"""
        try:
            with open(import_path, 'r') as f:
                imported_config = json.load(f)
            
            # Validate imported configuration
            validated_config = self._validate_config(imported_config)
            
            self.logger.info(f"Configuration imported from: {import_path}")
            return validated_config
            
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return None