"""
User data controller for Bible Search application.

This module handles business logic for groups, subjects, and verses:
- Group management (create, select, delete)
- Subject management (create, select, delete)
- Verse acquisition from search/reading windows
- Data validation and error handling
- Signal emission for UI updates

Author: Andrew Hopkins
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any, Optional
import sqlite3


class UserDataController(QObject):
    """
    Controls all user data operations (groups, subjects, verses).
    
    This controller separates business logic from UI and database concerns.
    It uses UserDataService for database operations and emits signals
    for UI updates. Maintains current selections for context-aware operations.
    
    Signals:
        groups_loaded: Emitted with list of groups
        subjects_loaded: Emitted with list of subjects for current group
        verses_loaded: Emitted with list of verses for current subject
        operation_success: Emitted with success message
        operation_failed: Emitted with error message
        
    Example:
        >>> controller = UserDataController(user_data_service)
        >>> controller.groups_loaded.connect(on_groups_loaded)
        >>> controller.operation_success.connect(show_success_message)
        >>> controller.load_groups()
    """
    
    # Signals
    groups_loaded = pyqtSignal(list)  # List of group dicts
    subjects_loaded = pyqtSignal(list)  # List of subject dicts
    verses_loaded = pyqtSignal(list)  # List of verse dicts
    operation_success = pyqtSignal(str)  # Success message
    operation_failed = pyqtSignal(str)  # Error message
    
    def __init__(self, user_data_service, parent=None):
        """
        Initialize the user data controller.
        
        Args:
            user_data_service: UserDataService instance for database operations
            parent (QObject, optional): Parent QObject for Qt parenting
            
        Side Effects:
            - Stores reference to user data service
            - Initializes current selection tracking
        """
        super().__init__(parent)
        
        self.service = user_data_service
        
        # Current selections for context-aware operations
        self.current_group_id = None
        self.current_subject_id = None
        
    # ==================== GROUP OPERATIONS ====================
    
    def load_groups(self):
        """
        Load all groups from database and emit signal.
        
        Side Effects:
            - Queries database for all groups
            - Emits groups_loaded signal with group list
            - Emits operation_failed if database error occurs
            
        Example:
            >>> controller.load_groups()
            >>> # groups_loaded signal emitted with list of groups
        """
        try:
            groups = self.service.get_all_groups()
            self.groups_loaded.emit(groups)
            
        except Exception as e:
            self.operation_failed.emit(f"Failed to load groups: {str(e)}")
            
    def create_group(self, name: str, description: str = ""):
        """
        Create a new group.
        
        Args:
            name (str): Group name (must be unique)
            description (str, optional): Group description
            
        Side Effects:
            - Creates group in database
            - Emits operation_success if successful
            - Emits operation_failed if name exists or error occurs
            - Reloads groups list on success
            
        Example:
            >>> controller.create_group("Pauline Epistles", "Paul's letters")
            >>> # operation_success emitted with "Group 'Pauline Epistles' created"
            >>> # groups_loaded emitted with updated group list
        """
        if not name or not name.strip():
            self.operation_failed.emit("Group name cannot be empty")
            return
            
        try:
            group_id = self.service.create_group(name.strip(), description.strip())
            self.operation_success.emit(f"Group '{name}' created successfully")
            
            # Reload groups to update UI
            self.load_groups()
            
            # Optionally auto-select the new group
            self.select_group(group_id)
            
        except sqlite3.IntegrityError:
            self.operation_failed.emit(f"Group '{name}' already exists")
            
        except Exception as e:
            self.operation_failed.emit(f"Failed to create group: {str(e)}")
            
    def delete_group(self, group_id: int):
        """
        Delete a group and all its subjects and verses.
        
        Args:
            group_id (int): ID of group to delete
            
        Side Effects:
            - Deletes group from database (cascades to subjects/verses)
            - Clears current_group_id if deleted group was selected
            - Clears current_subject_id
            - Emits operation_success if successful
            - Emits operation_failed if error occurs
            - Reloads groups list on success
            
        Note:
            UI should confirm deletion before calling this method.
            
        Example:
            >>> # After user confirms deletion
            >>> controller.delete_group(group_id)
            >>> # operation_success emitted
            >>> # groups_loaded emitted with updated list
        """
        try:
            # Get group name for success message
            group = self.service.get_group_by_id(group_id)
            if not group:
                self.operation_failed.emit("Group not found")
                return
                
            group_name = group['group_name']
            
            # Delete the group
            if self.service.delete_group(group_id):
                # Clear selections if this was the current group
                if self.current_group_id == group_id:
                    self.current_group_id = None
                    self.current_subject_id = None
                    
                self.operation_success.emit(f"Group '{group_name}' deleted successfully")
                
                # Reload groups to update UI
                self.load_groups()
            else:
                self.operation_failed.emit("Failed to delete group")
                
        except Exception as e:
            self.operation_failed.emit(f"Failed to delete group: {str(e)}")
            
    def select_group(self, group_id: int):
        """
        Select a group as the current context.
        
        Args:
            group_id (int): ID of group to select
            
        Side Effects:
            - Sets current_group_id
            - Clears current_subject_id (group change resets subject)
            - Loads subjects for the selected group
            - Emits subjects_loaded signal
            
        Example:
            >>> controller.select_group(group_id)
            >>> # subjects_loaded emitted with subjects for this group
        """
        self.current_group_id = group_id
        self.current_subject_id = None  # Reset subject when group changes
        
        # Load subjects for this group
        self.load_subjects_for_group(group_id)
        
    # ==================== SUBJECT OPERATIONS ====================
    
    def load_subjects_for_group(self, group_id: int):
        """
        Load all subjects for a specific group.
        
        Args:
            group_id (int): ID of the group
            
        Side Effects:
            - Queries database for subjects in this group
            - Emits subjects_loaded signal with subject list
            - Emits operation_failed if database error occurs
            
        Example:
            >>> controller.load_subjects_for_group(group_id)
            >>> # subjects_loaded signal emitted with list of subjects
        """
        try:
            subjects = self.service.get_subjects_by_group(group_id)
            self.subjects_loaded.emit(subjects)
            
        except Exception as e:
            self.operation_failed.emit(f"Failed to load subjects: {str(e)}")
            
    def create_subject(self, name: str, description: str = ""):
        """
        Create a new subject in the current group.
        
        Args:
            name (str): Subject name (must be unique within group)
            description (str, optional): Subject description
            
        Side Effects:
            - Creates subject in database under current_group_id
            - Emits operation_success if successful
            - Emits operation_failed if no group selected, name exists, or error occurs
            - Reloads subjects list on success
            
        Example:
            >>> controller.select_group(group_id)
            >>> controller.create_subject("Grace", "Verses about grace")
            >>> # operation_success emitted
            >>> # subjects_loaded emitted with updated list
        """
        if not self.current_group_id:
            self.operation_failed.emit("No group selected. Please select a group first.")
            return
            
        if not name or not name.strip():
            self.operation_failed.emit("Subject name cannot be empty")
            return
            
        try:
            subject_id = self.service.create_subject(
                self.current_group_id,
                name.strip(),
                description.strip()
            )
            
            self.operation_success.emit(f"Subject '{name}' created successfully")
            
            # Reload subjects to update UI
            self.load_subjects_for_group(self.current_group_id)
            
            # Optionally auto-select the new subject
            self.select_subject(subject_id)
            
        except sqlite3.IntegrityError:
            self.operation_failed.emit(f"Subject '{name}' already exists in this group")
            
        except Exception as e:
            self.operation_failed.emit(f"Failed to create subject: {str(e)}")
            
    def delete_subject(self, subject_id: int):
        """
        Delete a subject and all its verses.
        
        Args:
            subject_id (int): ID of subject to delete
            
        Side Effects:
            - Deletes subject from database (cascades to verses)
            - Clears current_subject_id if deleted subject was selected
            - Emits operation_success if successful
            - Emits operation_failed if error occurs
            - Reloads subjects list on success
            
        Note:
            UI should confirm deletion before calling this method.
            
        Example:
            >>> # After user confirms deletion
            >>> controller.delete_subject(subject_id)
            >>> # operation_success emitted
            >>> # subjects_loaded emitted with updated list
        """
        try:
            # Get subject name for success message
            subject = self.service.get_subject_by_id(subject_id)
            if not subject:
                self.operation_failed.emit("Subject not found")
                return
                
            subject_name = subject['subject_name']
            
            # Delete the subject
            if self.service.delete_subject(subject_id):
                # Clear selection if this was the current subject
                if self.current_subject_id == subject_id:
                    self.current_subject_id = None
                    
                self.operation_success.emit(f"Subject '{subject_name}' deleted successfully")
                
                # Reload subjects to update UI
                if self.current_group_id:
                    self.load_subjects_for_group(self.current_group_id)
            else:
                self.operation_failed.emit("Failed to delete subject")
                
        except Exception as e:
            self.operation_failed.emit(f"Failed to delete subject: {str(e)}")
            
    def select_subject(self, subject_id: int):
        """
        Select a subject as the current context.
        
        Args:
            subject_id (int): ID of subject to select
            
        Side Effects:
            - Sets current_subject_id
            - Loads verses for the selected subject
            - Emits verses_loaded signal
            
        Example:
            >>> controller.select_subject(subject_id)
            >>> # verses_loaded emitted with verses for this subject
        """
        self.current_subject_id = subject_id
        
        # Load verses for this subject
        self.load_verses_for_subject(subject_id)
        
    # ==================== VERSE OPERATIONS ====================
    
    def load_verses_for_subject(self, subject_id: int):
        """
        Load all verses for a specific subject.
        
        Args:
            subject_id (int): ID of the subject
            
        Side Effects:
            - Queries database for verses in this subject
            - Emits verses_loaded signal with verse list
            - Emits operation_failed if database error occurs
            
        Example:
            >>> controller.load_verses_for_subject(subject_id)
            >>> # verses_loaded signal emitted with list of verses
        """
        try:
            verses = self.service.get_verses_by_subject(subject_id)
            self.verses_loaded.emit(verses)
            
        except Exception as e:
            self.operation_failed.emit(f"Failed to load verses: {str(e)}")
            
    def acquire_verses(self, verse_data_list: List[Dict[str, str]]):
        """
        Add multiple verses to the current subject.
        
        Args:
            verse_data_list (list): List of verse dictionaries with keys:
                - reference (str): e.g., "Gen 1:1"
                - translation (str): e.g., "KJV"
                - text (str): Full verse text
                
        Side Effects:
            - Adds verses to database under current_subject_id
            - Emits operation_success with count
            - Emits operation_failed if no subject selected or error occurs
            - Reloads verses list on success
            
        Example:
            >>> verses = [
            ...     {'reference': 'Gen 1:1', 'translation': 'KJV', 
            ...      'text': 'In the beginning...'},
            ...     {'reference': 'John 1:1', 'translation': 'KJV',
            ...      'text': 'In the beginning was the Word...'}
            ... ]
            >>> controller.acquire_verses(verses)
            >>> # operation_success emitted: "2 verses added to subject"
            >>> # verses_loaded emitted with updated list
        """
        if not self.current_subject_id:
            self.operation_failed.emit("No subject selected. Please select a subject first.")
            return
            
        if not verse_data_list:
            self.operation_failed.emit("No verses to acquire")
            return
            
        try:
            acquired_count = 0
            duplicate_count = 0
            
            # Get existing verses to check for duplicates
            existing_verses = self.service.get_verses_by_subject(self.current_subject_id)
            existing_set = {
                (v['verse_reference'], v['translation']) 
                for v in existing_verses
            }
            
            # Add each verse
            for verse_data in verse_data_list:
                reference = verse_data['reference']
                translation = verse_data['translation']
                text = verse_data['text']
                
                # Check for duplicate
                if (reference, translation) in existing_set:
                    duplicate_count += 1
                    continue
                
                # Add to database
                self.service.add_verse_to_subject(
                    self.current_subject_id,
                    reference,
                    translation,
                    text
                )
                acquired_count += 1
                existing_set.add((reference, translation))
            
            # Build success message
            if acquired_count > 0:
                message = f"Added {acquired_count} verse"
                if acquired_count != 1:
                    message += "s"
                message += " to subject"
                
                if duplicate_count > 0:
                    message += f" ({duplicate_count} duplicate"
                    if duplicate_count != 1:
                        message += "s"
                    message += " skipped)"
                    
                self.operation_success.emit(message)
                
                # Reload verses to update UI
                self.load_verses_for_subject(self.current_subject_id)
            else:
                if duplicate_count > 0:
                    self.operation_failed.emit(f"All {duplicate_count} verses already exist in subject")
                else:
                    self.operation_failed.emit("No verses were added")
                    
        except Exception as e:
            self.operation_failed.emit(f"Failed to acquire verses: {str(e)}")
            
    def delete_verse(self, verse_id: int):
        """
        Delete a verse from the current subject.
        
        Args:
            verse_id (int): ID of the subject_verse to delete
            
        Side Effects:
            - Deletes verse from database
            - Emits operation_success if successful
            - Emits operation_failed if error occurs
            - Reloads verses list on success
            
        Example:
            >>> controller.delete_verse(verse_id)
            >>> # operation_success emitted
            >>> # verses_loaded emitted with updated list
        """
        try:
            if self.service.delete_verse(verse_id):
                self.operation_success.emit("Verse removed from subject")
                
                # Reload verses to update UI
                if self.current_subject_id:
                    self.load_verses_for_subject(self.current_subject_id)
            else:
                self.operation_failed.emit("Failed to delete verse")
                
        except Exception as e:
            self.operation_failed.emit(f"Failed to delete verse: {str(e)}")
            
    # ==================== UTILITY METHODS ====================
    
    def get_current_group_id(self) -> Optional[int]:
        """
        Get the currently selected group ID.
        
        Returns:
            int: Current group ID, or None if no group selected
        """
        return self.current_group_id
        
    def get_current_subject_id(self) -> Optional[int]:
        """
        Get the currently selected subject ID.
        
        Returns:
            int: Current subject ID, or None if no subject selected
        """
        return self.current_subject_id
        
    def has_group_and_subject_selected(self) -> bool:
        """
        Check if both group and subject are selected.
        
        Returns:
            bool: True if both group and subject are selected
            
        Example:
            >>> if controller.has_group_and_subject_selected():
            ...     # Safe to acquire verses
            ...     controller.acquire_verses(verse_list)
        """
        return self.current_group_id is not None and self.current_subject_id is not None
