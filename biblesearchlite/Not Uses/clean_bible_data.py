#!/usr/bin/env python3
"""
Script to clean formatting codes from the 10_Bibles.csv file and reprocess into SQLite database.
Removes HTML tags, HTML entities, and other formatting artifacts.
"""

import csv
import sqlite3
import re
import os
from typing import List, Tuple

def clean_text(text: str) -> str:
    """
    Clean formatting codes from text.
    
    Args:
        text: Raw text with formatting codes
        
    Returns:
        Cleaned text without formatting codes
    """
    if not text:
        return text
    
    # Remove HTML italic tags
    text = re.sub(r'<i>|</i>', '', text)
    
    # Remove HTML entities (like &#8212; which is em dash)
    text = re.sub(r'&#\d+;', '—', text)  # Replace with actual em dash
    
    # Remove other common HTML entities
    html_entities = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&apos;': "'",
        '&nbsp;': ' '
    }
    
    for entity, replacement in html_entities.items():
        text = text.replace(entity, replacement)
    
    # Remove any remaining HTML-like tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def process_csv_file(input_file: str, output_file: str) -> None:
    """
    Process the CSV file to remove formatting codes.
    
    Args:
        input_file: Path to the original CSV file
        output_file: Path to the cleaned CSV file
    """
    print(f"Processing {input_file}...")
    
    # Try different encodings
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    encoding_used = None
    
    for encoding in encodings:
        try:
            with open(input_file, 'r', encoding=encoding) as test_file:
                test_file.read()
            encoding_used = encoding
            print(f"Using encoding: {encoding}")
            break
        except UnicodeDecodeError:
            continue
    
    if not encoding_used:
        raise Exception("Could not determine file encoding")
    
    with open(input_file, 'r', encoding=encoding_used) as infile, \
         open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        
        # Process header
        header = next(reader)
        writer.writerow(header)
        
        row_count = 0
        cleaned_count = 0
        
        for row in reader:
            row_count += 1
            cleaned_row = []
            had_formatting = False
            
            for cell in row:
                cleaned_cell = clean_text(cell)
                if cleaned_cell != cell:
                    had_formatting = True
                cleaned_row.append(cleaned_cell)
            
            if had_formatting:
                cleaned_count += 1
            
            writer.writerow(cleaned_row)
            
            if row_count % 1000 == 0:
                print(f"Processed {row_count} rows...")
    
    print(f"Completed processing {row_count} rows")
    print(f"Found formatting codes in {cleaned_count} rows")

def create_database_table(db_path: str, table_name: str = 'bible_verses') -> None:
    """
    Create the database table for bible verses.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to create
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop existing table if it exists
    cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
    
    # Create new table
    cursor.execute(f'''
        CREATE TABLE {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verse TEXT NOT NULL,
            king_james_bible TEXT,
            american_standard_version TEXT,
            douay_rheims_bible TEXT,
            darby_bible_translation TEXT,
            english_revised_version TEXT,
            webster_bible_translation TEXT,
            world_english_bible TEXT,
            youngs_literal_translation TEXT,
            american_king_james_version TEXT,
            weymouth_new_testament TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Created table '{table_name}' in {db_path}")

def import_csv_to_database(csv_file: str, db_path: str, table_name: str = 'bible_verses') -> None:
    """
    Import the cleaned CSV data into SQLite database.
    
    Args:
        csv_file: Path to the cleaned CSV file
        db_path: Path to the SQLite database file
        table_name: Name of the table to import into
    """
    print(f"Importing {csv_file} into {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Try different encodings for the CSV file
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
    encoding_used = None
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as test_file:
                test_file.read()
            encoding_used = encoding
            break
        except UnicodeDecodeError:
            continue
    
    if not encoding_used:
        raise Exception("Could not determine file encoding for import")
    
    print(f"Using encoding for import: {encoding_used}")
    
    with open(csv_file, 'r', encoding=encoding_used) as infile:
        reader = csv.reader(infile)
        
        # Skip header
        header = next(reader)
        print(f"Header: {header}")
        
        row_count = 0
        for row in reader:
            if len(row) >= 11:  # Ensure we have all columns
                cursor.execute(f'''
                    INSERT INTO {table_name} (
                        verse, king_james_bible, american_standard_version, 
                        douay_rheims_bible, darby_bible_translation, 
                        english_revised_version, webster_bible_translation,
                        world_english_bible, youngs_literal_translation,
                        american_king_james_version, weymouth_new_testament
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', row)
                row_count += 1
                
                if row_count % 1000 == 0:
                    print(f"Imported {row_count} rows...")
                    conn.commit()
    
    conn.commit()
    conn.close()
    print(f"Import completed: {row_count} rows")

def create_indexes(db_path: str, table_name: str = 'bible_verses') -> None:
    """
    Create indexes on the database for better search performance.
    
    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to index
    """
    print("Creating indexes...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create FTS (Full-Text Search) table for better text searching
    cursor.execute(f'DROP TABLE IF EXISTS {table_name}_fts')
    cursor.execute(f'''
        CREATE VIRTUAL TABLE {table_name}_fts USING fts5(
            verse, king_james_bible, american_standard_version, 
            douay_rheims_bible, darby_bible_translation, 
            english_revised_version, webster_bible_translation,
            world_english_bible, youngs_literal_translation,
            american_king_james_version, weymouth_new_testament,
            content={table_name}
        )
    ''')
    
    # Create regular indexes
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_verse ON {table_name}(verse)')
    
    conn.commit()
    conn.close()
    print("Indexes created successfully")

def main():
    """Main function to orchestrate the cleaning and database operations."""
    base_dir = "/home/andrew/my-projects/AISQLBibleSearch"
    input_csv = os.path.join(base_dir, "10_Bibles.csv")
    cleaned_csv = os.path.join(base_dir, "10_Bibles_cleaned.csv")
    database_path = os.path.join(base_dir, "Bibles_cleaned.db")
    
    # Step 1: Clean the CSV file
    print("=" * 50)
    print("Step 1: Cleaning CSV file")
    print("=" * 50)
    process_csv_file(input_csv, cleaned_csv)
    
    # Step 2: Create database and table
    print("\n" + "=" * 50)
    print("Step 2: Creating database table")
    print("=" * 50)
    create_database_table(database_path)
    
    # Step 3: Import cleaned data
    print("\n" + "=" * 50)
    print("Step 3: Importing data to database")
    print("=" * 50)
    import_csv_to_database(cleaned_csv, database_path)
    
    # Step 4: Create indexes
    print("\n" + "=" * 50)
    print("Step 4: Creating indexes")
    print("=" * 50)
    create_indexes(database_path)
    
    print("\n" + "=" * 50)
    print("PROCESS COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    print(f"Cleaned CSV: {cleaned_csv}")
    print(f"New Database: {database_path}")
    print("The data has been cleaned and reprocessed.")

if __name__ == "__main__":
    main()