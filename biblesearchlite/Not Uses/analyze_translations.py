#!/usr/bin/env python3
"""
Analyze translations in bibles.txt vs SQLite database
"""

import sqlite3
import csv

def analyze_database_translations():
    """Get existing translations from database"""
    try:
        conn = sqlite3.connect('Bibles_cleaned.db')
        cursor = conn.cursor()
        
        # Get schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        schema = cursor.fetchall()
        print("Database Schema:")
        for table in schema:
            print(table[0])
        print("\n" + "="*50 + "\n")
        
        # Get column names from bible_verses table
        cursor.execute("PRAGMA table_info(bible_verses);")
        columns = cursor.fetchall()
        db_translations = [col[1] for col in columns if col[1] != 'id' and col[1] != 'verse']
        
        print(f"Found {len(db_translations)} translations in database:")
        for i, trans in enumerate(db_translations, 1):
            print(f"{i:2d}. {trans}")
        
        conn.close()
        return db_translations
        
    except Exception as e:
        print(f"Error analyzing database: {e}")
        return []

def analyze_bibles_txt():
    """Analyze bibles.txt file to extract translation names"""
    try:
        with open('bibles.txt', 'r', encoding='cp1252') as f:
            lines = f.readlines()
        
        # First line contains headers (translation names)
        header_line = lines[0].strip()
        translations = header_line.split('\t')[1:]  # Skip 'Verse' column
        
        print(f"\nFound {len(translations)} translations in bibles.txt:")
        for i, trans in enumerate(translations, 1):
            print(f"{i:2d}. {trans}")
        
        return translations
        
    except Exception as e:
        print(f"Error analyzing bibles.txt: {e}")
        return []

def compare_translations(db_translations, txt_translations):
    """Compare translations and find differences"""
    db_set = set(db_translations)
    txt_set = set(txt_translations)
    
    missing_from_db = txt_set - db_set
    extra_in_db = db_set - txt_set
    
    print(f"\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)
    
    if missing_from_db:
        print(f"\n{len(missing_from_db)} translations in bibles.txt NOT in database:")
        for i, trans in enumerate(sorted(missing_from_db), 1):
            print(f"{i:2d}. {trans}")
    else:
        print("\nAll translations from bibles.txt are already in database!")
    
    if extra_in_db:
        print(f"\n{len(extra_in_db)} translations in database NOT in bibles.txt:")
        for i, trans in enumerate(sorted(extra_in_db), 1):
            print(f"{i:2d}. {trans}")
    
    return missing_from_db, extra_in_db

def main():
    print("Bible Translations Analysis")
    print("="*60)
    
    # Analyze database
    db_translations = analyze_database_translations()
    
    # Analyze bibles.txt
    txt_translations = analyze_bibles_txt()
    
    # Compare them
    if db_translations and txt_translations:
        missing_from_db, extra_in_db = compare_translations(db_translations, txt_translations)
        
        if missing_from_db:
            print(f"\nRecommendation: Import {len(missing_from_db)} new translations from bibles.txt")
        else:
            print("\nNo new translations to import from bibles.txt")
    
if __name__ == "__main__":
    main()