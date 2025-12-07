"""
Custom PyQt6 widgets for Bible Search application.

This module contains reusable UI components for displaying and managing Bible verses:
- VerseItemWidget: Individual verse display with checkbox selection
- VerseListWidget: Scrollable container for multiple verses
- SectionWidget: Titled frame container for organizing UI sections

Author: Andrew Hopkins
"""

from PyQt6.QtWidgets import (QWidget, QLabel, QCheckBox, QVBoxLayout, 
                             QHBoxLayout, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class VerseItemWidget(QWidget):
    """
    Individual verse display with checkbox and formatted text.
    
    Displays a single Bible verse in a consistent format with:
    - Checkbox for selection
    - Translation abbreviation (e.g., KJV, NIV)
    - Book abbreviation (e.g., Gen, Mat)
    - Chapter and verse numbers
    - Full verse text with word wrapping
    
    Signals:
        selection_changed(str, bool): Emitted when checkbox state changes
            Args:
                verse_id (str): Unique identifier for this verse
                is_selected (bool): New selection state
                
        verse_clicked(str): Emitted when verse is clicked for navigation
            Args:
                verse_id (str): Unique identifier for this verse
    
    Example:
        >>> verse = VerseItemWidget(
        ...     verse_id="search_1",
        ...     translation="KJV",
        ...     book_abbrev="Gen",
        ...     chapter=1,
        ...     verse_number=1,
        ...     text="In the beginning God created the heaven and the earth."
        ... )
        >>> verse.selection_changed.connect(on_selection_changed)
    """
    
    selection_changed = pyqtSignal(str, bool)  # verse_id, is_selected
    verse_clicked = pyqtSignal(str)  # verse_id for navigation
    
    def __init__(self, verse_id, translation, book_abbrev, chapter, verse_number, 
                 text, window_id=None, parent=None):
        """
        Initialize a verse display widget.
        
        Args:
            verse_id (str): Unique identifier for this verse
            translation (str): Bible translation abbreviation (e.g., "KJV")
            book_abbrev (str): Book abbreviation (e.g., "Gen", "Mat")
            chapter (int): Chapter number
            verse_number (int): Verse number within the chapter
            text (str): Full verse text to display
            window_id (str, optional): ID of the parent window (e.g., "search", "reading")
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.verse_id = verse_id
        self.translation = translation
        self.book_abbrev = book_abbrev
        self.chapter = chapter
        self.verse_number = verse_number
        self.text = text
        self.window_id = window_id  # Store which window this verse belongs to

        self.setup_ui()
        self.setup_styling()
        
    def setup_ui(self):
        """
        Create the widget layout with checkbox, reference, and text.
        
        Layout structure:
        - Checkbox (20px fixed width)
        - Reference label (110px fixed width)
        - Verse text (expandable with word wrap)
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Checkbox (fixed width for alignment)
        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(20)
        self.checkbox.setStyleSheet("""
            QCheckBox {
                background-color: transparent;
                border: none;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #999;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
            }
        """)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Reference label (fixed width for column alignment)
        ref_text = f"{self.translation} {self.book_abbrev} {self.chapter}:{self.verse_number}"
        self.reference_label = QLabel(ref_text)
        self.reference_label.setFixedWidth(110)
        self.reference_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.reference_label, alignment=Qt.AlignmentFlag.AlignTop)
        
        # Verse text (expandable with word wrap)
        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.text_label.setMinimumHeight(20)
        layout.addWidget(self.text_label, stretch=1)
        
        # Make the entire widget clickable for navigation
        self.mousePressEvent = self.on_verse_clicked
        
    def setup_styling(self):
        """
        Apply styling to the verse item.
        
        Styles include:
        - White background with gray bottom border
        - Hover effect (light gray background)
        - Font sizes and colors for reference and text
        """
        self.setStyleSheet("""
            VerseItemWidget {
                background-color: white;
                border-bottom: 1px solid #e0e0e0;
                padding: 2px;
            }
            VerseItemWidget:hover {
                background-color: #f5f5f5;
            }
            QLabel {
                background-color: transparent;
                color: #333;
            }
        """)
        
        # Style the reference label
        font = QFont("Arial")
        font.setBold(False)
        font.setPointSize(9)
        self.reference_label.setFont(font)
        self.reference_label.setStyleSheet("color: black;")

        # Style the text label - same size as reference
        text_font = QFont("Arial")
        text_font.setPointSize(9)
        self.text_label.setFont(text_font)
        
    def on_checkbox_changed(self, state):
        """
        Handle checkbox state change and emit selection_changed signal.
        
        Args:
            state (int): Qt.CheckState value (Checked or Unchecked)
            
        Side Effects:
            - Emits selection_changed signal
            - Updates visual styling to show selection
        """
        is_selected = state == Qt.CheckState.Checked.value
        self.selection_changed.emit(self.verse_id, is_selected)
        
        # Update visual feedback for selection
        if is_selected:
            self.setStyleSheet("""
                VerseItemWidget {
                    background-color: #e6f3ff;
                    border-bottom: 1px solid #b3d9ff;
                    border-left: 3px solid #0078d4;
                    padding: 2px;
                }
            """)
        else:
            self.setup_styling()
            
    def on_verse_clicked(self, event):
        """
        Handle verse click for navigation and selection.
        
        Args:
            event (QMouseEvent): Mouse press event
            
        Side Effects:
            - Emits verse_clicked signal for navigation
        """
        # Just emit the navigation signal - checkbox toggling handled by VerseListWidget
        self.verse_clicked.emit(self.verse_id)
        
    def set_selected(self, selected):
        """
        Set checkbox state programmatically.
        
        Args:
            selected (bool): True to check the checkbox, False to uncheck
        """
        self.checkbox.setChecked(selected)
        
    def is_selected(self):
        """
        Return current selection state.
        
        Returns:
            bool: True if checkbox is checked, False otherwise
        """
        return self.checkbox.isChecked()
        
    def get_verse_reference(self):
        """
        Return formatted verse reference.
        
        Returns:
            str: Formatted reference (e.g., "KJV Gen 1:1")
        """
        return f"{self.translation} {self.book_abbrev} {self.chapter}:{self.verse_number}"
        
    def highlight_search_terms(self, search_terms):
        """
        Highlight search terms in the verse text.
        
        Args:
            search_terms (list): List of terms to highlight
            
        Note:
            In a full implementation, this would use HTML or rich text formatting.
            Currently implements simple text replacement.
        """
        if not search_terms:
            return

        text = self.text
        for term in search_terms:
            # Simple highlighting - in full implementation would use HTML or rich text
            text = text.replace(term, f"<b><u>{term}</u></b>")

        self.text_label.setText(text)

    def set_highlighted(self, highlighted):
        """
        Highlight this verse as the navigation target.
        
        Args:
            highlighted (bool): True to highlight, False to remove highlighting
            
        Side Effects:
            - Changes background color and border
            - Provides visual feedback for current navigation position
        """
        if highlighted:
            self.setStyleSheet("""
                VerseItemWidget {
                    background-color: #FFFF99;
                    border-bottom: 1px solid #FFD700;
                    border-left: 3px solid #FF8C00;
                    padding: 2px;
                }
                VerseItemWidget:hover {
                    background-color: #FFFF99;
                }
            """)
        else:
            self.setup_styling()


