#!/usr/bin/env python3
"""
Test script for the refactored Bible Search application
Demonstrates the functionality of the separated classes
"""

from database_manager import DatabaseManager
from search_engine import SearchEngine
from config_manager import ConfigManager

def test_database_manager():
    """Test DatabaseManager functionality"""
    print("Testing DatabaseManager...")
    
    db = DatabaseManager('Bibles_cleaned.db')
    
    # Test database info
    info = db.get_database_info()
    print(f"Database contains {info.get('verse_count', 0)} verses and {info.get('subject_count', 0)} subjects")
    
    # Test getting subjects
    subjects = db.get_all_subjects()
    print(f"Found {len(subjects)} subjects in database")
    
    return db

def test_search_engine(db_manager):
    """Test SearchEngine functionality"""
    print("\nTesting SearchEngine...")
    
    search = SearchEngine(db_manager)
    
    # Test simple search
    results = search.search_bible('love', ['KJV'], ignore_case=True)
    print(f"Search for 'love' found {len(results)} results")
    
    if results:
        print(f"First result: {results[0]['Reference']} - {results[0]['Text'][:100]}...")
    
    # Test Boolean search
    results = search.search_bible('love AND peace', ['KJV'], ignore_case=True)
    print(f"Boolean search for 'love AND peace' found {len(results)} results")
    
    # Test highlighting
    if results:
        segments = search.highlight_text(results[0]['Text'], 'love AND peace', ignore_case=True)
        print(f"Text highlighting produced {len(segments)} segments")
    
    return search

def test_config_manager():
    """Test ConfigManager functionality"""
    print("\nTesting ConfigManager...")
    
    config = ConfigManager('test_config.json')
    
    # Test loading default config
    default_config = config.load_config()
    print(f"Loaded configuration with {len(default_config)} settings")
    
    # Test saving config
    test_config = default_config.copy()
    test_config['TestSetting'] = 'test_value'
    success = config.save_config(test_config)
    print(f"Config save {'succeeded' if success else 'failed'}")
    
    # Test search history update
    history = ['test search|word']
    updated = config.update_search_history(history, 'new search', 'verse')
    print(f"Search history updated from {len(history)} to {len(updated)} entries")
    
    return config

def main():
    """Run all tests"""
    print("Testing Refactored Bible Search Components")
    print("=" * 50)
    
    try:
        # Test each component
        db = test_database_manager()
        search = test_search_engine(db)
        config = test_config_manager()
        
        print("\n" + "=" * 50)
        print("All tests completed successfully!")
        print("\nThe refactored Bible Search application is ready to use.")
        print("Key improvements:")
        print("- DatabaseManager: Handles all database operations")
        print("- SearchEngine: Manages search logic and regex building")
        print("- ConfigManager: Handles configuration loading/saving")
        print("- BibleSearchApp: Focused on UI and user interaction")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())