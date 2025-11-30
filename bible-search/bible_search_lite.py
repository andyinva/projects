import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QCheckBox, QPushButton, QComboBox, QLineEdit,
                             QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
                             QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

# Import Bible search functionality
from bible_search import BibleSearch
from bible_search_service import BibleSearchService, SearchSettings

class VerseItemWidget(QWidget):
    """Individual verse display with checkbox and formatted text"""
    
    selection_changed = pyqtSignal(str, bool)  # verse_id, is_selected
    verse_clicked = pyqtSignal(str)  # verse_id for navigation
    
    def __init__(self, verse_id, translation, book_abbrev, chapter, verse_number, text, parent=None):
        super().__init__(parent)
        self.verse_id = verse_id
        self.translation = translation
        self.book_abbrev = book_abbrev
        self.chapter = chapter
        self.verse_number = verse_number
        self.text = text
        
        self.setup_ui()
        self.setup_styling()
        
    def setup_ui(self):
        """Create the widget layout"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # Checkbox (fixed width for alignment)
        self.checkbox = QCheckBox()
        self.checkbox.setFixedWidth(20)
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        layout.addWidget(self.checkbox)
        
        # Reference label (fixed width for column alignment)
        ref_text = f"{self.translation} {self.book_abbrev} {self.chapter}:{self.verse_number}"
        self.reference_label = QLabel(ref_text)
        self.reference_label.setFixedWidth(85)
        self.reference_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.reference_label)
        
        # Verse text (expandable with word wrap)
        self.text_label = QLabel(self.text)
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.text_label.setMinimumHeight(20)
        layout.addWidget(self.text_label, stretch=1)
        
        # Make the entire widget clickable for navigation
        self.mousePressEvent = self.on_verse_clicked
        
    def setup_styling(self):
        """Apply styling to the verse item"""
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
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self.reference_label.setFont(font)
        self.reference_label.setStyleSheet("color: #000080;")  # Navy blue
        
        # Style the text label
        text_font = QFont()
        text_font.setPointSize(10)
        self.text_label.setFont(text_font)
        
    def on_checkbox_changed(self, state):
        """Handle checkbox state change"""
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
        """Handle verse click for navigation"""
        self.verse_clicked.emit(self.verse_id)
        
    def set_selected(self, selected):
        """Set checkbox state programmatically"""
        self.checkbox.setChecked(selected)
        
    def is_selected(self):
        """Return current selection state"""
        return self.checkbox.isChecked()
        
    def get_verse_reference(self):
        """Return formatted verse reference"""
        return f"{self.translation} {self.book_abbrev} {self.chapter}:{self.verse_number}"
        
    def highlight_search_terms(self, search_terms):
        """Highlight search terms in the verse text"""
        if not search_terms:
            return
            
        text = self.text
        for term in search_terms:
            # Simple highlighting - in a full implementation you'd use HTML or rich text
            text = text.replace(term, f"<b><u>{term}</u></b>")
        
        self.text_label.setText(text)


class VerseListWidget(QWidget):
    """Container widget for managing multiple verse items"""
    
    selection_changed = pyqtSignal()  # Emitted when selection changes
    verse_navigation_requested = pyqtSignal(str)  # verse_id for navigation
    
    def __init__(self, window_id, parent=None):
        super().__init__(parent)
        self.window_id = window_id
        self.verse_items = {}  # verse_id -> VerseItemWidget
        self.selected_verses = set()  # Set of selected verse_ids
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the scrollable list layout"""
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
        """Add a verse to the list"""
        if verse_id in self.verse_items:
            return  # Verse already exists
            
        verse_item = VerseItemWidget(verse_id, translation, book_abbrev, chapter, verse_number, text)
        verse_item.selection_changed.connect(self.on_verse_selection_changed)
        verse_item.verse_clicked.connect(self.on_verse_clicked)
        
        # Insert before the stretch at the end
        self.content_layout.insertWidget(self.content_layout.count() - 1, verse_item)
        self.verse_items[verse_id] = verse_item
        
    def on_verse_selection_changed(self, verse_id, is_selected):
        """Handle individual verse selection change"""
        if is_selected:
            self.selected_verses.add(verse_id)
        else:
            self.selected_verses.discard(verse_id)
            
        self.selection_changed.emit()
        
        # Make this window active when a checkbox is clicked
        if hasattr(self, 'main_window'):
            self.main_window.set_active_window(self.window_id)
            print(f"Checkbox clicked in {self.window_id} window - setting as active")
            # Directly call button update to ensure it triggers
            self.main_window.update_acquire_button_state()
        
    def on_verse_clicked(self, verse_id):
        """Handle verse click for navigation"""
        self.verse_navigation_requested.emit(verse_id)
        
    def clear_verses(self):
        """Remove all verses from the list"""
        for verse_item in self.verse_items.values():
            verse_item.setParent(None)
        self.verse_items.clear()
        self.selected_verses.clear()
        self.selection_changed.emit()
        
    def get_selected_verses(self):
        """Return list of selected verse IDs"""
        return list(self.selected_verses)
        
    def select_all(self):
        """Select all verses"""
        for verse_item in self.verse_items.values():
            verse_item.set_selected(True)
            
    def select_none(self):
        """Deselect all verses"""
        for verse_item in self.verse_items.values():
            verse_item.set_selected(False)
            
    def get_verse_count(self):
        """Return total number of verses"""
        return len(self.verse_items)
        
    def get_selected_count(self):
        """Return number of selected verses"""
        return len(self.selected_verses)
        
    def set_active(self, is_active):
        """Set visual state for active/inactive window"""
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
            print(f"Applied ACTIVE styling to {self.window_id}")
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
            print(f"Applied INACTIVE styling to {self.window_id}")
            
        # Force update
        self.scroll_area.update()
        self.update()
            
    def scroll_to_verse(self, verse_id):
        """Scroll to show a specific verse"""
        if verse_id in self.verse_items:
            verse_item = self.verse_items[verse_id]
            self.scroll_area.ensureWidgetVisible(verse_item)


