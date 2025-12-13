"""
Services module for Bible Search application.

This module contains service layer classes that handle database operations:
- UserDataService: Manages user_data.db (groups, subjects, verses)

Author: Andrew Hopkins
"""

from .user_data_service import UserDataService

__all__ = ['UserDataService']
