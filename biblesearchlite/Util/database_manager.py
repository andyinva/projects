#!/usr/bin/env python3
"""
Database Manager for Bible Search Application
Handles all database operations including connection management, queries, and schema validation
"""

import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_subjects_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_subjects_database(self):
        """Initialize the subjects database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create subjects table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create subject_verses table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS subject_verses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject_id INTEGER,
                        verse_reference TEXT NOT NULL,
                        verse_text TEXT NOT NULL,
                        translation TEXT NOT NULL,
                        comments TEXT DEFAULT '',
                        order_index INTEGER DEFAULT 0,
                        FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
                    )
                """)
                
                conn.commit()
                self.logger.info("Subjects database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Error initializing subjects database: {e}")
            raise
    
    def get_verses_from_database(self, parsed_ref: Dict[str, Any]) -> List[Tuple]:
        """Get verses from database using parsed reference"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                verse_reference = f"{parsed_ref['book']} {parsed_ref['chapter']}:{parsed_ref['verse']}"
                cursor.execute("SELECT * FROM bible_verses WHERE verse = ?", (verse_reference,))
                
                results = cursor.fetchall()
                return results
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting verses from database: {e}")
            return []
    
    def search_bible_verses(self, query: str, params: List[Any]) -> List[Tuple]:
        """Execute a bible verse search query"""
        try:
            with self.get_connection() as conn:
                # Add REGEXP function to SQLite
                def regexp(expr, item):
                    if item is None:
                        return False
                    try:
                        import re
                        return bool(re.search(expr, str(item)))
                    except:
                        return False
                
                conn.create_function("REGEXP", 2, regexp)
                cursor = conn.cursor()
                cursor.execute(query, params)
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            self.logger.error(f"Error searching bible verses: {e}")
            return []
    
    def test_database_connection(self) -> bool:
        """Test database connection and basic query"""
        try:
            with self.get_connection() as conn:
                test_cursor = conn.cursor()
                test_cursor.execute("SELECT COUNT(*) FROM bible_verses WHERE king_james_bible LIKE '%light%'")
                result = test_cursor.fetchone()
                return result is not None
                
        except sqlite3.Error as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_all_subjects(self) -> List[str]:
        """Get all subject names from database"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM subjects ORDER BY name")
                return [row[0] for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting subjects: {e}")
            return []
    
    def create_or_get_subject_id(self, subject_name: str) -> Optional[int]:
        """Create subject if it doesn't exist, return subject ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if subject exists
                cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    # Create new subject
                    cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
                    conn.commit()
                    return cursor.lastrowid
                    
        except sqlite3.Error as e:
            self.logger.error(f"Error creating/getting subject: {e}")
            return None
    
    def add_verse_to_subject(self, subject_id: int, verse_reference: str, 
                           verse_text: str, translation: str, comments: str = "") -> bool:
        """Add a verse to a subject"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get next order index
                cursor.execute("SELECT MAX(order_index) FROM subject_verses WHERE subject_id = ?", (subject_id,))
                max_order = cursor.fetchone()[0]
                next_order = (max_order or 0) + 1
                
                # Insert verse
                cursor.execute("""
                    INSERT INTO subject_verses 
                    (subject_id, verse_reference, verse_text, translation, comments, order_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (subject_id, verse_reference, verse_text, translation, comments, next_order))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error adding verse to subject: {e}")
            return False
    
    def create_new_subject(self, subject_name: str) -> Optional[int]:
        """Create a new subject and return its ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
                
                subject_id = cursor.lastrowid
                conn.commit()
                return subject_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Error creating new subject: {e}")
            return None
    
    def add_verses_to_new_subject(self, subject_id: int, verses: List[Dict[str, str]]) -> bool:
        """Add multiple verses to a new subject"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                for i, verse in enumerate(verses):
                    cursor.execute("""
                        INSERT INTO subject_verses 
                        (subject_id, verse_reference, verse_text, translation, comments, order_index)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (subject_id, verse['reference'], verse['text'], 
                         verse['translation'], verse.get('comments', ''), i))
                
                conn.commit()
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Error adding verses to new subject: {e}")
            return False
    
    def get_subject_verses(self, subject_name: str) -> List[Tuple]:
        """Get all verses for a subject"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT sv.verse_reference, sv.verse_text, sv.translation, sv.comments, sv.order_index
                    FROM subject_verses sv
                    JOIN subjects s ON sv.subject_id = s.id
                    WHERE s.name = ?
                    ORDER BY sv.order_index
                """, (subject_name,))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting subject verses: {e}")
            return []
    
    def update_subject_verse_comments(self, subject_name: str, verse_reference: str, 
                                    translation: str, comments: str) -> bool:
        """Update comments for a specific verse in a subject"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE subject_verses 
                    SET comments = ?
                    WHERE subject_id = (SELECT id FROM subjects WHERE name = ?)
                    AND verse_reference = ? AND translation = ?
                """, (comments, subject_name, verse_reference, translation))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Error updating subject verse comments: {e}")
            return False
    
    def delete_verse_from_subject(self, subject_name: str, verse_reference: str, 
                                translation: str) -> bool:
        """Delete a verse from a subject"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM subject_verses 
                    WHERE subject_id = (SELECT id FROM subjects WHERE name = ?)
                    AND verse_reference = ? AND translation = ?
                """, (subject_name, verse_reference, translation))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting verse from subject: {e}")
            return False
    
    def delete_subject(self, subject_name: str) -> bool:
        """Delete a subject and all its verses"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM subjects WHERE name = ?", (subject_name,))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except sqlite3.Error as e:
            self.logger.error(f"Error deleting subject: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                info = {}
                
                # Get table count
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                info['tables'] = [table[0] for table in tables]
                
                # Get verse count if bible_verses table exists
                if 'bible_verses' in info['tables']:
                    cursor.execute("SELECT COUNT(*) FROM bible_verses")
                    info['verse_count'] = cursor.fetchone()[0]
                
                # Get subject count
                if 'subjects' in info['tables']:
                    cursor.execute("SELECT COUNT(*) FROM subjects")
                    info['subject_count'] = cursor.fetchone()[0]
                
                return info
                
        except sqlite3.Error as e:
            self.logger.error(f"Error getting database info: {e}")
            return {}