#!/usr/bin/env python3
"""
Force equal window heights test.
"""

import json
import os

def force_equal_config():
    """Create a config file with equal heights and test."""
    config_file = "bible_search_config.json"
    
    # Create config with equal heights
    config = {
        "window_width": 1000,
        "window_height": 700,
        "window_heights": {
            "search_window": 120,
            "reading_window": 120,
            "subject_verses": 120,
            "verse_comments": 120
        },
        "static_heights": {
            "search_settings": 120,
            "message_window": 60
        },
        "search_settings": {
            "case_sensitive": False,
            "unique_verses": False,
            "abbreviate_results": False
        },
        "translations": []
    }
    
    # Save the config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created {config_file} with equal heights:")
    print("  search_window: 120px")
    print("  reading_window: 120px") 
    print("  subject_verses: 120px")
    print("  verse_comments: 120px")
    print()
    print("Now run: python3 bible_search_interface.py")
    print("All windows should start equal and resize together.")

if __name__ == "__main__":
    force_equal_config()