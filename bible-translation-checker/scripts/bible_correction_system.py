#!/usr/bin/env python3
"""
Bible Text Correction System

A comprehensive system for Bible text correction with SQLite database storage,
error detection, and tkinter GUI editor.

Features:
- Complete database schema for Bible verses and error tracking
- JSON import from existing Bible files
- Advanced error detection and correction
- Full-featured tkinter GUI editor
- Export capabilities and statistics

Usage:
    python3 bible_correction_system.py
"""

import sqlite3
import json
import re
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import unicodedata
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import csv

@dataclass
class VerseData:
    """Represents a Bible verse with correction metadata"""
    id: Optional[int]
    translation: str
    book: str
    book_name: str
    chapter: int
    verse: int
    original_text: str
    corrected_text: Optional[str]
    last_modified: Optional[datetime]
    correction_notes: Optional[str]
    has_errors: bool

@dataclass
class ErrorInstance:
    """Represents an error instance in the database"""
    id: Optional[int]
    verse_id: int
    error_type_id: int
    status: str
    error_text: str
    context: str
    line_reference: str
    detected_date: datetime
    resolved_date: Optional[datetime]
    resolution_notes: Optional[str]

class BibleDatabaseManager:
    """Comprehensive database manager for Bible text correction system"""
    
    def __init__(self, db_path: str = "bible_correction.db"):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
        self.setup_error_types()
    
    def setup_database(self):
        """Initialize database connection and create all tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
        
        # Create complete schema
        self.conn.executescript("""
            -- Store translation metadata
            CREATE TABLE IF NOT EXISTS translations (
                abbrev TEXT PRIMARY KEY,
                full_name TEXT,
                source_file TEXT,
                imported_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                total_verses INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            );
            
            -- Store the actual Bible text
            CREATE TABLE IF NOT EXISTS bible_verses (
                id INTEGER PRIMARY KEY,
                translation TEXT,
                book TEXT,
                book_name TEXT,
                chapter INTEGER,
                verse INTEGER,
                original_text TEXT,
                corrected_text TEXT,
                last_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                correction_notes TEXT,
                has_errors BOOLEAN DEFAULT 0,
                FOREIGN KEY (translation) REFERENCES translations(abbrev),
                UNIQUE(translation, book, chapter, verse)
            );
            
            -- Define error types
            CREATE TABLE IF NOT EXISTS error_types (
                id INTEGER PRIMARY KEY,
                error_code TEXT UNIQUE,
                description TEXT,
                severity TEXT, -- CRITICAL, WARNING, INFO
                fix_suggestion TEXT
            );
            
            -- Track specific error instances
            CREATE TABLE IF NOT EXISTS error_instances (
                id INTEGER PRIMARY KEY,
                verse_id INTEGER,
                error_type_id INTEGER,
                status TEXT DEFAULT 'open', -- open, fixed, ignored
                error_text TEXT,
                context TEXT,
                line_reference TEXT, -- "KJV Gen 10:1, line 941"
                detected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_date DATETIME,
                resolution_notes TEXT,
                FOREIGN KEY (verse_id) REFERENCES bible_verses(id),
                FOREIGN KEY (error_type_id) REFERENCES error_types(id)
            );
            
            -- Summary statistics
            CREATE TABLE IF NOT EXISTS error_statistics (
                error_type_id INTEGER PRIMARY KEY,
                total_count INTEGER DEFAULT 0,
                open_count INTEGER DEFAULT 0,
                fixed_count INTEGER DEFAULT 0,
                ignored_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (error_type_id) REFERENCES error_types(id)
            );
            
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_bible_verses_translation ON bible_verses(translation);
            CREATE INDEX IF NOT EXISTS idx_bible_verses_book ON bible_verses(book);
            CREATE INDEX IF NOT EXISTS idx_bible_verses_errors ON bible_verses(has_errors);
            CREATE INDEX IF NOT EXISTS idx_error_instances_verse ON error_instances(verse_id);
            CREATE INDEX IF NOT EXISTS idx_error_instances_status ON error_instances(status);
            CREATE INDEX IF NOT EXISTS idx_error_instances_type ON error_instances(error_type_id);
        """)
        self.conn.commit()
    
    def setup_error_types(self):
        """Initialize predefined error types with fix suggestions"""
        error_types = [
            ("NUMBERS_IN_TEXT", "Numbers found in verse text", "WARNING", 
             "Remove or spell out numbers (e.g., '3' → 'three')"),
            ("INVALID_CHARS", "Invalid characters in text", "CRITICAL", 
             "Replace with standard punctuation or remove"),
            ("MULTIPLE_SPACES", "Multiple consecutive spaces", "WARNING", 
             "Replace with single space"),
            ("MISSING_VERSES", "Missing verses in sequence", "CRITICAL", 
             "Add missing verse or verify sequence"),
            ("DUPLICATE_VERSES", "Duplicate verses found", "CRITICAL", 
             "Remove duplicate or fix numbering"),
            ("CHAPTER_SEQUENCE", "Chapter sequence issues", "CRITICAL", 
             "Fix chapter numbering"),
            ("VERSE_TOO_SHORT", "Suspiciously short verse (< 3 chars)", "WARNING", 
             "Verify text completeness"),
            ("VERSE_TOO_LONG", "Suspiciously long verse (> 500 chars)", "WARNING", 
             "Check for merged verses"),
            ("HTML_XML_REMNANTS", "XML/HTML tags or entities found", "CRITICAL", 
             "Remove tags and decode entities"),
            ("WHITESPACE_ISSUES", "Leading/trailing whitespace", "WARNING", 
             "Trim whitespace"),
            ("ENCODING_PROBLEMS", "Unusual encoding/unicode characters", "WARNING", 
             "Fix character encoding"),
            ("EMPTY_CONTENT", "Empty verse, chapter, or book", "CRITICAL", 
             "Add content or remove entry"),
            ("STRUCTURE_VIOLATION", "JSON structure problems", "CRITICAL", 
             "Fix JSON structure"),
            ("DUPLICATE_CONTENT", "Identical verse content found", "WARNING", 
             "Verify if intentional duplication"),
            ("CAPITALIZATION_ISSUES", "Unusual capitalization patterns", "INFO", 
             "Review capitalization consistency"),
            ("NON_INTEGER_REFERENCE", "Non-integer verse/chapter numbers", "CRITICAL", 
             "Fix to integer values"),
            ("PUNCTUATION_ERRORS", "Missing or incorrect punctuation", "WARNING", 
             "Add or correct punctuation"),
            ("SPELLING_ERRORS", "Potential spelling mistakes", "WARNING", 
             "Correct spelling"),
            ("FORMATTING_ISSUES", "Text formatting problems", "WARNING", 
             "Fix formatting"),
        ]
        
        for error_code, description, severity, fix_suggestion in error_types:
            self.conn.execute(
                "INSERT OR IGNORE INTO error_types (error_code, description, severity, fix_suggestion) VALUES (?, ?, ?, ?)",
                (error_code, description, severity, fix_suggestion)
            )
        self.conn.commit()
    
    def import_json_file(self, json_path: Path, translation_abbrev: str = None, 
                        progress_callback=None) -> Dict[str, int]:
        """Import JSON Bible file into database"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                bible_data = json.load(f)
        except Exception as e:
            raise Exception(f"Failed to load JSON file: {e}")
        
        # Extract translation info
        trans_info = bible_data.get('translation_info', {})
        abbrev = translation_abbrev or trans_info.get('abbrev', json_path.stem.upper())
        full_name = trans_info.get('name', f"{abbrev} Translation")
        
        # Insert/update translation record
        self.conn.execute("""
            INSERT OR REPLACE INTO translations (abbrev, full_name, source_file, imported_date)
            VALUES (?, ?, ?, ?)
        """, (abbrev, full_name, str(json_path), datetime.now()))
        
        # Clear existing verses for this translation
        self.conn.execute("DELETE FROM bible_verses WHERE translation = ?", (abbrev,))
        
        # Import verses
        books = bible_data.get('books', {})
        total_verses = 0
        
        # Book name mapping
        book_names = {
            'Gen': 'Genesis', 'Exo': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deu': 'Deuteronomy',
            'Jos': 'Joshua', 'Jdg': 'Judges', 'Rut': 'Ruth', '1Sa': '1 Samuel', '2Sa': '2 Samuel',
            '1Ki': '1 Kings', '2Ki': '2 Kings', '1Ch': '1 Chronicles', '2Ch': '2 Chronicles',
            'Ezr': 'Ezra', 'Neh': 'Nehemiah', 'Est': 'Esther', 'Job': 'Job', 'Psa': 'Psalms',
            'Pro': 'Proverbs', 'Ecc': 'Ecclesiastes', 'Son': 'Song of Songs', 'Isa': 'Isaiah',
            'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Eze': 'Ezekiel', 'Dan': 'Daniel',
            'Hos': 'Hosea', 'Joe': 'Joel', 'Amo': 'Amos', 'Oba': 'Obadiah', 'Jon': 'Jonah',
            'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk', 'Zep': 'Zephaniah', 'Hag': 'Haggai',
            'Zec': 'Zechariah', 'Mal': 'Malachi', 'Mat': 'Matthew', 'Mar': 'Mark', 'Luk': 'Luke',
            'Joh': 'John', 'Act': 'Acts', 'Rom': 'Romans', '1Co': '1 Corinthians', '2Co': '2 Corinthians',
            'Gal': 'Galatians', 'Eph': 'Ephesians', 'Phi': 'Philippians', 'Col': 'Colossians',
            '1Th': '1 Thessalonians', '2Th': '2 Thessalonians', '1Ti': '1 Timothy', '2Ti': '2 Timothy',
            'Tit': 'Titus', 'Phm': 'Philemon', 'Heb': 'Hebrews', 'Jas': 'James', '1Pe': '1 Peter',
            '2Pe': '2 Peter', '1Jo': '1 John', '2Jo': '2 John', '3Jo': '3 John', 'Jde': 'Jude', 'Rev': 'Revelation'
        }
        
        verse_data = []
        for book_abbrev, book_data in books.items():
            book_name = book_names.get(book_abbrev, book_data.get('name', book_abbrev))
            chapters = book_data.get('chapters', {})
            
            for chapter_str, verses in chapters.items():
                try:
                    chapter_num = int(chapter_str)
                except ValueError:
                    continue
                
                for verse_str, verse_text in verses.items():
                    try:
                        verse_num = int(verse_str)
                    except ValueError:
                        continue
                    
                    if isinstance(verse_text, str) and verse_text.strip():
                        verse_data.append((
                            abbrev, book_abbrev, book_name, chapter_num, 
                            verse_num, verse_text, None, datetime.now(), None, False
                        ))
                        total_verses += 1
                        
                        # Progress callback
                        if progress_callback and total_verses % 100 == 0:
                            progress_callback(total_verses, "verses imported")
        
        # Bulk insert verses
        if verse_data:
            self.conn.executemany("""
                INSERT INTO bible_verses 
                (translation, book, book_name, chapter, verse, original_text, corrected_text, 
                 last_modified, correction_notes, has_errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, verse_data)
        
        # Update translation statistics
        self.conn.execute(
            "UPDATE translations SET total_verses = ? WHERE abbrev = ?", 
            (total_verses, abbrev)
        )
        
        self.conn.commit()
        
        return {
            'translation': abbrev,
            'total_verses': total_verses,
            'books': len(books)
        }
    
    def get_translations(self) -> List[Dict]:
        """Get all translations with statistics"""
        cursor = self.conn.execute("""
            SELECT abbrev, full_name, source_file, imported_date, total_verses, error_count
            FROM translations
            ORDER BY abbrev
        """)
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_verses(self, translation: str = None, book: str = None, 
                   chapter: int = None, has_errors: bool = None, 
                   limit: int = None, offset: int = 0) -> List[VerseData]:
        """Get verses with optional filtering"""
        query = """
            SELECT id, translation, book, book_name, chapter, verse, 
                   original_text, corrected_text, last_modified, correction_notes, has_errors
            FROM bible_verses
            WHERE 1=1
        """
        params = []
        
        if translation:
            query += " AND translation = ?"
            params.append(translation)
        
        if book:
            query += " AND book = ?"
            params.append(book)
        
        if chapter is not None:
            query += " AND chapter = ?"
            params.append(chapter)
        
        if has_errors is not None:
            query += " AND has_errors = ?"
            params.append(has_errors)
        
        query += " ORDER BY translation, book, chapter, verse"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        cursor = self.conn.execute(query, params)
        verses = []
        
        for row in cursor.fetchall():
            verses.append(VerseData(
                id=row[0],
                translation=row[1],
                book=row[2],
                book_name=row[3],
                chapter=row[4],
                verse=row[5],
                original_text=row[6],
                corrected_text=row[7],
                last_modified=datetime.fromisoformat(row[8]) if row[8] else None,
                correction_notes=row[9],
                has_errors=bool(row[10])
            ))
        
        return verses
    
    def update_verse(self, verse_id: int, corrected_text: str, 
                    correction_notes: str = None) -> bool:
        """Update a verse with corrected text"""
        try:
            self.conn.execute("""
                UPDATE bible_verses 
                SET corrected_text = ?, correction_notes = ?, last_modified = ?
                WHERE id = ?
            """, (corrected_text, correction_notes, datetime.now(), verse_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to update verse {verse_id}: {e}")
            return False
    
    def get_error_types(self) -> List[Dict]:
        """Get all error types"""
        cursor = self.conn.execute("""
            SELECT id, error_code, description, severity, fix_suggestion
            FROM error_types
            ORDER BY severity DESC, error_code
        """)
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def add_error_instance(self, verse_id: int, error_type_id: int, 
                          error_text: str, context: str, line_reference: str) -> int:
        """Add a new error instance"""
        cursor = self.conn.execute("""
            INSERT INTO error_instances 
            (verse_id, error_type_id, error_text, context, line_reference, detected_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (verse_id, error_type_id, error_text, context, line_reference, datetime.now()))
        
        # Mark verse as having errors
        self.conn.execute(
            "UPDATE bible_verses SET has_errors = 1 WHERE id = ?", (verse_id,)
        )
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_error_instances(self, verse_id: int = None, status: str = None, 
                           error_type_id: int = None) -> List[Dict]:
        """Get error instances with optional filtering"""
        query = """
            SELECT ei.id, ei.verse_id, ei.error_type_id, ei.status, ei.error_text, 
                   ei.context, ei.line_reference, ei.detected_date, ei.resolved_date, 
                   ei.resolution_notes, et.error_code, et.description, et.severity,
                   bv.translation, bv.book, bv.chapter, bv.verse
            FROM error_instances ei
            JOIN error_types et ON ei.error_type_id = et.id
            JOIN bible_verses bv ON ei.verse_id = bv.id
            WHERE 1=1
        """
        params = []
        
        if verse_id:
            query += " AND ei.verse_id = ?"
            params.append(verse_id)
        
        if status:
            query += " AND ei.status = ?"
            params.append(status)
        
        if error_type_id:
            query += " AND ei.error_type_id = ?"
            params.append(error_type_id)
        
        query += " ORDER BY ei.detected_date DESC"
        
        cursor = self.conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def resolve_error(self, error_id: int, status: str, resolution_notes: str = None) -> bool:
        """Mark an error as resolved"""
        try:
            self.conn.execute("""
                UPDATE error_instances 
                SET status = ?, resolved_date = ?, resolution_notes = ?
                WHERE id = ?
            """, (status, datetime.now(), resolution_notes, error_id))
            
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to resolve error {error_id}: {e}")
            return False
    
    def update_error_statistics(self):
        """Update error statistics table"""
        # Clear existing statistics
        self.conn.execute("DELETE FROM error_statistics")
        
        # Calculate new statistics
        self.conn.execute("""
            INSERT INTO error_statistics (error_type_id, total_count, open_count, fixed_count, ignored_count, last_updated)
            SELECT 
                et.id,
                COALESCE(total.cnt, 0),
                COALESCE(open.cnt, 0),
                COALESCE(fixed.cnt, 0),
                COALESCE(ignored.cnt, 0),
                CURRENT_TIMESTAMP
            FROM error_types et
            LEFT JOIN (
                SELECT error_type_id, COUNT(*) as cnt 
                FROM error_instances 
                GROUP BY error_type_id
            ) total ON et.id = total.error_type_id
            LEFT JOIN (
                SELECT error_type_id, COUNT(*) as cnt 
                FROM error_instances 
                WHERE status = 'open'
                GROUP BY error_type_id
            ) open ON et.id = open.error_type_id
            LEFT JOIN (
                SELECT error_type_id, COUNT(*) as cnt 
                FROM error_instances 
                WHERE status = 'fixed'
                GROUP BY error_type_id
            ) fixed ON et.id = fixed.error_type_id
            LEFT JOIN (
                SELECT error_type_id, COUNT(*) as cnt 
                FROM error_instances 
                WHERE status = 'ignored'
                GROUP BY error_type_id
            ) ignored ON et.id = ignored.error_type_id
        """)
        
        # Update translation error counts
        self.conn.execute("""
            UPDATE translations SET error_count = (
                SELECT COUNT(DISTINCT ei.id)
                FROM error_instances ei
                JOIN bible_verses bv ON ei.verse_id = bv.id
                WHERE bv.translation = translations.abbrev
                AND ei.status = 'open'
            )
        """)
        
        self.conn.commit()
    
    def get_error_statistics(self) -> List[Dict]:
        """Get error statistics"""
        cursor = self.conn.execute("""
            SELECT et.id, et.error_code, et.description, et.severity,
                   COALESCE(es.total_count, 0) as total_count,
                   COALESCE(es.open_count, 0) as open_count,
                   COALESCE(es.fixed_count, 0) as fixed_count,
                   COALESCE(es.ignored_count, 0) as ignored_count
            FROM error_types et
            LEFT JOIN error_statistics es ON et.id = es.error_type_id
            ORDER BY COALESCE(es.total_count, 0) DESC, et.error_code
        """)
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_verses(self, search_text: str, translation: str = None, 
                     search_corrected: bool = False, limit: int = 100) -> List[Dict]:
        """Search for verses containing specific text"""
        text_field = "corrected_text" if search_corrected else "original_text"
        
        query = f"""
            SELECT id, translation, book, book_name, chapter, verse, 
                   original_text, corrected_text, has_errors
            FROM bible_verses
            WHERE {text_field} LIKE ? COLLATE NOCASE
        """
        params = [f"%{search_text}%"]
        
        if translation:
            query += " AND translation = ?"
            params.append(translation)
        
        query += f" ORDER BY translation, book, chapter, verse LIMIT {limit}"
        
        cursor = self.conn.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def export_translation(self, translation: str, use_corrected: bool = True) -> Dict:
        """Export a translation back to JSON format"""
        # Get translation info
        trans_cursor = self.conn.execute(
            "SELECT abbrev, full_name FROM translations WHERE abbrev = ?", 
            (translation,)
        )
        trans_row = trans_cursor.fetchone()
        if not trans_row:
            raise ValueError(f"Translation {translation} not found")
        
        # Get all verses
        verses = self.get_verses(translation=translation)
        
        # Organize into JSON structure
        result = {
            "translation_info": {
                "abbrev": trans_row[0],
                "name": trans_row[1]
            },
            "books": {}
        }
        
        for verse in verses:
            text = verse.corrected_text if (use_corrected and verse.corrected_text) else verse.original_text
            
            # Initialize book if needed
            if verse.book not in result["books"]:
                result["books"][verse.book] = {
                    "name": verse.book_name,
                    "chapters": {}
                }
            
            # Initialize chapter if needed
            chapter_str = str(verse.chapter)
            if chapter_str not in result["books"][verse.book]["chapters"]:
                result["books"][verse.book]["chapters"][chapter_str] = {}
            
            # Add verse
            result["books"][verse.book]["chapters"][chapter_str][str(verse.verse)] = text
        
        return result
    
    def get_books(self, translation: str) -> List[Dict]:
        """Get list of books for a translation"""
        cursor = self.conn.execute("""
            SELECT DISTINCT book, book_name, 
                   MIN(chapter) as first_chapter, MAX(chapter) as last_chapter,
                   COUNT(*) as verse_count
            FROM bible_verses
            WHERE translation = ?
            GROUP BY book, book_name
            ORDER BY MIN(rowid)
        """, (translation,))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_chapters(self, translation: str, book: str) -> List[Dict]:
        """Get list of chapters for a book"""
        cursor = self.conn.execute("""
            SELECT chapter, COUNT(*) as verse_count,
                   SUM(CASE WHEN has_errors THEN 1 ELSE 0 END) as error_count
            FROM bible_verses
            WHERE translation = ? AND book = ?
            GROUP BY chapter
            ORDER BY chapter
        """, (translation, book))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

class ErrorDetectionEngine:
    """Advanced error detection engine for Bible text"""
    
    def __init__(self, db_manager: BibleDatabaseManager):
        self.db = db_manager
        self.error_types = {et['error_code']: et['id'] for et in db_manager.get_error_types()}
    
    def scan_translation(self, translation: str, progress_callback=None) -> Dict[str, int]:
        """Scan a translation for errors and store them in database"""
        # Clear existing errors for this translation
        verse_ids = [v.id for v in self.db.get_verses(translation=translation)]
        if verse_ids:
            placeholders = ','.join('?' * len(verse_ids))
            self.db.conn.execute(f"DELETE FROM error_instances WHERE verse_id IN ({placeholders})", verse_ids)
            self.db.conn.execute("UPDATE bible_verses SET has_errors = 0 WHERE translation = ?", (translation,))
            self.db.conn.commit()
        
        # Get all verses for this translation
        verses = self.db.get_verses(translation=translation)
        total_verses = len(verses)
        error_count = 0
        verse_hashes = {}  # For duplicate detection
        
        for i, verse in enumerate(verses):
            if progress_callback and i % 100 == 0:
                progress_callback(i, total_verses, f"Scanning {verse.book} {verse.chapter}:{verse.verse}")
            
            # Detect errors in this verse
            errors = self._detect_verse_errors(verse, verse_hashes)
            
            for error_code, error_text, context in errors:
                if error_code in self.error_types:
                    line_ref = f"{translation} {verse.book} {verse.chapter}:{verse.verse}"
                    self.db.add_error_instance(
                        verse.id, self.error_types[error_code], 
                        error_text, context, line_ref
                    )
                    error_count += 1
        
        # Update statistics
        self.db.update_error_statistics()
        
        return {
            'total_verses': total_verses,
            'errors_found': error_count
        }
    
    def _detect_verse_errors(self, verse: VerseData, verse_hashes: Dict) -> List[Tuple[str, str, str]]:
        """Detect errors in a single verse"""
        errors = []
        text = verse.original_text
        
        if not text or not text.strip():
            errors.append(("EMPTY_CONTENT", "Empty verse text", ""))
            return errors
        
        context = f"{verse.book} {verse.chapter}:{verse.verse}: {text[:100]}..."
        
        # Check for numbers in text
        if re.search(r'\d', text):
            numbers = re.findall(r'\d+', text)
            errors.append(("NUMBERS_IN_TEXT", f"Contains numbers: {numbers}", context))
        
        # Check for invalid characters
        if not re.match(r'^[a-zA-Z\s\.,;:!?\'"()\[\]\/\-–—""''…]*$', text):
            invalid_chars = set(char for char in text 
                              if not re.match(r'[a-zA-Z\s\.,;:!?\'"()\[\]\/\-–—""''…]', char))
            errors.append(("INVALID_CHARS", f"Invalid characters: {list(invalid_chars)}", context))
        
        # Check for multiple spaces
        if re.search(r'  +', text):
            errors.append(("MULTIPLE_SPACES", "Multiple consecutive spaces found", context))
        
        # Check verse length
        if len(text) < 3:
            errors.append(("VERSE_TOO_SHORT", f"Very short verse ({len(text)} chars)", context))
        elif len(text) > 500:
            errors.append(("VERSE_TOO_LONG", f"Very long verse ({len(text)} chars)", context))
        
        # Check for HTML/XML remnants
        if re.search(r'<[^>]+>|&[a-zA-Z]+;', text):
            errors.append(("HTML_XML_REMNANTS", "HTML/XML tags or entities found", context))
        
        # Check for whitespace issues
        if text != text.strip():
            errors.append(("WHITESPACE_ISSUES", "Leading or trailing whitespace", context))
        
        # Check for encoding problems
        unusual_chars = []
        for char in text:
            if ord(char) > 127:
                category = unicodedata.category(char)
                if category.startswith('C'):  # Control characters
                    unusual_chars.append(char)
        
        if unusual_chars:
            errors.append(("ENCODING_PROBLEMS", f"Unusual characters: {unusual_chars[:5]}", context))
        
        # Check for duplicate content
        if len(text.strip()) > 10:  # Skip very short verses
            text_hash = hash(text.strip().lower())
            location = f"{verse.book} {verse.chapter}:{verse.verse}"
            
            if text_hash in verse_hashes:
                original_location = verse_hashes[text_hash]
                errors.append(("DUPLICATE_CONTENT", f"Identical to {original_location}", context))
            else:
                verse_hashes[text_hash] = location
        
        # Check capitalization
        words = text.split()
        if len(words) > 2:
            all_caps_count = sum(1 for word in words if word.isupper() and len(word) > 1)
            if all_caps_count > len(words) * 0.3:  # More than 30% all caps
                errors.append(("CAPITALIZATION_ISSUES", f"Many capitalized words ({all_caps_count}/{len(words)})", context))
        
        return errors

def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Initialize database
    db_manager = BibleDatabaseManager()
    
    # Import GUI here to avoid circular imports
    from bible_correction_gui import BibleCorrectionGUI
    
    # Create and run GUI
    root = tk.Tk()
    app = BibleCorrectionGUI(root, db_manager)
    
    try:
        root.mainloop()
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()