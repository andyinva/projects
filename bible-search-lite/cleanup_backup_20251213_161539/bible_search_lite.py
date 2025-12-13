import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QCheckBox, QPushButton, QComboBox, QLineEdit,
                             QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
                             QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette

# Import custom UI components, config, and controllers from refactored modules
from bible_search_ui.ui.widgets import VerseItemWidget, VerseListWidget, SectionWidget
from bible_search_ui.ui.dialogs import TranslationSelectorDialog, FontSettingsDialog, GroupDialog, SubjectDialog
from bible_search_ui.config import ConfigManager
from bible_search_ui.controllers import SearchController, UserDataController
from bible_search_ui.services import UserDataService

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

        # Configuration manager
        self.config_manager = ConfigManager("bible_search_lite_config.json")
        self.config_manager = ConfigManager("bible_search_lite_config.json")
        self.config_file = "bible_search_lite_config.json"

        # Set initial geometry (will be overridden by load_config if config exists)
        self.setGeometry(100, 100, 1200, 900)
        self.setStyleSheet("background-color: #f0f0f0;")

        # Font settings
        default_font = QFont("IBM Plex Mono", 9)
        self.setFont(default_font)

        # Font size settings (0=current/smallest, 1-4=larger sizes)
        self.title_font_size = 0  # Current: 9px
        self.verse_font_size = 0  # Current: 9px for reference and text
        self.title_font_sizes = [9, 9.5, 10, 10.5, 11]  # 5 choices, 0.5pt increments
        self.verse_font_sizes = [9, 9.5, 10, 10.5, 11]   # 5 choices, 0.5pt increments

        # Context-sensitive buttons (will be created in setup_ui)
        self.tips_btn = None
        self.copy_btn = None
        self.export_btn = None

        # Initialize search controller
        self.search_controller = SearchController()

        # Connect search controller signals
        self.search_controller.search_results_ready.connect(self.on_search_results_ready)
        self.search_controller.search_more_results_ready.connect(self.on_search_more_results_ready)
        self.search_controller.search_failed.connect(self.on_search_failed)
        self.search_controller.search_status.connect(self.on_search_status)
        self.search_controller.context_verses_ready.connect(self.on_context_verses_ready)

        # Initialize user data service and controller
        self.user_data_service = UserDataService("user_data.db")
        self.user_data_controller = UserDataController(self.user_data_service)

        # Connect user data controller signals
        self.user_data_controller.groups_loaded.connect(self.on_groups_loaded)
        self.user_data_controller.subjects_loaded.connect(self.on_subjects_loaded)
        self.user_data_controller.verses_loaded.connect(self.on_verses_loaded)
        self.user_data_controller.operation_success.connect(
            lambda msg: self.message_label.setText(msg) if self.message_label else None
        )
        self.user_data_controller.operation_failed.connect(
            lambda msg: self.message_label.setText(f"Error: {msg}") if self.message_label else None
        )

        # Selection manager
        self.selection_manager = SelectionManager()

        # Store references to verse list widgets
        self.verse_lists = {}

        # Message label for status updates
        self.message_label = None

        # Store splitter reference for saving state
        self.main_splitter = None

        self.setup_ui()

        # Load saved configuration after UI is set up
        config = self.load_config()
        self.add_sample_verses()

        # Load initial user data
        self.user_data_controller.load_groups()

        # Restore last selected group/subject from config if available
        if config and 'user_data' in config:
            user_data_config = config['user_data']
            if 'current_group_id' in user_data_config:
                # Will be restored after groups are loaded
                self.pending_group_id = user_data_config['current_group_id']
                self.pending_subject_id = user_data_config.get('current_subject_id')
            else:
                self.pending_group_id = None
                self.pending_subject_id = None
        else:
            self.pending_group_id = None
            self.pending_subject_id = None
        
    def setup_ui(self):
        """Set up the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # Create main vertical splitter
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(self.main_splitter)
        
        # 1. Message Window with context-sensitive buttons
        self.message_label = QLabel("Ready to search the Bible...")
        self.message_label.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")

        # Create context-sensitive buttons
        self.tips_btn = self.create_title_button("Tips")
        self.copy_btn = self.create_title_button("Copy")
        self.export_btn = self.create_title_button("Export")

        message_buttons = [self.tips_btn, self.copy_btn, self.export_btn]
        message_section = SectionWidget("1. Message Window", self.message_label,
                                       show_settings=True, title_buttons=message_buttons, main_window=self)
        self.main_splitter.addWidget(message_section)

        # 2. Search Results
        search_controls = self.create_search_controls()
        search_verses = VerseListWidget("search")
        search_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        self.verse_lists['search'] = search_verses
        self.selection_manager.register_window("search", search_verses)

        search_section = SectionWidget("2. Search Results", search_verses, search_controls)
        self.main_splitter.addWidget(search_section)

        # 3. Reading Window
        reading_controls = self.create_reading_controls()
        reading_verses = VerseListWidget("reading")
        reading_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        self.verse_lists['reading'] = reading_verses
        self.selection_manager.register_window("reading", reading_verses)

        reading_section = SectionWidget("3. Reading Window", reading_verses, reading_controls)
        self.main_splitter.addWidget(reading_section)

        # 4. Subject Verses
        subject_controls = self.create_subject_controls()
        subject_verses = VerseListWidget("subject")
        subject_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        self.verse_lists['subject'] = subject_verses
        self.selection_manager.register_window("subject", subject_verses)

        subject_section = SectionWidget("4. Subject Verses", subject_verses, subject_controls)
        self.main_splitter.addWidget(subject_section)

        # 5. Comments
        comment_controls = self.create_comment_controls()
        comments_widget = QLabel("Comments section - Add verse comments here")
        comments_widget.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")
        comments_section = SectionWidget("5. Verse Comments", comments_widget, comment_controls)
        self.main_splitter.addWidget(comments_section)

        # Set initial splitter sizes
        self.main_splitter.setSizes([80, 200, 250, 200, 100])
        
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

    def create_title_button(self, text):
        """Create a standardized button for section title bars"""
        from PyQt6.QtWidgets import QPushButton
        button = QPushButton(text)
        button.setFixedHeight(24)
        button.setMinimumWidth(60)
        button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #999;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #666;
            }
            QPushButton:disabled {
                background-color: #f0f0f0;
                color: #999;
                border: 1px solid #ccc;
            }
        """)
        # Connect to placeholder methods (will add functionality later)
        if text == "Tips":
            button.clicked.connect(self.on_tips_clicked)
        elif text == "Copy":
            button.clicked.connect(self.on_copy_clicked)
        elif text == "Export":
            button.clicked.connect(self.on_export_clicked)
        return button

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
        self.search_input.setMinimumWidth(400)  # Increased from 200 to 400
        self.search_input.setEditable(True)
        self.search_input.setStyleSheet(self.get_combobox_style())
        self.search_input.lineEdit().setPlaceholderText("Enter search terms...")
        self.search_input.addItems(["love", "faith", "hope"])  # Sample history

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.perform_search)
        search_button.setStyleSheet(self.get_button_style())

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_search_and_reading)
        clear_button.setStyleSheet(self.get_button_style())

        # Translation selector button
        self.translations_button = QPushButton("Translations")
        self.translations_button.clicked.connect(self.show_translation_selector)
        self.translations_button.setStyleSheet(self.get_button_style())

        # Store selected translations (default: KJV only)
        self.selected_translations = ["KJV"]

        self.books_combo = QComboBox()
        self.books_combo.setStyleSheet(self.get_combobox_style())
        self.books_combo.addItems(["All Books", "Old Testament", "New Testament", "Pentateuch", "Gospels"])

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)
        search_layout.addWidget(clear_button)
        search_layout.addWidget(self.translations_button)
        search_layout.addWidget(self.books_combo)
        search_layout.addStretch()

        layout.addLayout(search_layout)
        
        return controls_widget
        
    def create_reading_controls(self):
        """Create controls for the reading window"""
        controls_widget = QWidget()
        layout = QHBoxLayout(controls_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Translation selector for reading (all 17 translations)
        self.reading_translation_combo = QComboBox()
        self.reading_translation_combo.setStyleSheet(self.get_combobox_style())
        self.reading_translation_combo.addItems([
            "KJV", "ASV", "BBE", "DARBY", "DRA", "ERV", "GNVA",
            "JUB", "KJ21", "KJC", "KJVA", "LEB", "MKJV", "WEB",
            "WEBSTER", "WYC", "YLT"
        ])

        layout.addWidget(self.reading_translation_combo)
        layout.addStretch()

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

    def get_combobox_style(self):
        """Return consistent combobox styling"""
        return """
            QComboBox {
                background-color: white;
                border: 1px solid #999;
                padding: 4px 8px;
                border-radius: 2px;
                min-width: 80px;
                color: black;
            }
            QComboBox:hover {
                border: 1px solid #666;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #666;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #999;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 4px;
                min-height: 20px;
                color: black;
                background-color: white;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e6f3ff;
                color: black;
            }
        """

    def create_subject_controls(self):
        """Create subject controls with group and subject management"""
        controls_widget = QWidget()
        main_layout = QVBoxLayout(controls_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)

        # Row 1: Group management
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Group:"))

        self.group_combo = QComboBox()
        self.group_combo.setMinimumWidth(200)
        self.group_combo.setStyleSheet(self.get_combobox_style())
        self.group_combo.currentIndexChanged.connect(self.on_group_selected)
        group_layout.addWidget(self.group_combo)

        new_group_button = QPushButton("New Group")
        new_group_button.clicked.connect(self.create_new_group)
        new_group_button.setStyleSheet(self.get_button_style())
        group_layout.addWidget(new_group_button)

        delete_group_button = QPushButton("Delete Group")
        delete_group_button.clicked.connect(self.delete_group)
        delete_group_button.setStyleSheet(self.get_button_style())
        group_layout.addWidget(delete_group_button)

        group_layout.addStretch()
        main_layout.addLayout(group_layout)

        # Row 2: Subject management
        subject_layout = QHBoxLayout()
        subject_layout.addWidget(QLabel("Subject:"))

        self.subject_combo = QComboBox()
        self.subject_combo.setMinimumWidth(200)
        self.subject_combo.setStyleSheet(self.get_combobox_style())
        self.subject_combo.currentIndexChanged.connect(self.on_subject_selected)
        subject_layout.addWidget(self.subject_combo)

        new_subject_button = QPushButton("New Subject")
        new_subject_button.clicked.connect(self.create_new_subject)
        new_subject_button.setStyleSheet(self.get_button_style())
        subject_layout.addWidget(new_subject_button)

        delete_subject_button = QPushButton("Delete Subject")
        delete_subject_button.clicked.connect(self.delete_subject)
        delete_subject_button.setStyleSheet(self.get_button_style())
        subject_layout.addWidget(delete_subject_button)

        find_button = QPushButton("Find")
        find_button.clicked.connect(self.find_subject)
        find_button.setStyleSheet(self.get_button_style())
        subject_layout.addWidget(find_button)

        subject_layout.addStretch()
        main_layout.addLayout(subject_layout)

        # Row 3: Verse operations
        verse_layout = QHBoxLayout()

        self.acquire_button = QPushButton("Acquire")
        self.acquire_button.clicked.connect(self.acquire_verses)
        self.acquire_button.setStyleSheet(self.get_button_style())
        verse_layout.addWidget(self.acquire_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.verse_lists['subject'].clear_verses())
        clear_button.setStyleSheet(self.get_button_style())
        verse_layout.addWidget(clear_button)

        verse_layout.addStretch()

        main_layout.addLayout(verse_layout)

        return controls_widget

    def create_comment_controls(self):
        """Create comment controls with action buttons"""
        controls_widget = QWidget()
        layout = QHBoxLayout(controls_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Comment action buttons
        add_comment_button = QPushButton("Add Comment")
        add_comment_button.clicked.connect(self.on_add_comment)
        add_comment_button.setStyleSheet(self.get_button_style())

        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.on_edit_comment)
        edit_button.setStyleSheet(self.get_button_style())

        save_button = QPushButton("Save")
        save_button.clicked.connect(self.on_save_comment)
        save_button.setStyleSheet(self.get_button_style())

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.on_delete_comment)
        delete_button.setStyleSheet(self.get_button_style())

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.on_close_comment)
        close_button.setStyleSheet(self.get_button_style())

        layout.addWidget(add_comment_button)
        layout.addWidget(edit_button)
        layout.addWidget(save_button)
        layout.addWidget(delete_button)
        layout.addWidget(close_button)
        layout.addStretch()

        return controls_widget

    def set_active_window(self, window_id):
        """Set the active verse window"""
        print(f"Setting active window to: {window_id}")  # Debug output

        # Store the active window id so other components can check it
        self.active_window_id = window_id

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

    def clear_search_and_reading(self):
        """Clear both search results and reading window"""
        self.verse_lists['search'].clear_verses()
        self.verse_lists['reading'].clear_verses()
        self.message_label.setText("Search results and reading window cleared")

    def show_translation_selector(self):
        """Show dialog to select which translations to search"""
        dialog = TranslationSelectorDialog(
            self, 
            self.search_controller.bible_search.translations,
            self.selected_translations
        )
        
        if dialog.exec():
            self.selected_translations = dialog.get_selected_translations()
            print(f"Selected translations: {self.selected_translations}")
            # Update button text to show count
            count = len(self.selected_translations)
            self.translations_button.setText(f"Translations ({count})")


    def show_font_settings(self):
        """Show dialog to adjust font sizes"""
        dialog = FontSettingsDialog(
            self,
            self.title_font_sizes,
            self.verse_font_sizes,
            self.title_font_size,
            self.verse_font_size
        )
        
        if dialog.exec():
            self.title_font_size, self.verse_font_size = dialog.get_font_sizes()
            self.apply_font_settings()

    def apply_font_settings(self):
        """Apply the current font settings to all UI elements"""
        title_size = self.title_font_sizes[self.title_font_size]
        verse_size = self.verse_font_sizes[self.verse_font_size]

        # Update all section titles
        for widget in self.findChildren(SectionWidget):
            for label in widget.findChildren(QLabel):
                if "font-weight: bold" in label.styleSheet():
                    label.setStyleSheet(f"""
                        QLabel {{
                            font-family: "IBM Plex Mono";
                            font-weight: bold;
                            font-size: {title_size}pt;
                            color: #333;
                            background-color: transparent;
                            padding: 2px;
                        }}
                    """)

        # Update all verse items
        for verse_list in self.verse_lists.values():
            for verse_item in verse_list.verse_items.values():
                # Update the combined text label (reference + text)
                verse_font = QFont("IBM Plex Mono")
                verse_font.setBold(False)
                verse_font.setPointSizeF(verse_size)  # Use setPointSizeF for fractional sizes
                verse_item.text_label.setFont(verse_font)

    def perform_search(self):
        """Perform a Bible search using SearchController"""
        search_term = self.search_input.currentText().strip()
        if not search_term:
            self.message_label.setText("Please enter search terms")
            return

        # Add search term to history if not already there
        if search_term:
            # Find if term already exists
            index = self.search_input.findText(search_term)
            if index >= 0:
                # Remove it so we can add it to the top
                self.search_input.removeItem(index)
            # Add to top of list
            self.search_input.insertItem(0, search_term)
            self.search_input.setCurrentIndex(0)

        self.message_label.setText(f"Searching for: {search_term}...")

        # Delegate to search controller
        self.search_controller.search(
            search_term=search_term,
            case_sensitive=self.case_sensitive_cb.isChecked(),
            unique_verses=self.unique_verse_cb.isChecked(),
            abbreviate_results=self.abbreviate_results_cb.isChecked(),
            translations=self.selected_translations
        )


    def load_context_verses(self, center_verse_id):
        """Load context verses around a selected verse - delegates to SearchController"""
        # Get the verse widget from search results to extract its info
        if center_verse_id not in self.verse_lists['search'].verse_items:
            print(f"Verse {center_verse_id} not found in search results")
            return

        # Get the clicked verse information
        clicked_verse = self.verse_lists['search'].verse_items[center_verse_id]
        translation = clicked_verse.translation
        book = clicked_verse.book_abbrev
        chapter = clicked_verse.chapter
        start_verse = clicked_verse.verse_number

        print(f"Loading context for {translation} {book} {chapter}:{start_verse}")

        # Delegate to search controller
        self.search_controller.load_context(
            translation=translation,
            book=book,
            chapter=chapter,
            start_verse=start_verse,
            num_verses=50
        )

    def on_search_results_ready(self, verses, metadata):
        """Handle initial search results from SearchController"""
        print(f"Received {len(verses)} initial search results")
        
        # Clear previous results
        self.verse_lists['search'].clear_verses()
        
        # Add verses to search window
        for verse in verses:
            self.verse_lists['search'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text
            )
        
        # Connect scroll event for lazy loading if there are more results
        if metadata.get('has_more', False):
            scroll_bar = self.verse_lists['search'].scroll_area.verticalScrollBar()
            # Disconnect any existing connection first
            try:
                scroll_bar.valueChanged.disconnect()
            except:
                pass
            # Connect to lazy loading
            scroll_bar.valueChanged.connect(
                lambda value: self.search_controller.load_more_results(
                    value, scroll_bar.maximum()
                )
            )

    def on_search_more_results_ready(self, verses, metadata):
        """Handle additional search results from lazy loading"""
        print(f"Received {len(verses)} more search results")
        
        # Add verses to search window (don't clear existing ones)
        for verse in verses:
            self.verse_lists['search'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text
            )

    def on_search_failed(self, error_message):
        """Handle search failure"""
        self.message_label.setText(f"Search error: {error_message}")
        print(f"Search error details: {error_message}")

    def on_search_status(self, message):
        """Handle search status updates"""
        self.message_label.setText(message)

    def on_context_verses_ready(self, verses):
        """Handle context verses for reading window"""
        print(f"Received {len(verses)} context verses for reading window")
        
        # Clear reading window
        self.verse_lists['reading'].clear_verses()
        
        # Add verses to reading window
        for verse in verses:
            self.verse_lists['reading'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text
            )
        
        # Highlight the first verse (the one that was clicked)
        if verses:
            first_verse_id = verses[0].verse_id
            if first_verse_id in self.verse_lists['reading'].verse_items:
                self.verse_lists['reading'].verse_items[first_verse_id].set_highlighted(True)
                # Scroll to make the highlighted verse visible at the top
                self.verse_lists['reading'].scroll_to_verse(first_verse_id)

    def acquire_verses(self):
        """
        Move selected verses from active window to current subject.

        Validates that:
        - A group is selected
        - A subject is selected
        - Active window has selections
        - Active window is not 'subject' (can't acquire from itself)

        Side Effects:
            - Adds verses to current subject via controller
            - Clears selections in source window
            - Shows error messages for invalid states
        """
        # Validate group and subject are selected
        if not self.user_data_controller.has_group_and_subject_selected():
            self.message_label.setText("Please select both a group and subject first")
            return

        # Get active window
        active_window = self.selection_manager.active_window
        if not active_window:
            self.message_label.setText("No window is active")
            return

        # Can't acquire from subject window to itself
        if active_window == 'subject':
            self.message_label.setText("Cannot acquire from subject window")
            return

        # Get selected verses from active window
        selected_verse_ids = self.verse_lists[active_window].get_selected_verses()
        if not selected_verse_ids:
            self.message_label.setText("No verses selected in active window")
            return

        # Build verse data list for controller
        verse_data_list = []
        source_widget = self.verse_lists[active_window]

        for verse_id in selected_verse_ids:
            if verse_id in source_widget.verse_items:
                verse_item = source_widget.verse_items[verse_id]

                # Build verse reference (e.g., "Gen 1:1")
                reference = f"{verse_item.book_abbrev} {verse_item.chapter}:{verse_item.verse_number}"

                verse_data_list.append({
                    'reference': reference,
                    'translation': verse_item.translation,
                    'text': verse_item.text
                })

        # Acquire verses via controller
        self.user_data_controller.acquire_verses(verse_data_list)

        # Clear selections from source window after successful acquire
        source_widget.select_none()

        # Update acquire button state
        self.update_acquire_button_state()

    def on_verses_loaded(self, verses):
        """
        Handle verses loaded signal from controller.

        Args:
            verses (list): List of verse dictionaries for current subject

        Side Effects:
            - Clears and populates subject verses window
            - Updates message with verse count
        """
        # Clear existing verses
        self.verse_lists['subject'].clear_verses()

        # Add verses to subject window
        for verse in verses:
            # Parse verse reference to get book, chapter, verse
            reference = verse['verse_reference']  # e.g., "Gen 1:1"
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
                    chapter, verse_num = chapter_verse.split(':', 1)
                    chapter = int(chapter)
                    verse_num = int(verse_num)
                else:
                    chapter = 1
                    verse_num = 1
            else:
                book_abbrev = "Unk"
                chapter = 1
                verse_num = 1

            # Create unique verse ID
            verse_id = f"subject_{verse['id']}"

            # Add to verse list
            self.verse_lists['subject'].add_verse(
                verse_id,
                verse['translation'],
                book_abbrev,
                chapter,
                verse_num,
                verse['verse_text']
            )

        # Update message
        count = len(verses)
        if count > 0:
            self.message_label.setText(f"Loaded {count} verse{'s' if count != 1 else ''}")

    def copy_selected_verses(self):
        """Copy selected verses to clipboard"""
        active_selections = self.selection_manager.get_active_selections()
        print(f"Copying {len(active_selections)} verses to clipboard")
        
    def export_selected_verses(self):
        """Export selected verses to file"""
        active_selections = self.selection_manager.get_active_selections()
        print(f"Exporting {len(active_selections)} verses to file")

    # Placeholder button handlers for context-sensitive buttons
    def on_tips_clicked(self):
        """Show tips for the Message Window"""
        print("Tips button clicked - placeholder")
        self.message_label.setText("Tips: This is the message window where search results and status updates appear.")

    def on_copy_clicked(self):
        """Copy content from active window"""
        print("Copy button clicked - placeholder")
        active_selections = self.selection_manager.get_active_selections()
        if active_selections:
            print(f"Would copy {len(active_selections)} verses from active window")
        else:
            print("No verses selected in active window")

    def on_export_clicked(self):
        """Export content from active window"""
        print("Export button clicked - placeholder")
        active_selections = self.selection_manager.get_active_selections()
        if active_selections:
            print(f"Would export {len(active_selections)} verses from active window")
        else:
            print("No verses selected in active window")

    # Placeholder handlers for Subject controls
    def on_create_subject(self):
        """Create a new subject category"""
        print("Create Subject button clicked - placeholder")
        self.message_label.setText("Create Subject: Would open dialog to create new subject category")

    def on_delete_subject(self):
        """Delete the current subject category"""
        print("Delete Subject button clicked - placeholder")
        current_subject = self.subject_combo.currentText()
        self.message_label.setText(f"Delete Subject: Would delete subject '{current_subject}'")

    # Placeholder handlers for Comment controls
    def on_add_comment(self):
        """Add a comment to selected verse"""
        print("Add Comment button clicked - placeholder")
        self.message_label.setText("Add Comment: Would open comment editor for selected verse")

    def on_edit_comment(self):
        """Edit existing comment"""
        print("Edit Comment button clicked - placeholder")
        self.message_label.setText("Edit Comment: Would open comment editor to modify existing comment")

    def on_save_comment(self):
        """Save the current comment"""
        print("Save Comment button clicked - placeholder")
        self.message_label.setText("Save Comment: Would save the current comment to database")

    def on_delete_comment(self):
        """Delete the current comment"""
        print("Delete Comment button clicked - placeholder")
        self.message_label.setText("Delete Comment: Would delete the current comment")

    def on_close_comment(self):
        """Close the comment editor"""
        print("Close Comment button clicked - placeholder")
        self.message_label.setText("Close Comment: Would close the comment editor")

    # ==================== GROUP MANAGEMENT ====================

    def on_groups_loaded(self, groups):
        """
        Handle groups loaded signal from controller.

        Args:
            groups (list): List of group dictionaries from database

        Side Effects:
            - Populates group dropdown
            - Restores previous selection if available
            - Clears subject dropdown until group selected
        """
        # Clear and populate group dropdown
        self.group_combo.clear()

        for group in groups:
            # Store group_id as user data
            self.group_combo.addItem(group['group_name'], group['group_id'])

        # Restore previous selection if available
        if hasattr(self, 'pending_group_id') and self.pending_group_id is not None:
            # Find index of pending group
            for i in range(self.group_combo.count()):
                if self.group_combo.itemData(i) == self.pending_group_id:
                    self.group_combo.setCurrentIndex(i)
                    break

            self.pending_group_id = None  # Clear pending selection

    def on_group_selected(self, index):
        """
        Handle group selection from dropdown.

        Args:
            index (int): Index of selected item in dropdown

        Side Effects:
            - Loads subjects for selected group via controller
            - Clears subject verses display
        """
        if index < 0:
            return

        group_id = self.group_combo.itemData(index)
        if group_id is not None:
            self.user_data_controller.select_group(group_id)
            # Clear verses display since group changed
            self.verse_lists['subject'].clear_verses()

    def create_new_group(self):
        """
        Show dialog to create a new group.

        Side Effects:
            - Shows GroupDialog modal window
            - Creates group via controller if user accepts
        """
        dialog = GroupDialog(self, mode="create")
        if dialog.exec():
            name, description = dialog.get_values()
            self.user_data_controller.create_group(name, description)

    def delete_group(self):
        """
        Delete the currently selected group after confirmation.

        Side Effects:
            - Shows confirmation dialog
            - Deletes group via controller if confirmed
        """
        current_index = self.group_combo.currentIndex()
        if current_index < 0:
            self.message_label.setText("No group selected")
            return

        group_name = self.group_combo.currentText()
        group_id = self.group_combo.itemData(current_index)

        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete group '{group_name}' and all its subjects and verses?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.user_data_controller.delete_group(group_id)

    # ==================== SUBJECT MANAGEMENT ====================

    def on_subjects_loaded(self, subjects):
        """
        Handle subjects loaded signal from controller.

        Args:
            subjects (list): List of subject dictionaries for current group

        Side Effects:
            - Populates subject dropdown
            - Restores previous selection if available
            - Clears verse display until subject selected
        """
        # Clear and populate subject dropdown
        self.subject_combo.clear()

        for subject in subjects:
            # Store subject_id as user data
            self.subject_combo.addItem(subject['subject_name'], subject['subject_id'])

        # Restore previous selection if available
        if hasattr(self, 'pending_subject_id') and self.pending_subject_id is not None:
            # Find index of pending subject
            for i in range(self.subject_combo.count()):
                if self.subject_combo.itemData(i) == self.pending_subject_id:
                    self.subject_combo.setCurrentIndex(i)
                    break

            self.pending_subject_id = None  # Clear pending selection

    def on_subject_selected(self, index):
        """
        Handle subject selection from dropdown.

        Args:
            index (int): Index of selected item in dropdown

        Side Effects:
            - Loads verses for selected subject via controller
        """
        if index < 0:
            return

        subject_id = self.subject_combo.itemData(index)
        if subject_id is not None:
            self.user_data_controller.select_subject(subject_id)

    def create_new_subject(self):
        """
        Show dialog to create a new subject.

        Side Effects:
            - Shows SubjectDialog modal window
            - Creates subject via controller if user accepts
            - Shows error if no group selected
        """
        if not self.user_data_controller.current_group_id:
            self.message_label.setText("Please select a group first")
            return

        dialog = SubjectDialog(self, mode="create")
        if dialog.exec():
            name, description = dialog.get_values()
            self.user_data_controller.create_subject(name, description)

    def delete_subject(self):
        """
        Delete the currently selected subject after confirmation.

        Side Effects:
            - Shows confirmation dialog
            - Deletes subject via controller if confirmed
        """
        current_index = self.subject_combo.currentIndex()
        if current_index < 0:
            self.message_label.setText("No subject selected")
            return

        subject_name = self.subject_combo.currentText()
        subject_id = self.subject_combo.itemData(current_index)

        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Delete subject '{subject_name}' and all its verses?\n\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.user_data_controller.delete_subject(subject_id)

    def find_subject(self):
        """
        Show subject search dialog (Phase 1: placeholder).

        Side Effects:
            - Shows message about future implementation
        """
        self.message_label.setText("Subject search - coming in future update")

    def save_config(self):
        """Save window configuration using ConfigManager"""
        config = {
            'window_geometry': {
                'x': self.x(),
                'y': self.y(),
                'width': self.width(),
                'height': self.height()
            },
            'splitter_sizes': self.main_splitter.sizes(),
            'selected_translations': self.selected_translations,
            'checkboxes': {
                'case_sensitive': self.case_sensitive_cb.isChecked(),
                'unique_verse': self.unique_verse_cb.isChecked(),
                'abbreviate_results': self.abbreviate_results_cb.isChecked()
            },
            'font_settings': {
                'title_font_size': self.title_font_size,
                'verse_font_size': self.verse_font_size
            },
            'user_data': {
                'current_group_id': self.user_data_controller.get_current_group_id(),
                'current_subject_id': self.user_data_controller.get_current_subject_id()
            }
        }

        self.config_manager.save(config)

    def load_config(self):
        """Load window configuration using ConfigManager"""
        config = self.config_manager.load()
        if not config:
            return None

        # Restore window geometry
        if 'window_geometry' in config:
            geom = config['window_geometry']
            self.setGeometry(geom['x'], geom['y'], geom['width'], geom['height'])

        # Restore splitter sizes
        if 'splitter_sizes' in config and self.main_splitter:
            self.main_splitter.setSizes(config['splitter_sizes'])

        # Restore selected translations
        if 'selected_translations' in config:
            self.selected_translations = config['selected_translations']
            count = len(self.selected_translations)
            self.translations_button.setText(f"Translations ({count})")

        # Restore checkbox states
        if 'checkboxes' in config:
            cb_config = config['checkboxes']
            self.case_sensitive_cb.setChecked(cb_config.get('case_sensitive', False))
            self.unique_verse_cb.setChecked(cb_config.get('unique_verse', False))
            self.abbreviate_results_cb.setChecked(cb_config.get('abbreviate_results', True))

        # Restore font settings
        if 'font_settings' in config:
            font_config = config['font_settings']
            self.title_font_size = font_config.get('title_font_size', 0)
            self.verse_font_size = font_config.get('verse_font_size', 0)
            # Apply the loaded font settings
            self.apply_font_settings()

        return config

    def closeEvent(self, event):
        """Handle window close event - save configuration before closing"""
        print("Closing application - saving configuration...")
        self.save_config()
        event.accept()  # Allow the window to close

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