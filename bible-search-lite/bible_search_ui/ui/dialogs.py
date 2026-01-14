"""
Dialog windows for Bible Search application.

This module contains popup dialog windows for user settings and configuration:
- TranslationSelectorDialog: Select which Bible translations to search
- FontSettingsDialog: Adjust font sizes for titles and Bible text

Author: Andrew Hopkins
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QCheckBox, QGridLayout, QGroupBox, QRadioButton,
                             QDialogButtonBox, QScrollArea, QWidget, QLabel, QMessageBox, QLineEdit, QTextEdit)
from PyQt6.QtCore import Qt

# Translation publication dates
TRANSLATION_DATES = {
    'ACV': '',
    'AKJ': '',
    'AND': '1864',
    'ASV': '1901',
    'BBE': '1949',
    'BIS': '1568',
    'BSB': '2016',
    'BST': '1844',
    'COV': '1535',
    'CPD': '2009',
    'DBT': '1890',
    'DRB': '1582-1610',
    'DRC': '1749-52',
    'ERV': '1881-85',
    'GEN': '1560',
    'GN2': '1599',
    'HAW': '1795',
    'JPS': '1917',
    'JUB': '2000',
    'KJA': '1611',
    'KJV': '1611',
    'KPC': '1900',
    'LEB': '2012',
    'LIT': '1985',
    'MKJ': '1962',
    'NET': '2005',
    'NHE': '2023',
    'NHJ': '2023',
    'NHM': '2023',
    'NOY': '1869',
    'OEB': '2010',
    'OEC': '2010',
    'RLT': '',
    'RNK': '',
    'ROT': '1902',
    'RWB': '1833',
    'TWE': '1904',
    'TYD': '1525',
    'TYN': '1526-30',
    'UKJ': '',
    'WBT': '1833',
    'WEB': '2020',
    'WNT': '1903',
    'WYC': '1382-95',
    'YLT': '1862'
}


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

        # Sort translations by date (most recent first, then oldest, then no date)
        def get_sort_key(translation):
            """
            Returns a sort key for translations.
            Most recent dates first, oldest last, no dates at the end.
            """
            abbrev = translation.abbreviation
            date = TRANSLATION_DATES.get(abbrev, '')

            if not date:
                # No date - sort to end (use year 0)
                return 0

            # Extract year from date string
            # Handle ranges like "1582-1610" by taking the end year
            if '-' in date:
                parts = date.split('-')
                # Get the last part (end year)
                year_str = parts[-1]
            else:
                year_str = date

            try:
                year = int(year_str)
                # Negate to sort most recent first
                return -year
            except ValueError:
                # If we can't parse it, treat as no date
                return 0

        sorted_translations = sorted(self.translations, key=get_sort_key)

        # Create checkboxes for each translation in a grid
        grid = QGridLayout()
        row = 0
        col = 0
        max_cols = 4

        for translation in sorted_translations:
            # Create checkbox with full translation name and date
            abbrev = translation.abbreviation
            date = TRANSLATION_DATES.get(abbrev, '')

            if date:
                label = f"{abbrev} - {translation.full_name} ({date})"
            else:
                label = f"{abbrev} - {translation.full_name}"

            cb = QCheckBox(label)
            cb.setChecked(abbrev in self.selected_translations)
            self.checkboxes[abbrev] = cb
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

# ============================================================================
# PHASE 1 ADDITIONS - Groups and Subjects Dialogs
# ============================================================================

class GroupDialog(QDialog):
    """
    Dialog for creating or editing study groups.
    
    Provides input fields for:
    - Group name (required, unique)
    - Description (optional)
    
    Modes:
    - "create": Create new group
    - "edit": Edit existing group
    
    Example:
        >>> dialog = GroupDialog(self, mode="create")
        >>> if dialog.exec():
        ...     name, description = dialog.get_values()
        ...     controller.create_group(name, description)
    """
    
    def __init__(self, parent=None, group_name="", description="", mode="create"):
        """
        Initialize the group dialog.
        
        Args:
            parent (QWidget, optional): Parent window
            group_name (str): Initial group name (for edit mode)
            description (str): Initial description (for edit mode)
            mode (str): "create" or "edit"
            
        Side Effects:
            - Creates modal dialog window
            - Blocks parent window until closed
        """
        super().__init__(parent)
        
        self.mode = mode
        self.setWindowTitle("Create Group" if mode == "create" else "Edit Group")
        self.setMinimumWidth(400)
        
        self.setup_ui(group_name, description)
        
    def setup_ui(self, group_name, description):
        """
        Create the dialog user interface.
        
        Args:
            group_name (str): Initial group name value
            description (str): Initial description value
            
        Layout structure:
        - Title bar (from QDialog)
        - Group name label and input (single line)
        - Description label and input (multi-line)
        - OK / Cancel buttons
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Group name input (required)
        name_label = QLabel("Group Name: (required)")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(group_name)
        self.name_input.setPlaceholderText("e.g., New Testament, Pauline Epistles")
        layout.addWidget(self.name_input)
        
        # Description input (optional)
        desc_label = QLabel("Description: (optional)")
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlainText(description)
        self.description_input.setPlaceholderText("Optional description for this group...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to name input
        self.name_input.setFocus()
        
    def validate_and_accept(self):
        """
        Validate input and accept dialog if valid.
        
        Validation rules:
        - Group name cannot be empty
        - Group name cannot be only whitespace
        
        Side Effects:
            - Shows error message if validation fails
            - Accepts dialog if validation passes
        """
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Group name cannot be empty."
            )
            self.name_input.setFocus()
            return
            
        self.accept()
        
    def get_values(self):
        """
        Get the entered group name and description.
        
        Returns:
            tuple: (name, description) both as stripped strings
            
        Example:
            >>> if dialog.exec():
            ...     name, description = dialog.get_values()
            ...     print(f"Creating group: {name}")
        """
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        return (name, description)


