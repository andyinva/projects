import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QSplitter, QTextEdit, 
                             QLabel, QComboBox, QLineEdit, QPushButton, 
                             QListWidget, QScrollArea, QFrame, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Import existing classes from Tkinter version
from bible_search import BibleSearch

class ConfigManager:
    """Configuration management for the Bible search application."""
    
    def __init__(self, config_file: str = "bible_search_config.json"):
        self.config_file = config_file
        self.default_config = {
            "window_width": 1200,
            "window_height": 800,
            "font_size": 9,
            "enabled_translations": ["KJV", "ESV"],
            "search_history": [],
            "search_settings": {
                "case_sensitive": False,
                "unique_verses": False,
                "abbreviate_results": True,
                "synonyms": False,
                "fuzzy_match": False,
                "word_stems": False,
                "within_words": False
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file, creating with defaults if it doesn't exist."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to handle new keys
                    for key, value in self.default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return self.default_config.copy()
        except (json.JSONDecodeError, FileNotFoundError):
            return self.default_config.copy()
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key, value):
        """Set configuration value."""
        self.config[key] = value

class BibleSearchPyQt6(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.config_manager = ConfigManager()
        self.bible_search = BibleSearch()
        
        # Setup window
        self.setWindowTitle("Bible Search - PyQt6")
        window_width = self.config_manager.get('window_width', 1200)
        window_height = self.config_manager.get('window_height', 800)
        self.setGeometry(100, 100, window_width, window_height)
        
        # Initialize search variables
        self.selected_verses = []
        self.current_subject = None
        self.search_history = self.config_manager.get('search_history', [])
        
        # Set up close event handling
        self.setWindowTitle("Bible Search - PyQt6")
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main grid layout for 6 sections
        main_layout = QGridLayout()
        central_widget.setLayout(main_layout)
        
        # Create the 6 sections
        self.create_search_settings_window()
        self.create_messaging_window() 
        self.create_search_results_window()
        self.create_reading_window()
        self.create_subject_verse_window()
        self.create_comments_window()
        
        # Arrange sections in grid layout
        # Row 0: Search Settings (spans 2 columns)
        main_layout.addWidget(self.search_settings_frame, 0, 0, 1, 2)
        
        # Row 1: Messaging window (spans 2 columns, small height)
        main_layout.addWidget(self.messaging_frame, 1, 0, 1, 2)
        
        # Row 2: Search Results and Reading Window
        main_layout.addWidget(self.search_results_frame, 2, 0)
        main_layout.addWidget(self.reading_frame, 2, 1)
        
        # Row 3: Subject Verse and Comments
        main_layout.addWidget(self.subject_verse_frame, 3, 0)
        main_layout.addWidget(self.comments_frame, 3, 1)
        
        # Set row stretches to control heights
        main_layout.setRowStretch(0, 1)  # Search Settings
        main_layout.setRowStretch(1, 0)  # Messaging (minimal height)
        main_layout.setRowStretch(2, 3)  # Search Results & Reading
        main_layout.setRowStretch(3, 2)  # Subject Verse & Comments
        
        # Set column stretches for equal width
        main_layout.setColumnStretch(0, 1)
        main_layout.setColumnStretch(1, 1)
        
    def create_search_settings_window(self):
        """Window 1: Search Settings"""
        self.search_settings_frame = QFrame()
        self.search_settings_frame.setFrameStyle(QFrame.Shape.Box)
        self.search_settings_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("1. Search Settings")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Search controls
        search_layout = QHBoxLayout()
        
        # Search term input with history
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QComboBox()
        self.search_input.setEditable(True)
        self.search_input.lineEdit().setPlaceholderText("Enter search terms...")
        self.search_input.addItems(self.search_history[-10:])  # Last 10 searches
        search_layout.addWidget(self.search_input)
        
        # Load available translations from database
        search_layout.addWidget(QLabel("Translation:"))
        self.translation_combo = QComboBox()
        self.load_translations()
        search_layout.addWidget(self.translation_combo)
        
        # Search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Search options
        options_layout = QHBoxLayout()
        
        # Get search settings from config
        search_settings = self.config_manager.get('search_settings', {})
        
        # Case sensitive
        self.case_sensitive_cb = QCheckBox("Case Sensitive")
        self.case_sensitive_cb.setChecked(search_settings.get('case_sensitive', False))
        options_layout.addWidget(self.case_sensitive_cb)
        
        # Unique verses
        self.unique_verses_cb = QCheckBox("Unique Verses")
        self.unique_verses_cb.setChecked(search_settings.get('unique_verses', False))
        options_layout.addWidget(self.unique_verses_cb)
        
        # Abbreviate results
        self.abbreviate_results_cb = QCheckBox("Abbreviate Results")
        self.abbreviate_results_cb.setChecked(search_settings.get('abbreviate_results', True))
        options_layout.addWidget(self.abbreviate_results_cb)
        
        # Synonyms
        self.synonyms_cb = QCheckBox("Synonyms")
        self.synonyms_cb.setChecked(search_settings.get('synonyms', False))
        options_layout.addWidget(self.synonyms_cb)
        
        layout.addLayout(options_layout)
        
        self.search_settings_frame.setLayout(layout)
        
    def create_messaging_window(self):
        """Window 1: Messaging window for logs and error messages (3 lines high)"""
        self.messaging_frame = QFrame()
        self.messaging_frame.setFrameStyle(QFrame.Shape.Box)
        self.messaging_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        self.messaging_frame.setMaximumHeight(90)  # Expanded to 3 lines
        
        layout = QVBoxLayout()
        
        # Header with title and buttons
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel("1. Message Window")
        title_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        
        # Spacer to push buttons to right
        header_layout.addStretch()
        
        # Button container for vertical stacking
        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(2)
        
        # Gear button
        self.gear_button = QPushButton("⚙")
        self.gear_button.setFixedSize(25, 20)
        self.gear_button.clicked.connect(self.show_gear_menu)
        button_layout.addWidget(self.gear_button)
        
        # Info button below gear button
        self.info_button = QPushButton("i")
        self.info_button.setFixedSize(25, 20)
        self.info_button.clicked.connect(self.show_info_window)
        button_layout.addWidget(self.info_button)
        
        button_container.setLayout(button_layout)
        header_layout.addWidget(button_container)
        
        layout.addLayout(header_layout)
        
        # Message text area (expanded to 3 lines)
        self.message_text = QTextEdit()
        self.message_text.setMaximumHeight(55)  # 3 lines
        self.message_text.setReadOnly(True)
        self.message_text.setStyleSheet("QTextEdit { background-color: #f5f5f5; }")
        self.message_text.setPlainText("Bible Search Program initialized successfully.")
        layout.addWidget(self.message_text)
        
        layout.setContentsMargins(5, 2, 5, 2)
        self.messaging_frame.setLayout(layout)
        
    def create_search_results_window(self):
        """Window 3: Search Results"""
        self.search_results_frame = QFrame()
        self.search_results_frame.setFrameStyle(QFrame.Shape.Box)
        self.search_results_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("3. Search Results")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.itemClicked.connect(self.on_result_selected)
        layout.addWidget(self.results_list)
        
        # Status label
        self.results_status_label = QLabel("No search performed")
        layout.addWidget(self.results_status_label)
        
        self.search_results_frame.setLayout(layout)
        
    def create_reading_window(self):
        """Window 4: Reading Window with scroll functionality"""
        self.reading_frame = QFrame()
        self.reading_frame.setFrameStyle(QFrame.Shape.Box)
        self.reading_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("4. Reading Window")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Scrollable text area
        self.reading_text = QTextEdit()
        self.reading_text.setReadOnly(True)
        self.reading_text.setPlainText("Select a search result to view the verse in context...")
        layout.addWidget(self.reading_text)
        
        self.reading_frame.setLayout(layout)
        
    def create_subject_verse_window(self):
        """Window 5: Subject Verse Window"""
        self.subject_verse_frame = QFrame()
        self.subject_verse_frame.setFrameStyle(QFrame.Shape.Box)
        self.subject_verse_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("5. Subject Verses")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Subject verse list
        self.subject_verse_list = QListWidget()
        layout.addWidget(self.subject_verse_list)
        
        # Add/Remove controls
        controls_layout = QHBoxLayout()
        self.add_subject_button = QPushButton("Add to Subjects")
        self.add_subject_button.clicked.connect(self.add_to_subjects)
        controls_layout.addWidget(self.add_subject_button)
        
        self.remove_subject_button = QPushButton("Remove")
        self.remove_subject_button.clicked.connect(self.remove_from_subjects)
        controls_layout.addWidget(self.remove_subject_button)
        
        layout.addLayout(controls_layout)
        
        self.subject_verse_frame.setLayout(layout)
        
    def create_comments_window(self):
        """Window 6: Comments Window"""
        self.comments_frame = QFrame()
        self.comments_frame.setFrameStyle(QFrame.Shape.Box)
        self.comments_frame.setStyleSheet("QFrame { border: 1px solid gray; }")
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("6. Comments")
        title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Comments text area
        self.comments_text = QTextEdit()
        self.comments_text.setPlaceholderText("Add your comments and notes here...")
        layout.addWidget(self.comments_text)
        
        # Save/Clear controls
        controls_layout = QHBoxLayout()
        self.save_comments_button = QPushButton("Save Comments")
        self.save_comments_button.clicked.connect(self.save_comments)
        controls_layout.addWidget(self.save_comments_button)
        
        self.clear_comments_button = QPushButton("Clear")
        self.clear_comments_button.clicked.connect(self.clear_comments)
        controls_layout.addWidget(self.clear_comments_button)
        
        layout.addLayout(controls_layout)
        
        self.comments_frame.setLayout(layout)
        
    # Event handlers and methods
    def perform_search(self):
        """Handle search button click with real Bible search functionality"""
        search_term = self.search_input.currentText().strip()
        if not search_term:
            self.log_message("Please enter search terms")
            return
            
        # Add to search history
        if search_term not in self.search_history:
            self.search_history.insert(0, search_term)
            self.search_history = self.search_history[:10]  # Keep last 10
            self.config_manager.set('search_history', self.search_history)
            self.config_manager.save_config()
            
        self.log_message(f"Searching for: {search_term}")
        
        # Get search settings
        case_sensitive = self.case_sensitive_cb.isChecked()
        unique_verses = self.unique_verses_cb.isChecked()
        abbreviate_results = self.abbreviate_results_cb.isChecked()
        synonyms = self.synonyms_cb.isChecked()
        
        # Get selected translations
        enabled_translations = self.get_enabled_translations()
        
        try:
            # Perform real search using BibleSearch
            results = self.bible_search.search_verses(
                query=search_term,
                enabled_translations=enabled_translations,
                case_sensitive=case_sensitive,
                unique_verses=unique_verses,
                abbreviate_results=abbreviate_results
            )
            
            # Update results list
            self.results_list.clear()
            result_strings = []
            for result in results:
                if abbreviate_results:
                    result_str = f"{result.book} {result.chapter}:{result.verse} ({result.translation}) - {result.text[:80]}..."
                else:
                    result_str = f"{result.book} {result.chapter}:{result.verse} ({result.translation}) - {result.text}"
                result_strings.append(result_str)
                
            self.results_list.addItems(result_strings)
            self.results_status_label.setText(f"Found {len(results)} results")
            
            if results:
                self.log_message(f"Search completed: {len(results)} results found")
            else:
                self.log_message("No results found")
                
        except Exception as e:
            self.log_message(f"Search error: {str(e)}")
            print(f"Search error details: {e}")
        
    def on_result_selected(self, item):
        """Handle selection of search result"""
        selected_text = item.text()
        self.log_message(f"Selected: {selected_text}")
        
        # Mock reading content
        mock_reading = f"""
Chapter Context for {selected_text}:

This is where the full chapter or passage context would be displayed.
The user can scroll up and down to read more verses around the selected result.

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod 
tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, 
quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
        """
        self.reading_text.setPlainText(mock_reading)
        
    def add_to_subjects(self):
        """Add current verse to subject verses"""
        current_item = self.results_list.currentItem()
        if current_item:
            self.subject_verse_list.addItem(current_item.text())
            self.log_message("Added to subject verses")
        else:
            self.log_message("No verse selected to add")
            
    def remove_from_subjects(self):
        """Remove selected verse from subject verses"""
        current_row = self.subject_verse_list.currentRow()
        if current_row >= 0:
            item = self.subject_verse_list.takeItem(current_row)
            self.log_message(f"Removed: {item.text()}")
        else:
            self.log_message("No subject verse selected to remove")
            
    def save_comments(self):
        """Save comments"""
        self.log_message("Comments saved")
        
    def clear_comments(self):
        """Clear comments"""
        self.comments_text.clear()
        self.log_message("Comments cleared")
        
    def log_message(self, message: str):
        """Log message to the messaging window"""
        current_text = self.message_text.toPlainText()
        if current_text and not current_text.endswith('\n'):
            current_text += '\n'
        new_text = current_text + message
        
        # Keep only last 3 lines (updated from 2)
        lines = new_text.split('\n')
        if len(lines) > 3:
            lines = lines[-3:]
        
        self.message_text.setPlainText('\n'.join(lines))
        
    def show_gear_menu(self):
        """Show gear button menu with options"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.addAction("Translations", self.show_translations)
        menu.addAction("Font", self.show_font_settings)
        menu.addAction("Backup", self.show_backup_settings)
        
        # Show menu at gear button position
        menu.exec(self.gear_button.mapToGlobal(self.gear_button.rect().bottomLeft()))
        
    def show_info_window(self):
        """Show info window"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton
        
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("Information")
        info_dialog.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(info_dialog.accept)
        layout.addWidget(close_button)
        
        info_dialog.setLayout(layout)
        info_dialog.exec()
        
    def show_translations(self):
        """Show translations dialog (placeholder)"""
        self.log_message("Translations dialog would open here")
        
    def show_font_settings(self):
        """Show font settings dialog (placeholder)"""
        self.log_message("Font settings dialog would open here")
        
    def show_backup_settings(self):
        """Show backup settings dialog (placeholder)"""
        self.log_message("Backup settings dialog would open here")
        
    def load_translations(self):
        """Load available translations from database"""
        try:
            # First load translations into BibleSearch object
            self.bible_search.load_translations()
            # translations is a list of Translation objects
            translation_names = [t.abbreviation for t in self.bible_search.translations]
            
            self.translation_combo.clear()
            enabled_translations = self.config_manager.get('enabled_translations', ['KJV'])
            
            for translation in translation_names:
                self.translation_combo.addItem(translation)
                
            # Set default to first enabled translation
            if enabled_translations and enabled_translations[0] in translation_names:
                index = translation_names.index(enabled_translations[0])
                self.translation_combo.setCurrentIndex(index)
            elif translation_names:
                # If no enabled translation found, use first available
                self.translation_combo.setCurrentIndex(0)
                
        except Exception as e:
            print(f"Error loading translations: {e}")
            # Fallback to common translations
            self.translation_combo.addItems(["KJV", "ESV", "NIV", "NASB"])
            if hasattr(self, 'message_text'):
                self.log_message(f"Error loading translations: {e}")
            
    def get_enabled_translations(self):
        """Get list of enabled translations"""
        current_translation = self.translation_combo.currentText()
        if current_translation:
            return [current_translation]
        return self.config_manager.get('enabled_translations', ['KJV'])
        
    def closeEvent(self, event):
        """Handle application close event with proper cleanup"""
        try:
            # Save current window size
            self.config_manager.set('window_width', self.width())
            self.config_manager.set('window_height', self.height())
            
            # Save search settings
            search_settings = {
                'case_sensitive': self.case_sensitive_cb.isChecked(),
                'unique_verses': self.unique_verses_cb.isChecked(),
                'abbreviate_results': self.abbreviate_results_cb.isChecked(),
                'synonyms': self.synonyms_cb.isChecked()
            }
            self.config_manager.set('search_settings', search_settings)
            
            # Save current translation
            current_translation = self.translation_combo.currentText()
            if current_translation:
                self.config_manager.set('enabled_translations', [current_translation])
            
            # Save configuration
            self.config_manager.save_config()
            
        except Exception as e:
            print(f"Error saving config on close: {e}")
        
        # Accept the close event
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application properties for proper shutdown
    app.setQuitOnLastWindowClosed(True)
    
    try:
        window = BibleSearchPyQt6()
        window.show()
        
        # Run the application
        exit_code = app.exec()
        
    except Exception as e:
        print(f"Application error: {e}")
        exit_code = 1
    
    # Ensure clean exit
    sys.exit(exit_code)

if __name__ == "__main__":
    main()