#!/usr/bin/env python3
"""
Force perfect synchronization by setting all window heights to exactly the same value.
"""

import json

def force_perfect_sync():
    """Force all resizable windows to have exactly the same height."""
    config_file = "bible_search_config.json"
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except:
        print("No config file found")
        return
    
    # Get current heights
    heights = config.get('window_heights', {})
    print("Current heights:", heights)
    
    # Calculate average height (or use 120 as default)
    current_heights = [
        heights.get('search_window', 120),
        heights.get('reading_window', 120), 
        heights.get('subject_verses', 120),
        heights.get('verse_comments', 120)
    ]
    
    # Use the average, but round to ensure clean value
    avg_height = round(sum(current_heights) / len(current_heights))
    
    print(f"Setting all windows to {avg_height}px")
    
    # Force all to exactly the same height
    config['window_heights'] = {
        "search_window": avg_height,
        "reading_window": avg_height,
        "subject_verses": avg_height,
        "verse_comments": avg_height
    }
    
    # Save the config
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"All windows synchronized to {avg_height}px")
    print("Now run: python3 bible_search_interface.py")

if __name__ == "__main__":
    force_perfect_sync()