class SubjectDialog(QDialog):
    """
    Dialog for creating or editing study subjects.
    
    Provides input fields for:
    - Subject name (required, unique within group)
    - Description (optional)
    
    Modes:
    - "create": Create new subject
    - "edit": Edit existing subject
    
    Example:
        >>> dialog = SubjectDialog(self, mode="create")
        >>> if dialog.exec():
        ...     name, description = dialog.get_values()
        ...     controller.create_subject(name, description)
    """
    
    def __init__(self, parent=None, subject_name="", description="", mode="create"):
        """
        Initialize the subject dialog.
        
        Args:
            parent (QWidget, optional): Parent window
            subject_name (str): Initial subject name (for edit mode)
            description (str): Initial description (for edit mode)
            mode (str): "create" or "edit"
            
        Side Effects:
            - Creates modal dialog window
            - Blocks parent window until closed
        """
        super().__init__(parent)
        
        self.mode = mode
        self.setWindowTitle("Create Subject" if mode == "create" else "Edit Subject")
        self.setMinimumWidth(400)
        
        self.setup_ui(subject_name, description)
        
    def setup_ui(self, subject_name, description):
        """
        Create the dialog user interface.
        
        Args:
            subject_name (str): Initial subject name value
            description (str): Initial description value
            
        Layout structure:
        - Title bar (from QDialog)
        - Subject name label and input (single line)
        - Description label and input (multi-line)
        - OK / Cancel buttons
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Subject name input (required)
        name_label = QLabel("Subject Name: (required)")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setText(subject_name)
        self.name_input.setPlaceholderText("e.g., Prayer, Faith, Grace")
        layout.addWidget(self.name_input)
        
        # Description input (optional)
        desc_label = QLabel("Description: (optional)")
        layout.addWidget(desc_label)
        
        self.description_input = QTextEdit()
        self.description_input.setPlainText(description)
        self.description_input.setPlaceholderText("Optional description for this subject...")
        self.description_input.setMaximumHeight(100)
        layout.addWidget(self.description_input)
        
        # OK/Cancel buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Set focus to name input
        self.name_input.setFocus()
        
    def validate_and_accept(self):
        """
        Validate input and accept dialog if valid.
        
        Validation rules:
        - Subject name cannot be empty
        - Subject name cannot be only whitespace
        
        Side Effects:
            - Shows error message if validation fails
            - Accepts dialog if validation passes
        """
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(
                self,
                "Validation Error",
                "Subject name cannot be empty."
            )
            self.name_input.setFocus()
            return
            
        self.accept()
        
    def get_values(self):
        """
        Get the entered subject name and description.
        
        Returns:
            tuple: (name, description) both as stripped strings
            
        Example:
            >>> if dialog.exec():
            ...     name, description = dialog.get_values()
            ...     print(f"Creating subject: {name}")
        """
        name = self.name_input.text().strip()
        description = self.description_input.toPlainText().strip()
        return (name, description)


class SearchFilterDialog(QDialog):
    """
    Dialog for filtering search results by word variations.

    Shows all unique words found in search results with their counts,
    allowing users to uncheck words they want to exclude from the results.

    Features:
    - Scrollable list of words with checkboxes
    - Word counts displayed next to each word
    - "Uncheck All" button for quick deselection
    - Returns list of selected words to filter by

    Example:
        >>> word_counts = {"Send": 15, "Sending": 10, "Sent": 25}
        >>> dialog = SearchFilterDialog(self, word_counts)
        >>> if dialog.exec():
        ...     selected_words = dialog.get_selected_words()
        ...     # Re-filter search results using selected_words
    """

    def __init__(self, parent, word_counts):
        """
        Initialize the search filter dialog.

        Args:
            parent (QWidget): Parent window
            word_counts (dict): Dictionary mapping words to their occurrence counts
                Example: {"Send": 15, "Sending": 10, "Sent": 25}
        """
        super().__init__(parent)
        self.word_counts = word_counts
        self.checkboxes = {}  # Map word -> checkbox widget
        self.setup_ui()

    def setup_ui(self):
        """Create the dialog user interface."""
        self.setWindowTitle("Filter Search Results")
        self.setMinimumWidth(400)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)

        # Header label - show number of unique word variations found
        total_verses = sum(self.word_counts.values())
        header = QLabel(f"Found {len(self.word_counts)} word variation(s) in {total_verses} verse(s). Uncheck words to exclude:")
        header.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(header)

        # Scrollable area for word checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ccc; }")

        # Container widget for checkboxes
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(2)

        # Sort words alphabetically for display
        sorted_words = sorted(self.word_counts.keys())

        # Create checkbox for each word
        for word in sorted_words:
            count = self.word_counts[word]
            cb = QCheckBox(f"{word} ({count})")
            cb.setChecked(True)  # All checked by default
            cb.setStyleSheet("padding: 3px;")
            self.checkboxes[word] = cb
            container_layout.addWidget(cb)

        container_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Button layout
        button_layout = QHBoxLayout()

        # Uncheck All button
        uncheck_all_btn = QPushButton("Uncheck All")
        uncheck_all_btn.clicked.connect(self.uncheck_all)
        uncheck_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #999;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        button_layout.addWidget(uncheck_all_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def uncheck_all(self):
        """Uncheck all word checkboxes."""
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def get_selected_words(self):
        """
        Get list of words that are currently checked.

        Returns:
            list: List of word strings that have checkboxes checked
        """
        selected = []
        for word, cb in self.checkboxes.items():
            if cb.isChecked():
                selected.append(word)
        return selected


# END OF ADDITIONS TO dialogs.py
