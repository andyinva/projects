"""
Dialog windows for Bible Search application.

This module contains popup dialog windows for user settings and configuration:
- TranslationSelectorDialog: Select which Bible translations to search
- FontSettingsDialog: Adjust font sizes for titles and Bible text

Author: Andrew Hopkins
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QCheckBox, QGridLayout, QGroupBox, QRadioButton,
                             QDialogButtonBox)
from PyQt6.QtCore import Qt


class TranslationSelectorDialog(QDialog):
    """
    Dialog for selecting which Bible translations to include in searches.
    
    Displays a grid of checkboxes for all available Bible translations,
    allowing users to select which versions they want to search. Includes
    convenience buttons for selecting all or none.
    
    Features:
    - Grid layout with up to 4 columns
    - Select All / Select None buttons
    - Validation (prevents empty selection)
    - Returns list of selected translation abbreviations
    
    Example:
        >>> dialog = TranslationSelectorDialog(
        ...     parent=self,
        ...     translations=bible_search.translations,
        ...     selected_translations=["KJV", "NIV"]
        ... )
        >>> if dialog.exec():
        ...     new_selections = dialog.get_selected_translations()
        ...     print(f"User selected: {new_selections}")
    """
    
    def __init__(self, parent, translations, selected_translations):
        """
        Initialize the translation selector dialog.
        
        Args:
            parent (QWidget): Parent window (usually main window)
            translations (list): List of Translation objects with:
                - abbreviation (str): Translation abbreviation (e.g., "KJV")
                - full_name (str): Full translation name (e.g., "King James Version")
            selected_translations (list): List of currently selected abbreviations
                
        Side Effects:
            - Creates modal dialog window
            - Blocks parent window until closed
        """
        super().__init__(parent)
        self.translations = translations
        self.selected_translations = selected_translations
        self.checkboxes = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """
        Create the dialog user interface.
        
        Layout structure:
        - Title bar (from QDialog)
        - Select All / Select None buttons (horizontal layout)
        - Translation checkboxes (4-column grid)
        - OK / Cancel buttons (dialog button box)
        """
        self.setWindowTitle("Select Translations")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Add "Select All" and "Select None" buttons
        select_buttons_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_none_btn = QPushButton("Select None")
        select_buttons_layout.addWidget(select_all_btn)
        select_buttons_layout.addWidget(select_none_btn)
        select_buttons_layout.addStretch()
        layout.addLayout(select_buttons_layout)

        # Create checkboxes for each translation in a grid
        grid = QGridLayout()
        row = 0
        col = 0
        max_cols = 4

        for translation in self.translations:
            # Create checkbox with full translation name
            cb = QCheckBox(f"{translation.abbreviation} - {translation.full_name}")
            cb.setChecked(translation.abbreviation in self.selected_translations)
            self.checkboxes[translation.abbreviation] = cb
            grid.addWidget(cb, row, col)

            # Move to next grid position
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        layout.addLayout(grid)

        # Connect select all/none buttons
        select_all_btn.clicked.connect(self.select_all)
        select_none_btn.clicked.connect(self.select_none)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def select_all(self):
        """
        Check all translation checkboxes.
        
        Side Effects:
            - Sets all checkboxes to checked state
        """
        for cb in self.checkboxes.values():
            cb.setChecked(True)
            
    def select_none(self):
        """
        Uncheck all translation checkboxes.
        
        Side Effects:
            - Sets all checkboxes to unchecked state
        """
        for cb in self.checkboxes.values():
            cb.setChecked(False)
    
    def get_selected_translations(self):
        """
        Return list of selected translation abbreviations.
        
        Returns:
            list: Translation abbreviations that are checked (e.g., ["KJV", "NIV", "ESV"])
                  If no translations are selected, returns ["KJV"] as default
                  
        Note:
            Always returns at least one translation to prevent empty searches.
        """
        selected = [
            abbrev for abbrev, cb in self.checkboxes.items() 
            if cb.isChecked()
        ]
        
        # Ensure at least one translation is selected
        if not selected:
            selected = ["KJV"]
            
        return selected


class FontSettingsDialog(QDialog):
    """
    Dialog for adjusting font sizes throughout the application.
    
    Provides separate radio button groups for:
    - Title font sizes (section headers like "2. Search Results")
    - Verse font sizes (Bible text and references)
    
    Each group offers 5 size options with 1-point increments.
    
    Example:
        >>> dialog = FontSettingsDialog(
        ...     parent=self,
        ...     title_font_sizes=[11, 12, 13, 14, 15],
        ...     verse_font_sizes=[9, 10, 11, 12, 13],
        ...     current_title_size=0,  # Index 0 = 11px
        ...     current_verse_size=1   # Index 1 = 10px
        ... )
        >>> if dialog.exec():
        ...     title_idx, verse_idx = dialog.get_font_sizes()
        ...     title_px = title_font_sizes[title_idx]
        ...     verse_px = verse_font_sizes[verse_idx]
    """
    
    def __init__(self, parent, title_font_sizes, verse_font_sizes, 
                 current_title_size, current_verse_size):
        """
        Initialize the font settings dialog.
        
        Args:
            parent (QWidget): Parent window (usually main window)
            title_font_sizes (list): Available title font sizes in pixels
                Example: [11, 12, 13, 14, 15]
            verse_font_sizes (list): Available verse font sizes in pixels
                Example: [9, 10, 11, 12, 13]
            current_title_size (int): Index of currently selected title size
            current_verse_size (int): Index of currently selected verse size
                
        Side Effects:
            - Creates modal dialog window
            - Blocks parent window until closed
        """
        super().__init__(parent)
        self.title_font_sizes = title_font_sizes
        self.verse_font_sizes = verse_font_sizes
        self.current_title_size = current_title_size
        self.current_verse_size = current_verse_size
        
        # Store radio button references
        self.title_buttons = []
        self.verse_buttons = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """
        Create the dialog user interface.
        
        Layout structure:
        - Title bar (from QDialog)
        - Title font size group (radio buttons in vertical layout)
        - Verse font size group (radio buttons in vertical layout)
        - OK / Cancel buttons (dialog button box)
        """
        self.setWindowTitle("Font Settings")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Title font size selector
        title_group = QGroupBox("Title Font Size")
        title_layout = QVBoxLayout()

        for i, size in enumerate(self.title_font_sizes):
            # Label shows size number and pixel value
            label = f"Size {i+1} ({size}px)"
            if i == 0:
                label += " - Current"
                
            rb = QRadioButton(label)
            if i == self.current_title_size:
                rb.setChecked(True)
                
            self.title_buttons.append(rb)
            title_layout.addWidget(rb)

        title_group.setLayout(title_layout)
        layout.addWidget(title_group)

        # Verse font size selector
        verse_group = QGroupBox("Bible Text Font Size")
        verse_layout = QVBoxLayout()

        for i, size in enumerate(self.verse_font_sizes):
            # Label shows size number and pixel value
            label = f"Size {i+1} ({size}px)"
            if i == 0:
                label += " - Current"
                
            rb = QRadioButton(label)
            if i == self.current_verse_size:
                rb.setChecked(True)
                
            self.verse_buttons.append(rb)
            verse_layout.addWidget(rb)

        verse_group.setLayout(verse_layout)
        layout.addWidget(verse_group)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def get_font_sizes(self):
        """
        Return the selected font size indices.
        
        Returns:
            tuple: (title_font_index, verse_font_index)
                - title_font_index (int): Index into title_font_sizes list
                - verse_font_index (int): Index into verse_font_sizes list
                
        Example:
            >>> title_idx, verse_idx = dialog.get_font_sizes()
            >>> title_px = title_font_sizes[title_idx]  # e.g., 12
            >>> verse_px = verse_font_sizes[verse_idx]  # e.g., 10
        """
        # Find which title radio button is selected
        title_size_index = self.current_title_size
        for i, rb in enumerate(self.title_buttons):
            if rb.isChecked():
                title_size_index = i
                break

        # Find which verse radio button is selected
        verse_size_index = self.current_verse_size
        for i, rb in enumerate(self.verse_buttons):
            if rb.isChecked():
                verse_size_index = i
                break

        return title_size_index, verse_size_index
