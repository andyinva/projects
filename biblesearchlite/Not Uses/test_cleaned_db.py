#!/usr/bin/env python3
"""
Script to test the cleaned database and verify the formatting codes were removed.
"""

import sqlite3

def test_database():
    """Test the cleaned database functionality."""
    db_path = "/home/andrew/my-projects/AISQLBibleSearch/Bibles_cleaned.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check total count
    cursor.execute("SELECT COUNT(*) FROM bible_verses")
    total_count = cursor.fetchone()[0]
    print(f"Total verses in cleaned database: {total_count}")
    
    # Look for any remaining formatting codes
    print("\nChecking for remaining formatting codes...")
    
    # Check for HTML tags
    cursor.execute("SELECT COUNT(*) FROM bible_verses WHERE king_james_bible LIKE '%<i>%' OR king_james_bible LIKE '%</i>%'")
    html_tags = cursor.fetchone()[0]
    print(f"Verses with HTML tags in KJV: {html_tags}")
    
    # Check for HTML entities
    cursor.execute("SELECT COUNT(*) FROM bible_verses WHERE king_james_bible LIKE '%&#%'")
    html_entities = cursor.fetchone()[0]
    print(f"Verses with HTML entities in KJV: {html_entities}")
    
    # Show some sample verses that previously had formatting
    print("\nSample cleaned verses (originally had formatting):")
    cursor.execute("""
        SELECT verse, king_james_bible 
        FROM bible_verses 
        WHERE verse IN ('Genesis 1:2', 'Genesis 1:4', 'Genesis 1:16', 'Genesis 2:17')
        LIMIT 4
    """)
    
    for verse, text in cursor.fetchall():
        print(f"\n{verse}:")
        print(f"  {text}")
    
    # Test FTS functionality
    print("\nTesting Full-Text Search...")
    cursor.execute("""
        SELECT verse, king_james_bible 
        FROM bible_verses_fts 
        WHERE bible_verses_fts MATCH 'light' 
        LIMIT 3
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} results for 'light':")
    for verse, text in results:
        print(f"  {verse}: {text[:100]}...")
    
    conn.close()
    print("\nDatabase test completed successfully!")

if __name__ == "__main__":
    test_database()