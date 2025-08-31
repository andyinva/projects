#!/usr/bin/env python3
"""
Bible Error Analysis System - Enhanced Error Detection with SQLite Integration

Comprehensive error detection and database storage system for JSON Bible files.
Stores all errors in SQLite database for GUI analysis and reporting.

Usage:
    python3 bible_error_analyzer.py [--scan] [--db path/to/database]
"""

import json
import re
import os
import sqlite3
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import unicodedata

@dataclass
class ErrorInstance:
    """Represents a single error instance"""
    translation: str
    book: str
    chapter: int
    verse: int
    line_number: int
    error_code: str
    error_text: str
    context: str
    severity: str

class DatabaseManager:
    """Manages SQLite database operations for error storage"""
    
    def __init__(self, db_path: str = "bible_errors.db"):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
        self.setup_error_types()
    
    def setup_database(self):
        """Initialize database connection and create tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS error_types (
                id INTEGER PRIMARY KEY,
                error_code TEXT UNIQUE,
                description TEXT,
                severity TEXT
            );
            
            CREATE TABLE IF NOT EXISTS error_instances (
                id INTEGER PRIMARY KEY,
                translation TEXT,
                book TEXT,
                chapter INTEGER,
                verse INTEGER,
                line_number INTEGER,
                error_type_id INTEGER,
                error_text TEXT,
                context TEXT,
                reviewed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_type_id) REFERENCES error_types(id)
            );
            
            CREATE TABLE IF NOT EXISTS error_statistics (
                error_type_id INTEGER PRIMARY KEY,
                total_count INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_type_id) REFERENCES error_types(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_error_instances_translation ON error_instances(translation);
            CREATE INDEX IF NOT EXISTS idx_error_instances_book ON error_instances(book);
            CREATE INDEX IF NOT EXISTS idx_error_instances_error_type ON error_instances(error_type_id);
            CREATE INDEX IF NOT EXISTS idx_error_instances_reviewed ON error_instances(reviewed);
        """)
        self.conn.commit()
    
    def setup_error_types(self):
        """Initialize predefined error types"""
        error_types = [
            ("NUMBERS_IN_TEXT", "Numbers found in verse text", "WARNING"),
            ("INVALID_CHARS", "Invalid characters in text", "ERROR"),
            ("MULTIPLE_SPACES", "Multiple consecutive spaces", "WARNING"),
            ("MISSING_VERSES", "Missing verses in sequence", "ERROR"),
            ("DUPLICATE_VERSES", "Duplicate verses found", "ERROR"),
            ("CHAPTER_SEQUENCE", "Chapter sequence issues", "ERROR"),
            ("VERSE_TOO_SHORT", "Suspiciously short verse (< 3 chars)", "WARNING"),
            ("VERSE_TOO_LONG", "Suspiciously long verse (> 500 chars)", "WARNING"),
            ("HTML_XML_REMNANTS", "XML/HTML tags or entities found", "ERROR"),
            ("WHITESPACE_ISSUES", "Leading/trailing whitespace", "WARNING"),
            ("ENCODING_PROBLEMS", "Unusual encoding/unicode characters", "WARNING"),
            ("EMPTY_CONTENT", "Empty verse, chapter, or book", "ERROR"),
            ("STRUCTURE_VIOLATION", "JSON structure problems", "ERROR"),
            ("DUPLICATE_CONTENT", "Identical verse content found", "WARNING"),
            ("CAPITALIZATION_ISSUES", "Unusual capitalization patterns", "INFO"),
            ("NON_INTEGER_REFERENCE", "Non-integer verse/chapter numbers", "ERROR")
        ]
        
        for error_code, description, severity in error_types:
            self.conn.execute(
                "INSERT OR IGNORE INTO error_types (error_code, description, severity) VALUES (?, ?, ?)",
                (error_code, description, severity)
            )
        self.conn.commit()
    
    def get_error_type_id(self, error_code: str) -> int:
        """Get error type ID from error code"""
        cursor = self.conn.execute(
            "SELECT id FROM error_types WHERE error_code = ?", (error_code,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            raise ValueError(f"Unknown error code: {error_code}")
    
    def clear_translation_errors(self, translation: str):
        """Clear all errors for a specific translation before rescanning"""
        self.conn.execute(
            "DELETE FROM error_instances WHERE translation = ?", (translation,)
        )
        self.conn.commit()
    
    def store_error(self, error: ErrorInstance):
        """Store a single error instance in database"""
        try:
            error_type_id = self.get_error_type_id(error.error_code)
            
            self.conn.execute("""
                INSERT INTO error_instances 
                (translation, book, chapter, verse, line_number, error_type_id, error_text, context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                error.translation, error.book, error.chapter, error.verse,
                error.line_number, error_type_id, error.error_text, error.context
            ))
        except Exception as e:
            logging.error(f"Failed to store error: {e}")
    
    def update_statistics(self):
        """Update error statistics table"""
        # Clear existing statistics
        self.conn.execute("DELETE FROM error_statistics")
        
        # Calculate new statistics
        self.conn.execute("""
            INSERT INTO error_statistics (error_type_id, total_count, last_updated)
            SELECT error_type_id, COUNT(*), CURRENT_TIMESTAMP
            FROM error_instances
            GROUP BY error_type_id
        """)
        self.conn.commit()
    
    def get_error_statistics(self) -> List[Tuple]:
        """Get error statistics with type information"""
        cursor = self.conn.execute("""
            SELECT et.error_code, et.description, et.severity, COALESCE(es.total_count, 0)
            FROM error_types et
            LEFT JOIN error_statistics es ON et.id = es.error_type_id
            ORDER BY COALESCE(es.total_count, 0) DESC, et.error_code
        """)
        return cursor.fetchall()
    
    def get_translations(self) -> List[str]:
        """Get list of all translations in database"""
        cursor = self.conn.execute(
            "SELECT DISTINCT translation FROM error_instances ORDER BY translation"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_errors_filtered(self, translation: str = None, error_code: str = None, 
                          search_text: str = None, reviewed: bool = None) -> List[Dict]:
        """Get filtered error instances"""
        query = """
            SELECT ei.id, ei.translation, ei.book, ei.chapter, ei.verse, ei.line_number,
                   et.error_code, et.description, et.severity, ei.error_text, ei.context, ei.reviewed
            FROM error_instances ei
            JOIN error_types et ON ei.error_type_id = et.id
            WHERE 1=1
        """
        params = []
        
        if translation and translation != "All":
            query += " AND ei.translation = ?"
            params.append(translation)
        
        if error_code and error_code != "Show All":
            query += " AND et.error_code = ?"
            params.append(error_code)
        
        if search_text:
            query += " AND (ei.book LIKE ? OR ei.error_text LIKE ? OR ei.context LIKE ?)"
            search_param = f"%{search_text}%"
            params.extend([search_param, search_param, search_param])
        
        if reviewed is not None:
            query += " AND ei.reviewed = ?"
            params.append(reviewed)
        
        query += " ORDER BY ei.translation, ei.book, ei.chapter, ei.verse"
        
        cursor = self.conn.execute(query, params)
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def mark_reviewed(self, error_ids: List[int], reviewed: bool = True):
        """Mark errors as reviewed or unreviewed"""
        placeholders = ",".join("?" * len(error_ids))
        self.conn.execute(
            f"UPDATE error_instances SET reviewed = ? WHERE id IN ({placeholders})",
            [reviewed] + error_ids
        )
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class BibleErrorAnalyzer:
    """Enhanced Bible error analyzer with database integration"""
    
    # Expected 66 books
    EXPECTED_BOOKS = [
        'Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', 'Rut', '1Sa', '2Sa',
        '1Ki', '2Ki', '1Ch', '2Ch', 'Ezr', 'Neh', 'Est', 'Job', 'Psa', 'Pro',
        'Ecc', 'Son', 'Isa', 'Jer', 'Lam', 'Eze', 'Dan', 'Hos', 'Joe', 'Amo',
        'Oba', 'Jon', 'Mic', 'Nah', 'Hab', 'Zep', 'Hag', 'Zec', 'Mal', 'Mat',
        'Mar', 'Luk', 'Joh', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph', 'Phi',
        'Col', '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas', '1Pe',
        '2Pe', '1Jo', '2Jo', '3Jo', 'Jde', 'Rev'
    ]
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.line_number = 0
        self.errors = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_file(self, json_file: Path) -> List[ErrorInstance]:
        """Analyze a single JSON Bible file for errors"""
        self.errors = []
        self.line_number = 0
        translation = json_file.stem.upper()
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                bible_data = json.loads(content)
        except json.JSONDecodeError as e:
            self.errors.append(ErrorInstance(
                translation=translation,
                book="FILE",
                chapter=0,
                verse=0,
                line_number=getattr(e, 'lineno', 0),
                error_code="STRUCTURE_VIOLATION",
                error_text=f"Invalid JSON: {e}",
                context="",
                severity="ERROR"
            ))
            return self.errors
        except Exception as e:
            self.errors.append(ErrorInstance(
                translation=translation,
                book="FILE",
                chapter=0,
                verse=0,
                line_number=0,
                error_code="STRUCTURE_VIOLATION",
                error_text=f"File read error: {e}",
                context="",
                severity="ERROR"
            ))
            return self.errors
        
        # Structure validation
        self._check_structure(bible_data, translation, lines)
        
        # Content validation
        books = bible_data.get('books', {})
        verse_hashes = {}  # For duplicate detection
        
        for book_abbrev, book_data in books.items():
            self._check_book_structure(book_abbrev, book_data, translation, lines)
            
            chapters = book_data.get('chapters', {})
            self._check_chapter_sequence(book_abbrev, chapters, translation, lines)
            
            for chapter_str, verses in chapters.items():
                try:
                    chapter_num = int(chapter_str)
                except ValueError:
                    self.errors.append(ErrorInstance(
                        translation=translation,
                        book=book_abbrev,
                        chapter=0,
                        verse=0,
                        line_number=self._find_line_number(lines, f'"{chapter_str}"'),
                        error_code="NON_INTEGER_REFERENCE",
                        error_text=f"Non-integer chapter number: '{chapter_str}'",
                        context="",
                        severity="ERROR"
                    ))
                    continue
                
                self._check_verse_sequence(book_abbrev, chapter_num, verses, translation, lines)
                
                for verse_str, verse_text in verses.items():
                    try:
                        verse_num = int(verse_str)
                    except ValueError:
                        self.errors.append(ErrorInstance(
                            translation=translation,
                            book=book_abbrev,
                            chapter=chapter_num,
                            verse=0,
                            line_number=self._find_line_number(lines, f'"{verse_str}"'),
                            error_code="NON_INTEGER_REFERENCE",
                            error_text=f"Non-integer verse number: '{verse_str}'",
                            context="",
                            severity="ERROR"
                        ))
                        continue
                    
                    if isinstance(verse_text, str):
                        line_num = self._find_line_number(lines, verse_text)
                        location = f"{book_abbrev}:{chapter_num}:{verse_num}"
                        
                        # Text content analysis
                        self._check_text_content(verse_text, translation, book_abbrev, 
                                               chapter_num, verse_num, line_num, lines)
                        
                        # Duplicate detection
                        self._check_duplicates(verse_text, location, verse_hashes, 
                                             translation, book_abbrev, chapter_num, verse_num, line_num)
        
        return self.errors
    
    def _find_line_number(self, lines: List[str], text: str) -> int:
        """Find approximate line number for given text"""
        if not text or len(text) < 10:
            return 0
        
        search_text = text[:50] if len(text) > 50 else text
        for i, line in enumerate(lines):
            if search_text in line:
                return i + 1
        return 0
    
    def _check_structure(self, bible_data: Dict, translation: str, lines: List[str]):
        """Check overall JSON structure"""
        if 'translation_info' not in bible_data:
            self.errors.append(ErrorInstance(
                translation=translation,
                book="ROOT",
                chapter=0,
                verse=0,
                line_number=1,
                error_code="STRUCTURE_VIOLATION",
                error_text="Missing translation_info section",
                context="",
                severity="ERROR"
            ))
        else:
            trans_info = bible_data['translation_info']
            abbrev = trans_info.get('abbrev', '')
            
            if not abbrev or len(abbrev) != 3 or not abbrev.isupper():
                line_num = self._find_line_number(lines, '"abbrev"')
                self.errors.append(ErrorInstance(
                    translation=translation,
                    book="ROOT",
                    chapter=0,
                    verse=0,
                    line_number=line_num,
                    error_code="STRUCTURE_VIOLATION",
                    error_text=f"Invalid translation abbreviation: '{abbrev}'",
                    context=f"Expected 3 uppercase letters, got: '{abbrev}'",
                    severity="ERROR"
                ))
        
        if 'books' not in bible_data:
            self.errors.append(ErrorInstance(
                translation=translation,
                book="ROOT",
                chapter=0,
                verse=0,
                line_number=self._find_line_number(lines, '"books"'),
                error_code="STRUCTURE_VIOLATION",
                error_text="Missing books section",
                context="",
                severity="ERROR"
            ))
    
    def _check_book_structure(self, book_abbrev: str, book_data: Dict, 
                            translation: str, lines: List[str]):
        """Check individual book structure"""
        if not isinstance(book_data, dict):
            line_num = self._find_line_number(lines, f'"{book_abbrev}"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=0,
                verse=0,
                line_number=line_num,
                error_code="STRUCTURE_VIOLATION",
                error_text="Book data is not a dictionary",
                context="",
                severity="ERROR"
            ))
            return
        
        if 'chapters' not in book_data:
            line_num = self._find_line_number(lines, f'"{book_abbrev}"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=0,
                verse=0,
                line_number=line_num,
                error_code="STRUCTURE_VIOLATION",
                error_text="Missing chapters section",
                context="",
                severity="ERROR"
            ))
        elif not book_data['chapters']:
            line_num = self._find_line_number(lines, f'"{book_abbrev}"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=0,
                verse=0,
                line_number=line_num,
                error_code="EMPTY_CONTENT",
                error_text="Empty chapters section",
                context="",
                severity="ERROR"
            ))
    
    def _check_chapter_sequence(self, book_abbrev: str, chapters: Dict, 
                              translation: str, lines: List[str]):
        """Check chapter sequence for gaps and duplicates"""
        chapter_nums = []
        for chapter_str in chapters.keys():
            try:
                chapter_nums.append(int(chapter_str))
            except ValueError:
                continue  # Already handled in main analysis
        
        if not chapter_nums:
            return
        
        # Check for gaps
        expected_chapters = list(range(1, max(chapter_nums) + 1))
        missing_chapters = set(expected_chapters) - set(chapter_nums)
        
        if missing_chapters:
            line_num = self._find_line_number(lines, f'"{book_abbrev}"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=0,
                verse=0,
                line_number=line_num,
                error_code="CHAPTER_SEQUENCE",
                error_text=f"Missing chapters: {sorted(missing_chapters)}",
                context=f"Expected chapters 1-{max(chapter_nums)}",
                severity="ERROR"
            ))
        
        # Check for duplicates
        duplicates = [num for num in chapter_nums if chapter_nums.count(num) > 1]
        if duplicates:
            line_num = self._find_line_number(lines, f'"{book_abbrev}"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=0,
                verse=0,
                line_number=line_num,
                error_code="CHAPTER_SEQUENCE",
                error_text=f"Duplicate chapters: {sorted(set(duplicates))}",
                context="",
                severity="ERROR"
            ))
    
    def _check_verse_sequence(self, book_abbrev: str, chapter_num: int, 
                            verses: Dict, translation: str, lines: List[str]):
        """Check verse sequence within a chapter"""
        verse_nums = []
        for verse_str in verses.keys():
            try:
                verse_nums.append(int(verse_str))
            except ValueError:
                continue  # Already handled in main analysis
        
        if not verse_nums:
            return
        
        # Check for empty verses
        for verse_str, verse_text in verses.items():
            if not verse_text or not str(verse_text).strip():
                line_num = self._find_line_number(lines, f'"{verse_str}"')
                self.errors.append(ErrorInstance(
                    translation=translation,
                    book=book_abbrev,
                    chapter=chapter_num,
                    verse=int(verse_str) if verse_str.isdigit() else 0,
                    line_number=line_num,
                    error_code="EMPTY_CONTENT",
                    error_text="Empty verse content",
                    context="",
                    severity="ERROR"
                ))
        
        # Check for gaps in verse sequence
        expected_verses = list(range(1, max(verse_nums) + 1))
        missing_verses = set(expected_verses) - set(verse_nums)
        
        if missing_verses:
            line_num = self._find_line_number(lines, f'"chapters"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=chapter_num,
                verse=0,
                line_number=line_num,
                error_code="MISSING_VERSES",
                error_text=f"Missing verses: {sorted(missing_verses)}",
                context=f"Chapter {chapter_num}",
                severity="ERROR"
            ))
        
        # Check for duplicate verses
        duplicates = [num for num in verse_nums if verse_nums.count(num) > 1]
        if duplicates:
            line_num = self._find_line_number(lines, f'"chapters"')
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book_abbrev,
                chapter=chapter_num,
                verse=0,
                line_number=line_num,
                error_code="DUPLICATE_VERSES",
                error_text=f"Duplicate verses: {sorted(set(duplicates))}",
                context=f"Chapter {chapter_num}",
                severity="ERROR"
            ))
    
    def _check_text_content(self, text: str, translation: str, book: str, 
                          chapter: int, verse: int, line_num: int, lines: List[str]):
        """Check text content for various issues"""
        location_context = f"{book} {chapter}:{verse}"
        
        # Check for numbers
        if re.search(r'\d', text):
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="NUMBERS_IN_TEXT",
                error_text="Contains numeric characters",
                context=f"{location_context}: {text[:100]}..." if len(text) > 100 else f"{location_context}: {text}",
                severity="WARNING"
            ))
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z\s\.,;:!?\'"()\[\]\/\-–—""''…]*$', text):
            invalid_chars = set(char for char in text 
                              if not re.match(r'[a-zA-Z\s\.,;:!?\'"()\[\]\/\-–—""''…]', char))
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="INVALID_CHARS",
                error_text=f"Invalid characters: {list(invalid_chars)}",
                context=f"{location_context}: {text[:50]}...",
                severity="ERROR"
            ))
        
        # Check for multiple spaces
        if re.search(r'  +', text):
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="MULTIPLE_SPACES",
                error_text="Multiple consecutive spaces found",
                context=f"{location_context}: {text[:100]}...",
                severity="WARNING"
            ))
        
        # Check verse length
        if len(text) < 3:
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="VERSE_TOO_SHORT",
                error_text=f"Suspiciously short verse ({len(text)} chars)",
                context=f"{location_context}: '{text}'",
                severity="WARNING"
            ))
        elif len(text) > 500:
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="VERSE_TOO_LONG",
                error_text=f"Suspiciously long verse ({len(text)} chars)",
                context=f"{location_context}: {text[:100]}...",
                severity="WARNING"
            ))
        
        # Check for HTML/XML remnants
        if re.search(r'<[^>]+>|&[a-zA-Z]+;', text):
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="HTML_XML_REMNANTS",
                error_text="HTML/XML tags or entities found",
                context=f"{location_context}: {text[:100]}...",
                severity="ERROR"
            ))
        
        # Check for whitespace issues
        if text != text.strip():
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="WHITESPACE_ISSUES",
                error_text="Leading or trailing whitespace",
                context=f"{location_context}: '{text}'",
                severity="WARNING"
            ))
        
        # Check for unusual unicode/encoding
        unusual_chars = []
        for char in text:
            if ord(char) > 127:
                category = unicodedata.category(char)
                if category.startswith('C'):  # Control characters
                    unusual_chars.append(char)
        
        if unusual_chars:
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="ENCODING_PROBLEMS",
                error_text=f"Unusual unicode characters: {unusual_chars[:5]}",
                context=f"{location_context}: {text[:50]}...",
                severity="WARNING"
            ))
        
        # Check capitalization patterns
        words = text.split()
        if len(words) > 2:
            all_caps_count = sum(1 for word in words if word.isupper() and len(word) > 1)
            if all_caps_count > len(words) * 0.3:  # More than 30% all caps
                self.errors.append(ErrorInstance(
                    translation=translation,
                    book=book,
                    chapter=chapter,
                    verse=verse,
                    line_number=line_num,
                    error_code="CAPITALIZATION_ISSUES",
                    error_text=f"Unusual capitalization ({all_caps_count}/{len(words)} words all caps)",
                    context=f"{location_context}: {text[:100]}...",
                    severity="INFO"
                ))
    
    def _check_duplicates(self, text: str, location: str, verse_hashes: Dict, 
                         translation: str, book: str, chapter: int, verse: int, line_num: int):
        """Check for duplicate verse content"""
        if len(text.strip()) <= 10:  # Skip very short verses
            return
        
        text_hash = hash(text.strip().lower())
        if text_hash in verse_hashes:
            original_location = verse_hashes[text_hash]
            self.errors.append(ErrorInstance(
                translation=translation,
                book=book,
                chapter=chapter,
                verse=verse,
                line_number=line_num,
                error_code="DUPLICATE_CONTENT",
                error_text=f"Identical to {original_location}",
                context=f"{location}: {text[:100]}...",
                severity="WARNING"
            ))
        else:
            verse_hashes[text_hash] = location
    
    def scan_directory(self, directory: Path, progress_callback=None) -> Dict[str, int]:
        """Scan all JSON files in directory and store errors in database"""
        json_files = list(directory.glob("*.json"))
        if not json_files:
            self.logger.warning("No JSON files found in directory")
            return {}
        
        results = {}
        total_files = len(json_files)
        
        self.logger.info(f"Scanning {total_files} JSON files...")
        
        for i, json_file in enumerate(json_files):
            translation = json_file.stem.upper()
            self.logger.info(f"[{i+1}/{total_files}] Analyzing {json_file.name}...")
            
            # Clear existing errors for this translation
            self.db.clear_translation_errors(translation)
            
            # Analyze file
            errors = self.analyze_file(json_file)
            
            # Store errors in database
            for error in errors:
                self.db.store_error(error)
            
            results[translation] = len(errors)
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(i + 1, total_files, translation, len(errors))
        
        # Update statistics
        self.db.update_statistics()
        self.logger.info(f"Scan complete. Total errors found: {sum(results.values())}")
        
        return results

def main():
    """Main entry point for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bible Error Analysis System")
    parser.add_argument('--scan', action='store_true', 
                       help='Scan all JSON files and update database')
    parser.add_argument('--db', default='bible_errors.db',
                       help='Database file path')
    parser.add_argument('--dir', default='.',
                       help='Directory containing JSON files')
    
    args = parser.parse_args()
    
    # Initialize database
    db_manager = DatabaseManager(args.db)
    
    if args.scan:
        # Initialize analyzer and scan directory
        analyzer = BibleErrorAnalyzer(db_manager)
        directory = Path(args.dir)
        
        if not directory.exists():
            print(f"Directory not found: {directory}")
            sys.exit(1)
        
        results = analyzer.scan_directory(directory)
        
        print("\nScan Results:")
        print("=" * 50)
        for translation, error_count in sorted(results.items()):
            status = "✅ Clean" if error_count == 0 else f"⚠️  {error_count} errors"
            print(f"{translation:>3}: {status}")
        
        print(f"\nTotal errors found: {sum(results.values())}")
        print(f"Database updated: {args.db}")
    else:
        # Show current statistics
        stats = db_manager.get_error_statistics()
        print("\nCurrent Error Statistics:")
        print("=" * 60)
        print(f"{'Error Type':<25} {'Count':<8} {'Severity':<10}")
        print("-" * 60)
        
        total_errors = 0
        for error_code, description, severity, count in stats:
            if count > 0:
                print(f"{error_code:<25} {count:<8} {severity:<10}")
                total_errors += count
        
        print("-" * 60)
        print(f"{'TOTAL':<25} {total_errors:<8}")
        
        translations = db_manager.get_translations()
        if translations:
            print(f"\nTranslations in database: {', '.join(translations)}")
        else:
            print("\nNo data in database. Run with --scan to analyze files.")
    
    db_manager.close()

if __name__ == "__main__":
    main()