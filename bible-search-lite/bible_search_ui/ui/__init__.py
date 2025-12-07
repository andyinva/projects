"""
UI components for Bible Search application.

This package contains all PyQt6 user interface components:
- widgets: Reusable UI widgets (VerseItemWidget, VerseListWidget, SectionWidget)
- dialogs: Dialog windows (TranslationSelectorDialog, FontSettingsDialog)
- main_window: Main application window (to be created)
"""

from .widgets import VerseItemWidget, VerseListWidget, SectionWidget
from .dialogs import TranslationSelectorDialog, FontSettingsDialog

__all__ = [
    'VerseItemWidget', 
    'VerseListWidget', 
    'SectionWidget',
    'TranslationSelectorDialog',
    'FontSettingsDialog'
]