class VerseListWidget(QWidget):
    """
    Container widget for managing multiple verse items.
    
    Provides a scrollable list of VerseItemWidget instances with:
    - Automatic selection tracking
    - Batch operations (select all, select none)
    - Active/inactive visual states
    - Scroll-to-verse functionality
    
    Signals:
        selection_changed(): Emitted when any verse selection changes
        verse_navigation_requested(str): Emitted when navigation to a verse is requested
            Args:
                verse_id (str): Verse to navigate to
    
    Example:
        >>> verse_list = VerseListWidget("search")
        >>> verse_list.add_verse("v1", "KJV", "Gen", 1, 1, "In the beginning...")
        >>> verse_list.selection_changed.connect(on_selection_changed)
    """
    
    selection_changed = pyqtSignal()  # Emitted when selection changes
    verse_navigation_requested = pyqtSignal(str)  # verse_id for navigation
    
    def __init__(self, window_id, parent=None):
        """
        Initialize the verse list container.
        
        Args:
            window_id (str): Identifier for this window (e.g., "search", "reading", "subject")
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.window_id = window_id
        self.verse_items = {}  # verse_id -> VerseItemWidget
        self.selected_verses = set()  # Set of selected verse_ids
        
        self.setup_ui()
        
    def setup_ui(self):
        """
        Create the scrollable list layout.
        
        Structure:
        - Main layout contains scroll area
        - Scroll area contains content widget
        - Content widget has vertical layout for verses
        """
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Create content widget for verses
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addStretch()  # Push items to top
        
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        
        # Styling
        self.setStyleSheet("""
            VerseListWidget {
                background-color: white;
                border: 2px solid #ccc;
            }
            VerseListWidget:focus {
                border: 2px solid #0078d4;
            }
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
        
    def add_verse(self, verse_id, translation, book_abbrev, chapter, verse_number, text):
        """
        Add a verse to the list.
        
        Args:
            verse_id (str): Unique identifier for the verse
            translation (str): Bible translation abbreviation
            book_abbrev (str): Book abbreviation
            chapter (int): Chapter number
            verse_number (int): Verse number
            text (str): Full verse text
            
        Note:
            If verse_id already exists, the verse is not added again
        """
        if verse_id in self.verse_items:
            return  # Verse already exists

        verse_item = VerseItemWidget(verse_id, translation, book_abbrev, chapter, 
                                     verse_number, text, window_id=self.window_id)
        verse_item.selection_changed.connect(self.on_verse_selection_changed)
        verse_item.verse_clicked.connect(self.on_verse_clicked)
        
        # Insert before the stretch at the end
        self.content_layout.insertWidget(self.content_layout.count() - 1, verse_item)
        self.verse_items[verse_id] = verse_item
        
    def on_verse_selection_changed(self, verse_id, is_selected):
        """
        Handle individual verse selection change.
        
        Args:
            verse_id (str): Verse that changed selection
            is_selected (bool): New selection state
            
        Side Effects:
            - Updates selected_verses set
            - Emits selection_changed signal
            - Makes this window active in main window
        """
        if is_selected:
            self.selected_verses.add(verse_id)
        else:
            self.selected_verses.discard(verse_id)
            
        self.selection_changed.emit()
        
        # Make this window active when a checkbox is clicked
        if hasattr(self, 'main_window'):
            self.main_window.set_active_window(self.window_id)
            # Directly call button update to ensure it triggers
            self.main_window.update_acquire_button_state()
        
    def on_verse_clicked(self, verse_id):
        """
        Handle verse click for navigation.
        
        Args:
            verse_id (str): Verse that was clicked
            
        Side Effects:
            - Makes this window active
            - Updates acquire button state
            - Emits verse_navigation_requested signal
        """
        if hasattr(self, 'main_window'):
            # Make this window active when a verse is clicked
            self.main_window.set_active_window(self.window_id)
            # Update button state
            self.main_window.update_acquire_button_state()

        # Emit navigation signal (no checkbox toggling - user must click checkbox directly)
        self.verse_navigation_requested.emit(verse_id)
        
    def clear_verses(self):
        """
        Remove all verses from the list.
        
        Side Effects:
            - Removes all verse widgets
            - Clears verse_items dictionary
            - Clears selected_verses set
            - Emits selection_changed signal
        """
        for verse_item in self.verse_items.values():
            verse_item.setParent(None)
        self.verse_items.clear()
        self.selected_verses.clear()
        self.selection_changed.emit()
        
    def get_selected_verses(self):
        """
        Return list of selected verse IDs.
        
        Returns:
            list: List of verse_id strings for all selected verses
        """
        return list(self.selected_verses)
        
    def select_all(self):
        """
        Select all verses in the list.
        
        Side Effects:
            - Checks all verse checkboxes
            - Updates selection state for all verses
        """
        for verse_item in self.verse_items.values():
            verse_item.set_selected(True)
            
    def select_none(self):
        """
        Deselect all verses in the list.
        
        Side Effects:
            - Unchecks all verse checkboxes
            - Clears selection state for all verses
        """
        for verse_item in self.verse_items.values():
            verse_item.set_selected(False)
            
    def get_verse_count(self):
        """
        Return total number of verses.
        
        Returns:
            int: Total number of verses in the list
        """
        return len(self.verse_items)
        
    def get_selected_count(self):
        """
        Return number of selected verses.
        
        Returns:
            int: Number of currently selected verses
        """
        return len(self.selected_verses)
        
    def set_active(self, is_active):
        """
        Set visual state for active/inactive window.
        
        Args:
            is_active (bool): True for active state, False for inactive
            
        Side Effects:
            - Changes border color and background
            - Enables/disables scrolling for search and reading windows
            - Forces visual update
        """
        if is_active:
            # Use direct property setting instead of CSS
            self.setStyleSheet("")  # Clear any existing styles
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 3px solid #0078d4;
                    background-color: #f0f8ff;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: #f0f8ff;
                }
            """)
            # Enable scrolling when active
            self.scroll_area.verticalScrollBar().setEnabled(True)
        else:
            self.setStyleSheet("")  # Clear any existing styles
            self.scroll_area.setStyleSheet("""
                QScrollArea {
                    border: 2px solid #ccc;
                    background-color: white;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: white;
                }
            """)
            # Disable scrolling when inactive (only for search and reading windows)
            if self.window_id in ['search', 'reading']:
                self.scroll_area.verticalScrollBar().setEnabled(False)

        # Force update
        self.scroll_area.update()
        self.update()
            
    def scroll_to_verse(self, verse_id):
        """
        Scroll to show a specific verse at the top of the scroll area.
        
        Args:
            verse_id (str): Verse to scroll to
            
        Side Effects:
            - Adjusts scroll position to show the specified verse
        """
        if verse_id in self.verse_items:
            verse_item = self.verse_items[verse_id]
            # Get the position of the verse item relative to the content widget
            verse_position = verse_item.y()
            # Scroll to position the verse at the top of the scroll area
            self.scroll_area.verticalScrollBar().setValue(verse_position)


class SectionWidget(QFrame):
    """
    A section container with title and controls.
    
    Provides a consistent styled frame for major UI sections with:
    - Bold title label
    - Optional controls row (buttons, etc.)
    - Content area
    - Optional settings gear icon
    
    Example:
        >>> controls = create_search_controls()  # Your custom widget
        >>> content = VerseListWidget("search")
        >>> section = SectionWidget("2. Search Results", content, controls)
    """

    def __init__(self, title, content_widget, controls_widget=None, 
                 show_settings=False, main_window=None, parent=None):
        """
        Initialize a section container.
        
        Args:
            title (str): Section title text (e.g., "2. Search Results")
            content_widget (QWidget): Main content widget for this section
            controls_widget (QWidget, optional): Controls to display above content
            show_settings (bool): If True, displays a settings gear icon
            main_window (QMainWindow, optional): Reference to main window for settings callback
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            SectionWidget {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                margin: 0px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(2)

        # Title row with optional settings gear
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        # Title label
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 11px;
                color: #333;
                background-color: transparent;
                padding: 2px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        # Settings gear icon (only for message window)
        if show_settings and main_window:
            from PyQt6.QtWidgets import QPushButton
            settings_btn = QPushButton("⚙")
            settings_btn.setFixedSize(24, 24)
            settings_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #999;
                    border-radius: 3px;
                    font-size: 14px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                    border: 1px solid #666;
                }
            """)
            settings_btn.clicked.connect(main_window.show_font_settings)
            title_layout.addWidget(settings_btn)

        layout.addLayout(title_layout)

        # Controls (if provided)
        if controls_widget:
            layout.addWidget(controls_widget)

        # Content area
        layout.addWidget(content_widget)
