"""
Search controller for Bible Search application.

This module handles all search operations and result management:
- Executing searches via BibleSearchService
- Formatting search results for display
- Managing lazy loading of large result sets
- Loading context verses for reading window

Author: Andrew Hopkins
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Any, Optional
from bible_search import BibleSearch
from bible_search_service import BibleSearchService, SearchSettings


class FormattedVerse:
    """
    Container for a formatted verse ready for display.
    
    Attributes:
        verse_id (str): Unique identifier for the verse
        translation (str): Translation abbreviation (e.g., 'KJV')
        book_abbrev (str): 3-letter book abbreviation (e.g., 'Gen')
        chapter (int): Chapter number
        verse (int): Verse number
        text (str): Verse text content
    """
    
    def __init__(self, verse_id: str, translation: str, book_abbrev: str, 
                 chapter: int, verse: int, text: str):
        self.verse_id = verse_id
        self.translation = translation
        self.book_abbrev = book_abbrev
        self.chapter = chapter
        self.verse = verse
        self.text = text


class SearchController(QObject):
    """
    Controls all search operations and result management.
    
    This controller separates search business logic from UI concerns.
    It handles search execution, result parsing, lazy loading, and
    context loading while emitting signals for UI updates.
    
    Signals:
        search_results_ready: Emitted with initial batch of formatted verses
        search_more_results_ready: Emitted when lazy loading provides more verses
        search_failed: Emitted with error message on search failure
        search_progress: Emitted with progress message during search
        context_verses_ready: Emitted with context verses for reading window
        search_status: Emitted with status messages (count, time, etc.)
        
    Example:
        >>> controller = SearchController()
        >>> controller.search_results_ready.connect(on_results)
        >>> controller.search("love", case_sensitive=False, 
        ...                   translations=['KJV', 'NIV'])
    """
    
    # Signals
    search_results_ready = pyqtSignal(list, dict)  # (verses, metadata)
    search_more_results_ready = pyqtSignal(list, dict)  # (verses, metadata)
    search_failed = pyqtSignal(str)  # error_message
    search_progress = pyqtSignal(str)  # progress_message
    context_verses_ready = pyqtSignal(list)  # verses for reading window
    search_status = pyqtSignal(str)  # status message for UI
    
    def __init__(self, parent=None):
        """
        Initialize the search controller.
        
        Args:
            parent (QObject, optional): Parent QObject for Qt parenting.
            
        Side Effects:
            - Creates BibleSearch instance for context loading
            - Creates BibleSearchService instance for searches
            - Connects search service signals to handler methods
        """
        super().__init__(parent)
        
        # Search services
        self.bible_search = BibleSearch()
        self.search_service = BibleSearchService()
        
        # Connect search service signals
        self.search_service.search_completed.connect(self._on_service_search_completed)
        self.search_service.search_failed.connect(self._on_service_search_failed)
        self.search_service.search_progress.connect(self._on_service_search_progress)
        
        # Search state for lazy loading
        self.all_search_results = []
        self.loaded_results_count = 0
        self.batch_size = 100
        
    def search(self, search_term: str, case_sensitive: bool = False,
               unique_verses: bool = False, abbreviate_results: bool = False,
               translations: Optional[List[str]] = None, book_filter: Optional[List[str]] = None):
        """
        Execute a Bible search with specified parameters.

        Args:
            search_term (str): The search query (word, phrase, or verse reference)
            case_sensitive (bool): Whether search should be case-sensitive
            unique_verses (bool): Whether to show only unique verses (one translation)
            abbreviate_results (bool): Whether to abbreviate common words
            translations (list, optional): List of translation abbreviations to search.
                Defaults to ['KJV'] if not provided.
            book_filter (list, optional): List of book names to restrict search to.
                Empty list or None means search all books.

        Side Effects:
            - Initiates background search via BibleSearchService
            - Resets search state for new search
            - Will eventually emit search_results_ready or search_failed signal

        Example:
            >>> controller.search("faith hope love",
            ...                   case_sensitive=False,
            ...                   translations=['KJV', 'NIV', 'ESV'],
            ...                   book_filter=['Matthew', 'Mark', 'Luke', 'John'])
        """
        if not search_term or not search_term.strip():
            self.search_status.emit("Please enter search terms")
            return

        # Reset search state
        self.all_search_results = []
        self.loaded_results_count = 0

        # Create search settings
        settings = SearchSettings()
        settings.case_sensitive = case_sensitive
        settings.unique_verses = unique_verses
        settings.abbreviate_results = abbreviate_results
        settings.enabled_translations = translations or ['KJV']
        settings.book_filter = book_filter or []

        # Start search (will emit signals when complete)
        self.search_service.search(search_term, settings)
        
    def load_more_results(self, scroll_value: int, scroll_maximum: int):
        """
        Load next batch of search results (lazy loading).
        
        Called when user scrolls near bottom of search results. Checks if
        more results are available and loads the next batch if scroll position
        indicates user wants more.
        
        Args:
            scroll_value (int): Current scroll bar value
            scroll_maximum (int): Maximum scroll bar value
            
        Side Effects:
            - May emit search_more_results_ready with next batch
            - Updates loaded_results_count
            - Emits search_status with loading progress
            
        Example:
            >>> # Connect to scroll bar
            >>> scroll_bar.valueChanged.connect(
            ...     lambda v: controller.load_more_results(v, scroll_bar.maximum())
            ... )
        """
        # Check if scrolled near bottom (within 80% of max)
        if scroll_value <= scroll_maximum * 0.8:
            return
            
        # Check if there are more results to load
        if self.loaded_results_count >= len(self.all_search_results):
            return
            
        # Load next batch
        start_index = self.loaded_results_count
        end_index = min(start_index + self.batch_size, len(self.all_search_results))
        next_batch_raw = self.all_search_results[start_index:end_index]
        
        # Format the batch
        next_batch = []
        for i, result in enumerate(next_batch_raw):
            verse_id = f"search_{start_index + i}"
            formatted = self._format_search_result(result, verse_id)
            if formatted:
                next_batch.append(formatted)
        
        self.loaded_results_count = end_index
        
        # Prepare metadata
        total_results = len(self.all_search_results)
        search_term = self.all_search_results[0].get('search_term', '') if self.all_search_results else ''
        
        metadata = {
            'loaded_count': self.loaded_results_count,
            'total_count': total_results,
            'search_term': search_term,
            'has_more': self.loaded_results_count < total_results
        }
        
        # Emit signal with formatted verses
        self.search_more_results_ready.emit(next_batch, metadata)
        
        # Update status
        if self.loaded_results_count < total_results:
            self.search_status.emit(
                f"({search_term}) Loaded {self.loaded_results_count} of {total_results} results - scroll down for more"
            )
        else:
            self.search_status.emit(
                f"({search_term}) All {total_results} results loaded"
            )
            
    def load_context(self, translation: str, book: str, chapter: int, 
                    start_verse: int, num_verses: int = 50):
        """
        Load context verses for reading window.
        
        Loads continuous verses starting from a specific reference, crossing
        chapter boundaries if needed. Used when user clicks a verse to see
        surrounding context.
        
        Args:
            translation (str): Translation abbreviation (e.g., 'KJV')
            book (str): Book abbreviation (e.g., 'Gen')
            chapter (int): Chapter number
            start_verse (int): Starting verse number
            num_verses (int): Number of verses to load (default 50)
            
        Side Effects:
            - Emits context_verses_ready with formatted verses
            - First verse in list will be the clicked verse
            
        Example:
            >>> # User clicked John 3:16
            >>> controller.load_context('KJV', 'Joh', 3, 16, num_verses=50)
        """
        try:
            continuous_verses = self.bible_search.get_continuous_reading_cross_chapter(
                translation=translation,
                book=book,
                chapter=chapter,
                start_verse=start_verse,
                num_verses=num_verses
            )
            
            # Format verses for display
            formatted_verses = []
            for i, verse in enumerate(continuous_verses):
                verse_id = f"reading_{i}"
                formatted = FormattedVerse(
                    verse_id=verse_id,
                    translation=verse.translation,
                    book_abbrev=verse.book,
                    chapter=verse.chapter,
                    verse=verse.verse,
                    text=verse.text
                )
                formatted_verses.append(formatted)
            
            # Emit signal with formatted verses
            self.context_verses_ready.emit(formatted_verses)
            
        except Exception as e:
            print(f"Error loading context verses: {e}")
            import traceback
            traceback.print_exc()
            self.search_failed.emit(f"Failed to load context: {str(e)}")
            
    def _on_service_search_completed(self, results: List[Dict[str, Any]]):
        """
        Handle search completion from BibleSearchService.
        
        Internal handler that processes raw search results, formats them,
        and emits appropriate signals.
        
        Args:
            results (list): Raw search results from BibleSearchService
        """
        print(f"Search completed with {len(results)} results")
        
        # Store all results for lazy loading
        self.all_search_results = results
        self.loaded_results_count = 0
        
        if not results:
            self.search_status.emit("No results found")
            self.search_results_ready.emit([], {
                'loaded_count': 0,
                'total_count': 0,
                'search_term': '',
                'has_more': False
            })
            return
        
        # Load initial batch
        initial_batch_raw = results[:self.batch_size]
        
        # Format initial batch
        initial_batch = []
        for i, result in enumerate(initial_batch_raw):
            verse_id = f"search_{i}"
            formatted = self._format_search_result(result, verse_id)
            if formatted:
                initial_batch.append(formatted)
        
        self.loaded_results_count = len(initial_batch)
        
        # Prepare metadata
        total_results = len(results)
        search_time = results[0].get('search_time', 0) if results else 0
        search_term = results[0].get('search_term', '') if results else ''

        # Extract unique verse metadata if available
        unique_verses_enabled = results[0].get('unique_verses_enabled', False) if results else False
        total_before_filter = results[0].get('total_count', total_results) if results else 0
        unique_count = results[0].get('unique_count', total_results) if results else 0

        metadata = {
            'loaded_count': self.loaded_results_count,
            'total_count': total_results,
            'search_time': search_time,
            'search_term': search_term,
            'has_more': total_results > self.batch_size,
            'unique_verses_enabled': unique_verses_enabled,
            'total_before_filter': total_before_filter,
            'unique_count': unique_count
        }

        # Emit signal with formatted verses
        self.search_results_ready.emit(initial_batch, metadata)

        # Build status message
        if unique_verses_enabled and unique_count is not None:
            # Show both total and unique counts
            if total_results > self.batch_size:
                status_msg = f"({search_term}) Loaded {self.loaded_results_count} of {total_results} results ({total_before_filter} total, {unique_count} unique) in {search_time:.2f}s - scroll down for more"
            else:
                status_msg = f"({search_term}) Search completed: {total_before_filter} total, {unique_count} unique results in {search_time:.2f}s"
        else:
            # Normal message without unique count
            if total_results > self.batch_size:
                status_msg = f"({search_term}) Loaded {self.loaded_results_count} of {total_results} results in {search_time:.2f}s - scroll down for more"
            else:
                status_msg = f"({search_term}) Search completed: {total_results} results found in {search_time:.2f}s"

        self.search_status.emit(status_msg)
            
    def _on_service_search_failed(self, error_message: str):
        """Handle search failure from BibleSearchService"""
        self.search_failed.emit(error_message)
        self.search_status.emit(f"Search error: {error_message}")
        
    def _on_service_search_progress(self, message: str):
        """Handle search progress from BibleSearchService"""
        self.search_progress.emit(message)
        self.search_status.emit(message)
        
    def _format_search_result(self, result: Dict[str, Any], verse_id: str) -> Optional[FormattedVerse]:
        """
        Format a raw search result into a FormattedVerse object.
        
        Parses the reference string and extracts components for display.
        
        Args:
            result (dict): Raw search result with 'Translation', 'Reference', 'Text'
            verse_id (str): Unique ID for this verse
            
        Returns:
            FormattedVerse or None if parsing fails
        """
        try:
            translation = result['Translation']
            reference = result['Reference']
            text = result['Text']
            
            # Parse reference to get book, chapter, verse
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
            
            return FormattedVerse(
                verse_id=verse_id,
                translation=translation,
                book_abbrev=book_abbrev,
                chapter=chapter,
                verse=verse,
                text=text
            )
            
        except Exception as e:
            print(f"Error formatting result: {e}")
            return None
