"""
User data service for Bible Search application.

This module handles all user_data.db operations including:
- Database creation and initialization
- Group management (create, read, update, delete)
- Subject management (create, read, update, delete)
- Subject verse management (add, read, delete)
- Sample data creation on first run

Author: Andrew Hopkins
"""

import sqlite3
import os
from typing import List, Dict, Optional, Any
from datetime import datetime


class UserDataService:
    """
    Manages all user_data.db database operations.
    
    This service provides a clean interface for managing user study data
    including groups (collections of subjects), subjects (topical studies),
    and verses (Bible passages collected under subjects).
    
    Features:
    - Automatic database creation on first run
    - Sample data for new users
    - Foreign key constraints for data integrity
    - Transaction support for data consistency
    - ISO timestamp formatting
    
    Example:
        >>> service = UserDataService("user_data.db")
        >>> 
        >>> # Create a group
        >>> group_id = service.create_group("New Testament", "NT studies")
        >>> 
        >>> # Create a subject in the group
        >>> subject_id = service.create_subject(group_id, "Prayer", "Verses about prayer")
        >>> 
        >>> # Add a verse to the subject
        >>> verse_id = service.add_verse_to_subject(
        ...     subject_id, "Mat 6:9", "KJV",
        ...     "Our Father which art in heaven..."
        ... )
    """
    
    # Sample data to create on first run
    SAMPLE_DATA = {
        "New Testament": {
            "description": "Studies from the New Testament",
            "subjects": ["Faith", "Prayer", "Love"]
        },
        "Old Testament": {
            "description": "Studies from the Old Testament",
            "subjects": ["Creation", "Covenant", "Prophecy"]
        }
    }
    
    def __init__(self, db_path: str = "user_data.db"):
        """
        Initialize the user data service.
        
        Args:
            db_path (str): Path to the user database file.
                Default is "user_data.db" in current directory.
                
        Side Effects:
            - Creates database file if it doesn't exist
            - Creates all tables if they don't exist
            - Creates sample data if database is new
            - Enables foreign key constraints
        """
        self.db_path = db_path
        self._create_tables()
        self._check_and_create_sample_data()
        
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection with foreign keys enabled.
        
        Returns:
            sqlite3.Connection: Database connection ready for use.
            
        Note:
            Foreign keys must be enabled for each connection.
            This ensures CASCADE deletes work correctly.
        """
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
        
    def _create_tables(self):
        """
        Create all required database tables if they don't exist.
        
        Tables created:
        - groups: Study groups (e.g., "New Testament")
        - subjects: Study subjects within groups (e.g., "Prayer")
        - subject_verses: Bible verses collected under subjects
        - verse_comments: Rich text comments for verses (Phase 3)
        - email_contacts: Contact list for sharing (Phase 5)
        - db_version: Database schema version tracking
        
        Side Effects:
            - Creates tables in database
            - Inserts initial db_version record
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_date TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0
            )
        """)
        
        # Subjects table (belongs to a group)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                subject_name TEXT NOT NULL,
                description TEXT,
                created_date TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE CASCADE,
                UNIQUE(group_id, subject_name)
            )
        """)
        
        # Subject verses (verses collected under a subject)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subject_verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                verse_reference TEXT NOT NULL,
                translation TEXT NOT NULL,
                verse_text TEXT NOT NULL,
                created_timestamp TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id) ON DELETE CASCADE
            )
        """)
        
        # Verse comments (for Phase 3)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verse_comments (
                comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_verse_id INTEGER NOT NULL,
                comment_text TEXT,
                created_date TEXT NOT NULL,
                modified_date TEXT,
                FOREIGN KEY (subject_verse_id) REFERENCES subject_verses(id) ON DELETE CASCADE
            )
        """)
        
        # Email contacts (for Phase 5)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS email_contacts (
                contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                notes TEXT,
                created_date TEXT NOT NULL
            )
        """)
        
        # Database version tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS db_version (
                version INTEGER PRIMARY KEY,
                updated_date TEXT NOT NULL
            )
        """)
        
        # Insert initial version if not exists
        cursor.execute("SELECT version FROM db_version WHERE version = 1")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO db_version (version, updated_date) VALUES (?, ?)",
                (1, self._get_timestamp())
            )
        
        conn.commit()
        conn.close()
        
    def _check_and_create_sample_data(self):
        """
        Create sample groups and subjects if database is empty.
        
        Checks if any groups exist. If not, creates sample data
        from SAMPLE_DATA dictionary. This gives new users a starting
        point and demonstrates the group/subject structure.
        
        Side Effects:
            - Creates sample groups if database is empty
            - Creates sample subjects under each group
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Check if any groups exist
        cursor.execute("SELECT COUNT(*) FROM groups")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create sample data
            for group_name, group_data in self.SAMPLE_DATA.items():
                group_id = self.create_group(group_name, group_data["description"])
                
                for subject_name in group_data["subjects"]:
                    self.create_subject(group_id, subject_name, "")
                    
        conn.close()
        
    def _get_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.
        
        Returns:
            str: ISO 8601 timestamp (e.g., "2025-12-09T15:30:00")
            
        Note:
            All timestamps in the database use this format for consistency.
        """
        return datetime.now().isoformat(timespec='seconds')
    
    # ==================== GROUP OPERATIONS ====================
    
    def create_group(self, name: str, description: str = "") -> int:
        """
        Create a new study group.
        
        Args:
            name (str): Group name (must be unique)
            description (str, optional): Group description
            
        Returns:
            int: ID of the newly created group
            
        Raises:
            sqlite3.IntegrityError: If group name already exists
            
        Example:
            >>> group_id = service.create_group(
            ...     "Pauline Epistles",
            ...     "Studies from Paul's letters"
            ... )
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO groups (group_name, description, created_date, sort_order)
               VALUES (?, ?, ?, ?)""",
            (name, description, self._get_timestamp(), 0)
        )
        
        group_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return group_id
        
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """
        Get all study groups ordered by sort_order.
        
        Returns:
            list: List of group dictionaries with keys:
                - group_id (int)
                - group_name (str)
                - description (str)
                - created_date (str)
                - sort_order (int)
                
        Example:
            >>> groups = service.get_all_groups()
            >>> for group in groups:
            ...     print(f"{group['group_name']}: {group['description']}")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT group_id, group_name, description, created_date, sort_order
               FROM groups
               ORDER BY sort_order, group_name"""
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        groups = []
        for row in rows:
            groups.append({
                'group_id': row[0],
                'group_name': row[1],
                'description': row[2],
                'created_date': row[3],
                'sort_order': row[4]
            })
            
        return groups
        
    def get_group_by_id(self, group_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific group by ID.
        
        Args:
            group_id (int): The group's database ID
            
        Returns:
            dict: Group dictionary with keys (see get_all_groups), or
                  None if group not found
                  
        Example:
            >>> group = service.get_group_by_id(1)
            >>> if group:
            ...     print(f"Found: {group['group_name']}")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT group_id, group_name, description, created_date, sort_order
               FROM groups
               WHERE group_id = ?""",
            (group_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'group_id': row[0],
                'group_name': row[1],
                'description': row[2],
                'created_date': row[3],
                'sort_order': row[4]
            }
        return None
        
    def delete_group(self, group_id: int) -> bool:
        """
        Delete a group and all its subjects and verses.
        
        Args:
            group_id (int): The group's database ID
            
        Returns:
            bool: True if deletion successful, False otherwise
            
        Side Effects:
            - Deletes the group
            - Cascades to delete all subjects in the group
            - Cascades to delete all verses in those subjects
            
        Note:
            This is a permanent deletion. Consider confirmation in UI.
            
        Example:
            >>> if service.delete_group(group_id):
            ...     print("Group and all its data deleted")
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error deleting group: {e}")
            return False
            
    def update_group(self, group_id: int, name: str, description: str) -> bool:
        """
        Update a group's name and description.
        
        Args:
            group_id (int): The group's database ID
            name (str): New group name
            description (str): New group description
            
        Returns:
            bool: True if update successful, False otherwise
            
        Raises:
            sqlite3.IntegrityError: If new name conflicts with existing group
            
        Example:
            >>> service.update_group(
            ...     group_id=1,
            ...     name="New Testament Studies",
            ...     description="Updated description"
            ... )
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """UPDATE groups 
                   SET group_name = ?, description = ?
                   WHERE group_id = ?""",
                (name, description, group_id)
            )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error updating group: {e}")
            return False
    
    # ==================== SUBJECT OPERATIONS ====================
    
    def create_subject(self, group_id: int, name: str, description: str = "") -> int:
        """
        Create a new subject within a group.
        
        Args:
            group_id (int): ID of the parent group
            name (str): Subject name (must be unique within the group)
            description (str, optional): Subject description
            
        Returns:
            int: ID of the newly created subject
            
        Raises:
            sqlite3.IntegrityError: If subject name exists in this group
            
        Note:
            Same subject name can exist in different groups.
            
        Example:
            >>> subject_id = service.create_subject(
            ...     group_id=1,
            ...     name="Grace",
            ...     description="Verses about God's grace"
            ... )
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO subjects (group_id, subject_name, description, created_date, sort_order)
               VALUES (?, ?, ?, ?, ?)""",
            (group_id, name, description, self._get_timestamp(), 0)
        )
        
        subject_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return subject_id
        
    def get_subjects_by_group(self, group_id: int) -> List[Dict[str, Any]]:
        """
        Get all subjects for a specific group.
        
        Args:
            group_id (int): The group's database ID
            
        Returns:
            list: List of subject dictionaries with keys:
                - subject_id (int)
                - group_id (int)
                - subject_name (str)
                - description (str)
                - created_date (str)
                - sort_order (int)
                
        Example:
            >>> subjects = service.get_subjects_by_group(group_id=1)
            >>> for subject in subjects:
            ...     print(f"  - {subject['subject_name']}")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT subject_id, group_id, subject_name, description, created_date, sort_order
               FROM subjects
               WHERE group_id = ?
               ORDER BY sort_order, subject_name""",
            (group_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        subjects = []
        for row in rows:
            subjects.append({
                'subject_id': row[0],
                'group_id': row[1],
                'subject_name': row[2],
                'description': row[3],
                'created_date': row[4],
                'sort_order': row[5]
            })
            
        return subjects
        
    def get_all_subjects(self) -> List[Dict[str, Any]]:
        """
        Get all subjects across all groups.
        
        Returns:
            list: List of subject dictionaries (see get_subjects_by_group)
            
        Note:
            Includes group_name for display purposes.
            Useful for subject search feature.
            
        Example:
            >>> all_subjects = service.get_all_subjects()
            >>> for subject in all_subjects:
            ...     print(f"{subject['group_name']} > {subject['subject_name']}")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT s.subject_id, s.group_id, s.subject_name, s.description, 
                      s.created_date, s.sort_order, g.group_name
               FROM subjects s
               JOIN groups g ON s.group_id = g.group_id
               ORDER BY g.group_name, s.subject_name"""
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        subjects = []
        for row in rows:
            subjects.append({
                'subject_id': row[0],
                'group_id': row[1],
                'subject_name': row[2],
                'description': row[3],
                'created_date': row[4],
                'sort_order': row[5],
                'group_name': row[6]
            })
            
        return subjects
        
    def get_subject_by_id(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific subject by ID.
        
        Args:
            subject_id (int): The subject's database ID
            
        Returns:
            dict: Subject dictionary, or None if not found
            
        Example:
            >>> subject = service.get_subject_by_id(5)
            >>> if subject:
            ...     print(f"Subject: {subject['subject_name']}")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT subject_id, group_id, subject_name, description, created_date, sort_order
               FROM subjects
               WHERE subject_id = ?""",
            (subject_id,)
        )
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'subject_id': row[0],
                'group_id': row[1],
                'subject_name': row[2],
                'description': row[3],
                'created_date': row[4],
                'sort_order': row[5]
            }
        return None
        
    def delete_subject(self, subject_id: int) -> bool:
        """
        Delete a subject and all its verses.
        
        Args:
            subject_id (int): The subject's database ID
            
        Returns:
            bool: True if deletion successful, False otherwise
            
        Side Effects:
            - Deletes the subject
            - Cascades to delete all verses in the subject
            
        Note:
            This is a permanent deletion. Consider confirmation in UI.
            
        Example:
            >>> if service.delete_subject(subject_id):
            ...     print("Subject and all verses deleted")
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error deleting subject: {e}")
            return False
            
    def update_subject(self, subject_id: int, name: str, description: str) -> bool:
        """
        Update a subject's name and description.
        
        Args:
            subject_id (int): The subject's database ID
            name (str): New subject name
            description (str): New subject description
            
        Returns:
            bool: True if update successful, False otherwise
            
        Raises:
            sqlite3.IntegrityError: If new name conflicts within same group
            
        Example:
            >>> service.update_subject(
            ...     subject_id=5,
            ...     name="Prayer and Fasting",
            ...     description="Updated description"
            ... )
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """UPDATE subjects 
                   SET subject_name = ?, description = ?
                   WHERE subject_id = ?""",
                (name, description, subject_id)
            )
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error updating subject: {e}")
            return False
    
    # ==================== SUBJECT VERSE OPERATIONS ====================
    
    def add_verse_to_subject(self, subject_id: int, verse_reference: str, 
                           translation: str, verse_text: str) -> int:
        """
        Add a Bible verse to a subject.
        
        Args:
            subject_id (int): ID of the subject to add verse to
            verse_reference (str): Verse reference (e.g., "Gen 1:1")
            translation (str): Translation abbreviation (e.g., "KJV")
            verse_text (str): Full text of the verse
            
        Returns:
            int: ID of the newly created subject_verse record
            
        Note:
            Duplicates are allowed - same verse can be added multiple times.
            Use get_verses_by_subject() to check for duplicates if needed.
            
        Example:
            >>> verse_id = service.add_verse_to_subject(
            ...     subject_id=3,
            ...     verse_reference="John 3:16",
            ...     translation="KJV",
            ...     verse_text="For God so loved the world..."
            ... )
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get next sort order
        cursor.execute(
            "SELECT MAX(sort_order) FROM subject_verses WHERE subject_id = ?",
            (subject_id,)
        )
        max_order = cursor.fetchone()[0]
        next_order = (max_order + 1) if max_order is not None else 0
        
        cursor.execute(
            """INSERT INTO subject_verses 
               (subject_id, verse_reference, translation, verse_text, created_timestamp, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (subject_id, verse_reference, translation, verse_text, self._get_timestamp(), next_order)
        )
        
        verse_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return verse_id
        
    def get_verses_by_subject(self, subject_id: int) -> List[Dict[str, Any]]:
        """
        Get all verses for a specific subject.
        
        Args:
            subject_id (int): The subject's database ID
            
        Returns:
            list: List of verse dictionaries with keys:
                - id (int): Database ID
                - subject_id (int)
                - verse_reference (str): e.g., "Gen 1:1"
                - translation (str): e.g., "KJV"
                - verse_text (str): Full verse text
                - created_timestamp (str): ISO timestamp
                - sort_order (int): Display order
                
        Example:
            >>> verses = service.get_verses_by_subject(subject_id=3)
            >>> for verse in verses:
            ...     print(f"{verse['translation']} {verse['verse_reference']}")
            ...     print(f"  {verse['verse_text'][:50]}...")
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, subject_id, verse_reference, translation, verse_text, 
                      created_timestamp, sort_order
               FROM subject_verses
               WHERE subject_id = ?
               ORDER BY sort_order""",
            (subject_id,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        verses = []
        for row in rows:
            verses.append({
                'id': row[0],
                'subject_id': row[1],
                'verse_reference': row[2],
                'translation': row[3],
                'verse_text': row[4],
                'created_timestamp': row[5],
                'sort_order': row[6]
            })
            
        return verses
        
    def delete_verse(self, verse_id: int) -> bool:
        """
        Delete a verse from a subject.
        
        Args:
            verse_id (int): The subject_verse's database ID
            
        Returns:
            bool: True if deletion successful, False otherwise
            
        Example:
            >>> if service.delete_verse(verse_id):
            ...     print("Verse removed from subject")
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM subject_verses WHERE id = ?", (verse_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            print(f"Error deleting verse: {e}")
            return False
