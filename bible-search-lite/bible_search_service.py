#!/usr/bin/env python3
"""
PyQt6 Bible Search Service
Integrates existing BibleSearch with PyQt6 application
"""

from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import List, Dict, Any
import time

# Import your existing search engine
from bible_search import BibleSearch, SearchResult


class SearchSettings:
    """Container for search configuration"""

    def __init__(self):
        self.case_sensitive = False
        self.unique_verses = False
        self.abbreviate_results = False
        self.enabled_translations = ["KJV"]
        self.book_filter = []  # List of book names to filter by (empty = all books)


class SearchWorker(QThread):
    """
    Background thread for search operations to keep UI responsive.
    Emits signals for progress and completion.
    """

    # Signals
    search_started = pyqtSignal()
    search_completed = pyqtSignal(list)  # List of search results
    search_failed = pyqtSignal(str)  # Error message
    progress_update = pyqtSignal(str)  # Progress message

    def __init__(self, bible_search, search_term, settings, parent=None):
        super().__init__(parent)
        self.bible_search = bible_search
        self.search_term = search_term
        self.settings = settings
        
    def run(self):
        """Execute search in background thread"""
        try:
            self.search_started.emit()
            self.progress_update.emit("Searching Bible...")

            start_time = time.time()

            # Use existing BibleSearch for the actual search
            results = self.bible_search.search_verses(
                query=self.search_term,
                enabled_translations=self.settings.enabled_translations,
                case_sensitive=self.settings.case_sensitive,
                unique_verses=self.settings.unique_verses,
                abbreviate_results=self.settings.abbreviate_results,
                book_filter=self.settings.book_filter
            )

            search_time = time.time() - start_time

            # Get metadata from BibleSearch (includes unique verse counts if applicable)
            search_metadata = getattr(self.bible_search, 'last_search_metadata', {})

            # Convert SearchResult objects to dictionaries for compatibility
            results_dicts = []
            for result in results:
                results_dicts.append({
                    'Reference': f"{result.book} {result.chapter}:{result.verse}",
                    'Translation': result.translation,
                    'Text': result.highlighted_text if result.highlighted_text else result.text,
                    'search_time': search_time,
                    'search_term': self.search_term,
                    # Add metadata to each result for access in UI
                    'total_count': search_metadata.get('total_count', len(results_dicts)),
                    'unique_count': search_metadata.get('unique_count'),
                    'unique_verses_enabled': search_metadata.get('unique_verses_enabled', False)
                })

            self.progress_update.emit(f"Found {len(results_dicts)} results in {search_time:.2f}s")
            self.search_completed.emit(results_dicts)

        except Exception as e:
            self.search_failed.emit(str(e))


