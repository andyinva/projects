import sys
import os
import sqlite3
import urllib.request
import urllib.error
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QCheckBox, QPushButton, QComboBox, QLineEdit,
                             QVBoxLayout, QHBoxLayout, QSplitter, QFrame,
                             QScrollArea, QListWidget, QMessageBox, QProgressDialog, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QThread
from PyQt6.QtGui import QFont, QColor, QPalette

# Version number
VERSION = "1.1.3"

# Import custom UI components, config, and controllers from refactored modules
from bible_search_ui.ui.widgets import VerseItemWidget, VerseListWidget, SectionWidget
from bible_search_ui.ui.dialogs import TranslationSelectorDialog, FontSettingsDialog, SearchFilterDialog
from bible_search_ui.config import ConfigManager
from bible_search_ui.controllers import SearchController

# Import subject management (Windows 4 & 5)
from subject_manager import SubjectManager

# Book groups for filtering searches
BOOK_GROUPS = {
    "All Books": [],  # Empty list means no filter
    "Old Testament": [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
        "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther",
        "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
        "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"
    ],
    "New Testament": [
        "Matthew", "Mark", "Luke", "John", "Acts",
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
        "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude", "Revelation"
    ],
    "Pentateuch": [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy"
    ],
    "Wisdom Books": [
        "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon"
    ],
    "Major Prophets": [
        "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel"
    ],
    "Minor Prophets": [
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
        "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"
    ],
    "Gospels": [
        "Matthew", "Mark", "Luke", "John", "Acts"
    ],
    "Epistles": [
        "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
        "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
        "1 Timothy", "2 Timothy", "Titus", "Philemon",
        "Hebrews", "James", "1 Peter", "2 Peter",
        "1 John", "2 John", "3 John", "Jude"
    ]
}

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
        self.setWindowTitle(f"Bible Search Lite v{VERSION} (January 2026)")

        # Configuration manager
        self.config_manager = ConfigManager("bible_search_lite_config.json")
        self.config_manager = ConfigManager("bible_search_lite_config.json")
        self.config_file = "bible_search_lite_config.json"

        # Message log for Help menu
        self.message_log = []
        self.max_message_log_size = 500  # Keep last 500 messages

        # Debug log for Help menu (cleared on each app start)
        self.debug_log = []

        # Set initial geometry (will be overridden by load_config if config exists)
        self.setGeometry(100, 100, 1200, 900)

        # Set cross-platform stylesheet for consistent appearance on Windows and Linux
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                color: #000000;
            }
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #999999;
                border-radius: 3px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: #e6f2ff;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #cce4f7;
            }
            QPushButton:disabled {
                background-color: #e0e0e0;
                color: #999999;
            }
            QCheckBox {
                color: #000000;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #999999;
                border-radius: 2px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #0078d4;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border: 1px solid #0078d4;
                image: url(none);
            }
            QLineEdit, QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #999999;
                padding: 3px;
                border-radius: 2px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QLabel {
                color: #000000;
            }
            QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #999999;
            }
        """)

        # Font settings
        default_font = QFont("IBM Plex Mono", 9)
        self.setFont(default_font)

        # Font size settings (0=current/smallest, 1-4=larger sizes)
        self.title_font_size = 0  # Current: 10px
        self.verse_font_size = 0  # Current: 10px for reference and text
        self.title_font_sizes = [10, 10.5, 11, 11.5, 12, 12.5, 13]  # 7 choices, removed 9 and 9.5, added 12.5 and 13
        self.verse_font_sizes = [10, 10.5, 11, 11.5, 12, 12.5, 13]  # 7 choices, removed 9 and 9.5, added 12.5 and 13

        # Context-sensitive buttons (will be created in setup_ui)
        self.tips_btn = None
        self.copy_btn = None
        self.export_btn = None

        # Selection lock mode: when ANY boxes are checked, user must choose action
        self.selection_locked = False
        self.is_ctrl_a_selection = False  # True if selection was made via Ctrl+A
        self.blink_timer = None
        self.blink_state = False
        self.blink_auto_stop_timer = None  # Timer to auto-stop blinking after inactivity

        # Initialize search controller
        self.search_controller = SearchController()

        # Connect search controller signals
        self.search_controller.search_results_ready.connect(self.on_search_results_ready)
        self.search_controller.search_more_results_ready.connect(self.on_search_more_results_ready)
        self.search_controller.search_failed.connect(self.on_search_failed)
        self.search_controller.search_status.connect(self.on_search_status)
        self.search_controller.context_verses_ready.connect(self.on_context_verses_ready)

        # Selection manager
        self.selection_manager = SelectionManager()

        # Subject manager (Windows 4 & 5) - created in setup_ui
        self.subject_manager = None

        # Filter state
        self.last_search_term = ""
        self.last_search_params = {}
        self.filtered_words = None  # None means no filter, list means filter active
        self.available_word_variations = 0  # Count of available word variations for filter

        # Cross-reference history for "Go Back" functionality
        # Each entry is: (verse_reference, references_list, verse_list_state)
        # verse_list_state contains the verse data needed to restore Window 3
        self.cross_ref_history = []

        # Store references to verse list widgets
        self.verse_lists = {}

        # Message label for status updates
        self.message_label = None

        self.setup_ui()  # Create the UI (creates self.main_splitter)

        # Load saved configuration after UI is set up (restores window sizes)
        self.load_config()
        self.add_sample_verses()

    def log_message(self, message):
        """Add a message to the message log with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.message_log.append(log_entry)

        # Keep only the last N messages
        if len(self.message_log) > self.max_message_log_size:
            self.message_log = self.message_log[-self.max_message_log_size:]

    def set_message(self, message):
        """Set message label text and log it"""
        self.message_label.setText(message)
        self.log_message(message)

    def show_message_log(self):
        """Display the message log in a dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Message Log")
        dialog.setMinimumSize(800, 600)

        layout = QVBoxLayout(dialog)

        # Text area to display log
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setStyleSheet("font-family: monospace; background-color: white;")

        if self.message_log:
            log_text.setPlainText("\n".join(self.message_log))
            # Scroll to bottom to show most recent messages
            log_text.verticalScrollBar().setValue(log_text.verticalScrollBar().maximum())
        else:
            log_text.setPlainText("No messages logged yet.")

        layout.addWidget(log_text)

        # Buttons
        button_layout = QHBoxLayout()

        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(lambda: (self.message_log.clear(), log_text.setPlainText("Message log cleared.")))
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def debug_print(self, *args, **kwargs):
        """Capture print() calls and add to debug log with timestamp, then print to console"""
        import builtins
        from datetime import datetime

        # Convert args to string like self.debug_print() does
        message = ' '.join(str(arg) for arg in args)

        # Add to debug log with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.debug_log.append(log_entry)

        # Still print to console for real-time viewing
        builtins.print(*args, **kwargs)

    def show_debug_log(self):
        """Display the debug log in a dialog"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("Debug Log (Session)")
        dialog.setMinimumSize(900, 700)

        layout = QVBoxLayout(dialog)

        # Info label
        info_label = QLabel("Debug log shows technical messages from this session. Cleared on app restart.")
        info_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(info_label)

        # Text area to display log
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_text.setStyleSheet("font-family: monospace; font-size: 10px; background-color: white;")

        if self.debug_log:
            log_text.setPlainText("\n".join(self.debug_log))
            # Scroll to bottom to show most recent messages
            log_text.verticalScrollBar().setValue(log_text.verticalScrollBar().maximum())
        else:
            log_text.setPlainText("No debug messages logged yet.")

        layout.addWidget(log_text)

        # Buttons
        button_layout = QHBoxLayout()

        # Clear log button
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(lambda: (self.debug_log.clear(), log_text.setPlainText("Debug log cleared.")))
        button_layout.addWidget(clear_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        dialog.exec()

    def load_available_translations(self):
        """Load available translations from database"""
        import sqlite3
        translations = []
        try:
            db_path = self.search_service.database_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT abbreviation, name FROM translations ORDER BY abbreviation")
            translations = [row[0] for row in cursor.fetchall()]
            conn.close()
            self.debug_print(f"✓ Loaded {len(translations)} translations from database")
        except Exception as e:
            self.debug_print(f"⚠️  Error loading translations: {e}")
            # Fallback to common translations if database read fails
            translations = ["KJV", "ASV", "WEB", "YLT"]

        return translations if translations else ["KJV"]

    def setup_ui(self):
        """Set up the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)  # Reduced from 2 to 1 for thinner border
        main_layout.setSpacing(2)
        
        # Create main vertical splitter
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        # Style splitter handles to be visible and easy to grab
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #c0c0c0;
                border: 1px solid #999;
                height: 3px;
            }
            QSplitter::handle:hover {
                background-color: #4CAF50;
            }
        """)
        main_layout.addWidget(self.main_splitter)
        
        # 1. Message Window with context-sensitive buttons
        self.message_label = QLabel("Ready to search the Bible...")
        self.message_label.setStyleSheet("background-color: white; padding: 10px;")

        # Wrap message label and load more button in a beveled frame
        message_frame = QFrame()
        message_frame.setFrameShape(QFrame.Shape.Panel)
        message_frame.setFrameShadow(QFrame.Shadow.Sunken)
        message_frame.setLineWidth(3)
        message_frame.setMidLineWidth(2)
        message_layout = QHBoxLayout(message_frame)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(5)
        message_layout.addWidget(self.message_label)

        # Load More button (hidden by default, shown when there are more results)
        self.load_more_btn = QPushButton("Load Next 300")
        self.load_more_btn.setVisible(False)
        self.load_more_btn.clicked.connect(self.load_more_results_batch)
        self.load_more_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        message_layout.addWidget(self.load_more_btn)

        # Create context-sensitive buttons
        self.tips_btn = self.create_title_button("Help")
        self.copy_btn = self.create_title_button("Copy")
        self.export_btn = self.create_title_button("Export")

        # Create toggle button for Windows 4 & 5
        self.subject_toggle_btn = QPushButton("📑")  # Document icon
        self.subject_toggle_btn.setFixedSize(24, 24)
        self.subject_toggle_btn.setCheckable(True)  # Make it a toggle button
        self.subject_toggle_btn.setChecked(False)  # Default unchecked
        self.subject_toggle_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.subject_toggle_btn.setToolTip("Show/Hide Subject Features (Windows 4 & 5)")
        self.subject_toggle_btn.clicked.connect(self.on_subject_toggle_clicked)
        # Initial styling (unchecked state)
        self.update_subject_toggle_style(False)

        message_buttons = [self.tips_btn, self.copy_btn, self.export_btn, self.subject_toggle_btn]
        message_section = SectionWidget("1. Message Window", message_frame,
                                       show_settings=True, title_buttons=message_buttons, main_window=self)
        self.main_splitter.addWidget(message_section)

        # 2. Search Results
        search_controls = self.create_search_controls()
        search_verses = VerseListWidget("search")
        search_verses.main_window = self  # Enable click-to-activate
        search_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        search_verses.selection_changed.connect(self.update_subject_acquire_button)
        search_verses.selection_changed.connect(self.update_window3_acquire_style)
        search_verses.selection_changed.connect(self.update_copy_button_style)
        self.verse_lists['search'] = search_verses
        self.selection_manager.register_window("search", search_verses)

        search_section = SectionWidget("2. Search Results", search_verses, search_controls, main_window=self)
        self.main_splitter.addWidget(search_section)

        # 3. Reading Window
        reading_controls = self.create_reading_controls()
        reading_verses = VerseListWidget("reading")
        reading_verses.main_window = self  # Enable click-to-activate
        reading_verses.verse_navigation_requested.connect(self.on_verse_navigation)
        reading_verses.selection_changed.connect(self.update_subject_acquire_button)
        reading_verses.selection_changed.connect(self.update_window3_acquire_style)
        reading_verses.selection_changed.connect(self.update_copy_button_style)
        self.verse_lists['reading'] = reading_verses
        self.selection_manager.register_window("reading", reading_verses)

        reading_section = SectionWidget("3. Reading Window", reading_verses, reading_controls,
                                       main_window=self, show_translation=True)
        self.reading_section = reading_section  # Store reference to update translation label
        self.main_splitter.addWidget(reading_section)

        # 4 & 5. Subject Verses and Comments (modular, toggleable, combined)
        # Create subject manager
        self.subject_manager = SubjectManager(self.config_manager, self)
        combined_container, _ = self.subject_manager.create_ui(self.main_splitter)

        # Subject manager handles its own visibility based on config
        if combined_container:
            self.debug_print("✓ Subject features (Windows 4 & 5) initialized as combined unit")
            # Sync toggle button state with current visibility
            self.subject_toggle_btn.setChecked(self.subject_manager.is_visible)
            self.update_subject_toggle_style(self.subject_manager.is_visible)

            # Load subjects into Window 3's subject dropdown
            self.load_subjects_for_reading()
        else:
            self.debug_print("⚠️  Subject features not initialized")

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
            
        # Start with no active window - user must click to activate
        self.active_window_id = None
        # Set all windows to inactive state initially
        for wid, verse_list in self.verse_lists.items():
            verse_list.set_active(False)
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
                self.debug_print(f"Acquire button highlighted - selections available")
            else:
                self.acquire_button.setStyleSheet(self.get_button_style())
                self.debug_print(f"Acquire button normal - no selections available")

    def update_subject_acquire_button(self):
        """Update the Acquire button state and style in Window 4 when selections change in Windows 2 or 3"""
        if not self.subject_manager:
            return

        # If Windows 4 & 5 are not visible, the verse_manager won't exist yet
        if not self.subject_manager.verse_manager:
            return

        # Check if there are any selected verses in Windows 2 or 3
        search_count = self.verse_lists['search'].get_selected_count()
        reading_count = self.verse_lists['reading'].get_selected_count()
        has_selections = (search_count > 0) or (reading_count > 0)

        # Check if a subject is selected in EITHER Window 3 OR Window 4
        # This allows using Window 3's subject dropdown to enable Window 4's Acquire button
        has_subject_in_window4 = self.subject_manager.verse_manager.current_subject_id is not None
        has_subject_in_window3 = bool(self.reading_subject_combo.currentText().strip())
        has_subject = has_subject_in_window4 or has_subject_in_window3

        self.subject_manager.verse_manager.acquire_btn.setEnabled(has_subject and has_selections)

        # Green style when selections are available and subject is selected
        green_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #45a049;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """

        # Normal style
        normal_style = self.get_button_style()

        # Apply green style if both conditions met, otherwise normal
        if has_subject and has_selections:
            self.subject_manager.verse_manager.acquire_btn.setStyleSheet(green_style)
        else:
            self.subject_manager.verse_manager.acquire_btn.setStyleSheet(normal_style)

        self.debug_print(f"Subject Acquire button: W4_subject={has_subject_in_window4}, W3_subject={has_subject_in_window3}, selections={has_selections}, search={search_count}, reading={reading_count}")

    def update_window3_acquire_style(self):
        """Update Window 3 Acquire button styling and enabled state based on selections"""
        # Check if there are any selected verses in Windows 2 or 3
        search_count = self.verse_lists['search'].get_selected_count()
        reading_count = self.verse_lists['reading'].get_selected_count()
        has_selections = (search_count > 0) or (reading_count > 0)

        # Check if a subject is selected in Window 3
        has_subject = bool(self.reading_subject_combo.currentText().strip())

        # Enable button only if subject is selected AND there are selections in Windows 2/3
        # This matches Window 4's behavior - Acquire only works with Windows 2/3 verses
        self.send_btn.setEnabled(has_subject and has_selections)

        # Green style when selections are available and subject is selected
        green_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #45a049;
                border-radius: 3px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """

        # Normal style
        normal_style = self.get_button_style()

        # Apply green style if both conditions met, otherwise normal
        if has_subject and has_selections:
            self.send_btn.setStyleSheet(green_style)
        else:
            self.send_btn.setStyleSheet(normal_style)

    def update_copy_button_style(self):
        """Update Copy button styling based on selections in Windows 2, 3, or 4"""
        # Check if there are any selected verses in Windows 2, 3, or 4
        search_count = self.verse_lists['search'].get_selected_count()
        reading_count = self.verse_lists['reading'].get_selected_count()
        subject_count = self.verse_lists.get('subject', None)
        subject_count = subject_count.get_selected_count() if subject_count else 0

        has_selections = (search_count > 0) or (reading_count > 0) or (subject_count > 0)

        # Green style for title button (matches create_title_button style)
        green_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #45a049;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
                border: 1px solid #3d8b40;
            }
        """

        # Normal title button style
        normal_style = """
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
        """

        # Apply green style if selections exist, otherwise normal
        if has_selections:
            self.copy_btn.setStyleSheet(green_style)
        else:
            self.copy_btn.setStyleSheet(normal_style)

    def create_title_button(self, text):
        """Create a standardized button for section title bars"""
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtCore import Qt

        button = QPushButton(text)
        button.setFixedHeight(24)
        button.setMinimumWidth(60)

        # Don't steal focus when clicked - preserve active window
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)

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
        if text == "Tips" or text == "Help":
            button.clicked.connect(self.on_tips_clicked)
        elif text == "Copy":
            button.clicked.connect(self.on_copy_clicked)
        elif text == "Export":
            button.clicked.connect(self.on_export_clicked)
        return button

    def create_search_controls(self):
        """Create controls for the search section - SINGLE ROW LAYOUT"""
        controls_widget = QWidget()
        layout = QHBoxLayout(controls_widget)  # Changed to single HBoxLayout
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Left side - search controls
        self.search_input = QComboBox()
        self.search_input.setMinimumWidth(200)  # Reduced to fit in single row
        self.search_input.setEditable(True)
        self.search_input.setStyleSheet(self.get_combobox_style())
        self.search_input.lineEdit().setPlaceholderText("Enter search terms...")
        # Search history will be populated from config in load_config()

        # Connect signal to update search button style when text changes
        self.search_input.lineEdit().textChanged.connect(self.update_search_button_style)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        self.search_button.setStyleSheet(self.get_button_style())  # Start gray (empty)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_search_and_reading)
        clear_button.setStyleSheet(self.get_button_style())
        
        delete_verses_btn = QPushButton("Delete")
        # Translation selector button
        self.translations_button = QPushButton("Translations (1)")
        self.translations_button.clicked.connect(self.show_translation_selector)
        self.translations_button.setStyleSheet(self.get_button_style())

        # Store selected translations (default: KJV only)
        self.selected_translations = ["KJV"]

        # Search history (will be loaded from config)
        self.search_history = []

        # Book filter - changed from QComboBox to QPushButton with menu
        self.selected_book_filter = "All Books"  # Track current selection
        self.books_button = QPushButton("All Books")
        self.books_button.setStyleSheet(self.get_button_style())
        self.books_button.clicked.connect(self.show_book_menu)

        # NEW: Filter button (store as instance variable for highlighting)
        self.filter_button = QPushButton("Filter")
        self.filter_button.setMinimumWidth(100)  # Wide enough for "Filter (999)"
        self.filter_button.setStyleSheet(self.get_button_style())
        self.filter_button.clicked.connect(self.show_filter_dialog)

        # Add left-side controls
        layout.addWidget(self.search_input)
        layout.addWidget(self.search_button)
        layout.addWidget(clear_button)
        layout.addWidget(self.translations_button)
        layout.addWidget(self.books_button)
        layout.addWidget(self.filter_button)
        
        # Stretch to push checkboxes to the right
        layout.addStretch()
        
        # Right side - checkboxes
        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        self.unique_verse_cb = QCheckBox("Unique Verse")
        self.abbreviate_results_cb = QCheckBox("Abbreviate Results")
        self.abbreviate_results_cb.setChecked(True)  # Default to checked

        layout.addWidget(self.case_sensitive_cb)
        layout.addWidget(self.unique_verse_cb)
        layout.addWidget(self.abbreviate_results_cb)
        
        return controls_widget
        
    def create_reading_controls(self):
        """Create controls for the reading window"""
        controls_widget = QWidget()
        controls_widget.setStyleSheet("background-color: #f0f0f0; padding: 5px;")
        layout = QHBoxLayout(controls_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Subject dropdown for quick save - LEFT SIDE
        self.reading_subject_combo = QComboBox()
        self.reading_subject_combo.setEditable(True)
        self.reading_subject_combo.setPlaceholderText("Select or create subject...")
        self.reading_subject_combo.setMinimumWidth(200)
        self.reading_subject_combo.currentTextChanged.connect(self.on_reading_subject_changed)

        # Style dropdown for visibility on all platforms
        self.reading_subject_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: black;
                border: 1px solid #999;
                padding: 4px 8px;
                border-radius: 2px;
                min-width: 150px;
            }
            QComboBox:editable {
                background-color: white;
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
                border-top: 5px solid #555;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: #0078d4;
                selection-color: white;
                border: 1px solid #999;
            }
            QLineEdit {
                background-color: white;
                color: black;
            }
        """)

        layout.addWidget(self.reading_subject_combo)

        # Create button (creates new subject from dropdown text)
        self.create_subject_btn = QPushButton("Create")
        self.create_subject_btn.clicked.connect(self.on_create_subject_from_reading)
        self.create_subject_btn.setToolTip("Create a new subject with the typed name")
        layout.addWidget(self.create_subject_btn)

        # Acquire button (adds checked verses to selected subject)
        self.send_btn = QPushButton("Acquire")
        self.send_btn.setEnabled(False)  # Disabled until subject selected
        self.send_btn.clicked.connect(self.on_send_to_subject)
        self.send_btn.setToolTip("Acquire checked verses to selected subject")
        layout.addWidget(self.send_btn)

        # Stretch to push References dropdown to the right
        layout.addStretch()

        # Go Back button - only visible when references are shown
        self.go_back_btn = QPushButton("Go Back →")
        self.go_back_btn.setVisible(False)  # Hidden by default
        self.go_back_btn.clicked.connect(self.on_go_back_references)
        self.go_back_btn.setToolTip("Return to previous reference list")
        self.go_back_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: 1px solid #1976D2;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
                border: 1px solid #9E9E9E;
            }
        """)
        layout.addWidget(self.go_back_btn)

        # Cross-References dropdown - RIGHT SIDE
        self.cross_references_combo = QComboBox()
        self.cross_references_combo.setMinimumWidth(300)
        self.cross_references_combo.addItem("References (0)")
        self.cross_references_combo.setEnabled(False)  # Grayed out by default
        self.cross_references_combo.currentIndexChanged.connect(self.on_cross_reference_selected)

        # Style for References dropdown (will be updated when active)
        self.cross_references_combo.setStyleSheet(self.get_combobox_style())

        layout.addWidget(self.cross_references_combo)

        return controls_widget
        
    def get_button_style(self, active=False):
        """Return consistent button styling

        Args:
            active (bool): If True, return highlighted style for active state
        """
        if active:
            # Highlighted style for active filter
            return """
                QPushButton {
                    background-color: #4CAF50;
                    border: 2px solid #2E7D32;
                    padding: 4px 8px;
                    border-radius: 2px;
                    min-width: 50px;
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """
        else:
            # Normal style
            return """
                QPushButton {
                    background-color: #e0e0e0;
                    border: 1px solid #999;
                    padding: 4px 8px;
                    border-radius: 2px;
                    min-width: 50px;
                    color: #000000;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                    color: #000000;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                    color: #000000;
                }
                QPushButton:disabled {
                    background-color: #f0f0f0;
                    color: #999999;
                    border: 1px solid #ccc;
                }
            """

    def flash_button_green(self, button):
        """
        Temporarily flash a button green to indicate successful save.

        Args:
            button (QPushButton): The button to flash green
        """
        from PyQt6.QtCore import QTimer

        # Store original style
        original_style = button.styleSheet()

        # Green flash style (no padding to maintain button size)
        green_style = """
            QPushButton {
                background-color: #4CAF50;
                border: 2px solid #2E7D32;
                color: white;
                font-weight: bold;
            }
        """

        # Apply green style
        button.setStyleSheet(green_style)

        # Restore original style after 500ms
        def restore_style():
            button.setStyleSheet(original_style)
            button.update()  # Force button to repaint

        QTimer.singleShot(500, restore_style)

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

    def create_comment_controls(self):
        """DEPRECATED: Old comment controls - now handled by SubjectCommentManager"""
        # This method is no longer used - kept for reference only
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
        self.debug_print(f"Setting active window to: {window_id}")  # Debug output

        # Store the active window id so other components can check it
        self.active_window_id = window_id

        self.selection_manager.set_active_window(window_id)

        # Update visual feedback
        for wid, verse_list in self.verse_lists.items():
            is_active = (wid == window_id)
            verse_list.set_active(is_active)
            self.debug_print(f"Window {wid} active state: {is_active}")  # Debug output

            # Give keyboard focus to the active window for Ctrl+A to work
            if is_active:
                verse_list.setFocus()
                self.debug_print(f"✅ Focus set to window: {wid}")

    def update_filter_button_state(self):
        """Update the Filter button appearance based on filter active state"""
        if self.filtered_words is not None and len(self.filtered_words) > 0:
            # Filter is active - highlight the button and show count
            word_count = len(self.filtered_words)
            self.filter_button.setText(f"Filter ({word_count})")
            self.filter_button.setStyleSheet(self.get_button_style(active=True))
            self.debug_print(f"🟢 Filter button highlighted - {word_count} word(s) active")
        else:
            # No filter - normal appearance, check if we have available variations to show
            if hasattr(self, 'available_word_variations') and self.available_word_variations > 0:
                self.filter_button.setText(f"Filter ({self.available_word_variations})")
            else:
                self.filter_button.setText("Filter")
            self.filter_button.setStyleSheet(self.get_button_style(active=False))
            self.debug_print("⚪ Filter button normal - no filter active")

    def update_search_button_style(self):
        """Update search button style based on whether search box has text"""
        search_text = self.search_input.currentText().strip()

        if search_text:
            # Has text - blue/active style
            self.search_button.setStyleSheet(self.get_button_style(active=True))
        else:
            # Empty - gray/inactive style
            self.search_button.setStyleSheet(self.get_button_style(active=False))

    def show_book_menu(self):
        """Show hierarchical book filter menu"""
        menu = QMenu(self)

        # Add "All Books" option
        all_books_action = menu.addAction("All Books")
        all_books_action.triggered.connect(lambda: self.select_book_filter("All Books"))

        menu.addSeparator()

        # Create Old Testament submenu
        ot_menu = QMenu("Old Testament", self)
        # Add action to select entire Old Testament
        ot_all_action = ot_menu.addAction("✓ All Old Testament Books")
        ot_all_action.triggered.connect(lambda: self.select_book_filter("Old Testament"))
        ot_menu.addSeparator()
        # Add individual OT books
        for book in BOOK_GROUPS["Old Testament"]:
            book_action = ot_menu.addAction(book)
            book_action.triggered.connect(lambda checked, b=book: self.select_book_filter(b))
        menu.addMenu(ot_menu)

        # Create New Testament submenu
        nt_menu = QMenu("New Testament", self)
        # Add action to select entire New Testament
        nt_all_action = nt_menu.addAction("✓ All New Testament Books")
        nt_all_action.triggered.connect(lambda: self.select_book_filter("New Testament"))
        nt_menu.addSeparator()
        # Add individual NT books
        for book in BOOK_GROUPS["New Testament"]:
            book_action = nt_menu.addAction(book)
            book_action.triggered.connect(lambda checked, b=book: self.select_book_filter(b))
        menu.addMenu(nt_menu)

        menu.addSeparator()

        # Add other book groups
        other_groups = ["Pentateuch", "Wisdom Books", "Major Prophets", "Minor Prophets", "Gospels", "Epistles"]
        for group in other_groups:
            group_action = menu.addAction(group)
            group_action.triggered.connect(lambda checked, g=group: self.select_book_filter(g))

        # Show the menu at the button position
        menu.exec(self.books_button.mapToGlobal(self.books_button.rect().bottomLeft()))

    def select_book_filter(self, filter_name):
        """Handle book filter selection"""
        self.selected_book_filter = filter_name

        # Update button text
        if filter_name in BOOK_GROUPS and filter_name not in ["All Books", "Old Testament", "New Testament"]:
            # For specific book groups, show the group name
            self.books_button.setText(filter_name)
        elif filter_name in ["Old Testament", "New Testament"]:
            # For testaments, show abbreviated form
            short_name = "OT" if filter_name == "Old Testament" else "NT"
            self.books_button.setText(short_name)
        elif filter_name == "All Books":
            self.books_button.setText("All Books")
        else:
            # For individual books, show the book name
            self.books_button.setText(filter_name)

        self.debug_print(f"📚 Book filter selected: {filter_name}")

    def on_verse_navigation(self, verse_id):
        """Handle verse navigation between windows"""
        self.debug_print(f"Navigate to verse: {verse_id}")

        # When verse selected in search results, show context in reading window
        if verse_id.startswith("search_"):
            # Load context verses in reading window
            self.load_context_verses(verse_id)

        # When verse clicked in reading window, update cross-references dropdown
        elif verse_id.startswith("reading_"):
            # Get the verse widget to extract reference information
            if verse_id in self.verse_lists['reading'].verse_items:
                item, verse_widget = self.verse_lists['reading'].verse_items[verse_id]
                # Build verse reference from the widget data
                verse_reference = f"{verse_widget.book_abbrev} {verse_widget.chapter}:{verse_widget.verse_number}"
                # Update the cross-references dropdown
                self.update_cross_references_dropdown(verse_reference)
                self.debug_print(f"🔗 Updated cross-references for clicked verse: {verse_reference}")

    def clear_search_and_reading(self):
        """Clear search results, reading window, references dropdown, and subject selections"""
        self.verse_lists['search'].clear_verses()
        self.verse_lists['reading'].clear_verses()

        # Clear translation label in Reading Window
        if hasattr(self, 'reading_section') and hasattr(self.reading_section, 'translation_label') and self.reading_section.translation_label:
            self.reading_section.translation_label.setText("")

        # Clear the cross-references dropdown
        self.cross_references_combo.clear()
        self.cross_references_combo.addItem("References (0)")
        self.cross_references_combo.setEnabled(False)
        self.cross_references_combo.setStyleSheet(self.get_combobox_style())

        # Hide the Go Back button in Window 3
        self.go_back_btn.setVisible(False)

        # Clear subject dropdown in Window 3
        if hasattr(self, 'reading_subject_combo'):
            self.reading_subject_combo.setCurrentIndex(0)  # Reset to empty

        # Clear subject dropdown in Window 4
        if self.subject_manager and self.subject_manager.verse_manager:
            self.subject_manager.verse_manager.subject_dropdown.setCurrentIndex(0)
            self.subject_manager.verse_manager.current_subject = None
            self.subject_manager.verse_manager.current_subject_id = None
            # Update button states in Window 4
            self.subject_manager.verse_manager.update_button_states()

        # Clear remaining search results and hide Load More button
        self.remaining_search_results = []
        if hasattr(self, 'all_formatted_verses'):
            self.all_formatted_verses = []
        self.load_more_btn.setVisible(False)

        # Clear filter state and reset filter button
        self.filtered_words = None
        self.available_word_variations = 0
        self.update_filter_button_state()

        # Clear the search input box
        self.search_input.setCurrentIndex(-1)
        self.search_input.lineEdit().clear()

        # Stop blinking message if selection was locked
        self.unlock_selection_mode()

        self.set_message("Search results, reading window, references, and subjects cleared")

    def show_translation_selector(self):
        """Show dialog to select which translations to search"""
        dialog = TranslationSelectorDialog(
            self, 
            self.search_controller.bible_search.translations,
            self.selected_translations
        )
        
        if dialog.exec():
            self.selected_translations = dialog.get_selected_translations()
            self.debug_print(f"Selected translations: {self.selected_translations}")
            # Update button text to show count
            count = len(self.selected_translations)
            self.translations_button.setText(f"Translations ({count})")


    def show_font_settings(self):
        """Show settings menu with multiple options"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QCheckBox, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(300)

        layout = QVBoxLayout(dialog)

        # Font Settings button
        font_btn = QPushButton("Font Size Settings")
        font_btn.clicked.connect(lambda: [dialog.accept(), self.show_font_size_dialog()])
        layout.addWidget(font_btn)

        # Check for Updates button
        update_btn = QPushButton("Check for Updates")
        update_btn.clicked.connect(lambda: [dialog.accept(), self.check_for_updates()])
        layout.addWidget(update_btn)

        # Backup & Restore button
        backup_btn = QPushButton("Backup & Restore Subjects")
        backup_btn.clicked.connect(lambda: [dialog.accept(), self.show_backup_restore_dialog()])
        layout.addWidget(backup_btn)

        # Subject Features toggle
        layout.addWidget(QLabel(""))  # Spacer
        subject_label = QLabel("Subject Features (Windows 4 & 5):")
        layout.addWidget(subject_label)

        subject_checkbox = QCheckBox("Show Subject Verses && Comments")
        subject_checkbox.setChecked(self.subject_manager and self.subject_manager.is_visible)
        subject_checkbox.stateChanged.connect(lambda state: self.toggle_subject_features(state == 2))
        layout.addWidget(subject_checkbox)

        # Close button
        layout.addWidget(QLabel(""))  # Spacer
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def show_font_size_dialog(self):
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

    def toggle_subject_features(self, show):
        """Toggle visibility of Windows 4 & 5"""
        if not self.subject_manager:
            self.set_message("⚠️  Subject features not initialized")
            return

        if show:
            self.subject_manager.show()
            self.set_message("✓ Subject features enabled")

            # If Window 3 has a subject selected, sync it to Window 4 and load verses
            if hasattr(self, 'reading_subject_combo'):
                subject_name = self.reading_subject_combo.currentText().strip()
                if subject_name and self.subject_manager.verse_manager:
                    # Get subject ID
                    try:
                        cursor = self.subject_manager.db_conn.cursor()
                        cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                        result = cursor.fetchone()
                        if result:
                            subject_id = result['id']
                            # Set Window 4's dropdown to match Window 3
                            self.subject_manager.verse_manager.subject_dropdown.setCurrentText(subject_name)
                            self.subject_manager.verse_manager.current_subject = subject_name
                            self.subject_manager.verse_manager.current_subject_id = subject_id
                            # Load the verses
                            self.subject_manager.verse_manager.load_subject_verses()
                            self.debug_print(f"✓ Auto-loaded subject '{subject_name}' verses into Window 4")
                    except Exception as e:
                        self.debug_print(f"⚠️ Error auto-loading subject: {e}")
        else:
            self.subject_manager.hide()
            self.set_message("✓ Subject features hidden")

    def show_backup_restore_dialog(self):
        """Show dialog with backup and restore options"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel

        dialog = QDialog(self)
        dialog.setWindowTitle("Backup & Restore Subjects")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Info label
        info = QLabel("Backup your subjects, verses, and comments to share with others\nor restore from a backup file.")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px; color: #666;")
        layout.addWidget(info)

        # Create Backup button
        backup_btn = QPushButton("📦 Create Backup")
        backup_btn.setMinimumHeight(50)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        backup_btn.clicked.connect(lambda: [dialog.accept(), self.create_backup()])
        layout.addWidget(backup_btn)

        # Restore Backup button
        restore_btn = QPushButton("📥 Restore from Backup")
        restore_btn.setMinimumHeight(50)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        restore_btn.clicked.connect(lambda: [dialog.accept(), self.restore_backup()])
        layout.addWidget(restore_btn)

        layout.addSpacing(20)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def create_backup(self):
        """Create a backup zip file of all subjects, verses, and comments"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json
        import zipfile
        from datetime import datetime

        if not self.subject_manager:
            self.set_message("⚠️  Subject features not available")
            return

        # Ask user where to save backup
        default_filename = f"bible_subjects_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup File",
            default_filename,
            "Zip Files (*.zip)"
        )

        if not filename:
            return

        try:
            # Export subjects data from database
            cursor = self.subject_manager.db_conn.cursor()

            # Get all subjects
            cursor.execute("SELECT id, name FROM subjects ORDER BY name")
            subjects = cursor.fetchall()

            backup_data = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "subjects": []
            }

            # For each subject, get its verses and comments
            for subject in subjects:
                subject_id = subject['id']
                subject_name = subject['name']

                # Get verses for this subject
                cursor.execute("""
                    SELECT verse_ref, verse_text, translation, comments
                    FROM subject_verses
                    WHERE subject_id = ?
                    ORDER BY id
                """, (subject_id,))
                verses = cursor.fetchall()

                subject_data = {
                    "name": subject_name,
                    "verses": [
                        {
                            "reference": v['verse_ref'],
                            "text": v['verse_text'],
                            "translation": v['translation'],
                            "comments": v['comments'] or ""
                        }
                        for v in verses
                    ]
                }

                backup_data["subjects"].append(subject_data)

            # Create zip file with JSON data
            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                json_data = json.dumps(backup_data, indent=2)
                zipf.writestr("subjects_backup.json", json_data)

            subject_count = len(backup_data["subjects"])
            verse_count = sum(len(s["verses"]) for s in backup_data["subjects"])

            self.set_message(f"✓ Backup created: {subject_count} subjects, {verse_count} verses")
            self.debug_print(f"✓ Backup saved to: {filename}")

            QMessageBox.information(
                self,
                "Backup Complete",
                f"Successfully backed up:\n\n"
                f"• {subject_count} subjects\n"
                f"• {verse_count} verses with comments\n\n"
                f"File: {filename}"
            )

        except Exception as e:
            self.set_message(f"⚠️  Error creating backup: {e}")
            self.debug_print(f"⚠️  Backup error: {e}")
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{e}")

    def restore_backup(self):
        """Restore subjects from a backup zip file"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QLineEdit
        import json
        import zipfile

        if not self.subject_manager:
            self.set_message("⚠️  Subject features not available")
            return

        # Ask user to select backup file
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Backup File",
            "",
            "Zip Files (*.zip)"
        )

        if not filename:
            return

        try:
            # Extract and read JSON from zip
            with zipfile.ZipFile(filename, 'r') as zipf:
                json_data = zipf.read("subjects_backup.json").decode('utf-8')
                backup_data = json.loads(json_data)

            self.debug_print(f"✓ Loaded backup file: {filename}")
            self.debug_print(f"✓ Backup version: {backup_data.get('version', 'unknown')}")
            self.debug_print(f"✓ Backup created: {backup_data.get('created', 'unknown')}")

            cursor = self.subject_manager.db_conn.cursor()

            # Get existing subjects
            cursor.execute("SELECT name FROM subjects")
            existing_subjects = {row['name'] for row in cursor.fetchall()}

            restored_count = 0
            merged_count = 0
            renamed_count = 0

            # Process each subject in backup
            for subject_data in backup_data["subjects"]:
                subject_name = subject_data["name"]
                verses = subject_data["verses"]

                # Check if subject already exists
                if subject_name in existing_subjects:
                    # Show conflict resolution dialog
                    action, new_name = self.show_conflict_dialog(subject_name, len(verses))

                    if action == "cancel":
                        continue
                    elif action == "rename":
                        subject_name = new_name
                        renamed_count += 1
                    elif action == "merge":
                        merged_count += 1

                # Get or create subject
                if subject_name in existing_subjects and action != "rename":
                    # Merge into existing subject
                    cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
                    subject_id = cursor.fetchone()['id']
                else:
                    # Create new subject
                    cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
                    subject_id = cursor.lastrowid
                    existing_subjects.add(subject_name)

                # Add all verses
                for verse in verses:
                    # Check if verse already exists in this subject
                    cursor.execute("""
                        SELECT id FROM subject_verses
                        WHERE subject_id = ? AND verse_ref = ? AND translation = ?
                    """, (subject_id, verse['reference'], verse['translation']))

                    existing_verse = cursor.fetchone()

                    if existing_verse:
                        # Update existing verse (merge comments)
                        verse_id = existing_verse['id']
                        cursor.execute("""
                            UPDATE subject_verses
                            SET comments = ?
                            WHERE id = ?
                        """, (verse['comments'], verse_id))
                    else:
                        # Insert new verse
                        cursor.execute("""
                            INSERT INTO subject_verses (subject_id, verse_ref, verse_text, translation, comments)
                            VALUES (?, ?, ?, ?, ?)
                        """, (subject_id, verse['reference'], verse['text'], verse['translation'], verse['comments']))

                restored_count += 1

            self.subject_manager.db_conn.commit()

            # Reload subjects in dropdowns
            if hasattr(self, 'reading_subject_combo'):
                self.load_subjects_for_reading()
            if self.subject_manager.verse_manager:
                self.subject_manager.verse_manager.load_subjects()

            self.set_message(f"✓ Restored {restored_count} subjects from backup")
            self.debug_print(f"✓ Restore complete: {restored_count} subjects, {merged_count} merged, {renamed_count} renamed")

            QMessageBox.information(
                self,
                "Restore Complete",
                f"Successfully restored backup:\n\n"
                f"• {restored_count} subjects restored\n"
                f"• {merged_count} subjects merged\n"
                f"• {renamed_count} subjects renamed"
            )

        except Exception as e:
            self.set_message(f"⚠️  Error restoring backup: {e}")
            self.debug_print(f"⚠️  Restore error: {e}")
            QMessageBox.critical(self, "Restore Error", f"Failed to restore backup:\n{e}")

    def show_conflict_dialog(self, subject_name, verse_count):
        """Show dialog to resolve subject name conflict"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QLineEdit, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Subject Name Conflict")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        # Info message
        info = QLabel(f"The subject '{subject_name}' already exists in your database.\n"
                     f"The backup contains {verse_count} verses for this subject.\n\n"
                     f"How would you like to proceed?")
        info.setWordWrap(True)
        info.setStyleSheet("padding: 10px;")
        layout.addWidget(info)

        # Radio button group
        button_group = QButtonGroup(dialog)

        merge_radio = QRadioButton(f"Merge with existing '{subject_name}' (add new verses, keep existing)")
        merge_radio.setChecked(True)
        button_group.addButton(merge_radio, 1)
        layout.addWidget(merge_radio)

        rename_radio = QRadioButton("Import as new subject with different name:")
        button_group.addButton(rename_radio, 2)
        layout.addWidget(rename_radio)

        # Name input for rename option
        name_layout = QHBoxLayout()
        name_layout.addSpacing(30)
        name_input = QLineEdit(f"{subject_name} (imported)")
        name_input.setEnabled(False)
        name_layout.addWidget(name_input)
        layout.addLayout(name_layout)

        rename_radio.toggled.connect(name_input.setEnabled)

        skip_radio = QRadioButton("Skip this subject (don't import)")
        button_group.addButton(skip_radio, 3)
        layout.addWidget(skip_radio)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel Restore")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        result = dialog.exec()

        if not result:
            return ("cancel", None)

        if merge_radio.isChecked():
            return ("merge", subject_name)
        elif rename_radio.isChecked():
            new_name = name_input.text().strip()
            if not new_name:
                new_name = f"{subject_name} (imported)"
            return ("rename", new_name)
        else:  # skip
            return ("cancel", None)

    def on_subject_toggle_clicked(self, checked):
        """Handle toggle button click for Windows 4 & 5"""
        self.toggle_subject_features(checked)
        self.update_subject_toggle_style(checked)

    def update_subject_toggle_style(self, is_active):
        """Update the toggle button styling based on state"""
        if is_active:
            # Green/highlighted when active
            self.subject_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #45a049;
                    border-radius: 3px;
                    font-size: 14px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                    border: 2px solid #3d8b40;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #45a049;
                }
            """)
        else:
            # Normal white style when inactive (matches other title buttons)
            self.subject_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #333;
                    border: 1px solid #999;
                    border-radius: 3px;
                    font-size: 14px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border: 1px solid #666;
                }
                QPushButton:checked {
                    background-color: white;
                    color: #333;
                    border: 1px solid #999;
                }
            """)

    def show_filter_dialog(self):
        """Show filter dialog to select which word variations to include"""
        self.debug_print("🔍 Filter button clicked!")

        # Check if there are search results
        if 'search' not in self.verse_lists:
            self.debug_print("❌ 'search' not in verse_lists")
            self.set_message("No search results to filter. Perform a search first.")
            return

        if not self.verse_lists['search'].verse_items:
            self.debug_print(f"❌ No verse items in search window (count: {len(self.verse_lists['search'].verse_items)})")
            self.set_message("No search results to filter. Perform a search first.")
            return

        self.debug_print(f"✅ Found {len(self.verse_lists['search'].verse_items)} verses in search results")

        # Extract word counts from current search results
        word_counts = self.extract_word_counts()
        self.debug_print(f"📊 Extracted {len(word_counts)} unique words")

        if not word_counts:
            self.set_message("No words found in search results")
            return

        # Store the count of available word variations
        self.available_word_variations = len(word_counts)

        self.debug_print("📦 Opening SearchFilterDialog...")
        # Show the filter dialog
        dialog = SearchFilterDialog(self, word_counts)
        if dialog.exec():
            # Get selected words
            selected_words = dialog.get_selected_words()

            # Store filtered words for the next search
            self.filtered_words = selected_words if selected_words else None

            # Update the Filter button appearance based on filter state
            self.update_filter_button_state()

            # Display message about filter
            if self.filtered_words:
                self.set_message(f"Filter applied: {len(self.filtered_words)} word(s) selected. Click Search to re-filter results.")
            else:
                self.set_message("All words unchecked - filter cleared")

    def _extract_phrase_patterns(self, all_results, query):
        """Extract phrase patterns for word placeholder queries.

        For example, query "who & sent" would extract:
        - "who had sent": 5
        - "who hath sent": 3
        - "who was sent": 2
        etc.

        Returns:
            dict: Mapping of complete phrase -> count
        """
        import re

        phrase_counts = {}

        # Build regex pattern from query with & placeholders
        regex_parts = []
        parts = query.split()

        for part in parts:
            if part == '&':
                # & matches any single word - capture it
                regex_parts.append(r'(\w+)')
            else:
                # Regular word - convert wildcards to regex and capture
                # Both * and % are stem/root wildcards
                word_pattern = part.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
                regex_parts.append(f'({word_pattern})')

        # Join with \s+ (one or more whitespace)
        regex_pattern = r'\b' + r'\s+'.join(regex_parts) + r'\b'

        self.debug_print(f"📊 Extracting phrase patterns with regex: {regex_pattern}")

        # Extract matching phrases from all results
        for result in all_results:
            # Get text from result
            if isinstance(result, dict):
                text = result.get('Text', '')
            elif hasattr(result, 'text'):
                text = result.text
            else:
                text = str(result)

            # Remove highlight brackets
            text_cleaned = text.replace('[', '').replace(']', '')

            # Find all matches in this verse
            for match in re.finditer(regex_pattern, text_cleaned, flags=re.IGNORECASE):
                # Build the complete matched phrase
                matched_words = match.groups()
                # Capitalize each word for consistent display
                phrase = ' '.join(word.capitalize() for word in matched_words)
                phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1

        # Print summary
        self.debug_print(f"📊 Found {len(phrase_counts)} unique phrase pattern(s) from {len(all_results)} verses:")
        for phrase, count in sorted(phrase_counts.items(), key=lambda x: (-x[1], x[0]))[:20]:
            self.debug_print(f"   {phrase}: {count}")
        if len(phrase_counts) > 20:
            self.debug_print(f"   ... and {len(phrase_counts) - 20} more")

        return phrase_counts

    def extract_word_counts(self):
        """
        Extract unique words and their counts from ALL search results.
        Re-queries the database to get complete results, not just displayed verses.
        Handles AND searches by extracting patterns for each search term.

        Returns:
            dict: Mapping of word -> count
        """
        import re

        word_counts = {}

        # Get ALL search results from search controller's cached results
        # The search_controller stores all results in all_search_results
        # This is MUCH more efficient than re-querying the database
        all_results = self.search_controller.all_search_results

        if not all_results:
            self.debug_print("⚠️  No search results available in controller")
            self.debug_print("   Falling back to displayed verses only")
            # Fallback: use displayed verses
            all_results = []
            for verse_id, verse_item in self.verse_lists['search'].verse_items.items():
                _, widget = verse_item
                # Create a simple object with text attribute
                class FallbackResult:
                    def __init__(self, text):
                        self.text = text
                all_results.append(FallbackResult(widget.text))

        self.debug_print(f"📊 Extracting from {len(all_results)} total search results (not just displayed {len(self.verse_lists['search'].verse_items)})")

        # Check if query contains & (word placeholder)
        query = self.current_search_query if hasattr(self, 'current_search_query') else ""
        contains_word_placeholder = '&' in query and ' & ' in query

        if contains_word_placeholder:
            # Extract phrase patterns for word placeholder queries
            # For "who & sent", extract patterns like "who had sent", "who hath sent", etc.
            self.debug_print(f"🔍 Query contains word placeholder: '{query}'")
            return self._extract_phrase_patterns(all_results, query)

        # Original logic for non-placeholder queries
        # Get search patterns from current search query
        search_patterns = []
        if hasattr(self, 'current_search_query') and self.current_search_query:
            # Parse the search query to get individual search terms
            search_term = self.current_search_query

            # Split on AND/OR (case insensitive)
            terms = re.split(r'\s+(?:AND|OR)\s+', search_term, flags=re.IGNORECASE)

            # If no AND/OR was found, split on spaces (each word is a separate term)
            # For example: "who sen*" → ["who", "sen*"]
            # But keep quoted phrases together: '"love one another"' → ['"love one another"']
            if len(terms) == 1 and ' ' in terms[0]:
                # Split on spaces, but keep quoted phrases together
                # Use regex to match quoted strings or individual words
                terms = re.findall(r'"[^"]*"|\'[^\']*\'|\S+', terms[0])

            for term in terms:
                term = term.strip()
                if not term:
                    continue

                # Strip parentheses from terms (they're used for grouping in queries)
                term = term.strip('()')
                if not term:
                    continue

                # Check if term is quoted (for exact matching)
                is_quoted = (term.startswith('"') and term.endswith('"')) or \
                           (term.startswith("'") and term.endswith("'"))

                # Remove quotes for pattern building
                term_clean = term.strip('"\'')
                if not term_clean:
                    continue

                term_lower = term_clean.lower()

                # Check if this is a multi-word phrase (contains spaces)
                is_phrase = ' ' in term_lower

                # Build pattern based on whether term is quoted
                if is_quoted:
                    if is_phrase:
                        # Multi-word quoted phrase like "love one another"
                        # Don't add to search_patterns - we'll extract the whole phrase below
                        # Store phrase pattern for later extraction
                        if not hasattr(self, '_phrase_patterns_for_filter'):
                            self._phrase_patterns_for_filter = []
                        # Escape the phrase and match it as a whole
                        phrase_pattern = re.compile(re.escape(term_lower), re.IGNORECASE)
                        self._phrase_patterns_for_filter.append((term_lower, phrase_pattern))
                        continue
                    else:
                        # Single-word quoted term
                        # Check if quoted term contains wildcards
                        # "sing*" should match words starting with "sing"
                        if '*' in term_lower or '%' in term_lower or '?' in term_lower:
                            # Quoted wildcard - build pattern with word boundaries
                            pattern_parts = []
                            pattern_parts.append(r'^')

                            for char in term_lower:
                                if char in ('*', '%'):
                                    # Match word characters including apostrophes
                                    pattern_parts.append(r"[a-zA-Z]*(?:[''][a-zA-Z]*)*")
                                elif char == '?':
                                    pattern_parts.append(r'\w')
                                else:
                                    pattern_parts.append(re.escape(char))

                            pattern_parts.append(r'$')
                            pattern = ''.join(pattern_parts)
                            search_patterns.append(re.compile(pattern))
                        else:
                            # Quoted term without wildcards: exact word match only (strict)
                            # Pattern: ^word$ matches only the exact word
                            pattern = r'^' + re.escape(term_lower) + r'$'
                            search_patterns.append(re.compile(pattern))
                else:
                    # Unquoted term: partial match (matches word containing the term)
                    # Wildcards are NOT supported for unquoted terms - treat as literal characters
                    # For unquoted terms, match words CONTAINING the search term
                    # Example: "sent" matches "sent", "presents", "sentries", "resent"
                    # Example: "sing*" (with asterisk) matches literal "sing*" text
                    # Pattern: ^\w*term\w*$ matches any word containing "term"
                    pattern = r'^\w*' + re.escape(term_lower) + r'\w*$'
                    search_patterns.append(re.compile(pattern))

            self.debug_print(f"🔍 Search patterns for filtering: {[p.pattern for p in search_patterns]}")

        # Check if we have phrase patterns to extract
        has_phrase_patterns = hasattr(self, '_phrase_patterns_for_filter') and self._phrase_patterns_for_filter

        if has_phrase_patterns:
            # Extract phrase occurrences instead of individual words
            phrase_counts = {}
            for result in all_results:
                if isinstance(result, dict):
                    text = result.get('Text', '')
                elif hasattr(result, 'text'):
                    text = result.text
                else:
                    text = str(result)
                text_cleaned = text.replace('[', '').replace(']', '')

                # Search for each phrase pattern
                for phrase_text, phrase_pattern in self._phrase_patterns_for_filter:
                    # Find all occurrences of the phrase in this verse
                    matches = phrase_pattern.findall(text_cleaned)
                    for match in matches:
                        # Normalize phrase to title case for display
                        phrase_normalized = ' '.join(word.capitalize() for word in match.split())
                        phrase_counts[phrase_normalized] = phrase_counts.get(phrase_normalized, 0) + 1

            # Clean up temporary phrase patterns
            del self._phrase_patterns_for_filter

            self.debug_print(f"📊 Found {len(phrase_counts)} unique phrase(s) from {len(all_results)} verses:")
            for phrase, count in sorted(phrase_counts.items(), key=lambda x: (-x[1], x[0])):
                self.debug_print(f"   {phrase}: {count}")

            return phrase_counts

        # Extract words from all results (non-phrase queries)
        for result in all_results:
            # Extract words from verse text
            # IMPORTANT: Remove highlight brackets [  ] and curly braces {  } from text before word extraction
            # Our bracket notation uses [base]{variation} format
            # Results from controller are dicts with 'Text' key
            if isinstance(result, dict):
                text = result.get('Text', '')
            elif hasattr(result, 'text'):
                text = result.text
            else:
                text = str(result)
            text_cleaned = text.replace('[', '').replace(']', '').replace('{', '').replace('}', '')

            # Split on word boundaries, keep alphanumeric words including possessives (father's)
            # Pattern matches: word or word's or word'
            words = re.findall(r"\b[a-zA-Z]+(?:[''][a-zA-Z]*)?\b", text_cleaned)

            for word in words:
                # Only include words that match one of the search patterns
                word_lower = word.lower()
                matches_pattern = False

                if search_patterns:
                    for pattern in search_patterns:
                        if pattern.match(word_lower):
                            matches_pattern = True
                            break
                else:
                    # If no search patterns, include all words (fallback)
                    matches_pattern = True

                if matches_pattern:
                    # Normalize to title case for display
                    word_normalized = word.capitalize()
                    word_counts[word_normalized] = word_counts.get(word_normalized, 0) + 1

        # Print summary of matched words
        self.debug_print(f"📊 Found {len(word_counts)} unique word(s) from {len(all_results)} verses:")
        for word, count in sorted(word_counts.items(), key=lambda x: (-x[1], x[0]))[:20]:
            self.debug_print(f"   {word}: {count}")
        if len(word_counts) > 20:
            self.debug_print(f"   ... and {len(word_counts) - 20} more")

        return word_counts

    def parse_search_patterns(self, search_term):
        """
        Parse search term and extract individual patterns for filtering.
        Handles AND, OR, wildcards, and phrases.

        Args:
            search_term (str): Original search term (e.g., "who AND sent*")

        Returns:
            list: List of regex patterns to match
        """
        import re

        if not search_term:
            return []

        patterns = []

        # Remove quotes
        search_term = search_term.strip().strip('"\'')

        # Split on AND/OR (case insensitive)
        terms = re.split(r'\s+(?:AND|OR)\s+', search_term, flags=re.IGNORECASE)

        for term in terms:
            term = term.strip()
            if not term:
                continue

            # Convert wildcard pattern to regex with word boundaries
            # Handle *, %, and ? wildcards properly
            term_lower = term.lower()
            pattern_parts = []

            # Add start anchor
            pattern_parts.append(r'^')

            # Convert term character by character
            i = 0
            while i < len(term_lower):
                char = term_lower[i]
                if char in ('*', '%'):
                    pattern_parts.append(r'\w*')  # Match word characters
                elif char == '?':
                    pattern_parts.append(r'\w')   # Match single word character
                else:
                    pattern_parts.append(re.escape(char))
                i += 1

            # Add end anchor
            pattern_parts.append(r'$')

            pattern = ''.join(pattern_parts)
            patterns.append(pattern)
            self.debug_print(f"   Pattern: {term} → {pattern}")

        return patterns

    def convert_search_to_regex(self, search_term):
        """
        Convert a search term with wildcards to a regex pattern.

        Args:
            search_term (str): Search term (may include * wildcards)

        Returns:
            str: Regex pattern for matching words
        """
        import re

        if not search_term:
            return None

        # Remove quotes and extra spaces
        search_term = search_term.strip().strip('"\'')

        # If it's a phrase (contains spaces), just use the first word
        if ' ' in search_term:
            search_term = search_term.split()[0]

        # Convert wildcard pattern to regex with word boundaries
        # Handle *, %, and ? wildcards properly
        pattern_parts = []
        starts_with_wildcard = search_term.startswith('*') or search_term.startswith('%')

        # Add word boundary at start if not starting with wildcard
        if not starts_with_wildcard:
            pattern_parts.append(r'\b')

        # Convert term character by character
        i = 0
        while i < len(search_term):
            char = search_term[i]
            if char in ('*', '%'):
                pattern_parts.append(r'\w*')  # Match word characters
            elif char == '?':
                pattern_parts.append(r'\w')   # Match single word character
            else:
                pattern_parts.append(re.escape(char))
            i += 1

        # Always add word boundary at end
        pattern_parts.append(r'\b')

        pattern = ''.join(pattern_parts)
        return pattern

    def apply_word_filter(self, verses):
        """
        Filter verses to only include those containing selected words.
        Also re-applies highlighting to show only the filtered words.

        Args:
            verses (list): List of SearchResult objects

        Returns:
            list: Filtered list of SearchResult objects with updated highlighting
        """
        import re

        if not self.filtered_words:
            return verses

        filtered = []

        # Convert filtered words to lowercase set for case-insensitive matching
        allowed_words_lower = {word.lower() for word in self.filtered_words}
        self.debug_print(f"🔍 Filtering for words: {allowed_words_lower}")

        for verse in verses:
            # IMPORTANT: Remove highlight brackets AND curly braces before word extraction
            # Our bracket notation uses [base]{variation} format for two-color highlighting
            text_cleaned = verse.text.replace('[', '').replace(']', '').replace('{', '').replace('}', '')

            # Extract words from verse text, including possessives (father's)
            # Pattern matches: word or word's or word'
            words = re.findall(r"\b[a-zA-Z]+(?:[''][a-zA-Z]*)?\b", text_cleaned)
            # Normalize to lowercase
            verse_words_lower = {word.lower() for word in words}

            # Check if any of the verse's words are in the allowed set
            matched_words = verse_words_lower & allowed_words_lower
            if matched_words:
                # Re-highlight the verse text to show only the filtered words
                # Build a pattern that matches any of the filtered words (case-insensitive)
                patterns = []
                for word in self.filtered_words:
                    # Escape special regex characters (including apostrophes) and add word boundaries
                    escaped_word = re.escape(word)
                    patterns.append(escaped_word)

                # Combine patterns with OR
                combined_pattern = r'\b(' + '|'.join(patterns) + r')\b'

                # Find all matches and their positions in the cleaned text
                matches = []
                for match in re.finditer(combined_pattern, text_cleaned, re.IGNORECASE):
                    matches.append((match.start(), match.end(), match.group(0)))

                # Sort by position in reverse order to preserve indices when inserting brackets
                matches.sort(key=lambda x: x[0], reverse=True)

                # Apply new highlighting (single-color green only)
                highlighted_text = text_cleaned
                for start, end, matched_text in matches:
                    highlighted_text = highlighted_text[:start] + '[' + matched_text + ']' + highlighted_text[end:]

                # Update the verse text with new highlighting
                verse.text = highlighted_text
                filtered.append(verse)

        self.debug_print(f"✅ Filter kept {len(filtered)} of {len(verses)} verses")
        return filtered

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
                # Unpack tuple: (QListWidgetItem, VerseItemWidget)
                _, widget = verse_item

                # Update the combined text label (reference + text)
                verse_font = QFont("IBM Plex Mono")
                verse_font.setBold(False)
                verse_font.setPointSizeF(verse_size)  # Use setPointSizeF for fractional sizes
                widget.text_label.setFont(verse_font)

            # Recalculate verse heights after font change
            verse_list.update_item_sizes()

    def perform_search(self):
        """Perform a Bible search using SearchController"""
        import time

        self.debug_print(f"\n{'='*60}")
        self.debug_print(f"🔍 SEARCH BUTTON CLICKED")
        self.debug_print(f"{'='*60}")

        search_term = self.search_input.currentText().strip()
        if not search_term:
            self.set_message("Please enter search terms")
            self.debug_print("❌ No search term entered")
            return

        # Check for unquoted wildcards and show helpful message
        # Wildcards * and ? must be inside quotes to work
        import re

        # Better approach: extract all quoted sections, then check if wildcards exist outside them
        # Find all quoted sections (content between quotes)
        quoted_sections = re.findall(r'"[^"]*"', search_term)

        # Remove all quoted sections temporarily to get unquoted portion
        unquoted_portion = search_term
        for quoted in quoted_sections:
            unquoted_portion = unquoted_portion.replace(quoted, '', 1)

        # Now check if there are any wildcards in the unquoted portion
        if '*' in unquoted_portion or '?' in unquoted_portion:
            # Find the specific wildcard term to show in the message
            wildcard_match = re.search(r'(\w*[*?]+\w*)', unquoted_portion)
            if wildcard_match:
                term = wildcard_match.group(1)
                self.set_message(f"💡 Wildcards (* or ?) need quotation marks to work. Try: \"{term}\"")
                self.debug_print(f"⚠️  Unquoted wildcard detected: {term}")
                return

        # Record search start time and search query
        self.search_start_time = time.time()
        self.current_search_query = search_term

        self.debug_print(f"📝 Search term: '{search_term}'")

        # Note: Search history is now added in on_search_results_ready(),
        # and only if the search returns results

        # Get selected book filter
        selected_book_group = self.selected_book_filter
        # Check if it's an individual book (not in BOOK_GROUPS)
        if selected_book_group in BOOK_GROUPS:
            book_filter = BOOK_GROUPS.get(selected_book_group, [])
        else:
            # Individual book selected
            book_filter = [selected_book_group]

        # Save search parameters for potential re-filtering
        self.last_search_term = search_term
        self.last_search_params = {
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'unique_verses': self.unique_verse_cb.isChecked(),
            'abbreviate_results': self.abbreviate_results_cb.isChecked(),
            'translations': self.selected_translations,
            'book_filter': book_filter
        }

        # Build search message
        search_msg = f"Searching for: {search_term}"
        if selected_book_group != "All Books":
            search_msg += f" in {selected_book_group}"
        if self.filtered_words is not None:
            search_msg += f" (filtered by {len(self.filtered_words)} word(s))"
        self.set_message(search_msg + "...")

        self.debug_print(f"📚 Book filter: {selected_book_group} ({len(book_filter)} books)")
        if self.filtered_words is not None:
            self.debug_print(f"🔍 Word filter: {len(self.filtered_words)} word(s) selected: {self.filtered_words}")
        else:
            self.debug_print(f"🔍 Word filter: None (no filter active)")

        # Detect if this is a verse reference search
        # For verse references like "John 1:1", automatically disable unique verses
        # so user sees all translations
        search_type = self.search_controller.bible_search.detect_search_type(search_term)
        is_verse_reference = (search_type == "verse_reference")

        # Use unique_verses setting from checkbox, but override to False for verse references
        unique_verses_setting = self.unique_verse_cb.isChecked() and not is_verse_reference

        if is_verse_reference and self.unique_verse_cb.isChecked():
            self.debug_print(f"📖 Verse reference detected - automatically disabling 'Unique Verse' for this search")

        self.debug_print(f"🚀 Calling search_controller.search()...")

        # Delegate to search controller
        try:
            self.search_controller.search(
                search_term=search_term,
                case_sensitive=self.case_sensitive_cb.isChecked(),
                unique_verses=unique_verses_setting,
                abbreviate_results=self.abbreviate_results_cb.isChecked(),
                translations=self.selected_translations,
                book_filter=book_filter
            )
            self.debug_print(f"✅ search_controller.search() called successfully")
        except Exception as e:
            self.debug_print(f"❌ ERROR in search_controller.search(): {e}")
            import traceback
            traceback.print_exc()
            self.set_message(f"Search error: {e}")

        # Keep filtered_words active until user clicks Filter again or clears it
        # (filter persists across multiple searches)
        self.debug_print(f"{'='*60}\n")


    def load_context_verses(self, center_verse_id):
        """Load context verses around a selected verse - delegates to SearchController"""
        # Get the verse widget from search results to extract its info
        if center_verse_id not in self.verse_lists['search'].verse_items:
            self.debug_print(f"Verse {center_verse_id} not found in search results")
            return

        # Clear previous highlights in Window 2 (search)
        from PyQt6.QtGui import QColor, QBrush
        for verse_id, verse_item in self.verse_lists['search'].verse_items.items():
            list_item, verse_widget = verse_item
            verse_widget.set_highlighted(False)
            # Clear the QListWidgetItem background
            list_item.setBackground(QBrush(QColor(255, 255, 255)))  # White

        # Get the clicked verse information
        # verse_items now returns (QListWidgetItem, VerseItemWidget) tuple
        item, clicked_verse = self.verse_lists['search'].verse_items[center_verse_id]

        # Highlight the clicked verse in Window 2 (blue tint)
        clicked_verse.set_highlighted(True)
        # Set blue background on the QListWidgetItem
        item.setBackground(QBrush(QColor(214, 233, 255)))  # #D6E9FF blue tint
        self.debug_print(f"🔵 Highlighted clicked verse in Window 2: {center_verse_id}")

        translation = clicked_verse.translation
        book = clicked_verse.book_abbrev
        chapter = clicked_verse.chapter
        start_verse = clicked_verse.verse_number

        self.debug_print(f"Loading context for {translation} {book} {chapter}:{start_verse}")

        # Delegate to search controller
        self.search_controller.load_context(
            translation=translation,
            book=book,
            chapter=chapter,
            start_verse=start_verse,
            num_verses=50
        )

    def extract_highlight_terms(self, search_query):
        """
        Extract terms to highlight from search query.
        Preserves quoted phrases as single terms, removes operators and wildcards.

        Args:
            search_query (str): The original search query

        Returns:
            list: List of terms/phrases to highlight
        """
        import re

        if not search_query:
            return []

        # Normalize apostrophes: Convert standard apostrophe (U+0027) to right single quotation mark (U+2019)
        # The database uses U+2019 for apostrophes
        search_query = search_query.replace("'", "\u2019")

        highlight_terms = []

        # Extract quoted phrases first (keep them as complete phrases)
        quoted_pattern = r'"([^"]+)"|\'([^\']+)\''
        quoted_matches = re.finditer(quoted_pattern, search_query)

        for match in quoted_matches:
            # Get the quoted phrase (from either single or double quotes)
            phrase = match.group(1) or match.group(2)
            if phrase and phrase.strip():
                # Keep quotes around the phrase to indicate exact matching
                # This tells the UI to use word boundaries, not partial matching
                # "sent" will be treated differently from sent (without quotes)
                highlight_terms.append(f'"{phrase.strip()}"')

        # Remove quoted phrases from query to process remaining terms
        query_without_quotes = re.sub(quoted_pattern, '', search_query)

        # Split on AND/OR operators (as whole words)
        terms = re.split(r'\b(?:AND|OR)\b', query_without_quotes, flags=re.IGNORECASE)

        # Process remaining individual words (non-quoted terms)
        for term in terms:
            term = term.strip()
            if not term:
                continue
            # Keep wildcards for proper highlighting
            # *sing? should highlight matching patterns
            # Remove special operators like ~, >, & (but keep wildcards *, %, ?)
            term = re.sub(r'[~>&]', '', term)
            # Split multi-word terms
            words = term.split()
            for word in words:
                word = word.strip()
                if word and len(word) > 1:  # Only highlight words longer than 1 char
                    highlight_terms.append(word)

        return highlight_terms

    def on_search_results_ready(self, verses, metadata):
        """Handle initial search results from SearchController"""
        self.debug_print(f"\n{'='*60}")
        self.debug_print(f"📥 ON_SEARCH_RESULTS_READY CALLED")
        self.debug_print(f"{'='*60}")
        self.debug_print(f"Received {len(verses)} initial search results")
        self.debug_print(f"Total results in controller: {len(self.search_controller.all_search_results)}")

        # Track whether a filter was actually applied in this search
        # This is different from just checking filtered_words, because filtered_words
        # gets cleared after use, but we need to know if it WAS used for the message
        self.filter_was_applied = False

        # Get ALL results from controller and format them
        all_raw_results = self.search_controller.all_search_results

        # Only add to search history if there are results
        # This prevents failed/empty searches from cluttering the history
        search_term = self.current_search_query
        if search_term and len(all_raw_results) > 0:
            # Remove from search_history if it already exists (to avoid duplicates)
            if search_term in self.search_history:
                self.search_history.remove(search_term)

            # Add to the beginning of search_history list
            self.search_history.insert(0, search_term)

            # Limit search history to 50 items maximum
            if len(self.search_history) > 50:
                self.search_history = self.search_history[:50]

            # Update the combo box to match search_history
            self.search_input.clear()
            self.search_input.addItems(self.search_history)
            self.search_input.setCurrentIndex(0)

            # Save config with updated search history
            try:
                self.debug_print(f"💾 Saving search to history (found {len(all_raw_results)} results)...")
                self.save_config()
                self.debug_print(f"✅ Search history saved")
            except Exception as e:
                self.debug_print(f"⚠️  Error saving config: {e}")
                # Don't let config save errors block the search display
        else:
            if search_term and len(all_raw_results) == 0:
                self.debug_print(f"⚠️  Not saving '{search_term}' to history (no results found)")

        self.debug_print(f"📝 Formatting ALL {len(all_raw_results)} results...")
        all_formatted_verses = []
        for i, result in enumerate(all_raw_results):
            verse_id = f"search_{i}"
            # Format the result (using same logic as search_controller)
            formatted = self.search_controller._format_search_result(result, verse_id)
            if formatted:
                all_formatted_verses.append(formatted)

        self.debug_print(f"✅ Formatted {len(all_formatted_verses)} verses")

        # If filter is active, apply it to ALL results
        if self.filtered_words is not None:
            self.filter_was_applied = True  # Mark that filter is being applied
            self.debug_print(f"🔍 Filter active! Applying to {len(all_formatted_verses)} results...")
            self.debug_print(f"🔍 Word filter: {self.filtered_words}")

            # Apply filter to ALL formatted verses
            original_count = len(all_formatted_verses)
            try:
                verses = self.apply_word_filter(all_formatted_verses)
                self.debug_print(f"After word filtering: {len(verses)} results (from {original_count} total)")
            except Exception as e:
                self.debug_print(f"❌ ERROR in apply_word_filter: {e}")
                import traceback
                traceback.print_exc()
                self.set_message(f"Filter error: {e}")
                return

            # Update message if filter produced no results
            if len(verses) == 0 and original_count > 0:
                self.set_message(f"Filter active: 0 results from {original_count} verses. No verses contain the selected {len(self.filtered_words)} word(s).")
        else:
            # No filter - use all formatted verses
            verses = all_formatted_verses
            self.debug_print(f"🔍 No word filter active - loading ALL {len(verses)} results")

        # Clear previous results
        self.verse_lists['search'].clear_verses()

        # Smart loading: For large result sets, load in batches to prevent freezing
        # Initial load: 300 verses (fast and responsive)
        # User can scroll to load more, or refine search for better results
        max_initial_load = 300
        verses_to_load = verses[:max_initial_load]
        remaining_verses = verses[max_initial_load:] if len(verses) > max_initial_load else []

        # Extract terms to highlight from the search query
        highlight_terms = self.extract_highlight_terms(self.current_search_query)

        # Add initial batch to search window with highlighting
        for verse in verses_to_load:
            self.verse_lists['search'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text,
                highlight_terms=highlight_terms
            )

        # Store remaining verses for lazy loading
        self.remaining_search_results = remaining_verses
        self.all_formatted_verses = verses  # Store all for reference

        # Force Qt to process events to ensure widgets are fully rendered
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

        # Apply saved font settings to newly loaded search results
        self.apply_font_settings()
        self.debug_print(f"✓ Applied font settings to search results (verse_font_size={self.verse_font_size}, size={self.verse_font_sizes[self.verse_font_size]}pt)")

        # QListWidget handles rendering automatically, no refresh needed
        self.debug_print(f"🔄 Loaded {len(verses_to_load)} verses into search window")
        if remaining_verses:
            self.debug_print(f"⏳ {len(remaining_verses)} more results available (scroll to load more)")

        # Note: Message will be set by on_search_status() which is called after this method
        # We don't set it here because it would be immediately overwritten

        # Don't use scroll-based loading - it slows down scrolling
        # Instead, show a "Load More" prompt in the message
        if remaining_verses:
            self.debug_print(f"⏳ {len(remaining_verses)} more results available - use message bar to load more")
        else:
            self.debug_print("✅ All results loaded - scroll bar enabled")

        # Automatically activate Window 2 (Search Results) after search completes
        # This allows user to immediately use Ctrl+A or Copy without clicking
        if len(verses) > 0:
            self.set_active_window('search')
            self.debug_print("🎯 Auto-activated Window 2 (Search Results)")

        # Extract word counts to update filter button with available variations count
        if len(verses) > 0:
            word_counts = self.extract_word_counts()
            self.available_word_variations = len(word_counts)
            self.debug_print(f"📊 Updated available word variations: {self.available_word_variations}")

        # Clear filter after one use - turn off green button
        # User can click Filter again if they want to reapply or change filter
        if self.filtered_words is not None:
            self.debug_print(f"🔄 Clearing filter after use (was: {self.filtered_words})")
            self.filtered_words = None
        self.update_filter_button_state()

    def on_scroll_load_more(self, value):
        """Load more results when user scrolls near the bottom"""
        # Only load if there are remaining results
        if not hasattr(self, 'remaining_search_results') or not self.remaining_search_results:
            return

        # Check if scrolled near bottom (within 10% of max)
        scroll_bar = self.verse_lists['search'].list_widget.verticalScrollBar()
        if value < scroll_bar.maximum() * 0.9:
            return  # Not near bottom yet

        # Load next batch (200 at a time when scrolling)
        batch_size = 200
        next_batch = self.remaining_search_results[:batch_size]
        self.remaining_search_results = self.remaining_search_results[batch_size:]

        self.debug_print(f"📥 Loading {len(next_batch)} more results on scroll...")

        # Add to window
        for verse in next_batch:
            self.verse_lists['search'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text
            )

        # Apply font settings
        self.apply_font_settings()

        # Update message
        self.on_search_status("More results loaded")

        # If no more remaining, disconnect scroll handler
        if not self.remaining_search_results:
            self.debug_print("✅ All results now loaded")
            scroll_bar.valueChanged.disconnect(self.on_scroll_load_more)

    def load_more_results_batch(self):
        """Load the next 300 results when Load More button is clicked"""
        if not hasattr(self, 'remaining_search_results') or not self.remaining_search_results:
            self.debug_print("⚠️  No more results to load")
            self.load_more_btn.setVisible(False)
            return

        self.debug_print(f"📥 Loading next batch of results...")

        # Load next 300 (or whatever's left)
        batch_size = 300
        next_batch = self.remaining_search_results[:batch_size]
        self.remaining_search_results = self.remaining_search_results[batch_size:]

        # Get current displayed count
        current_displayed = len(self.verse_lists['search'].verse_items)

        # Extract terms to highlight (same as initial load)
        highlight_terms = self.extract_highlight_terms(self.current_search_query)

        # Add to search window with highlighting
        for verse in next_batch:
            self.verse_lists['search'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text,
                highlight_terms=highlight_terms
            )

        # Apply font settings
        self.apply_font_settings()

        # Update displayed count
        new_displayed = len(self.verse_lists['search'].verse_items)
        total_results = len(self.all_formatted_verses) if hasattr(self, 'all_formatted_verses') else new_displayed

        # Update message
        if self.remaining_search_results:
            # More results still available
            remaining = len(self.remaining_search_results)
            self.set_message(f"Displaying {new_displayed} of {total_results} results | {remaining} more available")
            self.load_more_btn.setVisible(True)
            self.debug_print(f"✅ Loaded {len(next_batch)} more results. {remaining} remaining.")
        else:
            # All results now loaded
            self.set_message(f"All {total_results} results loaded")
            self.load_more_btn.setVisible(False)
            self.debug_print(f"✅ All {total_results} results now loaded")

    def load_next_results(self):
        """Load the next batch of search results when Next button is clicked"""
        self.debug_print("🔵 Next button clicked - loading more results")

        # Get current displayed count
        current_count = len(self.verse_lists['search'].verse_items)
        total_count = len(self.search_controller.all_search_results)

        # Calculate how many more to load (100 at a time)
        batch_size = 100
        remaining = total_count - current_count
        to_load = min(batch_size, remaining)

        if to_load <= 0:
            self.debug_print("⚠️  No more results to load")
            self.next_results_btn.setVisible(False)
            return

        # Get next batch
        next_batch = self.search_controller.all_search_results[current_count:current_count + to_load]

        self.debug_print(f"📥 Loading results {current_count + 1} to {current_count + to_load} of {total_count}")

        # Format and add to search window
        for i, result in enumerate(next_batch):
            verse_id = f"search_{current_count + i}"
            formatted = self.search_controller._format_search_result(result, verse_id)
            if formatted:
                self.verse_lists['search'].add_verse(
                    formatted.verse_id,
                    formatted.translation,
                    formatted.book_abbrev,
                    formatted.chapter,
                    formatted.verse,
                    formatted.text
                )

        # Apply saved font settings to newly added verses
        self.apply_font_settings()

        # Update message with new displayed count
        self.on_search_status("Results loaded")

        self.debug_print(f"✅ Loaded {to_load} more results. Now displaying {current_count + to_load} of {total_count}")

    def on_search_more_results_ready(self, verses, metadata):
        """Handle additional search results from lazy loading"""
        self.debug_print(f"Received {len(verses)} more search results")

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

        # Apply saved font settings to newly added verses
        self.apply_font_settings()

        # Update message with new displayed count
        self.on_search_status("More results loaded")

    def on_search_failed(self, error_message):
        """Handle search failure"""
        self.set_message(f"Search error: {error_message}")
        self.debug_print(f"Search error details: {error_message}")

    def on_search_status(self, message):
        """Handle search status updates - build comprehensive message format"""
        import time

        # Get counts from search_controller
        # IMPORTANT: all_search_results might be deduplicated if Unique Verse checkbox is checked
        # So we need to get the ORIGINAL total_count from metadata
        if not self.search_controller.all_search_results:
            self.set_message(message)
            return

        # Calculate search time
        search_time = 0.0
        if hasattr(self, 'search_start_time'):
            search_time = time.time() - self.search_start_time

        # Get search query
        search_query = getattr(self, 'current_search_query', 'Unknown')

        # Get total_count from metadata (before unique filtering)
        # This is the TRUE total - even if Unique Verse checkbox reduced the results
        first_result = self.search_controller.all_search_results[0]
        total_before_unique = len(self.search_controller.all_search_results)
        unique_count = total_before_unique

        if isinstance(first_result, dict):
            # Check if unique verses filtering was enabled
            total_from_metadata = first_result.get('total_count', None)
            unique_from_metadata = first_result.get('unique_count', None)
            unique_enabled = first_result.get('unique_verses_enabled', False)

            self.debug_print(f"🔍 Metadata: total_count={total_from_metadata}, unique_count={unique_from_metadata}, unique_enabled={unique_enabled}")

            # If unique verses was enabled, use the metadata counts
            if unique_enabled and total_from_metadata is not None:
                # Total = original count before deduplication
                total_results = total_from_metadata
                # Unique = deduplicated count
                unique_count = unique_from_metadata if unique_from_metadata else total_before_unique
                self.debug_print(f"✅ Using metadata: total={total_results}, unique={unique_count}")
            else:
                # Unique verses NOT enabled - total and unique are the same
                total_results = total_before_unique
                unique_count = total_before_unique
                self.debug_print(f"✅ No unique filtering: total={total_results}, unique={unique_count}")
        else:
            # No metadata, use length of results
            total_results = total_before_unique
            unique_count = total_before_unique

        # Get filtered count from displayed verses
        displayed_count = len(self.verse_lists['search'].verse_items) if 'search' in self.verse_lists else 0

        self.debug_print(f"📊 Status message: total={total_results}, unique={unique_count}, displayed={displayed_count}")

        # Build comprehensive message
        # Format: Search: "query" | Total: 5809 | Displayed: 300 | Time: 2.45s (scroll for more)
        filter_was_used = hasattr(self, 'filter_was_applied') and self.filter_was_applied

        # Start with search query
        custom_message = f'Search: "{search_query}" | Total: {total_results}'

        # Only show Unique count if it's different from Total (i.e., unique filtering was applied)
        if unique_count != total_results:
            custom_message += f' | Unique: {unique_count}'

        # Show displayed count if not all results are loaded
        if displayed_count < total_results:
            if filter_was_used:
                custom_message += f' | Filtered: {displayed_count}'
            else:
                custom_message += f' | Displayed: {displayed_count}'

        # Add search time
        custom_message += f' | Time: {search_time:.2f}s'

        # Show/hide Load More button based on whether there are remaining results
        if hasattr(self, 'remaining_search_results') and self.remaining_search_results:
            remaining = len(self.remaining_search_results)
            custom_message += f' | {remaining} more available'
            self.load_more_btn.setVisible(True)
        else:
            self.load_more_btn.setVisible(False)

        self.debug_print(f"📝 Custom message: {custom_message}")
        self.set_message(custom_message)

    def on_context_verses_ready(self, verses):
        """Handle context verses for reading window"""
        self.debug_print(f"Received {len(verses)} context verses for reading window")

        # Save current Window 3 state to history BEFORE clearing
        # (This must happen before clearing so we save the OLD verses, not the new ones)
        if verses:
            first_verse = verses[0]
            new_verse_reference = f"{first_verse.book_abbrev} {first_verse.chapter}:{first_verse.verse}"
            self.save_window3_to_history_before_update(new_verse_reference)

        # Clear reading window
        self.verse_lists['reading'].clear_verses()

        # Update translation label in Reading Window header
        if verses and hasattr(self, 'reading_section') and hasattr(self.reading_section, 'translation_label') and self.reading_section.translation_label:
            # Get translation abbreviation from first verse
            translation_abbrev = verses[0].translation
            # Look up full name from translations list
            translation_name = translation_abbrev  # Default to abbreviation
            for trans in self.search_controller.bible_search.translations:
                if trans.abbreviation == translation_abbrev:
                    translation_name = trans.full_name
                    break
            self.reading_section.translation_label.setText(translation_name)
            self.debug_print(f"✓ Updated Reading Window translation label: {translation_name}")

        # Add verses to reading window and immediately apply font to each
        from PyQt6.QtGui import QFont
        verse_size = self.verse_font_sizes[self.verse_font_size]

        for verse in verses:
            self.verse_lists['reading'].add_verse(
                verse.verse_id,
                verse.translation,
                verse.book_abbrev,
                verse.chapter,
                verse.verse,
                verse.text
            )

            # Immediately apply font to this verse
            verse_id = verse.verse_id
            if verse_id in self.verse_lists['reading'].verse_items:
                _, verse_widget = self.verse_lists['reading'].verse_items[verse_id]
                verse_font = QFont("IBM Plex Mono")
                verse_font.setBold(False)
                verse_font.setPointSizeF(verse_size)
                verse_widget.text_label.setFont(verse_font)

        self.debug_print(f"✓ Applied {verse_size}pt font to {len(verses)} context verses individually")

        # Update size hints after font changes to prevent text cutoff
        self.verse_lists['reading'].update_item_sizes()
        self.debug_print(f"✓ Updated size hints for all verses in reading window")

        # Highlight the first verse (the one that was clicked)
        if verses:
            # Clear any previous highlights in Window 3 first
            from PyQt6.QtGui import QColor, QBrush
            for verse_id, verse_item in self.verse_lists['reading'].verse_items.items():
                list_item, verse_widget = verse_item
                verse_widget.set_highlighted(False)
                list_item.setBackground(QBrush(QColor(255, 255, 255)))  # White

            first_verse_id = verses[0].verse_id
            if first_verse_id in self.verse_lists['reading'].verse_items:
                # verse_items now returns (QListWidgetItem, VerseItemWidget) tuple
                item, verse_widget = self.verse_lists['reading'].verse_items[first_verse_id]
                verse_widget.set_highlighted(True)
                # Set blue background on the QListWidgetItem
                item.setBackground(QBrush(QColor(214, 233, 255)))  # #D6E9FF blue tint
                # Scroll to make the highlighted verse visible at the top
                self.verse_lists['reading'].scroll_to_verse(first_verse_id)

            # Load cross-references for the clicked verse
            first_verse = verses[0]
            verse_reference = f"{first_verse.book_abbrev} {first_verse.chapter}:{first_verse.verse}"
            self.update_cross_references_dropdown(verse_reference)
            self.debug_print(f"🔗 Loading cross-references for {verse_reference}")

            # NOTE: We used to auto-activate Window 3 here, but that prevented
            # Window 2 from staying active when clicking verses in it.
            # Users can click Window 3 if they want to work there.
            # self.set_active_window('reading')
            # self.debug_print("🎯 Auto-activated Window 3 (Reading Window)")

    def on_tips_clicked(self):
        """Show context-sensitive tips based on active window"""
        from PyQt6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QPushButton, QLabel
        from PyQt6.QtCore import Qt

        # Determine which window is active
        active_window = None
        for window_id, verse_list in self.verse_lists.items():
            if hasattr(verse_list, 'is_active') and verse_list.is_active:
                active_window = window_id
                self.debug_print(f"✓ Active window detected: {window_id}")
                break

        self.debug_print(f"Active window result: {active_window}")

        # If we can detect active window, show specific help
        if active_window == 'search':
            self.show_search_window_tips()
        elif active_window == 'reading':
            self.show_reading_window_tips()
        elif active_window == 'subject':
            self.show_subject_window_tips()
        else:
            # Show menu to choose which help to view
            self.show_help_menu()

    def show_help_menu(self):
        """Show a menu to select which help screen to view"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Bible Search Help")
        dialog.setMinimumSize(400, 300)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Select Help Topic")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Instruction
        instruction = QLabel("Choose which window's help you'd like to view:")
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setWordWrap(True)
        layout.addWidget(instruction)

        layout.addSpacing(20)

        # Button for Window 2 (Search)
        search_btn = QPushButton("Window 2: Search Results Help")
        search_btn.setMinimumHeight(50)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        search_btn.clicked.connect(lambda: (dialog.accept(), self.show_search_window_tips()))
        layout.addWidget(search_btn)

        # Button for Window 3 (Reading)
        reading_btn = QPushButton("Window 3: Reading Window Help")
        reading_btn.setMinimumHeight(50)
        reading_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        reading_btn.clicked.connect(lambda: (dialog.accept(), self.show_reading_window_tips()))
        layout.addWidget(reading_btn)

        # Button for Window 4 (Subject)
        subject_btn = QPushButton("Window 4: Subject Window Help")
        subject_btn.setMinimumHeight(50)
        subject_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        subject_btn.clicked.connect(lambda: (dialog.accept(), self.show_subject_window_tips()))
        layout.addWidget(subject_btn)

        # Button for Export Feature
        export_btn = QPushButton("Export Feature Help")
        export_btn.setMinimumHeight(50)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        export_btn.clicked.connect(lambda: (dialog.accept(), self.show_export_help()))
        layout.addWidget(export_btn)

        # Button for Comprehensive Documentation
        docs_btn = QPushButton("📚 Comprehensive Documentation")
        docs_btn.setMinimumHeight(50)
        docs_btn.setStyleSheet("""
            QPushButton {
                background-color: #00897B;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #00695C;
            }
        """)
        docs_btn.clicked.connect(lambda: (dialog.accept(), self.show_comprehensive_docs()))
        layout.addWidget(docs_btn)

        # Button for License Information
        license_btn = QPushButton("📜 License Information")
        license_btn.setMinimumHeight(50)
        license_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        license_btn.clicked.connect(lambda: (dialog.accept(), self.show_license_info()))
        layout.addWidget(license_btn)

        # Button for Message Log
        log_btn = QPushButton("📋 View Message Log")
        log_btn.setMinimumHeight(50)
        log_btn.setStyleSheet("""
            QPushButton {
                background-color: #3F51B5;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #303F9F;
            }
        """)
        log_btn.clicked.connect(lambda: (dialog.accept(), self.show_message_log()))
        layout.addWidget(log_btn)

        # Button for Debug Log
        debug_btn = QPushButton("🔧 View Debug Log")
        debug_btn.setMinimumHeight(50)
        debug_btn.setStyleSheet("""
            QPushButton {
                background-color: #795548;
                color: white;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5D4037;
            }
        """)
        debug_btn.clicked.connect(lambda: (dialog.accept(), self.show_debug_log()))
        layout.addWidget(debug_btn)

        layout.addSpacing(20)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        layout.addWidget(cancel_btn)

        dialog.exec()

    def show_search_window_tips(self):
        """Show comprehensive search help with tabbed dialog"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                                     QTextEdit, QLabel, QPushButton, QWidget)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Bible Search Help")
        dialog.setMinimumSize(750, 650)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Bible Search Help & Reference")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Create tabbed interface
        tabs = QTabWidget()

        # Tab 1: Basic Usage
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        text1 = QTextEdit()
        text1.setReadOnly(True)
        text1.setHtml("""
        <h2>Window 2: Search Results</h2>

        <h3>Purpose</h3>
        <p>Displays Bible verses matching your search query from selected translations.</p>

        <h3>How to Search</h3>
        <ol>
            <li>Enter search terms in the search box</li>
            <li>Select options (translations, filters, etc.)</li>
            <li>Click <b>Search</b> button or press Enter</li>
            <li>Results appear in this window</li>
        </ol>

        <h3>Working with Results</h3>
        <ul>
            <li><b>Click a verse:</b> Loads context in Window 3 (Reading Window)</li>
            <li><b>Check boxes:</b> Select verses for Copy or Acquire</li>
            <li><b>Ctrl+A:</b> Select all verses (Copy-only mode)</li>
            <li><b>Ctrl+D:</b> Deselect all verses</li>
        </ul>

        <h3>Selection Modes</h3>
        <ul>
            <li><b>Manual selection:</b> Check individual boxes → Copy or Acquire available</li>
            <li><b>Ctrl+A selection:</b> Select all → Only Copy available (protects against accidental mass Acquire)</li>
            <li><b>Locked mode:</b> When ANY boxes are checked, you must Copy, Acquire, or Deselect (Ctrl+D) before doing other actions</li>
        </ul>

        <h3>Buttons</h3>
        <ul>
            <li><b>Search:</b> Execute search with current settings</li>
            <li><b>Clear:</b> Remove all search results</li>
            <li><b>Copy:</b> Copy checked verses to clipboard</li>
            <li><b>Translations:</b> Choose which Bible versions to search</li>
            <li><b>Filter:</b> Shows word variations found in search results. Click to select which variations to include.</li>
        </ul>

        <h3>Filter Button Tips</h3>
        <ul>
            <li><b>Word Variations:</b> The Filter button shows the count of unique word variations found (e.g., "sing", "singing", "singer")</li>
            <li><b>With Unique Verse checked:</b> Filter extracts variations from all results but displays only unique verses</li>
            <li><b>💡 Pro Tip:</b> To see ALL word variations from ALL verses (including duplicates across translations), uncheck the "Unique Verse" checkbox before searching. This gives you the complete list of every word variation without deduplication.</li>
        </ul>

        <h3>Window Activation</h3>
        <ul>
            <li>Active window has a <b>blue border</b></li>
            <li>Click anywhere in the window to activate it</li>
            <li>Copy and Acquire work on the active window</li>
        </ul>
        """)
        tab1_layout.addWidget(text1)
        tabs.addTab(tab1, "Basic Usage")

        # Tab 2: Wildcards & Operators
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        text2 = QTextEdit()
        text2.setReadOnly(True)
        text2.setHtml("""
        <h2>Wildcards & Search Operators</h2>

        <h3>Understanding Search Operators</h3>
        <p style="background-color: #e8f5e9; padding: 10px; border-left: 4px solid #4caf50;">
        <b>Two Types of Search Control:</b><br>
        • <b>Word Structure Operators (* and ?)</b> - Control what the word itself looks like (requires quotes)<br>
        • <b>Word Relationship Operators (>, ~, &)</b> - Control how words relate to each other in order and distance (no quotes needed)
        </p>

        <h3>Word Structure Operators (Wildcards)</h3>
        <p style="color: #d32f2f;"><b>⚠️ IMPORTANT: Wildcards REQUIRE quotation marks to work!</b></p>

        <h4>Asterisk (*) - Multiple Characters</h4>
        <p>Matches any number of characters (including zero). Modifies the structure of a word. <b>Automatically includes possessive forms (with apostrophes).</b></p>
        <ul>
            <li><b>"love*"</b> → love, loved, loves, loving, lovingkindness, love's</li>
            <li><b>"father*"</b> → father, fathers, father's, fathers'</li>
            <li><b>"*tion"</b> → salvation, nation, redemption</li>
            <li><b>"righ*ness"</b> → righteousness, richness</li>
        </ul>
        <p style="color: #d32f2f;"><b>✗ Wrong:</b> love* (treats asterisk as literal character - finds nothing)<br>
        <span style="color: #388e3c;"><b>✓ Correct:</b> "love*" (wildcard works - finds variations including possessives)</span></p>

        <h4>Question Mark (?) - Single Character</h4>
        <p>Matches exactly one character. Modifies the structure of a word.</p>
        <ul>
            <li><b>"l?ve"</b> → love, live (not leave or believe)</li>
            <li><b>"m?n"</b> → man, men, min, mon</li>
            <li><b>"s?ng"</b> → sing, sang, sung, song</li>
        </ul>
        <p style="color: #d32f2f;"><b>✗ Wrong:</b> bles? (treats ? as literal character - finds nothing)<br>
        <span style="color: #388e3c;"><b>✓ Correct:</b> "bles?" (wildcard works - finds bless, blest)</span></p>

        <h4>Understanding Quote Requirements</h4>
        <p><b>Unquoted terms</b> = simple and forgiving (partial matching):</p>
        <ul>
            <li><b>sing</b> → finds words <i>containing</i> "sing" (singing, singers, blessing)</li>
        </ul>
        <p><b>Quoted terms</b> = precision and control (exact matching + wildcards):</p>
        <ul>
            <li><b>"sing"</b> → finds only the exact word "sing"</li>
            <li><b>"sing*"</b> → finds words <i>starting with</i> "sing" (sing, singing, singers)</li>
        </ul>

        <h4>Wildcards with Relationship Operators</h4>
        <p>You can use quoted wildcards with relationship operators:</p>
        <ul>
            <li><b>"bless*" > fertile</b> → blessed/blessing before fertile</li>
            <li><b>"love*" ~4 God</b> → love/loved/loving within 4 words of God</li>
            <li><b>who & "sen*"</b> → who [word] sent/send/sending</li>
        </ul>

        <h3>Word Relationship Operators</h3>
        <p>These operators control how words relate to each other in order, distance, and placement. <b>No quotes needed</b> - they work directly on words.</p>

        <h4>Ampersand (&) - Word Placeholder</h4>
        <p>Matches any single word. Controls word relationships by specifying gaps between terms.</p>
        <ul>
            <li><b>who & sent</b> → "who had sent", "who hath sent", "who will send"</li>
            <li><b>I & you</b> → "I tell you", "I command you", "I say you"</li>
            <li><b>who & & sent</b> → "who will then send" (two words between)</li>
            <li><b>love & & God</b> → "love dwelleth in God", "love is of God"</li>
        </ul>
        <p><i>Tip: Combine with quoted wildcards: <b>who & "sen*"</b> → "who had sent", "who will send"</i></p>

        <h4>Greater Than (>) - Ordered Words</h4>
        <p>Controls word order - ensures words appear in the specified sequence (but not necessarily consecutive).</p>
        <ul>
            <li><b>love > neighbour</b> → "love thy neighbour" (love before neighbour)</li>
            <li><b>faith > works</b> → verses where "faith" comes before "works"</li>
            <li><b>God > love > man</b> → three words in sequence</li>
            <li><b>"bless*" > fertile</b> → blessed/blessing before fertile (with quoted wildcard)</li>
        </ul>
        <p><i>Note: Order matters! "love > God" gives different results than "God > love"</i></p>

        <h4>Tilde (~N) - Proximity Operator</h4>
        <p>Controls word distance - finds words within N words or less of each other.</p>
        <ul>
            <li><b>love ~0 God</b> → "love God" (adjacent words only)</li>
            <li><b>love ~2 God</b> → "love of God", "love the God" (0-2 words between)</li>
            <li><b>love ~4 God</b> → "love the Lord thy God" (0-4 words between)</li>
            <li><b>faith ~5 works</b> → "faith" and "works" within 5 words</li>
            <li><b>"believ*" ~3 Jesus</b> → any "believe" form within 3 words of "Jesus" (with quoted wildcard)</li>
        </ul>
        <p><i>Tip: Smaller numbers give more precise matches. ~0 means adjacent, ~10 allows wide spacing.</i></p>

        <h3>Boolean Operators</h3>

        <h4>AND</h4>
        <p>Both terms must appear in the verse (in any order).</p>
        <ul>
            <li><b>faith AND works</b> → verses containing both words</li>
            <li><b>prayer AND fasting</b> → both terms present</li>
        </ul>
        <p><i>Note: Use CAPITAL letters for AND/OR operators</i></p>

        <h4>OR</h4>
        <p>Either term (or both) must appear.</p>
        <ul>
            <li><b>peace OR joy</b> → verses with either or both</li>
            <li><b>angel OR messenger</b> → either term</li>
        </ul>

        <h4>Parentheses ( ) - Control Operator Precedence</h4>
        <p>Use parentheses to control the order of operations when mixing AND and OR.</p>
        <p style="background-color: #fff3e0; padding: 10px; border-left: 4px solid #ff9800;">
        <b>Why you need them:</b><br>
        • Without parentheses: <b>"sleep*" OR "slep*" AND father</b><br>
        &nbsp;&nbsp;→ Evaluated as: "sleep*" OR ("slep*" AND father) due to AND having higher precedence<br>
        &nbsp;&nbsp;→ Returns: verses with sleep*, OR verses with BOTH slep* and father<br><br>
        • With parentheses: <b>("sleep*" OR "slep*") AND father</b><br>
        &nbsp;&nbsp;→ Evaluated as: ("sleep*" OR "slep*") AND father<br>
        &nbsp;&nbsp;→ Returns: verses with father AND (sleep* OR slep*)
        </p>
        <p><b>Examples:</b></p>
        <ul>
            <li><b>("faith" OR "belief") AND works</b> → verses with works AND either faith or belief</li>
            <li><b>("Holy Spirit" OR "Spirit of God") AND power</b> → verses with power AND either phrase</li>
            <li><b>("love*" OR "charity") AND neighbor</b> → verses with neighbor AND any love form or charity</li>
        </ul>
        <p><i>Note: Parentheses only work with AND/OR operators, not with special operators like >, ~, or &</i></p>

        <h3>Exact Phrases</h3>
        <p>Use quotation marks for exact word order or to enable wildcards.</p>
        <ul>
            <li><b>"in the beginning"</b> → exact phrase only</li>
            <li><b>"love the Lord"</b> → exact phrase in this order</li>
            <li><b>"I am"</b> → exact two-word phrase</li>
        </ul>

        <h3>Combining Operators</h3>
        <p>Mix different operators for powerful searches:</p>
        <ul>
            <li><b>"faith without" AND works</b> → exact phrase plus word</li>
            <li><b>"love*" AND neighbor</b> → any form of "love" with "neighbor" (quoted wildcard)</li>
            <li><b>"Holy Spirit" OR "Spirit of God"</b> → either phrase</li>
            <li><b>("love*" OR "charity") AND neighbor</b> → verses with neighbor AND either love or charity (parentheses)</li>
            <li><b>"believ*" > Jesus</b> → any "believe" form before "Jesus" (quoted wildcard with operator)</li>
            <li><b>I & "lov*" > God</b> → "I [word] love/loved God" (quoted wildcard)</li>
            <li><b>"believ*" ~3 Jesus</b> → any "believe" form within 3 words of "Jesus" (quoted wildcard)</li>
            <li><b>"pray*" ~5 faith</b> → any "pray" form within 5 words of "faith" (quoted wildcard)</li>
            <li><b>("faith" OR "belief") AND ("works" OR "deeds")</b> → complex AND/OR combinations (parentheses)</li>
        </ul>

        <h3>Important Limitations</h3>
        <p style="background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107;">
        <b>⚠️ Cannot Mix > and ~ Operators:</b><br>
        You cannot combine ordered (>) and proximity (~) operators in the same query.<br>
        ✓ <b>"bless*" > fertile > increase</b> (multiple ordered words)<br>
        ✓ <b>fertile ~4 increase</b> (proximity search)<br>
        ✗ <b>"bless*" > fertile ~4 increase</b> (mixing operators - NOT supported)
        </p>

        <h3>Quick Reference</h3>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse;">
            <tr style="background-color: #e0e0e0;">
                <th>Operator</th>
                <th>Type</th>
                <th>Example</th>
                <th>Quotes?</th>
            </tr>
            <tr>
                <td><b>*</b></td>
                <td>Word structure - multiple chars</td>
                <td>"love*" → loved, loving</td>
                <td style="color: #d32f2f;"><b>Required</b></td>
            </tr>
            <tr>
                <td><b>?</b></td>
                <td>Word structure - single char</td>
                <td>"m?n" → man, men</td>
                <td style="color: #d32f2f;"><b>Required</b></td>
            </tr>
            <tr>
                <td><b>&</b></td>
                <td>Word relationship - placeholder</td>
                <td>who & sent → "who had sent"</td>
                <td style="color: #388e3c;">No</td>
            </tr>
            <tr>
                <td><b>></b></td>
                <td>Word relationship - order</td>
                <td>love > God → love before God</td>
                <td style="color: #388e3c;">No</td>
            </tr>
            <tr>
                <td><b>~N</b></td>
                <td>Word relationship - distance</td>
                <td>love ~4 God → within 4 words</td>
                <td style="color: #388e3c;">No</td>
            </tr>
            <tr>
                <td><b>AND</b></td>
                <td>Both terms required</td>
                <td>faith AND works</td>
            </tr>
            <tr>
                <td><b>OR</b></td>
                <td>Either term (or both)</td>
                <td>peace OR joy</td>
            </tr>
            <tr>
                <td><b>" "</b></td>
                <td>Exact phrase</td>
                <td>"in the beginning"</td>
            </tr>
        </table>
        """)
        tab2_layout.addWidget(text2)
        tabs.addTab(tab2, "Wildcards")

        # Tab 3: Search Examples
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        text3 = QTextEdit()
        text3.setReadOnly(True)
        text3.setHtml("""
        <h2>Search Examples</h2>

        <h3>Basic Searches</h3>
        <ul>
            <li><b>love</b> → all verses containing "love"</li>
            <li><b>salvation</b> → all verses with "salvation"</li>
            <li><b>faith hope</b> → both words near each other</li>
        </ul>

        <h3>Wildcard Examples</h3>
        <ul>
            <li><b>bless*</b> → blessed, blessing, blessings, blessedness</li>
            <li><b>righ*</b> → right, righteous, righteousness, rightly</li>
            <li><b>*ness</b> → righteousness, holiness, goodness, kindness</li>
            <li><b>believ%</b> → believe, believed, believer, believing (stem/root)</li>
            <li><b>pray%</b> → pray, prayed, prayer, prayers, praying (stem/root)</li>
        </ul>

        <h3>Word Placeholder Examples (&)</h3>
        <ul>
            <li><b>who & sent</b> → "who had sent", "who hath sent", "who will send"</li>
            <li><b>I & you</b> → "I tell you", "I command you", "I pray you"</li>
            <li><b>God & love</b> → "God so loved", "God is love"</li>
            <li><b>who & & sent</b> → "who will then send" (two words between)</li>
            <li><b>love & & God</b> → "love dwelleth in God", "love is of God"</li>
        </ul>

        <h3>Ordered Words Examples (>)</h3>
        <ul>
            <li><b>love > neighbour</b> → "love thy neighbour" (love before neighbour)</li>
            <li><b>faith > works</b> → faith mentioned before works in verse</li>
            <li><b>God > love > man</b> → all three words in this sequence</li>
            <li><b>lov% > God</b> → "love the Lord thy God" (with wildcard)</li>
            <li><b>I > love > you</b> → "But I say unto you, Love your enemies"</li>
        </ul>

        <h3>Proximity Examples (~N)</h3>
        <ul>
            <li><b>love ~0 God</b> → "love God" (words must be adjacent)</li>
            <li><b>love ~2 God</b> → "love of God", "love the God" (0-2 words between)</li>
            <li><b>love ~4 God</b> → "love the Lord thy God" (0-4 words between)</li>
            <li><b>faith ~5 works</b> → "faith" and "works" within 5 words</li>
            <li><b>believ% ~3 Jesus</b> → any "believe" form within 3 words of "Jesus"</li>
            <li><b>pray% ~5 faith</b> → any "pray" form within 5 words of "faith"</li>
        </ul>

        <h3>Exact Phrase Examples</h3>
        <ul>
            <li><b>"in the beginning"</b> → Genesis 1:1, John 1:1, etc.</li>
            <li><b>"love the Lord"</b> → exact phrase matches</li>
            <li><b>"I am"</b> → the exact two-word phrase</li>
        </ul>

        <h3>Boolean Examples</h3>
        <ul>
            <li><b>faith AND works</b> → James 2:14-26 area</li>
            <li><b>prayer AND fasting</b> → Matthew 17:21, Mark 9:29</li>
            <li><b>peace OR joy</b> → verses with either concept</li>
        </ul>

        <h3>Combined Advanced Examples</h3>
        <ul>
            <li><b>"Holy Spirit" OR "Spirit of God"</b> → either phrase</li>
            <li><b>love* AND neighbor</b> → "love your neighbor" passages</li>
            <li><b>believ% > Jesus</b> → believe forms before Jesus</li>
            <li><b>I & lov% > God</b> → complex pattern with placeholder + wildcard + order</li>
            <li><b>who & sen* > Israel</b> → "who [word] sent/send to Israel"</li>
            <li><b>believ% ~3 Jesus</b> → any "believe" form within 3 words of "Jesus"</li>
            <li><b>pray% ~5 faith</b> → any "pray" form within 5 words of "faith"</li>
        </ul>

        <h3>Advanced Thematic Searches</h3>
        <ul>
            <li><b>prayer AND (answer* OR hear*)</b> → answered prayers</li>
            <li><b>David AND (king OR shepherd)</b> → David's roles</li>
            <li><b>Moses AND (law OR commandment*)</b> → Mosaic law</li>
            <li><b>faith > lov%</b> → faith mentioned before any form of love</li>
        </ul>

        <h3>Using Filters</h3>
        <p>Combine searches with filters for precision:</p>
        <ul>
            <li><b>"I am"</b> + Filter: Gospel of John</li>
            <li><b>wisdom</b> + Filter: Proverbs</li>
            <li><b>covenant</b> + Filter: Old Testament</li>
        </ul>
        """)
        tab3_layout.addWidget(text3)
        tabs.addTab(tab3, "Examples")

        # Tab 4: Tips & Tricks
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        text4 = QTextEdit()
        text4.setReadOnly(True)
        text4.setHtml("""
        <h2>Tips & Tricks</h2>

        <h3>Search Strategy</h3>
        <ol>
            <li><b>Start broad, then narrow:</b> Begin with simple search, then add filters</li>
            <li><b>Use wildcards for concepts:</b> "righ*" finds all righteousness-related words</li>
            <li><b>Check context:</b> Click verses to see surrounding text in Reading Window</li>
        </ol>

        <h3>Efficient Searching</h3>
        <ul>
            <li><b>Search history:</b> Recent searches saved in dropdown for quick re-use</li>
            <li><b>Multiple translations:</b> Search KJV, NIV, ESV simultaneously</li>
            <li><b>Filter by testament:</b> Reduce noise by limiting to OT or NT</li>
            <li><b>Unique verses:</b> Enable to see each reference only once</li>
        </ul>

        <h3>Working with Results</h3>
        <ol>
            <li>Search for main topic → Check relevant verses</li>
            <li>Click a verse → Reading Window shows context</li>
            <li>Check additional context verses if needed</li>
            <li>Acquire all to Subject for organized study</li>
        </ol>

        <h3>Common Patterns</h3>
        <ul>
            <li><b>Commandments:</b> "thou shalt" OR "you shall"</li>
            <li><b>Messianic prophecy:</b> messiah OR christ (OT filter)</li>
            <li><b>Prayer examples:</b> pray* AND (Lord OR God OR Father)</li>
        </ul>

        <h3>Troubleshooting</h3>
        <h4>No Results?</h4>
        <ul>
            <li>Check spelling</li>
            <li>Try wildcards: pray* instead of prayer</li>
            <li>Remove filters and restrictions</li>
            <li>Use OR instead of AND</li>
        </ul>

        <h4>Too Many Results?</h4>
        <ul>
            <li>Add more specific terms with AND</li>
            <li>Use exact phrases instead of single words</li>
            <li>Apply book or testament filters</li>
            <li>Remove wildcards for precision</li>
        </ul>

        <h3>Best Practices</h3>
        <ul>
            <li>Always check context before using verses</li>
            <li>Compare multiple translations</li>
            <li>Organize findings in Subject Verses</li>
            <li>Add comments to document insights</li>
            <li>Export important research</li>
        </ul>
        """)
        tab4_layout.addWidget(text4)
        tabs.addTab(tab4, "Tips & Tricks")

        layout.addWidget(tabs)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        close_button.setMaximumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def show_reading_window_tips(self):
        """Show comprehensive Reading Window help with tabbed dialog"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                                     QTextEdit, QLabel, QPushButton, QWidget)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Reading Window Help")
        dialog.setMinimumSize(750, 650)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Reading Window Help & Reference")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Create tabbed interface
        tabs = QTabWidget()

        # Tab 1: Basic Usage
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        text1 = QTextEdit()
        text1.setReadOnly(True)
        text1.setHtml("""
        <h2 style='color: #4CAF50;'>Window 3: Reading Window</h2>

        <h3>Purpose</h3>
        <p>Provides context verses for in-depth reading and cross-reference exploration. This window helps you understand verses in their surrounding context.</p>

        <h3>How It Works</h3>
        <ol>
            <li>Search for a topic in Window 2 (Search Results)</li>
            <li>Click on any verse that interests you</li>
            <li>Window 3 loads ~50 verses of context around that verse</li>
            <li>The clicked verse is highlighted for easy reference</li>
            <li>Explore cross-references to discover related passages</li>
        </ol>

        <h3>Controls</h3>
        <ul>
            <li><b>Translation Dropdown (Left):</b> Choose which Bible version to display (KJV, NIV, ESV, etc.)</li>
            <li><b>References Dropdown (Right):</b> Navigate to cross-referenced verses</li>
        </ul>

        <h3>Working with Verses</h3>
        <ul>
            <li><b>Read context:</b> Scroll to read surrounding verses</li>
            <li><b>Check boxes:</b> Select verses to save or copy</li>
            <li><b>Click verses:</b> Re-activate the window</li>
            <li><b>Ctrl+A:</b> Select all verses (Copy-only mode)</li>
            <li><b>Ctrl+D:</b> Deselect all verses</li>
        </ul>

        <h3>Selection Modes</h3>
        <ul>
            <li><b>Manual selection:</b> Check individual boxes → Copy or Acquire available</li>
            <li><b>Ctrl+A selection:</b> Select all → Only Copy available</li>
            <li><b>Locked mode:</b> Must Copy, Acquire, or Deselect before other actions</li>
        </ul>

        <h3>Window Features</h3>
        <ul>
            <li><b>Highlighted verse:</b> Yellow background shows the verse you clicked</li>
            <li><b>Active border:</b> Green border when this window is active</li>
            <li><b>17 Translations:</b> All available translations can be displayed</li>
            <li><b>Context length:</b> Shows 50 verses centered on your selection</li>
        </ul>
        """)
        tab1_layout.addWidget(text1)
        tabs.addTab(tab1, "Basic Usage")

        # Tab 2: Cross-References
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        text2 = QTextEdit()
        text2.setReadOnly(True)
        text2.setHtml("""
        <h2 style='color: #4CAF50;'>Cross-References Feature</h2>

        <h3>What Are Cross-References?</h3>
        <p>Cross-references are related Bible verses that share themes, prophecies, parallel accounts, or theological connections. They help you discover how Scripture interprets Scripture.</p>

        <h3>How to Use Cross-References</h3>
        <ol>
            <li>Click a verse in Window 2 to load it in Window 3</li>
            <li>Look at the <b>References dropdown</b> on the right side</li>
            <li><b>Green dropdown</b> = Cross-references available</li>
            <li><b>Gray dropdown</b> = No references for this verse</li>
            <li>Click the dropdown to see the list</li>
            <li>Select any reference to jump to that verse</li>
            <li>The new verse loads with its own cross-references</li>
            <li>Keep exploring to follow chains of related verses!</li>
        </ol>

        <h3>Understanding the Dropdown</h3>
        <ul>
            <li><b>"References (6)"</b> → 6 cross-references found</li>
            <li><b>Green background</b> → References available, ready to use</li>
            <li><b>Light blue highlight</b> → Hovering over a reference</li>
            <li><b>Black text always</b> → Easy to read at all times</li>
        </ul>

        <h3>Cross-Reference Display</h3>
        <p>Each reference shows:</p>
        <ul>
            <li><b>Reference:</b> "Genesis 3:19" (book chapter:verse)</li>
            <li><b>Text preview:</b> First 80 characters of the verse</li>
            <li><b>Relevance score:</b> Higher scores = stronger connections</li>
        </ul>

        <h3>Navigation Flow</h3>
        <ol>
            <li>Start at Genesis 3:23 (Adam expelled from Eden)</li>
            <li>See 6 references available</li>
            <li>Select "Genesis 3:19" (consequence of the Fall)</li>
            <li>Window loads Genesis 3:19 with context</li>
            <li>New cross-references load for Genesis 3:19</li>
            <li>Continue exploring connected passages</li>
        </ol>

        <h3>Benefits of Cross-References</h3>
        <ul>
            <li><b>Discover connections:</b> Find related themes across Scripture</li>
            <li><b>Understand context:</b> See how verses relate to each other</li>
            <li><b>Study themes:</b> Follow topics through the Bible</li>
            <li><b>Parallel passages:</b> Compare Gospel accounts or OT/NT parallels</li>
            <li><b>Prophecy fulfillment:</b> See OT prophecies and NT fulfillments</li>
        </ul>
        """)
        tab2_layout.addWidget(text2)
        tabs.addTab(tab2, "Cross-References")

        # Tab 3: Examples
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        text3 = QTextEdit()
        text3.setReadOnly(True)
        text3.setHtml("""
        <h2>Cross-Reference Examples</h2>

        <h3>Example 1: Genesis 3:23</h3>
        <p><b>Original Verse:</b> "Therefore the LORD God sent him forth from the garden of Eden, to till the ground from whence he was taken."</p>

        <p><b>Cross-References Found (6):</b></p>
        <ul>
            <li><b>Genesis 4:2</b> (score: 5) - "Abel was a keeper of sheep..."
                <br><i>Why related: Both mention tilling/working the ground</i></li>
            <li><b>Genesis 4:12</b> (score: 4) - "When thou tillest the ground..."
                <br><i>Why related: Consequences of sin affecting ground work</i></li>
            <li><b>Genesis 3:19</b> (score: 4) - "In the sweat of thy face shalt thou eat bread..."
                <br><i>Why related: Same chapter, consequences of the Fall</i></li>
            <li><b>Genesis 2:5</b> (score: 3) - "Every plant of the field before it was in the earth..."
                <br><i>Why related: Pre-Fall ground conditions</i></li>
            <li><b>Ecclesiastes 5:9</b> (score: 3) - "The profit of the earth is for all..."
                <br><i>Why related: Theological reflection on working the ground</i></li>
            <li><b>Genesis 9:20</b> (score: 2) - "Noah began to be a husbandman..."
                <br><i>Why related: Working/tilling the ground after judgment</i></li>
        </ul>

        <h3>Example 2: John 3:16</h3>
        <p><b>Original Verse:</b> "For God so loved the world, that he gave his only begotten Son..."</p>

        <p><b>Cross-References Include:</b></p>
        <ul>
            <li><b>Romans 5:8</b> - God's love demonstrated in Christ's death</li>
            <li><b>1 John 4:9-10</b> - God's love manifested by sending His Son</li>
            <li><b>Romans 8:32</b> - God who spared not His own Son</li>
        </ul>

        <h3>Example 3: Psalm 23:1</h3>
        <p><b>Original Verse:</b> "The LORD is my shepherd; I shall not want."</p>

        <p><b>Cross-References Include:</b></p>
        <ul>
            <li><b>John 10:11</b> - "I am the good shepherd"</li>
            <li><b>Ezekiel 34:11-12</b> - God as shepherd of Israel</li>
            <li><b>Isaiah 40:11</b> - "He shall feed his flock like a shepherd"</li>
        </ul>

        <h3>Using Cross-References for Study</h3>

        <h4>Thematic Study Example:</h4>
        <ol>
            <li>Search for "faith" in Window 2</li>
            <li>Click on Hebrews 11:1</li>
            <li>Check cross-references for related faith passages</li>
            <li>Follow chain through Romans, James, Galatians</li>
            <li>Build comprehensive understanding of Biblical faith</li>
        </ol>

        <h4>Prophecy Study Example:</h4>
        <ol>
            <li>Search for messianic prophecy (e.g., Isaiah 53)</li>
            <li>Check cross-references</li>
            <li>See NT fulfillments in Gospels and Acts</li>
            <li>Follow connections between prophecy and fulfillment</li>
        </ol>
        """)
        tab3_layout.addWidget(text3)
        tabs.addTab(tab3, "Examples")

        # Tab 4: Tips & Best Practices
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        text4 = QTextEdit()
        text4.setReadOnly(True)
        text4.setHtml("""
        <h2>Tips & Best Practices</h2>

        <h3>Reading Strategy</h3>
        <ol>
            <li><b>Start with search:</b> Find verses in Window 2</li>
            <li><b>Load context:</b> Click verse to see it in Window 3</li>
            <li><b>Read surrounding verses:</b> Understand the full context</li>
            <li><b>Explore cross-references:</b> Discover related passages</li>
            <li><b>Follow connections:</b> Build comprehensive understanding</li>
        </ol>

        <h3>Translation Comparison</h3>
        <ul>
            <li>Read a verse in KJV (traditional language)</li>
            <li>Switch to NIV or ESV (modern language)</li>
            <li>Compare how different translations render the passage</li>
            <li>Gain deeper understanding from multiple perspectives</li>
        </ul>

        <h3>Cross-Reference Workflow</h3>
        <ol>
            <li><b>Primary verse:</b> Start with your main verse of interest</li>
            <li><b>Check references:</b> Look for green References dropdown</li>
            <li><b>Review list:</b> Scan all available cross-references</li>
            <li><b>Select most relevant:</b> Click references with highest scores first</li>
            <li><b>Read context:</b> Don't just read the cross-reference, read its context too</li>
            <li><b>Follow chains:</b> Each reference may have its own references</li>
            <li><b>Take notes:</b> Use comments feature to record insights</li>
        </ol>

        <h3>Efficient Exploration</h3>
        <ul>
            <li><b>Relevance scores:</b> Higher scores (5-10) = stronger connections</li>
            <li><b>Text preview:</b> Read preview to decide if relevant before jumping</li>
            <li><b>Keep main window active:</b> Click back to Window 2 to try different verses</li>
            <li><b>Acquire key verses:</b> Save important discoveries to Subject window</li>
        </ul>

        <h3>Study Patterns</h3>

        <h4>Word Study:</h4>
        <p>Search for "righteousness" → Click key verses → Follow cross-references to build comprehensive understanding of the concept</p>

        <h4>Character Study:</h4>
        <p>Search for "David" → Read context of events → Follow cross-references to see prophecies about David's line</p>

        <h4>Doctrine Study:</h4>
        <p>Search for "salvation" → Follow cross-references through OT prophecy → NT fulfillment → Epistles explanation</p>

        <h3>Keyboard Efficiency</h3>
        <ul>
            <li><b>Ctrl+A:</b> Quick select all for copying entire context</li>
            <li><b>Ctrl+D:</b> Quick deselect if you change your mind</li>
            <li><b>Tab key:</b> Navigate between dropdowns</li>
            <li><b>Arrow keys:</b> Navigate dropdown items</li>
            <li><b>Enter:</b> Select highlighted dropdown item</li>
        </ul>

        <h3>Best Practices</h3>
        <ul>
            <li><b>Always read context:</b> Don't rely on single verses alone</li>
            <li><b>Follow multiple references:</b> Get full picture of a theme</li>
            <li><b>Compare translations:</b> Deepen understanding</li>
            <li><b>Document insights:</b> Use comments or export findings</li>
            <li><b>Build subject collections:</b> Acquire verses for organized study</li>
            <li><b>Cross-check interpretations:</b> Use multiple cross-references</li>
        </ul>

        <h3>Common Questions</h3>
        <p><b>Q: Why is the dropdown gray?</b></p>
        <p>A: No cross-references exist for this particular verse in the database.</p>

        <p><b>Q: Can I go back to previous verses?</b></p>
        <p>A: Yes, click the original verse in Window 2 again, or use your search history.</p>

        <p><b>Q: How are relevance scores determined?</b></p>
        <p>A: Based on shared themes, parallel passages, prophecy-fulfillment, and theological connections.</p>
        """)
        tab4_layout.addWidget(text4)
        tabs.addTab(tab4, "Tips & Best Practices")

        layout.addWidget(tabs)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        close_button.setMaximumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def show_subject_window_tips(self):
        """Show comprehensive Subject Window help with tabbed dialog"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                                     QTextEdit, QLabel, QPushButton, QWidget)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Subject Window Help")
        dialog.setMinimumSize(750, 650)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Subject Window Help & Reference")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Create tabbed interface
        tabs = QTabWidget()

        # Tab 1: Basic Usage
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        text1 = QTextEdit()
        text1.setReadOnly(True)
        text1.setHtml("""
        <h2 style='color: #FF9800;'>Window 4: Subject Window</h2>

        <h3>Purpose</h3>
        <p>Store and organize Bible verses for specific topics, themes, or studies. Think of it as your personal verse collection organized by subject matter.</p>

        <h3>Structure</h3>
        <p>The Subject Window uses a two-level organization:</p>
        <ul>
            <li><b>Groups:</b> Top-level categories (e.g., "Theology", "Sermon Prep", "Personal Study")</li>
            <li><b>Subjects:</b> Specific topics within each group (e.g., under "Theology" → "Grace", "Faith", "Salvation")</li>
        </ul>

        <h3>Basic Workflow</h3>
        <ol>
            <li><b>Create a Group:</b> Click + next to Groups dropdown</li>
            <li><b>Create a Subject:</b> Click + next to Subjects dropdown</li>
            <li><b>Search for verses:</b> Use Window 2 to find relevant verses</li>
            <li><b>Check verses:</b> Select verses in Window 2 or 3</li>
            <li><b>Acquire:</b> Click Acquire button to save to current subject</li>
            <li><b>View collection:</b> All saved verses appear in Window 4</li>
        </ol>

        <h3>Controls</h3>
        <ul>
            <li><b>Groups dropdown:</b> Select which group to work with</li>
            <li><b>+ (Groups):</b> Create new group</li>
            <li><b>- (Groups):</b> Delete current group and all its subjects</li>
            <li><b>Subjects dropdown:</b> Select which subject to view/edit</li>
            <li><b>+ (Subjects):</b> Create new subject in current group</li>
            <li><b>- (Subjects):</b> Delete current subject and all its verses</li>
            <li><b>Acquire button:</b> Add checked verses to current subject</li>
            <li><b>Delete Verses:</b> Remove checked verses from subject</li>
            <li><b>Clear button:</b> Remove all verses from current subject</li>
        </ul>

        <h3>Data Persistence</h3>
        <p>All groups, subjects, and verses are stored in the database and persist between sessions. Your collections are saved automatically.</p>
        """)
        tab1_layout.addWidget(text1)
        tabs.addTab(tab1, "Basic Usage")

        # Tab 2: Organization
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        text2 = QTextEdit()
        text2.setReadOnly(True)
        text2.setHtml("""
        <h2>Organization Strategies</h2>

        <h3>Topical Organization</h3>
        <p>Group by theological themes:</p>
        <ul>
            <li><b>Group: "Theology"</b>
                <ul>
                    <li>Subject: "Grace"</li>
                    <li>Subject: "Faith"</li>
                    <li>Subject: "Salvation"</li>
                    <li>Subject: "Sanctification"</li>
                </ul>
            </li>
            <li><b>Group: "Christian Living"</b>
                <ul>
                    <li>Subject: "Prayer"</li>
                    <li>Subject: "Wisdom"</li>
                    <li>Subject: "Love for Others"</li>
                </ul>
            </li>
        </ul>

        <h3>Study-Based Organization</h3>
        <p>Group by Bible study series:</p>
        <ul>
            <li><b>Group: "Romans Study 2024"</b>
                <ul>
                    <li>Subject: "Week 1: Introduction"</li>
                    <li>Subject: "Week 2: Sin and Righteousness"</li>
                    <li>Subject: "Week 3: Justification by Faith"</li>
                </ul>
            </li>
        </ul>

        <h3>Ministry Organization</h3>
        <p>Group by ministry purpose:</p>
        <ul>
            <li><b>Group: "Sermon Prep"</b>
                <ul>
                    <li>Subject: "January 7: New Beginnings"</li>
                    <li>Subject: "January 14: Faith in Trials"</li>
                </ul>
            </li>
            <li><b>Group: "Counseling"</b>
                <ul>
                    <li>Subject: "Anxiety and Fear"</li>
                    <li>Subject: "Forgiveness"</li>
                    <li>Subject: "Marriage"</li>
                </ul>
            </li>
        </ul>

        <h3>Character Studies</h3>
        <ul>
            <li><b>Group: "People of the Bible"</b>
                <ul>
                    <li>Subject: "David - Shepherd Years"</li>
                    <li>Subject: "David - King Years"</li>
                    <li>Subject: "Paul - Conversion"</li>
                    <li>Subject: "Paul - Missionary Journeys"</li>
                </ul>
            </li>
        </ul>

        <h3>Best Practices</h3>
        <ul>
            <li><b>Use descriptive names:</b> "Prayer in NT" better than "Prayer 1"</li>
            <li><b>Keep groups broad:</b> Don't create too many top-level groups</li>
            <li><b>Subjects specific:</b> Break down topics into manageable subjects</li>
            <li><b>Date studies:</b> Include dates for time-sensitive collections</li>
            <li><b>Regular review:</b> Periodically review and reorganize as needed</li>
        </ul>
        """)
        tab2_layout.addWidget(text2)
        tabs.addTab(tab2, "Organization")

        # Tab 3: Acquiring Verses
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        text3 = QTextEdit()
        text3.setReadOnly(True)
        text3.setHtml("""
        <h2>Acquiring Verses</h2>

        <h3>From Search Results (Window 2)</h3>
        <ol>
            <li>Search for your topic (e.g., "faith")</li>
            <li>Review the results</li>
            <li>Check boxes next to relevant verses</li>
            <li>Make sure Window 4 shows the target subject</li>
            <li>Click <b>Acquire</b> button</li>
            <li>Verses are added to the current subject</li>
        </ol>

        <h3>From Reading Window (Window 3)</h3>
        <ol>
            <li>Click a verse in Window 2 to load context</li>
            <li>Read the surrounding verses in Window 3</li>
            <li>Check boxes for additional relevant context verses</li>
            <li>Click <b>Acquire</b> button</li>
            <li>Both searched verse and context verses are saved</li>
        </ol>

        <h3>Mixed Selection</h3>
        <p>You can select verses from BOTH Windows 2 and 3:</p>
        <ol>
            <li>Check some verses in Window 2</li>
            <li>Click a verse to load Window 3</li>
            <li>Check additional verses in Window 3</li>
            <li>Click <b>Acquire</b> once</li>
            <li>All checked verses from both windows are saved</li>
        </ol>

        <h3>Selection Lock Mode</h3>
        <p>When verses are checked:</p>
        <ul>
            <li><b>Locked state:</b> Must Copy, Acquire, or Deselect (Ctrl+D)</li>
            <li><b>Copy button:</b> Green and available</li>
            <li><b>Acquire button:</b> Green if manual selection, gray if Ctrl+A</li>
            <li><b>Blinking message:</b> Reminds you to take action</li>
        </ul>

        <h3>Duplicate Handling</h3>
        <p>If you try to acquire a verse that's already in the subject:</p>
        <ul>
            <li>System detects the duplicate</li>
            <li>Skips adding it again</li>
            <li>Shows count of new vs duplicate verses</li>
            <li>Example: "Acquired 5 verses (2 duplicates skipped)"</li>
        </ul>

        <h3>After Acquiring</h3>
        <ul>
            <li>Checkboxes are automatically cleared</li>
            <li>Selection lock is released</li>
            <li>New verses appear in Window 4</li>
            <li>Can immediately search for more verses</li>
        </ul>
        """)
        tab3_layout.addWidget(text3)
        tabs.addTab(tab3, "Acquiring Verses")

        # Tab 4: Managing Content
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        text4 = QTextEdit()
        text4.setReadOnly(True)
        text4.setHtml("""
        <h2>Managing Groups, Subjects, and Verses</h2>

        <h3>Creating Groups</h3>
        <ol>
            <li>Click <b>+</b> button next to Groups dropdown</li>
            <li>Enter group name in dialog</li>
            <li>Click OK</li>
            <li>New group is created and selected</li>
        </ol>

        <h3>Creating Subjects</h3>
        <ol>
            <li>Select the parent group</li>
            <li>Click <b>+</b> button next to Subjects dropdown</li>
            <li>Enter subject name in dialog</li>
            <li>Click OK</li>
            <li>New subject is created and selected</li>
        </ol>

        <h3>Deleting Groups</h3>
        <p><b>⚠️ Warning:</b> Deleting a group deletes ALL subjects and verses within it!</p>
        <ol>
            <li>Select the group to delete</li>
            <li>Click <b>-</b> button next to Groups dropdown</li>
            <li>Confirm the deletion</li>
            <li>Group and all contents are permanently removed</li>
        </ol>

        <h3>Deleting Subjects</h3>
        <p><b>⚠️ Warning:</b> Deleting a subject deletes ALL verses within it!</p>
        <ol>
            <li>Select the subject to delete</li>
            <li>Click <b>-</b> button next to Subjects dropdown</li>
            <li>Confirm the deletion</li>
            <li>Subject and all verses are permanently removed</li>
        </ol>

        <h3>Deleting Individual Verses</h3>
        <ol>
            <li>Check boxes next to verses you want to remove</li>
            <li>Click <b>Delete Verses</b> button</li>
            <li>Confirm if prompted</li>
            <li>Selected verses are removed from the subject</li>
        </ol>

        <h3>Clearing All Verses</h3>
        <p>To remove all verses but keep the subject:</p>
        <ol>
            <li>Click <b>Clear</b> button</li>
            <li>Confirm the action</li>
            <li>All verses are removed</li>
            <li>Subject remains for future use</li>
        </ol>

        <h3>Reloading Subjects</h3>
        <p>If the verse list seems out of date:</p>
        <ol>
            <li>Switch to a different subject</li>
            <li>Switch back to the original subject</li>
            <li>Verses are reloaded from database</li>
        </ol>

        <h3>Best Practices</h3>
        <ul>
            <li><b>Think before deleting:</b> Group/subject deletion is permanent</li>
            <li><b>Export before major changes:</b> Save important collections externally</li>
            <li><b>Regular backups:</b> The database file contains all your data</li>
            <li><b>Test with small subjects:</b> Learn the system before building large collections</li>
        </ul>
        """)
        tab4_layout.addWidget(text4)
        tabs.addTab(tab4, "Managing Content")

        # Tab 5: Tips & Workflows
        tab5 = QWidget()
        tab5_layout = QVBoxLayout(tab5)
        text5 = QTextEdit()
        text5.setReadOnly(True)
        text5.setHtml("""
        <h2>Tips & Workflows</h2>

        <h3>Workflow 1: Building a Topical Study</h3>
        <ol>
            <li>Create Group: "Doctrine Study"</li>
            <li>Create Subject: "Justification by Faith"</li>
            <li>Search: "faith" (Window 2)</li>
            <li>Acquire relevant verses</li>
            <li>Search: "justified" </li>
            <li>Acquire more verses</li>
            <li>Use cross-references to find additional passages</li>
            <li>Build comprehensive collection</li>
        </ol>

        <h3>Workflow 2: Sermon Preparation</h3>
        <ol>
            <li>Create Group: "Sermons 2024"</li>
            <li>Create Subject: "Jan 7: New Year, New Faith"</li>
            <li>Search for key passages</li>
            <li>Load context in Window 3</li>
            <li>Acquire main points</li>
            <li>Add illustrations from cross-references</li>
            <li>Export final verse list for notes</li>
        </ol>

        <h3>Workflow 3: Character Study</h3>
        <ol>
            <li>Create Group: "Bible Characters"</li>
            <li>Create Subject: "David - Early Life"</li>
            <li>Search: "David" with OT filter</li>
            <li>Review chronologically (1 Samuel)</li>
            <li>Acquire key events</li>
            <li>Use cross-references for prophecies about David</li>
            <li>Create additional subjects for different periods</li>
        </ol>

        <h3>Efficiency Tips</h3>
        <ul>
            <li><b>Use cross-references:</b> Discover related verses you might miss in search</li>
            <li><b>Context is key:</b> Acquire context verses with your main verse</li>
            <li><b>Check duplicates:</b> System prevents duplicates automatically</li>
            <li><b>Multiple subjects:</b> Same verse can be in multiple subjects (different themes)</li>
            <li><b>Export regularly:</b> Save your collections for external use</li>
        </ul>

        <h3>Integration with Other Windows</h3>
        <ul>
            <li><b>Window 2:</b> Search results → acquire to subjects</li>
            <li><b>Window 3:</b> Context verses → acquire additional context</li>
            <li><b>Window 5:</b> Add comments to verses in your subjects</li>
            <li><b>Copy button:</b> Copy subject verses to clipboard for use elsewhere</li>
            <li><b>Export button:</b> Save subject to text file</li>
        </ul>

        <h3>Advanced Organization</h3>
        <p><b>Multi-translation collections:</b></p>
        <ul>
            <li>Search same topic in multiple translations</li>
            <li>Acquire verses from different translations</li>
            <li>Build subject with translation variety</li>
            <li>Compare renderings within your collection</li>
        </ul>

        <p><b>Cross-subject connections:</b></p>
        <ul>
            <li>Subject: "Prayer - Examples" (actual prayers)</li>
            <li>Subject: "Prayer - Teaching" (instruction about prayer)</li>
            <li>Subject: "Prayer - Promises" (answered prayer promises)</li>
            <li>Build related but distinct collections</li>
        </ul>

        <h3>Common Questions</h3>
        <p><b>Q: Can I move verses between subjects?</b></p>
        <p>A: Delete from one subject, then acquire to another. Or just acquire to multiple subjects (verses can exist in multiple places).</p>

        <p><b>Q: What happens if I delete a group by accident?</b></p>
        <p>A: It's permanent. Consider backing up your database file regularly.</p>

        <p><b>Q: Can I rename groups or subjects?</b></p>
        <p>A: Currently no. Delete and recreate with new name, then re-acquire verses.</p>

        <p><b>Q: How many verses can a subject hold?</b></p>
        <p>A: No practical limit. Organize by subtopics if collections get very large.</p>
        """)
        tab5_layout.addWidget(text5)
        tabs.addTab(tab5, "Tips & Workflows")

        layout.addWidget(tabs)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        close_button.setMaximumWidth(100)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)

        dialog.exec()

    def show_export_help(self):
        """Show export feature help dialog"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel)
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Export Feature Help")
        dialog.setMinimumSize(700, 600)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("Export Feature - Comprehensive Verse Export")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Help content
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_content = """
<h2>Export Feature Overview</h2>
<p>The Export feature allows you to export Bible verses from multiple sources in various formats.</p>

<h3>How to Access</h3>
<p>Click the <b>Export</b> button in Window 1 (Message Window) to open the Export Dialog.</p>

<h3>Export Sources</h3>
<ul>
<li><b>Search Results (Window 2)</b> - Export verses from your current search results</li>
<li><b>Reading Window (Window 3)</b> - Export context/reading window verses</li>
<li><b>Subject Verses (Window 4)</b> - Export verses saved to a subject (requires Windows 4 & 5 to be open)</li>
<li><b>Messages Database</b> - Export messages from the message window</li>
</ul>

<h3>Selection Options</h3>
<ul>
<li><b>Selected verses only (checked)</b> - Export only verses with checkboxes checked</li>
<li><b>All verses in window/subject</b> - Export every verse in the selected source</li>
<li><b>Include comments</b> - (Subject export only) Export comments alongside verses</li>
</ul>

<h3>Export Formats</h3>
<ul>
<li><b>CSV (Comma delimited)</b> - Best for Excel, Google Sheets, data analysis<br>
    Format: Reference, Text, Comment columns</li>
<li><b>RTF (Rich Text Format)</b> - Best for Word, printing, sharing<br>
    Formatted with bold references, plain text verses, italic comments</li>
</ul>

<h3>Save Location</h3>
<ul>
<li><b>Default</b> - Files save to <code>downloads/</code> subfolder in app directory</li>
<li><b>Custom</b> - Click <b>Browse...</b> to choose any folder</li>
<li><b>Reset to Default</b> - Click to return to default downloads folder</li>
</ul>

<h3>File Naming</h3>
<p>Files are automatically named: <code>[Source]_[Timestamp].[ext]</code></p>
<p>Examples:</p>
<ul>
<li>Search_Results_20251228_103045.csv</li>
<li>Subject_Love_Verses_20251228_104500.rtf</li>
<li>Reading_Window_20251228_105200.csv</li>
</ul>

<h3>Export Actions</h3>
<ul>
<li><b>Export to File</b> - Save verses to CSV or RTF file</li>
<li><b>Send to Printer</b> - Print verses directly (formatted as readable document)</li>
<li><b>Cancel</b> - Close dialog without exporting</li>
</ul>

<h3>Example Workflows</h3>

<h4>1. Export Search Results to Excel</h4>
<ol>
<li>Search for "faith" in Window 2</li>
<li>Click <b>Export</b> button</li>
<li>Select <b>Search Results (Window 2)</b></li>
<li>Choose <b>All verses</b> or check specific verses and select <b>Selected only</b></li>
<li>Select <b>CSV (Comma delimited)</b></li>
<li>Click <b>Export to File</b></li>
<li>Open the CSV file in Excel for analysis</li>
</ol>

<h4>2. Export Subject with Comments to Word</h4>
<ol>
<li>Open Windows 4 & 5 (click 📑 button)</li>
<li>Select subject in Window 4 dropdown</li>
<li>Click <b>Export</b> button</li>
<li>Select <b>Subject Verses (Window 4)</b></li>
<li>Choose <b>All verses in subject</b></li>
<li>Check <b>Include comments</b></li>
<li>Select <b>RTF (Rich Text Format)</b></li>
<li>Click <b>Export to File</b></li>
<li>Open RTF file in Word to view formatted document</li>
</ol>

<h4>3. Print Chapter for Study</h4>
<ol>
<li>Click a verse in Window 2 to load chapter in Window 3</li>
<li>Review verses and check key verses to emphasize</li>
<li>Click <b>Export</b> button</li>
<li>Select <b>Reading Window (Window 3)</b></li>
<li>Choose <b>Selected verses only</b></li>
<li>Select <b>RTF (Rich Text Format)</b></li>
<li>Click <b>Send to Printer</b></li>
<li>Configure print settings and print</li>
</ol>

<h3>Tips</h3>
<ul>
<li>Use CSV for data analysis and importing into other programs</li>
<li>Use RTF for reading, printing, and sharing formatted documents</li>
<li>Always include comments when exporting subjects for complete backup</li>
<li>Export regularly to backup your subject collections</li>
<li>Use the printer option for quick printouts of selected verses</li>
</ul>

<h3>Error Messages</h3>
<ul>
<li><b>"No Verses to Export"</b> - Check at least one verse or select "All verses" option</li>
<li><b>"No Subject Selected"</b> - Select a subject in Window 4 first</li>
<li><b>"Subject Features Not Available"</b> - Click 📑 button to open Windows 4 & 5</li>
</ul>

<p><i>For more detailed information, see EXPORT_FEATURE.md in the app directory.</i></p>
"""
        help_text.setHtml(help_content)
        layout.addWidget(help_text)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        close_button.setMaximumWidth(100)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

        dialog.exec()

    def show_comprehensive_docs(self):
        """Open comprehensive documentation in external viewer or show in dialog"""
        import os
        import subprocess
        from PyQt6.QtWidgets import QMessageBox

        # Path to README.md in app directory
        readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")

        if not os.path.exists(readme_path):
            QMessageBox.warning(
                self,
                "Documentation Not Found",
                "Could not find README.md in the application directory."
            )
            return

        # Try to open with system default markdown viewer
        try:
            if sys.platform == 'win32':
                os.startfile(readme_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', readme_path])
            else:  # Linux and other Unix-like
                # Try common markdown viewers, fall back to text editor
                viewers = ['typora', 'ghostwriter', 'remarkable', 'retext', 'gedit', 'kate', 'xdg-open']
                opened = False
                for viewer in viewers:
                    try:
                        subprocess.run([viewer, readme_path], check=True)
                        opened = True
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        continue

                if not opened:
                    # Fallback: show message with path
                    QMessageBox.information(
                        self,
                        "Open Documentation",
                        f"Please open the documentation file:\n\n{readme_path}\n\n"
                        "You can view it with any text editor or Markdown viewer."
                    )
        except Exception as e:
            # If all else fails, show the path
            QMessageBox.information(
                self,
                "Open Documentation",
                f"Please open the documentation file:\n\n{readme_path}\n\n"
                f"Error opening automatically: {e}"
            )

    def show_license_info(self):
        """Show license information dialog (MIT License + NET Bible Copyright)"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont

        dialog = QDialog(self)
        dialog.setWindowTitle("Bible Search Lite - License Information")
        dialog.setMinimumSize(700, 650)

        layout = QVBoxLayout(dialog)

        # Title
        title = QLabel("📜 License Information")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # License text
        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setPlainText("""MIT License

Copyright (c) 2026 Andrew Hopkins

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

In simple terms:

✅ Free to use for any purpose (personal, commercial, ministry)
✅ Free to modify and distribute
✅ Free to include in other projects
✅ No warranty or liability
ℹ️  Just keep the copyright notice

This permissive license allows maximum freedom while protecting the author
from liability. It's the same license used by many popular open-source projects.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NET Bible® Copyright Notice

THE NET BIBLE®, New English Translation (NET)

Scripture quoted by permission. Quotations designated (NET) are from the
NET Bible® copyright ©1996, 2019 by Biblical Studies Press, L.L.C.
http://netbible.com All rights reserved.

This application includes the NET Bible® translation in the bibles.db database.
The NET Bible® text is used under the terms of the NET Bible® copyright for
non-commercial use.

For complete NET Bible® copyright information and permissions, visit:
https://netbible.org/copyright/

THE NAMES: THE NET BIBLE®, NEW ENGLISH TRANSLATION COPYRIGHT (c) 1996 BY
BIBLICAL STUDIES PRESS, L.L.C. NET Bible® IS A REGISTERED TRADEMARK.
THE NET BIBLE® LOGO, SERVICE MARK COPYRIGHT (c) 1997 BY BIBLICAL STUDIES
PRESS, L.L.C. ALL RIGHTS RESERVED.""")

        layout.addWidget(license_text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def check_for_updates(self):
        """Check for application updates on GitHub"""
        try:
            # Show checking message
            self.set_message("⏳ Checking for updates...")
            QApplication.processEvents()  # Update UI immediately

            # Fetch version from GitHub
            version_url = "https://raw.githubusercontent.com/andyinva/bible-search-lite/main/VERSION.txt"

            try:
                with urllib.request.urlopen(version_url, timeout=10) as response:
                    latest_version = response.read().decode('utf-8').strip()
            except urllib.error.URLError as e:
                QMessageBox.warning(
                    self,
                    "Update Check Failed",
                    f"Could not check for updates.\n\n"
                    f"Error: {e}\n\n"
                    f"Please check your internet connection."
                )
                self.set_message("❌ Update check failed")
                return

            # Compare versions
            current = VERSION

            if latest_version > current:
                # Update available
                reply = QMessageBox.question(
                    self,
                    "Update Available",
                    f"A new version is available!\n\n"
                    f"Current version: {current}\n"
                    f"Latest version: {latest_version}\n\n"
                    f"Would you like to download the update?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.download_update()
                else:
                    self.set_message("Update cancelled")
            else:
                # Already up to date
                QMessageBox.information(
                    self,
                    "No Updates Available",
                    f"You are running the latest version ({current}).\n\n"
                    f"No updates are available at this time."
                )
                self.set_message(f"✓ Up to date (v{current})")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Update Check Error",
                f"An error occurred while checking for updates:\n\n{e}"
            )
            self.set_message("❌ Update check error")

    def download_update(self):
        """Download and install application update"""
        import tempfile
        import shutil
        import platform

        try:
            # Create progress dialog
            progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
            progress.setWindowTitle("Updating Bible Search Lite")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            # Determine which file to download
            system = platform.system()
            if system == "Windows":
                file_url = "https://raw.githubusercontent.com/andyinva/bible-search-lite/main/bible_search_lite.py"
                file_name = "bible_search_lite.py"
            else:
                file_url = "https://raw.githubusercontent.com/andyinva/bible-search-lite/main/bible_search_lite.py"
                file_name = "bible_search_lite.py"

            # Download to temp file
            temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.py')

            def download_progress(count, block_size, total_size):
                if progress.wasCanceled():
                    raise Exception("Download cancelled by user")
                if total_size > 0:
                    percent = int(count * block_size * 100 / total_size)
                    progress.setValue(min(percent, 100))
                    QApplication.processEvents()

            urllib.request.urlretrieve(file_url, temp_file.name, download_progress)
            temp_file.close()

            progress.setValue(100)
            progress.close()

            # Backup current file
            backup_name = "bible_search_lite.py.backup"
            if os.path.exists(file_name):
                shutil.copy2(file_name, backup_name)

            # Replace with new version
            shutil.move(temp_file.name, file_name)

            # Success message
            QMessageBox.information(
                self,
                "Update Complete",
                "Bible Search Lite has been updated successfully!\n\n"
                "Please restart the application for changes to take effect.\n\n"
                f"A backup of the previous version was saved as:\n{backup_name}"
            )

            self.set_message("✓ Update downloaded - Please restart")

        except Exception as e:
            if "cancelled" not in str(e).lower():
                QMessageBox.critical(
                    self,
                    "Update Failed",
                    f"Failed to download update:\n\n{e}\n\n"
                    f"You can manually update by downloading from:\n"
                    f"https://github.com/andyinva/bible-search-lite"
                )
            self.set_message("❌ Update failed")

            # Clean up temp file if it exists
            try:
                if 'temp_file' in locals() and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
            except:
                pass


    def on_copy_clicked(self):
        """Copy selected verses to clipboard"""
        from PyQt6.QtWidgets import QApplication, QMessageBox

        # Get active window
        active = getattr(self, 'active_window_id', None)
        self.debug_print(f"📋 Copy button clicked - Active window: {active}")

        # Check if a window is active
        if active is None:
            self.debug_print(f"❌ No window selected")
            self.set_message("Please click on a window (2, 3, or 4) first to select it")
            return

        # Allow copying from search (Window 2), reading (Window 3), and subject (Window 4)
        if active not in ['search', 'reading', 'subject']:
            self.debug_print(f"❌ Cannot copy from window: {active}")
            self.set_message("Copy only works from Windows 2, 3, or 4")
            return

        if active not in self.verse_lists:
            self.debug_print(f"❌ Active window not in verse_lists")
            return

        selected = self.verse_lists[active].get_selected_verses()
        self.debug_print(f"📋 Selected verses: {len(selected)}")
        if not selected:
            self.set_message("No verses selected to copy")
            return

        # Build clipboard text
        text_lines = []
        for verse_id in selected:
            if verse_id in self.verse_lists[active].verse_items:
                # verse_items now returns (QListWidgetItem, VerseItemWidget) tuple
                list_item, verse_widget = self.verse_lists[active].verse_items[verse_id]
                ref = verse_widget.get_verse_reference()
                # Remove highlight brackets from text before copying
                clean_text = verse_widget.text.replace('[', '').replace(']', '')
                text_lines.append(f"{ref} {clean_text}")

        if not text_lines:
            self.set_message("No verses to copy")
            return

        # Check size limits: warn if more than 50 verses or 50KB
        clipboard_text = "\n".join(text_lines)
        verse_count = len(text_lines)
        text_size_kb = len(clipboard_text.encode('utf-8')) / 1024

        # Warn if too much data
        if verse_count > 50:
            reply = QMessageBox.question(
                self,
                "Large Copy Warning",
                f"You are copying {verse_count} verses ({text_size_kb:.1f} KB).\n\n"
                f"This is a large amount of data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        elif text_size_kb > 50:
            reply = QMessageBox.question(
                self,
                "Large Copy Warning",
                f"You are copying {text_size_kb:.1f} KB of text ({verse_count} verses).\n\n"
                f"This is a large amount of data. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Copy to clipboard
        QApplication.clipboard().setText(clipboard_text)
        self.debug_print(f"📋 Copied to clipboard:")
        self.debug_print(f"   First verse: {text_lines[0][:100]}..." if text_lines else "   (empty)")

        # Uncheck all boxes in Windows 2, 3, & 4 after copying (this will auto-unlock via checkbox handler)
        self.verse_lists['search'].select_none()
        self.verse_lists['reading'].select_none()
        if 'subject' in self.verse_lists:
            self.verse_lists['subject'].select_none()
        self.debug_print(f"📋 Unchecked all verses in Windows 2, 3, & 4")

        # Show success message (unlock happens automatically when boxes uncheck)
        self.set_message(f"Copied {verse_count} verse(s) to clipboard ({text_size_kb:.1f} KB)")
        self.debug_print(f"✅ Copy complete: {verse_count} verses, {text_size_kb:.1f} KB")
    
    def on_export_clicked(self):
        """Open the comprehensive export dialog"""
        from export_dialog import ExportDialog

        dialog = ExportDialog(self)
        dialog.exec()


    def on_find(self):
        """Find/filter verses in current subject"""
        from PyQt6.QtWidgets import QInputDialog
        
        if not hasattr(self, 'current_subject_id') or not self.current_subject_id:
            self.set_message("Please select a subject first")
            return
        
        search_term, ok = QInputDialog.getText(
            self,
            "Find in Subject",
            "Enter search term:"
        )
        
        if ok and search_term.strip():
            # Simple case-insensitive search in displayed verses
            found_count = 0
            if 'subject' in self.verse_lists:
                    for verse_id, verse_item in self.verse_lists['subject'].verse_items.items():
                        # Unpack tuple: (QListWidgetItem, VerseItemWidget)
                        _, widget = verse_item
                        if search_term.lower() in widget.text.lower():
                            found_count += 1
            
            if found_count > 0:
                self.set_message(f"Found '{search_term}' in {found_count} verse(s)")
            else:
                self.set_message(f"'{search_term}' not found")



    def on_add_comment(self):
        """Add comment to selected verse - placeholder"""
        self.set_message("Comment functionality coming soon")
    
    def on_edit_comment(self):
        """Edit comment - placeholder"""
        self.set_message("Comment functionality coming soon")
    
    def on_delete_comment(self):
        """Delete comment - placeholder"""
        self.set_message("Comment functionality coming soon")


    def on_save_comment(self):
        """Save comment - placeholder"""
        self.set_message("Comment functionality coming soon")


    def on_close_comment(self):
        """Close comment editor - placeholder"""
        self.set_message("Comment functionality coming soon")


    def load_config(self):
        """Load saved configuration including window geometry, splitter sizes, and search history"""
        config = self.config_manager.load()
        if config:
            # Restore window geometry
            if 'window_geometry' in config:
                geom = config['window_geometry']
                x = geom['x']
                y = geom['y']
                width = geom['width']
                height = geom['height']

                # Ensure window is not positioned off-screen (especially on Windows)
                # Minimum y position should be at least 0 (not above screen top)
                if y < 0:
                    y = 0
                    self.debug_print(f"⚠️  Adjusted window y position from {geom['y']} to {y} (was off-screen)")

                # Ensure x position is reasonable (not too far left)
                if x < -100:  # Allow some negative for multi-monitor, but not extreme
                    x = 100
                    self.debug_print(f"⚠️  Adjusted window x position from {geom['x']} to {x} (was off-screen)")

                self.setGeometry(x, y, width, height)
                self.debug_print(f"✓ Restored window geometry: {width}x{height} at ({x}, {y})")

            # Restore main splitter sizes (after UI is created)
            if 'splitter_sizes' in config and hasattr(self, 'main_splitter'):
                self.main_splitter.setSizes(config['splitter_sizes'])
                self.debug_print(f"✓ Restored main splitter sizes: {config['splitter_sizes']}")

            # Restore checkbox states
            if 'checkboxes' in config:
                checkboxes = config['checkboxes']
                if hasattr(self, 'case_sensitive_cb'):
                    self.case_sensitive_cb.setChecked(checkboxes.get('case_sensitive', False))
                if hasattr(self, 'unique_verse_cb'):
                    self.unique_verse_cb.setChecked(checkboxes.get('unique_verse', False))
                if hasattr(self, 'abbreviate_results_cb'):
                    self.abbreviate_results_cb.setChecked(checkboxes.get('abbreviate_results', False))
                self.debug_print(f"✓ Restored checkbox states: case_sensitive={checkboxes.get('case_sensitive', False)}, unique_verse={checkboxes.get('unique_verse', False)}, abbreviate={checkboxes.get('abbreviate_results', False)}")

            # Restore selected translations
            if 'selected_translations' in config:
                saved_translations = config['selected_translations']
                # Validate that saved translations exist in current database
                available_abbreviations = [t.abbreviation for t in self.search_controller.bible_search.translations]
                valid_translations = [t for t in saved_translations if t in available_abbreviations]
                if valid_translations:
                    self.selected_translations = valid_translations
                    # Update button text to show count
                    count = len(self.selected_translations)
                    self.translations_button.setText(f"Translations ({count})")
                    self.debug_print(f"✓ Restored {len(self.selected_translations)} selected translations: {self.selected_translations}")
                else:
                    self.debug_print(f"⚠️  No valid translations in saved config, using default [KJV]")

            # Restore font settings
            if 'font_settings' in config:
                font_settings = config['font_settings']
                self.title_font_size = font_settings.get('title_font_size', 0)
                self.verse_font_size = font_settings.get('verse_font_size', 0)
                # Apply the font settings
                self.apply_font_settings()
                self.debug_print(f"✓ Restored font settings: title={self.title_font_size}, verse={self.verse_font_size}")

            # Load search history
            if 'search_history' in config:
                self.search_history = config['search_history']
                # Populate the search input dropdown with history (if widget exists)
                if hasattr(self, 'search_input') and self.search_input is not None:
                    self.search_input.clear()
                    self.search_input.addItems(self.search_history)
                    # Set to empty on startup (don't auto-select first item)
                    self.search_input.setCurrentIndex(-1)
                    self.search_input.lineEdit().clear()
                    self.debug_print(f"✓ Loaded {len(self.search_history)} search history items (starting empty)")

            # Restore book filter selection
            if 'selected_book_filter' in config:
                self.selected_book_filter = config['selected_book_filter']
                if hasattr(self, 'books_button') and self.books_button is not None:
                    # Update button text based on selection
                    filter_name = self.selected_book_filter
                    if filter_name in ["Old Testament", "New Testament"]:
                        short_name = "OT" if filter_name == "Old Testament" else "NT"
                        self.books_button.setText(short_name)
                    else:
                        self.books_button.setText(filter_name)
                    self.debug_print(f"✓ Restored book filter: {self.selected_book_filter}")
        self.debug_print("✓ Configuration loaded")

    def save_config(self):
        """Save current configuration including search history and window sizes"""
        config = {
            'window_geometry': {
                'x': self.x(),
                'y': self.y(),
                'width': self.width(),
                'height': self.height()
            },
            'splitter_sizes': self.main_splitter.sizes() if hasattr(self, 'main_splitter') and self.main_splitter else [80, 200, 250, 200, 100],
            'selected_translations': self.selected_translations,
            'selected_book_filter': self.selected_book_filter,
            'checkboxes': {
                'case_sensitive': self.case_sensitive_cb.isChecked(),
                'unique_verse': self.unique_verse_cb.isChecked(),
                'abbreviate_results': self.abbreviate_results_cb.isChecked()
            },
            'font_settings': {
                'title_font_size': self.title_font_size,
                'verse_font_size': self.verse_font_size
            },
            'search_history': self.search_history
        }

        # Save Windows 4 & 5 internal splitter sizes
        if self.subject_manager and hasattr(self.subject_manager, 'container_widget'):
            subject_splitter = self.subject_manager.container_widget.findChild(QSplitter)
            if subject_splitter:
                config['subject_splitter_sizes'] = subject_splitter.sizes()
                self.debug_print(f"✓ Saved Windows 4 & 5 splitter sizes: {subject_splitter.sizes()}")

        self.config_manager.save(config)

    def closeEvent(self, event):
        """Handle application close event - save configuration and cleanup"""
        # Clear subject dropdown selections
        if hasattr(self, 'reading_subject_combo'):
            self.reading_subject_combo.setCurrentIndex(0)  # Reset to empty
            self.debug_print("✓ Cleared subject dropdown selection")

        # Save configuration (including window sizes)
        self.save_config()
        self.debug_print("✓ Configuration saved on exit")

        event.accept()

    def add_sample_verses(self):
        """Add sample verses for demonstration - optional"""
        # Sample verses can be added here if desired
        # Currently no samples are added by default
        pass

    def load_cross_references(self, verse_reference):
        """
        Load cross-references for a given verse from the database.

        Args:
            verse_reference (str): Verse reference (e.g., "Gen 1:1", "John 3:16")
                                  Can be abbreviation or full name

        Returns:
            list: List of tuples (to_reference, to_text, relevance_score)
        """
        import sqlite3

        try:
            # Connect to the bibles database
            db_path = self.search_controller.bible_search.database_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Convert abbreviation to full book name if needed
            # Parse the reference to extract book abbreviation
            parts = verse_reference.split()
            if parts[0].isdigit() and len(parts) > 1:
                # Numbered book like "1 Sam" or "1Sa"
                book_abbrev = f"{parts[0]} {parts[1]}"
                chapter_verse = parts[2] if len(parts) > 2 else ""
            else:
                # Single-word book like "Gen" or "Genesis"
                book_abbrev = parts[0]
                chapter_verse = parts[1] if len(parts) > 1 else ""

            # Look up full book name from abbreviation
            cursor.execute("SELECT name FROM books WHERE abbreviation = ?", (book_abbrev,))
            result = cursor.fetchone()

            if result:
                full_book_name = result[0]
                full_reference = f"{full_book_name} {chapter_verse}"
            else:
                # Already a full name or not found
                full_reference = verse_reference

            # Query cross-references ordered by relevance
            cursor.execute("""
                SELECT to_reference, to_text, relevance_score
                FROM cross_references
                WHERE from_reference = ?
                ORDER BY relevance_score DESC
                LIMIT 20
            """, (full_reference,))

            references = cursor.fetchall()
            conn.close()

            self.debug_print(f"📖 Found {len(references)} cross-references for {full_reference}")
            return references

        except Exception as e:
            self.debug_print(f"❌ Error loading cross-references: {e}")
            return []

    def save_window3_to_history_before_update(self, new_verse_reference):
        """
        Save current Window 3 state to history before loading new verses.
        This should be called BEFORE clearing Window 3.

        Args:
            new_verse_reference (str): The verse reference we're about to load
        """
        # Only save if we have a current verse AND it's different from the new one
        current_verse = getattr(self, '_current_cross_ref_verse', None)
        if not current_verse or current_verse == new_verse_reference:
            return

        # Only save if the cross-references dropdown has content
        if not (self.cross_references_combo.isEnabled() and self.cross_references_combo.count() > 1):
            return

        # Save the current references list
        current_refs = []
        for i in range(1, self.cross_references_combo.count()):
            ref = self.cross_references_combo.itemData(i)
            text = self.cross_references_combo.itemText(i)
            if ref:
                current_refs.append((ref, text))

        # Save Window 3 verse list state (THIS is why we call before clearing!)
        verse_list_state = []
        try:
            for verse_id, verse_item in self.verse_lists['reading'].verse_items.items():
                _, verse_widget = verse_item
                verse_list_state.append({
                    'verse_id': verse_id,
                    'translation': verse_widget.translation,
                    'book_abbrev': verse_widget.book_abbrev,
                    'chapter': verse_widget.chapter,
                    'verse_number': verse_widget.verse_number,
                    'text': verse_widget.text_label.text(),
                    'is_highlighted': verse_widget.is_highlighted
                })

            # Add to history stack (verse_reference, references_list, verse_list_state)
            self.cross_ref_history.append((current_verse, current_refs, verse_list_state))
            self.debug_print(f"📚 Saved to history: {current_verse} ({len(current_refs)} refs, {len(verse_list_state)} verses)")
        except Exception as e:
            self.debug_print(f"⚠️  Error saving Window 3 state to history: {e}")
            # Still add to history with empty verse list if there's an error
            self.cross_ref_history.append((current_verse, current_refs, []))
            self.debug_print(f"📚 Saved to history (without verse list): {current_verse} ({len(current_refs)} refs)")

    def update_cross_references_dropdown(self, verse_reference):
        """
        Update the cross-references dropdown with references for the selected verse.
        Note: History saving is now done in save_window3_to_history_before_update()
        which is called BEFORE Window 3 is cleared.

        Args:
            verse_reference (str): Verse reference (e.g., "Genesis 1:1")
        """
        # Store the new verse reference
        self._current_cross_ref_verse = verse_reference

        # Load cross-references from database
        references = self.load_cross_references(verse_reference)

        # Clear existing items
        self.cross_references_combo.clear()

        if len(references) > 0:
            # Add header item
            self.cross_references_combo.addItem(f"References ({len(references)})")

            # Add each cross-reference
            for to_ref, to_text, score in references:
                # Truncate text if too long
                display_text = to_text[:80] + "..." if to_text and len(to_text) > 80 else to_text
                item_text = f"{to_ref} - {display_text}" if to_text else to_ref
                self.cross_references_combo.addItem(item_text)

                # Store the full reference in item data
                self.cross_references_combo.setItemData(
                    self.cross_references_combo.count() - 1,
                    to_ref
                )

            # Enable and highlight the dropdown
            self.cross_references_combo.setEnabled(True)

            # Green highlight style
            self.cross_references_combo.setStyleSheet("""
                QComboBox {
                    background-color: #e8f5e9;
                    border: 2px solid #4CAF50;
                    padding: 4px;
                    border-radius: 2px;
                    min-height: 20px;
                    font-weight: bold;
                }
                QComboBox:hover {
                    background-color: #c8e6c9;
                }
                QComboBox::drop-down {
                    border: none;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    selection-background-color: #e3f2fd;
                    selection-color: black;
                    color: black;
                }
                QComboBox QAbstractItemView::item {
                    color: black;
                    padding: 4px;
                }
                QComboBox QAbstractItemView::item:selected {
                    background-color: #e3f2fd;
                    color: black;
                }
                QComboBox QAbstractItemView::item:hover {
                    background-color: #bbdefb;
                    color: black;
                }
            """)

            self.debug_print(f"✅ Cross-references dropdown updated with {len(references)} references")

            # Show Go Back button if there's history
            if len(self.cross_ref_history) > 0:
                self.go_back_btn.setVisible(True)
                self.go_back_btn.setEnabled(True)
            else:
                self.go_back_btn.setVisible(False)

        else:
            # No references found - gray out
            self.cross_references_combo.addItem("References (0)")
            self.cross_references_combo.setEnabled(False)
            self.cross_references_combo.setStyleSheet(self.get_combobox_style())

            # Hide Go Back button when no references
            self.go_back_btn.setVisible(False)

            self.debug_print(f"⚪ No cross-references found for {verse_reference}")

    def on_go_back_references(self):
        """Restore the previous cross-reference list and Window 3 verse list from history."""
        if len(self.cross_ref_history) == 0:
            self.debug_print("⚠️  No history to go back to")
            return

        # Pop the last state from history
        verse_reference, references_list, verse_list_state = self.cross_ref_history.pop()

        self.debug_print(f"⬅️  Going back to: {verse_reference} ({len(references_list)} refs, {len(verse_list_state)} verses)")

        # Restore Window 3 verse list
        from PyQt6.QtGui import QFont, QColor, QBrush

        # Clear reading window
        self.verse_lists['reading'].clear_verses()

        # Get verse font size
        verse_size = self.verse_font_sizes[self.verse_font_size]

        # Restore verses
        for verse_data in verse_list_state:
            self.verse_lists['reading'].add_verse(
                verse_data['verse_id'],
                verse_data['translation'],
                verse_data['book_abbrev'],
                verse_data['chapter'],
                verse_data['verse_number'],
                verse_data['text']
            )

            # Apply font
            verse_id = verse_data['verse_id']
            if verse_id in self.verse_lists['reading'].verse_items:
                list_item, verse_widget = self.verse_lists['reading'].verse_items[verse_id]
                verse_font = QFont("IBM Plex Mono")
                verse_font.setBold(False)
                verse_font.setPointSizeF(verse_size)
                verse_widget.text_label.setFont(verse_font)

                # Restore highlighting
                if verse_data.get('is_highlighted', False):
                    verse_widget.set_highlighted(True)
                    list_item.setBackground(QBrush(QColor(214, 233, 255)))  # #D6E9FF blue tint
                else:
                    verse_widget.set_highlighted(False)
                    list_item.setBackground(QBrush(QColor(255, 255, 255)))  # White

        # Update size hints after font changes
        self.verse_lists['reading'].update_item_sizes()

        # Update translation label in Reading Window header
        if verse_list_state and hasattr(self, 'reading_section') and hasattr(self.reading_section, 'translation_label') and self.reading_section.translation_label:
            translation_abbrev = verse_list_state[0]['translation']
            translation_name = translation_abbrev  # Default to abbreviation
            for trans in self.search_controller.bible_search.translations:
                if trans.abbreviation == translation_abbrev:
                    translation_name = trans.full_name
                    break
            self.reading_section.translation_label.setText(translation_name)

        self.debug_print(f"✓ Restored {len(verse_list_state)} verses to Window 3")

        # Update the current verse reference
        self._current_cross_ref_verse = verse_reference

        # Clear and rebuild the references dropdown
        self.cross_references_combo.clear()
        self.cross_references_combo.addItem(f"References ({len(references_list)})")

        # Add saved references
        for ref, text in references_list:
            self.cross_references_combo.addItem(text)
            self.cross_references_combo.setItemData(
                self.cross_references_combo.count() - 1,
                ref
            )

        # Enable and style the dropdown
        self.cross_references_combo.setEnabled(True)
        self.cross_references_combo.setStyleSheet("""
            QComboBox {
                background-color: #e8f5e9;
                border: 2px solid #4CAF50;
                padding: 4px;
                border-radius: 2px;
                min-height: 20px;
                font-weight: bold;
            }
            QComboBox:hover {
                background-color: #c8e6c9;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #e3f2fd;
                selection-color: black;
                color: black;
            }
            QComboBox QAbstractItemView::item {
                color: black;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item:selected {
                background-color: #e3f2fd;
                color: black;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #bbdefb;
                color: black;
            }
        """)

        # Hide Go Back button if no more history
        if len(self.cross_ref_history) == 0:
            self.go_back_btn.setVisible(False)

        self.debug_print(f"✅ Restored references and verses for {verse_reference}")

    def on_cross_reference_selected(self, index):
        """
        Handle cross-reference selection from dropdown.
        Navigate to the selected verse reference in the Reading Window.

        Args:
            index (int): Selected index in dropdown
        """
        if index <= 0:  # Index 0 is the header
            return

        # Get the reference from item data
        reference = self.cross_references_combo.itemData(index)
        if not reference:
            return

        self.debug_print(f"🔗 Cross-reference selected: {reference}")

        # Parse the reference and load context
        # The reference format is like "Genesis 1:1" or "John 3:16"
        try:
            import sqlite3

            # Use KJV as default translation for cross-references
            translation = "KJV"

            # Parse book, chapter, verse from reference
            # Format: "Book Chapter:Verse" or "Book Chapter:Verse-EndVerse"
            parts = reference.split()

            # Handle multi-word book names (e.g., "1 Corinthians")
            if parts[0].isdigit() and len(parts[0]) == 1:
                # Numbered book like "1 Corinthians"
                book_full_name = f"{parts[0]} {parts[1]}"
                chapter_verse = parts[2]
            else:
                # Single-word book
                book_full_name = parts[0]
                chapter_verse = parts[1]

            # Convert full book name to abbreviation
            db_path = self.search_controller.bible_search.database_path
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT abbreviation FROM books WHERE name = ?", (book_full_name,))
            result = cursor.fetchone()
            conn.close()

            if not result:
                self.debug_print(f"❌ Book '{book_full_name}' not found in database")
                self.set_message(f"Error: Book '{book_full_name}' not found")
                return

            book_abbrev = result[0]

            # Split chapter:verse
            chapter_part, verse_part = chapter_verse.split(':')
            chapter = int(chapter_part)

            # Handle verse ranges (take the first verse)
            if '-' in verse_part:
                verse = int(verse_part.split('-')[0])
            else:
                verse = int(verse_part)

            self.debug_print(f"   Parsed: {translation} {book_abbrev} {chapter}:{verse}")

            # Load context verses for this reference in the reading window
            self.search_controller.load_context(
                translation=translation,
                book=book_abbrev,
                chapter=chapter,
                start_verse=verse,
                num_verses=50
            )

        except Exception as e:
            self.debug_print(f"❌ Error parsing cross-reference '{reference}': {e}")
            import traceback
            traceback.print_exc()
            self.set_message(f"Error loading reference: {reference}")

    def lock_selection_mode(self, is_ctrl_a=False):
        """
        Lock the UI when selections are made - user must choose Copy or Acquire.

        Args:
            is_ctrl_a (bool): True if selection was made via Ctrl+A
        """
        from PyQt6.QtCore import QTimer

        self.selection_locked = True
        self.is_ctrl_a_selection = is_ctrl_a

        # Green button style (matches original button size from create_title_button)
        green_style = """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 1px solid #45a049;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
                border: 1px solid #3d8b40;
            }
        """

        # Gray disabled style
        gray_style = """
            QPushButton {
                background-color: #cccccc;
                color: #666666;
                border: 1px solid #999;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
            }
        """

        # Highlight Copy button (always green when locked)
        self.copy_btn.setStyleSheet(green_style)

        if is_ctrl_a:
            # Ctrl+A mode: Only Copy available
            if hasattr(self, 'acquire_button') and self.acquire_button:
                self.acquire_button.setEnabled(False)
                self.acquire_button.setStyleSheet(gray_style)
            message = "⚠️ ACTION REQUIRED: Click COPY, press Ctrl+D, or uncheck all boxes"
        else:
            # Manual selection mode: Both Copy and Acquire available
            if hasattr(self, 'acquire_button') and self.acquire_button:
                self.acquire_button.setEnabled(True)
                self.acquire_button.setStyleSheet(green_style)
            message = "⚠️ ACTION REQUIRED: Click COPY or ACQUIRE, press Ctrl+D, or uncheck all boxes"

        # Start blinking message
        self.blink_state = True
        self.set_message(message)
        self.message_label.setStyleSheet("""
            background-color: #fffacd;
            padding: 10px;
            border: 2px solid #ff6b6b;
            font-weight: bold;
            color: #d32f2f;
        """)

        # Start blink timer
        if self.blink_timer:
            self.blink_timer.stop()
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_message)
        self.blink_timer.start(500)  # Blink every 500ms

        # Start/restart auto-stop timer (12 seconds of inactivity)
        # This prevents infinite CPU drain if user moves to other windows
        if self.blink_auto_stop_timer:
            self.blink_auto_stop_timer.stop()
        self.blink_auto_stop_timer = QTimer()
        self.blink_auto_stop_timer.timeout.connect(self.auto_stop_blinking)
        self.blink_auto_stop_timer.setSingleShot(True)  # Fire only once
        self.blink_auto_stop_timer.start(12000)  # 12 seconds

        self.debug_print(f"🔒 Selection LOCKED - {'Ctrl+A' if is_ctrl_a else 'Manual'} mode - auto-stop in 12s")

    def blink_message(self):
        """Toggle message visibility for blinking effect"""
        if not self.selection_locked:
            if self.blink_timer:
                self.blink_timer.stop()
            return

        self.blink_state = not self.blink_state

        if self.blink_state:
            self.message_label.setStyleSheet("""
                background-color: #fffacd;
                padding: 10px;
                border: 2px solid #ff6b6b;
                font-weight: bold;
                color: #d32f2f;
            """)
        else:
            self.message_label.setStyleSheet("""
                background-color: #ffebee;
                padding: 10px;
                border: 2px solid #ff6b6b;
                font-weight: bold;
                color: #d32f2f;
            """)

    def auto_stop_blinking(self):
        """
        Auto-stop blinking after 12 seconds of inactivity.
        Stops CPU drain but keeps selections and shows static reminder.
        """
        if not self.selection_locked:
            return

        self.debug_print("⏰ Auto-stopping blink after 12 seconds of inactivity")

        # Stop the blink timer
        if self.blink_timer:
            self.blink_timer.stop()
            self.blink_timer = None

        # Show static (non-blinking) reminder message
        if self.is_ctrl_a_selection:
            message = "Verses still selected in Window 2/3 - Copy, press Ctrl+D, or uncheck boxes"
        else:
            message = "Verses still selected in Window 2/3 - Copy, Acquire, press Ctrl+D, or uncheck boxes"

        self.set_message(message)
        # Set static yellow background (no more blinking)
        self.message_label.setStyleSheet("""
            background-color: #fff9c4;
            padding: 10px;
            border: 2px solid #ffa726;
            font-weight: bold;
            color: #e65100;
        """)

        # Keep selection_locked = True so buttons stay highlighted
        # User still needs to take action, just not with annoying blink

    def unlock_selection_mode(self):
        """
        Unlock the UI after user has made their choice.
        """
        if not self.selection_locked:
            return

        self.selection_locked = False
        self.is_ctrl_a_selection = False

        # Stop blinking
        if self.blink_timer:
            self.blink_timer.stop()
            self.blink_timer = None

        # Stop auto-stop timer
        if self.blink_auto_stop_timer:
            self.blink_auto_stop_timer.stop()
            self.blink_auto_stop_timer = None

        # Restore normal button styles
        # Copy button uses title button style (from create_title_button)
        title_button_style = """
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
        """
        self.copy_btn.setStyleSheet(title_button_style)
        self.send_btn.setStyleSheet(self.get_button_style())  # Window 3 Acquire button

        if hasattr(self, 'acquire_button') and self.acquire_button:
            self.acquire_button.setEnabled(True)
            self.update_acquire_button_state()

        # Update Window 3 Acquire button styling
        self.update_window3_acquire_style()

        # Restore normal message label style
        self.message_label.setStyleSheet("background-color: white; padding: 10px; border: 1px solid #ccc;")

        self.debug_print("🔓 Selection UNLOCKED")

    def load_subjects_for_reading(self):
        """Load subjects from database into Window 3's subject dropdown."""
        if not self.subject_manager or not self.subject_manager.verse_manager:
            return

        try:
            cursor = self.subject_manager.db_conn.cursor()
            cursor.execute("SELECT id, name FROM subjects ORDER BY name")
            subjects = cursor.fetchall()

            self.reading_subject_combo.clear()
            self.reading_subject_combo.addItem("")  # Empty item for "no selection"

            for subject in subjects:
                self.reading_subject_combo.addItem(subject['name'])

            self.debug_print(f"✓ Loaded {len(subjects)} subjects into Window 3 dropdown")
        except Exception as e:
            self.debug_print(f"Error loading subjects for reading: {e}")

    def on_reading_subject_changed(self, subject_name):
        """Handle subject selection change in Window 3."""
        # Prevent infinite recursion when syncing dropdowns
        if hasattr(self, '_syncing_subjects') and self._syncing_subjects:
            return

        # Update Window 4's Acquire button state
        self.update_subject_acquire_button()

        # Update Window 3 Acquire button styling and enabled state
        # (This now handles both based on subject selection AND verse selections)
        self.update_window3_acquire_style()

        has_subject = bool(subject_name and subject_name.strip())
        if has_subject:
            self.debug_print(f"✓ Reading window subject selected: {subject_name}")

            # Sync to Window 4 and load verses
            if self.subject_manager and self.subject_manager.verse_manager:
                try:
                    # Set flag to prevent recursion
                    self._syncing_subjects = True

                    # Get subject ID
                    cursor = self.subject_manager.db_conn.cursor()
                    cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name.strip(),))
                    result = cursor.fetchone()
                    if result:
                        subject_id = result['id']
                        # Set Window 4's dropdown to match Window 3
                        self.subject_manager.verse_manager.subject_dropdown.setCurrentText(subject_name)
                        self.subject_manager.verse_manager.current_subject = subject_name
                        self.subject_manager.verse_manager.current_subject_id = subject_id
                        # Load the verses
                        self.subject_manager.verse_manager.load_subject_verses()
                        self.debug_print(f"✓ Synced Window 4 to Window 3 subject: '{subject_name}'")
                except Exception as e:
                    self.debug_print(f"⚠️  Error syncing subject to Window 4: {e}")
                finally:
                    self._syncing_subjects = False

    def on_create_subject_from_reading(self):
        """Create a new subject from Window 3's dropdown text."""
        subject_name = self.reading_subject_combo.currentText().strip()

        if not subject_name:
            self.set_message("⚠️  Enter a subject name")
            return

        if not self.subject_manager:
            self.set_message("⚠️  Subject features not initialized")
            return

        try:
            cursor = self.subject_manager.db_conn.cursor()
            cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
            self.subject_manager.db_conn.commit()
            subject_id = cursor.lastrowid

            # Reload subjects in Window 3 dropdown
            self.load_subjects_for_reading()
            self.reading_subject_combo.setCurrentText(subject_name)

            # Sync to Window 4
            if self.subject_manager.verse_manager:
                self.subject_manager.verse_manager.load_subjects()
                self.subject_manager.verse_manager.subject_dropdown.setCurrentText(subject_name)
                self.subject_manager.verse_manager.current_subject = subject_name
                self.subject_manager.verse_manager.current_subject_id = subject_id

            self.set_message(f"✓ Created subject: {subject_name}")
            self.debug_print(f"✓ Created subject from Window 3: {subject_name} (ID: {subject_id})")

            # Flash the Create button green to indicate success
            self.flash_button_green(self.create_subject_btn)

        except sqlite3.IntegrityError:
            self.set_message(f"⚠️  Subject '{subject_name}' already exists")
        except Exception as e:
            self.set_message(f"⚠️  Error creating subject: {e}")

    def on_send_to_subject(self):
        """Acquire checked verses from Window 3 (reading) to selected subject."""
        subject_name = self.reading_subject_combo.currentText().strip()

        if not subject_name:
            self.set_message("⚠️ Please select or create a subject")
            return

        if not self.subject_manager:
            self.set_message("⚠️ Subject features not initialized")
            return

        # Get checked verses from BOTH Windows 2 & 3
        search_verses = self.verse_lists['search'].get_selected_verses()
        reading_verses = self.verse_lists['reading'].get_selected_verses()
        checked_verses = search_verses + reading_verses

        if not checked_verses:
            self.set_message("⚠️ No verses selected in Windows 2 or 3")
            return

        self.debug_print(f"📊 Window 3 Acquire: Found {len(search_verses)} verses in Window 2, {len(reading_verses)} verses in Window 3")

        try:
            # Check if subject exists, create if not
            cursor = self.subject_manager.db_conn.cursor()
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
            result = cursor.fetchone()

            if result:
                subject_id = result['id']
                self.debug_print(f"✓ Found existing subject: {subject_name} (ID: {subject_id})")
            else:
                # Create new subject
                cursor.execute(
                    "INSERT INTO subjects (name) VALUES (?)",
                    (subject_name,)
                )
                self.subject_manager.db_conn.commit()
                subject_id = cursor.lastrowid
                self.debug_print(f"✓ Created new subject: {subject_name} (ID: {subject_id})")

                # Reload subjects in both dropdowns
                self.load_subjects_for_reading()
                if self.subject_manager.verse_manager:
                    self.subject_manager.verse_manager.load_subjects()
                    # Select the newly created subject in Window 4
                    self.subject_manager.verse_manager.subject_dropdown.setCurrentText(subject_name)
                    self.subject_manager.verse_manager.current_subject = subject_name
                    self.subject_manager.verse_manager.current_subject_id = subject_id

            # Add verses to subject
            added_count = 0
            for verse_id in checked_verses:
                # Check both search and reading windows for this verse
                verse_widget = None
                if verse_id in self.verse_lists['search'].verse_items:
                    item, verse_widget = self.verse_lists['search'].verse_items[verse_id]
                elif verse_id in self.verse_lists['reading'].verse_items:
                    item, verse_widget = self.verse_lists['reading'].verse_items[verse_id]

                if verse_widget:
                    # Insert verse into subject_verses table
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO subject_verses
                            (subject_id, verse_reference, verse_text, translation, order_index)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            subject_id,
                            f"{verse_widget.book_abbrev} {verse_widget.chapter}:{verse_widget.verse_number}",
                            verse_widget.text,
                            verse_widget.translation,
                            added_count
                        ))
                        if cursor.rowcount > 0:
                            added_count += 1
                    except Exception as e:
                        self.debug_print(f"Error adding verse: {e}")

            self.subject_manager.db_conn.commit()

            # Uncheck all verses in both Windows 2 & 3 after acquiring
            self.verse_lists['search'].select_none()
            self.verse_lists['reading'].select_none()

            # Update message
            if added_count > 0:
                self.set_message(
                    f"✓ Sent {added_count} verse(s) to subject: {subject_name}"
                )
                self.debug_print(f"✓ Added {added_count} verses to subject '{subject_name}'")

                # Refresh Window 4 if it's showing this subject
                if (self.subject_manager.verse_manager and
                    self.subject_manager.verse_manager.current_subject == subject_name):
                    self.subject_manager.verse_manager.load_subject_verses()
            else:
                self.set_message(
                    f"ℹ️ Verses already exist in subject: {subject_name}"
                )

        except Exception as e:
            self.set_message(f"❌ Error sending verses: {str(e)}")
            self.debug_print(f"Error in on_send_to_subject: {e}")
            import traceback
            traceback.print_exc()

def main():
    app = QApplication(sys.argv)
    window = BibleSearchProgram()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()