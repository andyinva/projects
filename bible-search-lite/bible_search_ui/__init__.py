"""
Bible Search - Verse-Centric Bible Study Application.

A PyQt6-based application for searching, reading, and organizing Bible verses.

Modules:
    ui: User interface components (widgets, dialogs)
    config: Configuration management
    controllers: Business logic controllers

Author: Andrew Hopkins
Email: ajhinva@gmail.com
"""

from .config import ConfigManager
from .controllers import SearchController, FormattedVerse

__version__ = '1.0.0'
__author__ = 'Andrew Hopkins'
__all__ = ['ConfigManager', 'SearchController', 'FormattedVerse']