class BibleSearchService(QObject):
    """
    Main search service for PyQt6 application.
    Coordinates search operations and manages search history.
    """

    # Signals
    search_completed = pyqtSignal(list)  # Search results
    search_failed = pyqtSignal(str)  # Error message
    search_progress = pyqtSignal(str)  # Progress updates

    def __init__(self, database_path=None, parent=None):
        super().__init__(parent)

        # Initialize BibleSearch
        self.bible_search = BibleSearch(database_path)

        # Search history
        self.search_history = []
        self.max_history = 50

        # Current search worker
        self.current_worker = None
        
    def search(self, search_term: str, settings: SearchSettings):
        """
        Initiate a search operation.

        Args:
            search_term: The term/phrase to search for
            settings: SearchSettings object with search parameters
        """
        # Cancel any existing search
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.terminate()
            self.current_worker.wait()

        # Add to search history
        self._add_to_history(search_term)

        # Create and start search worker
        self.current_worker = SearchWorker(self.bible_search, search_term, settings)
        self.current_worker.search_completed.connect(self._on_search_completed)
        self.current_worker.search_failed.connect(self._on_search_failed)
        self.current_worker.progress_update.connect(self.search_progress.emit)

        self.current_worker.start()
    
    def _on_search_completed(self, results):
        """Handle search completion"""
        self.search_completed.emit(results)
    
    def _on_search_failed(self, error_message):
        """Handle search failure"""
        self.search_failed.emit(error_message)
    
    def _add_to_history(self, search_term: str):
        """Add search to history"""
        # Remove if already exists
        if search_term in self.search_history:
            self.search_history.remove(search_term)

        # Add to beginning
        self.search_history.insert(0, search_term)

        # Limit size
        if len(self.search_history) > self.max_history:
            self.search_history = self.search_history[:self.max_history]
    
    def get_search_history(self) -> List[str]:
        """Get search history list"""
        return self.search_history.copy()
    
    def clear_history(self):
        """Clear search history"""
        self.search_history.clear()
    
    def format_verse_for_display(self, verse_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Format a verse for display in PyQt6 widgets.

        Args:
            verse_data: Dictionary with Reference, Translation, Text

        Returns:
            Dictionary with formatted components for display
        """
        reference = verse_data['Reference']
        translation = verse_data['Translation']
        text = verse_data['Text']

        # Parse reference into components
        parts = reference.split()
        if len(parts) >= 2:
            # Handle books with numbers (e.g., "1 Samuel")
            if parts[0].isdigit():
                book_full = f"{parts[0]} {parts[1]}"
                chapter_verse = parts[2] if len(parts) > 2 else ""
            else:
                book_full = parts[0]
                chapter_verse = parts[1] if len(parts) > 1 else ""

            # Get 3-letter book abbreviation
            book_abbrev = self._get_book_abbreviation(book_full)

            # Parse chapter:verse
            if ':' in chapter_verse:
                chapter, verse = chapter_verse.split(':', 1)
            else:
                chapter = chapter_verse
                verse = "1"
        else:
            book_abbrev = "Unk"
            chapter = "1"
            verse = "1"

        return {
            'translation': translation,
            'book_abbrev': book_abbrev,
            'chapter': chapter,
            'verse': verse,
            'text': text
        }
    
    def _get_book_abbreviation(self, book_name: str) -> str:
        """Convert full book name to 3-letter abbreviation"""
        abbreviations = {
            'Genesis': 'Gen', 'Exodus': 'Exo', 'Leviticus': 'Lev', 'Numbers': 'Num', 
            'Deuteronomy': 'Deu', 'Joshua': 'Jos', 'Judges': 'Jdg', 'Ruth': 'Rut',
            '1 Samuel': '1Sa', '2 Samuel': '2Sa', '1 Kings': '1Ki', '2 Kings': '2Ki',
            '1 Chronicles': '1Ch', '2 Chronicles': '2Ch', 'Ezra': 'Ezr', 'Nehemiah': 'Neh',
            'Esther': 'Est', 'Job': 'Job', 'Psalm': 'Psa', 'Psalms': 'Psa', 'Proverbs': 'Pro',
            'Ecclesiastes': 'Ecc', 'Song': 'Son', 'Song of Songs': 'Son', 'Isaiah': 'Isa',
            'Jeremiah': 'Jer', 'Lamentations': 'Lam', 'Ezekiel': 'Eze', 'Daniel': 'Dan',
            'Hosea': 'Hos', 'Joel': 'Joe', 'Amos': 'Amo', 'Obadiah': 'Oba', 'Jonah': 'Jon',
            'Micah': 'Mic', 'Nahum': 'Nah', 'Habakkuk': 'Hab', 'Zephaniah': 'Zep',
            'Haggai': 'Hag', 'Zechariah': 'Zec', 'Malachi': 'Mal',
            'Matthew': 'Mat', 'Mark': 'Mar', 'Luke': 'Luk', 'John': 'Joh', 'Acts': 'Act',
            'Romans': 'Rom', '1 Corinthians': '1Co', '2 Corinthians': '2Co', 'Galatians': 'Gal',
            'Ephesians': 'Eph', 'Philippians': 'Phi', 'Colossians': 'Col', 
            '1 Thessalonians': '1Th', '2 Thessalonians': '2Th', '1 Timothy': '1Ti',
            '2 Timothy': '2Ti', 'Titus': 'Tit', 'Philemon': 'Phm', 'Hebrews': 'Heb',
            'James': 'Jam', '1 Peter': '1Pe', '2 Peter': '2Pe', '1 John': '1Jo',
            '2 John': '2Jo', '3 John': '3Jo', 'Jude': 'Jud', 'Revelation': 'Rev'
        }
        
        return abbreviations.get(book_name, book_name[:3].capitalize())


# Example integration with PyQt6 application
class SearchIntegrationExample:
    """
    Example of how to integrate BibleSearchService into PyQt6 application
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
        
        # Create search service
        self.search_service = BibleSearchService("database/bibles.db")
        
        # Connect signals
        self.search_service.search_completed.connect(self.on_search_completed)
        self.search_service.search_failed.connect(self.on_search_failed)
        self.search_service.search_progress.connect(self.on_search_progress)
    
    def perform_search(self, search_term):
        """Trigger a search"""
        # Create search settings from UI
        settings = SearchSettings()
        settings.ignore_case = True  # Get from checkbox
        settings.unique_only = False  # Get from checkbox
        settings.selected_translations = ["KJV", "NIV"]  # Get from UI
        settings.search_mode = "word"  # Get from radio buttons
        
        # Start search
        self.search_service.search(search_term, settings)
    
    def on_search_completed(self, results):
        """Handle search results"""
        # Clear existing results
        self.main_window.verse_lists['search'].clear_verses()
        
        # Add results to UI
        for result in results:
            formatted = self.search_service.format_verse_for_display(result)
            
            # Create unique verse ID
            verse_id = f"search_{result['Reference']}_{result['Translation']}"
            
            # Add to verse list widget
            self.main_window.verse_lists['search'].add_verse(
                verse_id,
                formatted['translation'],
                formatted['book_abbrev'],
                int(formatted['chapter']),
                int(formatted['verse']),
                formatted['text']
            )
        
        # Update status
        unique_count = len(set(r['Reference'] for r in results))
        print(f"Search complete: {len(results)} results, {unique_count} unique verses")
    
    def on_search_failed(self, error_message):
        """Handle search failure"""
        print(f"Search failed: {error_message}")
    
    def on_search_progress(self, message):
        """Handle search progress updates"""
        print(f"Search progress: {message}")