class SectionWidget(QFrame):
    """A section container with title and controls"""
    
    def __init__(self, title, content_widget, controls_widget=None, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            SectionWidget {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                margin: 2px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
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
        layout.addWidget(title_label)
        
        # Controls (if provided)
        if controls_widget:
            layout.addWidget(controls_widget)
            
        # Content area
        layout.addWidget(content_widget)


class SelectionManager:
    """Manages verse selections across all windows"""
    
    def __init__(self):
        self.active_window = None
        self.window_selections = {}  # window_id -> set of verse_ids
        
    def register_window(self, window_id, verse_list_widget):
        """Register a verse list widget"""
        self.window_selections[window_id] = set()
        verse_list_widget.selection_changed.connect(
            lambda: self.update_selections(window_id, verse_list_widget.get_selected_verses())
        )
        
    def update_selections(self, window_id, selected_verses):
        """Update selections for a window"""
        self.window_selections[window_id] = set(selected_verses)
        
    def set_active_window(self, window_id):
        """Set the currently active window"""
        self.active_window = window_id
        
    def get_active_selections(self):
        """Get selections from the currently active window"""
        if self.active_window and self.active_window in self.window_selections:
            return list(self.window_selections[self.active_window])
        return []
        
    def clear_selections(self, window_id=None):
        """Clear selections for a window or all windows"""
        if window_id:
            self.window_selections[window_id] = set()
        else:
            for window_id in self.window_selections:
                self.window_selections[window_id] = set()


class BibleSearchProgram(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bible Search Lite")
        self.setGeometry(100, 100, 1200, 900)
        self.setStyleSheet("background-color: #f0f0f0;")

        # Font settings
        default_font = QFont("Segoe UI", 9)
        self.setFont(default_font)

        # Initialize Bible search service
        self.bible_search = BibleSearch()
        self.search_service = BibleSearchService()

        # Connect search service signals
        self.search_service.search_completed.connect(self.on_search_completed)
        self.search_service.search_failed.connect(self.on_search_failed)
        self.search_service.search_progress.connect(self.on_search_progress)

        # Selection manager
        self.selection_manager = SelectionManager()

        # Store references to verse list widgets
        self.verse_lists = {}

        # Message label for status updates
        self.message_label = None

        self.setup_ui()
        self.add_sample_verses()
        
    def setup_ui(self):
        """Set up the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        
        # Create main vertical splitter
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(main_splitter)
        
        # 1. Message Window
        self.message_label = QLabel("Ready to search the Bible...")
        self.message_label.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")
        message_section = SectionWidget("1. Message Window", self.message_label)
        main_splitter.addWidget(message_section)
        
        # 2. Search Results
        search_controls = self.create_search_controls()
        search_verses = VerseListWidget("search")
        search_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        self.verse_lists['search'] = search_verses
        self.selection_manager.register_window("search", search_verses)
        
        search_section = SectionWidget("2. Search Results", search_verses, search_controls)
        main_splitter.addWidget(search_section)
        
        # 3. Reading Window
        reading_controls = self.create_reading_controls()
        reading_verses = VerseListWidget("reading")
        reading_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        self.verse_lists['reading'] = reading_verses
        self.selection_manager.register_window("reading", reading_verses)
        
        reading_section = SectionWidget("3. Reading Window", reading_verses, reading_controls)
        main_splitter.addWidget(reading_section)
        
        # 4. Subject Verses
        subject_controls = self.create_subject_controls()
        subject_verses = VerseListWidget("subject")
        subject_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        self.verse_lists['subject'] = subject_verses
        self.selection_manager.register_window("subject", subject_verses)
        
        subject_section = SectionWidget("4. Subject Verses", subject_verses, subject_controls)
        main_splitter.addWidget(subject_section)
        
        # 5. Comments (simplified)
        comments_widget = QLabel("Comments section - Add verse comments here")
        comments_widget.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")
        comments_section = SectionWidget("5. Verse Comments", comments_widget)
        main_splitter.addWidget(comments_section)
        
        # Set initial splitter sizes
        main_splitter.setSizes([80, 200, 250, 200, 100])
        
        # Connect window focus events AND store reference to main window
        for window_id, verse_list in self.verse_lists.items():
            # Store reference to main window in each verse list
            verse_list.main_window = self
            
            # Create a proper mouse press event handler for each window
            def make_click_handler(wid):
                def handler(event):
                    self.set_active_window(wid)
                    # Call the original mouse press event if it exists
                    return QWidget.mousePressEvent(verse_list, event)
                return handler
            
            verse_list.mousePressEvent = make_click_handler(window_id)
            
        # Set initial active window and update button state
        self.set_active_window('search')
        self.update_acquire_button_state()
        
    def update_acquire_button_state(self):
        """Update Acquire button highlighting based on available selections"""
        # Check if any window (except subject) has selected verses
        has_selections = False
        for window_id, verse_list in self.verse_lists.items():
            if window_id != 'subject' and verse_list.get_selected_count() > 0:
                has_selections = True
                break
        
        # Update acquire button style
        if hasattr(self, 'acquire_button'):
            if has_selections:
                self.acquire_button.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        border: 2px solid #45a049;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 2px;
                        min-width: 50px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                print(f"Acquire button highlighted - selections available")
            else:
                self.acquire_button.setStyleSheet(self.get_button_style())
                print(f"Acquire button normal - no selections available")
            
    def create_search_controls(self):
        """Create controls for the search section"""
        controls_widget = QWidget()
        layout = QVBoxLayout(controls_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # First row - checkboxes
        checkbox_layout = QHBoxLayout()

        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        self.unique_verse_cb = QCheckBox("Unique Verse")
        self.abbreviate_results_cb = QCheckBox("Abbreviate Results")
        self.abbreviate_results_cb.setChecked(True)  # Default to checked

        checkbox_layout.addWidget(self.case_sensitive_cb)
        checkbox_layout.addWidget(self.unique_verse_cb)
        checkbox_layout.addWidget(self.abbreviate_results_cb)
        checkbox_layout.addStretch()

        layout.addLayout(checkbox_layout)

        # Second row - search controls
        search_layout = QHBoxLayout()

        self.search_input = QComboBox()
        self.search_input.setMinimumWidth(200)
        self.search_input.setEditable(True)
        self.search_input.lineEdit().setPlaceholderText("Enter search terms...")
        self.search_input.addItems(["love", "faith", "hope"])  # Sample history

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.perform_search)
        search_button.setStyleSheet(self.get_button_style())

        self.version_combo = QComboBox()
        # Load translations from BibleSearch
        for translation in self.bible_search.translations:
            self.version_combo.addItem(translation.abbreviation)

        self.books_combo = QComboBox()
        self.books_combo.addItems(["All Books", "Old Testament", "New Testament", "Pentateuch", "Gospels"])
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.verse_lists['search'].clear_verses())
        clear_button.setStyleSheet(self.get_button_style())

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(self.version_combo)
        search_layout.addWidget(self.books_combo)
        search_layout.addWidget(clear_button)
        search_layout.addStretch()
        
        # Right side buttons
        tips_button = QPushButton("Tips")
        tips_button.setStyleSheet(self.get_button_style())
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.copy_selected_verses)
        copy_button.setStyleSheet(self.get_button_style())
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_selected_verses)
        export_button.setStyleSheet(self.get_button_style())
        
        search_layout.addWidget(tips_button)
        search_layout.addWidget(copy_button)
        search_layout.addWidget(export_button)
        
        layout.addLayout(search_layout)
        
        return controls_widget
        
    def create_reading_controls(self):
        """Create controls for the reading window"""
        controls_widget = QWidget()
        layout = QHBoxLayout(controls_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Navigation controls
        prev_button = QPushButton("◀ Previous")
        prev_button.setStyleSheet(self.get_button_style())
        
        next_button = QPushButton("Next ▶")
        next_button.setStyleSheet(self.get_button_style())
        
        # Translation selector for reading
        translation_combo = QComboBox()
        translation_combo.addItems(["KJV", "NIV", "ESV", "NASB"])
        
        layout.addWidget(prev_button)
        layout.addWidget(next_button)
        layout.addWidget(QLabel("Translation:"))
        layout.addWidget(translation_combo)
        layout.addStretch()
        
        # Right side buttons
        copy_button = QPushButton("Copy")
        copy_button.clicked.connect(self.copy_selected_verses)
        copy_button.setStyleSheet(self.get_button_style())
        
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_selected_verses)
        export_button.setStyleSheet(self.get_button_style())
        
        layout.addWidget(copy_button)
        layout.addWidget(export_button)
        
        return controls_widget
        
    def get_button_style(self):
        """Return consistent button styling"""
        return """
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #999;
                padding: 4px 8px;
                border-radius: 2px;
                min-width: 50px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """
        
    def create_subject_controls(self):
        """Create subject controls"""
        controls_widget = QWidget()
        layout = QHBoxLayout(controls_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        acquire_button = QPushButton("Acquire")
        acquire_button.clicked.connect(self.acquire_verses)
        
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.verse_lists['subject'].clear_verses())
        
        layout.addWidget(acquire_button)
        layout.addWidget(clear_button)
        layout.addStretch()
        
        # Context-sensitive buttons
        clip_button = QPushButton("Copy")
        clip_button.clicked.connect(self.copy_selected_verses)
        export_button = QPushButton("Export")
        export_button.clicked.connect(self.export_selected_verses)
        
        layout.addWidget(clip_button)
        layout.addWidget(export_button)
        
        return controls_widget
        
    def set_active_window(self, window_id):
        """Set the active verse window"""
        print(f"Setting active window to: {window_id}")  # Debug output
        self.selection_manager.set_active_window(window_id)
        
        # Update visual feedback
        for wid, verse_list in self.verse_lists.items():
            is_active = (wid == window_id)
            verse_list.set_active(is_active)
            print(f"Window {wid} active state: {is_active}")  # Debug output
            
    def on_verse_navigation(self, verse_id):
        """Handle verse navigation between windows"""
        print(f"Navigate to verse: {verse_id}")
        
        # Example: When verse selected in search results, show context in reading window
        if verse_id.startswith("search_"):
            # Load context verses in reading window
            self.load_context_verses(verse_id)
            
    def perform_search(self):
        """Perform a Bible search using BibleSearchService"""
        search_term = self.search_input.currentText().strip()
        if not search_term:
            self.message_label.setText("Please enter search terms")
            return

        self.message_label.setText(f"Searching for: {search_term}...")

        # Create search settings
        settings = SearchSettings()
        settings.case_sensitive = self.case_sensitive_cb.isChecked()
        settings.unique_verses = self.unique_verse_cb.isChecked()
        settings.abbreviate_results = self.abbreviate_results_cb.isChecked()

        # Get selected translations
        selected_translation = self.version_combo.currentText()
        settings.enabled_translations = [selected_translation]

        # Perform search using the service (runs in background thread)
        self.search_service.search(search_term, settings)

    def on_search_completed(self, results):
        """Handle search completion from BibleSearchService"""
        # Clear previous results
        self.verse_lists['search'].clear_verses()

        # Add results to the search window
        for i, result in enumerate(results):
            verse_id = f"search_{i}"
            translation = result['Translation']

            # Parse reference to get book, chapter, verse
            reference = result['Reference']
            parts = reference.split()

            if len(parts) >= 2:
                # Handle books with numbers (e.g., "1 Samuel")
                if parts[0].isdigit():
                    book_abbrev = f"{parts[0]}{parts[1][:3]}"
                    chapter_verse = parts[2] if len(parts) > 2 else ""
                else:
                    book_abbrev = parts[0][:3]
                    chapter_verse = parts[1] if len(parts) > 1 else ""

                # Parse chapter:verse
                if ':' in chapter_verse:
                    chapter, verse = chapter_verse.split(':', 1)
                    chapter = int(chapter)
                    verse = int(verse)
                else:
                    chapter = 1
                    verse = 1
            else:
                book_abbrev = "Unk"
                chapter = 1
                verse = 1

            text = result['Text']

            # Add verse to the list
            self.verse_lists['search'].add_verse(
                verse_id, translation, book_abbrev, chapter, verse, text
            )

        # Update message
        if results:
            self.message_label.setText(f"Search completed: {len(results)} results found")
        else:
            self.message_label.setText("No results found")

    def on_search_failed(self, error_message):
        """Handle search failure from BibleSearchService"""
        self.message_label.setText(f"Search error: {error_message}")
        print(f"Search error details: {error_message}")

    def on_search_progress(self, message):
        """Handle search progress updates"""
        self.message_label.setText(message)
            
    def load_context_verses(self, center_verse_id):
        """Load context verses around a selected verse"""
        # Clear reading window
        self.verse_lists['reading'].clear_verses()
        
        # Add context verses (demo implementation)
        context_verses = [
            ("context_1", "KJV", "Joh", 3, 15, "That whosoever believeth in him should not perish, but have eternal life."),
            ("context_2", "KJV", "Joh", 3, 16, "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish, but have everlasting life."),
            ("context_3", "KJV", "Joh", 3, 17, "For God sent not his Son into the world to condemn the world; but that the world through him might be saved."),
        ]
        
        for verse_id, translation, book, chapter, verse, text in context_verses:
            self.verse_lists['reading'].add_verse(verse_id, translation, book, chapter, verse, text)
            
    def acquire_verses(self):
        """Move selected verses from active window to subject verses"""
        active_window = self.selection_manager.active_window
        if not active_window or active_window not in self.verse_lists:
            print("No active window selected")
            return
            
        # Don't acquire from subject window to itself
        if active_window == 'subject':
            print("Cannot acquire from subject window to itself")
            return
            
        # Get selected verse IDs from the active window
        selected_verse_ids = self.verse_lists[active_window].get_selected_verses()
        if not selected_verse_ids:
            print("No verses selected in active window")
            return
            
        # Get the actual verse data for selected verses
        source_widget = self.verse_lists[active_window]
        acquired_count = 0
        
        for verse_id in selected_verse_ids:
            if verse_id in source_widget.verse_items:
                verse_item = source_widget.verse_items[verse_id]
                
                # Create new verse ID for subject window
                subject_verse_id = f"subject_{verse_id}"
                
                # Add to subject verses (avoid duplicates)
                if subject_verse_id not in self.verse_lists['subject'].verse_items:
                    self.verse_lists['subject'].add_verse(
                        subject_verse_id,
                        verse_item.translation,
                        verse_item.book_abbrev, 
                        verse_item.chapter,
                        verse_item.verse_number,
                        verse_item.text
                    )
                    acquired_count += 1
        
        # Clear selections from the active window after successful acquire
        source_widget.select_none()
        
        print(f"Acquired {acquired_count} verses to subject from {active_window} window")
        print(f"Cleared selections in {active_window} window")
        
        # Update Acquire button state
        self.update_acquire_button_state()
        
    def copy_selected_verses(self):
        """Copy selected verses to clipboard"""
        active_selections = self.selection_manager.get_active_selections()
        print(f"Copying {len(active_selections)} verses to clipboard")
        
    def export_selected_verses(self):
        """Export selected verses to file"""
        active_selections = self.selection_manager.get_active_selections()
        print(f"Exporting {len(active_selections)} verses to file")
        
    def add_sample_verses(self):
        """Add sample verses for demonstration"""
        # Add sample verse to subject window
        self.verse_lists['subject'].add_verse(
            "subject_demo", "KJV", "Psa", 23, 1,
            "The LORD is my shepherd; I shall not want."
        )


def main():
    app = QApplication(sys.argv)
    window = BibleSearchProgram()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()