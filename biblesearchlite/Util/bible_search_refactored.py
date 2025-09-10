#!/usr/bin/env python3
"""
Refactored Python version of BibleSearch4.ps1 - AI-Assisted Bible Search Program with SQLite
Split into separate classes for better maintainability
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import sqlite3
import json
import logging
import re
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from itertools import permutations

from database_manager import DatabaseManager
from search_engine import SearchEngine
from config_manager import ConfigManager


class BibleSearchApp:
    def __init__(self):
        self.root = tk.Tk()
        self.config_path = "BibleSearchConfig.json"
        self.sqlite_db_path = "Bibles_cleaned.db"
        self.log_path = "BibleSearch.log"
        
        self.setup_logging()
        self.log_message("Application starting")
        
        # Initialize managers
        self.db_manager = DatabaseManager(self.sqlite_db_path)
        self.search_engine = SearchEngine(self.db_manager)
        self.config_manager = ConfigManager(self.config_path)
        
        # Initialize current search results and subject system
        self.current_results = []
        self.selected_search_results = []
        self.current_subject = None
        self.subject_verses = []
        self.selected_subject_verses = []
        
        # Initialize message history early
        self.message_history = ["Ready"]  # Store last 10 messages
        
        # Initialize Bible scrolling position
        self.current_bible_position = 1  # Start at Genesis 1:1
        self.bible_verses_per_view = 20  # Number of verses to show at once
        self.editing_mode = False
        
        # Placeholder functionality
        self.placeholder_active = True
        self.word_search_placeholder = 'love AND peace'
        self.verse_search_placeholder = 'John 3:16, Rom 8:28'
        self.subject_placeholder_active = True
        self.subject_placeholder = 'Subject'
        
        self.init_book_abbreviations()
        self.setup_ui()
        self.load_config()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def log_message(self, message: str):
        """Log a message with timestamp"""
        self.logger.info(message)
    
    def init_book_abbreviations(self):
        """Initialize Bible book abbreviations mapping"""
        self.book_abbreviations = {
            # Full names to abbreviations
            'Genesis': 'Gen', 'Exodus': 'Exo', 'Leviticus': 'Lev', 'Numbers': 'Num', 'Deuteronomy': 'Deu',
            'Joshua': 'Jos', 'Judges': 'Jdg', 'Ruth': 'Rut', '1 Samuel': '1Sa', '2 Samuel': '2Sa',
            '1 Kings': '1Ki', '2 Kings': '2Ki', '1 Chronicles': '1Ch', '2 Chronicles': '2Ch',
            'Ezra': 'Ezr', 'Nehemiah': 'Neh', 'Esther': 'Est', 'Job': 'Job', 'Psalms': 'Psa',
            'Psalm': 'Psa', 'Proverbs': 'Pro', 'Ecclesiastes': 'Ecc', 'Song of Songs': 'Son',
            'Song': 'Son', 'Isaiah': 'Isa', 'Jeremiah': 'Jer', 'Lamentations': 'Lam',
            'Ezekiel': 'Eze', 'Daniel': 'Dan', 'Hosea': 'Hos', 'Joel': 'Joe', 'Amos': 'Amo',
            'Obadiah': 'Oba', 'Jonah': 'Jon', 'Micah': 'Mic', 'Nahum': 'Nah', 'Habakkuk': 'Hab',
            'Zephaniah': 'Zep', 'Haggai': 'Hag', 'Zechariah': 'Zec', 'Malachi': 'Mal',
            'Matthew': 'Mat', 'Mark': 'Mar', 'Luke': 'Luk', 'John': 'Joh', 'Acts': 'Act',
            'Romans': 'Rom', '1 Corinthians': '1Co', '2 Corinthians': '2Co', 'Galatians': 'Gal',
            'Ephesians': 'Eph', 'Philippians': 'Phi', 'Colossians': 'Col', '1 Thessalonians': '1Th',
            '2 Thessalonians': '2Th', '1 Timothy': '1Ti', '2 Timothy': '2Ti', 'Titus': 'Tit',
            'Philemon': 'Phm', 'Hebrews': 'Heb', 'James': 'Jam', '1 Peter': '1Pe', '2 Peter': '2Pe',
            '1 John': '1Jo', '2 John': '2Jo', '3 John': '3Jo', 'Jude': 'Jud', 'Revelation': 'Rev'
        }
        
        # Common abbreviations mapping to full names
        self.abbreviation_to_full = {v: k for k, v in self.book_abbreviations.items()}
        
        # Additional common abbreviations
        common_abbrevs = {
            'Gen': 'Genesis', 'Ex': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deut': 'Deuteronomy',
            'Josh': 'Joshua', 'Judg': 'Judges', '1Sam': '1 Samuel', '2Sam': '2 Samuel',
            '1Kgs': '1 Kings', '2Kgs': '2 Kings', '1Chr': '1 Chronicles', '2Chr': '2 Chronicles',
            'Ps': 'Psalms', 'Prov': 'Proverbs', 'Eccl': 'Ecclesiastes', 'SS': 'Song of Songs',
            'Isa': 'Isaiah', 'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Ezek': 'Ezekiel',
            'Dan': 'Daniel', 'Hos': 'Hosea', 'Joel': 'Joel', 'Amos': 'Amos', 'Obad': 'Obadiah',
            'Jonah': 'Jonah', 'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk',
            'Zeph': 'Zephaniah', 'Hag': 'Haggai', 'Zech': 'Zechariah', 'Mal': 'Malachi',
            'Matt': 'Matthew', 'Mk': 'Mark', 'Lk': 'Luke', 'Jn': 'John',
            'Rom': 'Romans', '1Cor': '1 Corinthians', '2Cor': '2 Corinthians', 'Gal': 'Galatians',
            'Eph': 'Ephesians', 'Phil': 'Philippians', 'Col': 'Colossians',
            '1Thess': '1 Thessalonians', '2Thess': '2 Thessalonians',
            '1Tim': '1 Timothy', '2Tim': '2 Timothy', 'Tit': 'Titus', 'Phlm': 'Philemon',
            'Heb': 'Hebrews', 'Jas': 'James', '1Pet': '1 Peter', '2Pet': '2 Peter',
            '1Jn': '1 John', '2Jn': '2 John', '3Jn': '3 John', 'Rev': 'Revelation'
        }
        
        self.abbreviation_to_full.update(common_abbrevs)
    
    def load_config(self):
        """Load configuration using ConfigManager"""
        config = self.config_manager.load_config()
        
        # Apply configuration to UI variables
        self.search_box['values'] = config.get('SearchHistory', [])
        
        # Set boolean variables
        self.ignore_case_var.set(config.get('IgnoreCase', False))
        self.unique_only_var.set(config.get('UniqueOnly', False))
        self.abbreviate_var.set(config.get('Abbreviate', False))
        self.bible_scope_var.set(config.get('BibleScope', 'bible'))
        
        # Set numeric variables
        self.proximity_var.set(config.get('ProximityWindow', 5))
        self.main_font_size_var.set(config.get('MainFontSize', 10))
        self.other_font_size_var.set(config.get('OtherFontSize', 9))
        self.chapter_var.set(config.get('Chapter', 0))
        
        # Set selection variables
        self.book_var.set(config.get('Book', 'All'))
        self.translation_var.set(config.get('Translation', 'All') if config.get('Translation') else "All")
        
        # Load translation selections
        selected_translations = config.get('SelectedTranslations', {})
        for code, selected in selected_translations.items():
            if code in self.translation_vars:
                self.translation_vars[code].set(selected)
        
        # Load translation order
        translation_order = config.get('TranslationOrder', {})
        for code, order in translation_order.items():
            if code in self.translation_order_vars:
                self.translation_order_vars[code].set(order)
        
        # Update search engine translation order
        self.search_engine.translation_order.update(translation_order)
        
        # Load window heights
        self.search_height_var.set(config.get('SearchHeight', 10))
        self.verse_height_var.set(config.get('VerseHeight', 15))
        self.subject_height_var.set(config.get('SubjectHeight', 10))
        self.comments_height_var.set(config.get('CommentsHeight', 5))
        
        # Restore window geometry
        window_geometry = config.get('WindowGeometry')
        if window_geometry:
            try:
                self.root.geometry(window_geometry)
                self.log_message(f"Restored window geometry: {window_geometry}")
            except Exception as e:
                self.log_message(f"Error restoring window geometry: {e}")
        
        # Update UI after loading configuration
        if hasattr(self, 'results_tree'):
            self.update_search_height()
        if hasattr(self, 'verse_display_text'):
            self.update_verse_height()
        if hasattr(self, 'subject_tree'):
            self.update_subject_height()
        if hasattr(self, 'comments_text'):
            self.update_comments_height()
        
        self.update_font_size()
        self.log_message("Configuration loaded successfully")
    
    def save_config(self):
        """Save configuration using ConfigManager"""
        config = {
            'SearchHistory': list(self.search_box['values']),
            'IgnoreCase': self.ignore_case_var.get(),
            'UniqueOnly': self.unique_only_var.get(),
            'Abbreviate': self.abbreviate_var.get(),
            'BibleScope': self.bible_scope_var.get(),
            'ProximityWindow': self.proximity_var.get(),
            'MainFontSize': self.main_font_size_var.get(),
            'OtherFontSize': self.other_font_size_var.get(),
            'Book': self.book_var.get(),
            'Chapter': self.chapter_var.get(),
            'Translation': self.translation_var.get() if self.translation_var.get() != "All" else "",
            'SelectedTranslations': {code: var.get() for code, var in self.translation_vars.items()},
            'TranslationOrder': {code: var.get() for code, var in self.translation_order_vars.items()},
            'SearchHeight': self.search_height_var.get(),
            'VerseHeight': self.verse_height_var.get(),
            'SubjectHeight': self.subject_height_var.get(),
            'CommentsHeight': self.comments_height_var.get(),
            'WindowGeometry': self.root.geometry()
        }
        
        success = self.config_manager.save_config(config)
        if success:
            self.log_message("Configuration saved successfully")
        else:
            self.log_message("Error saving configuration")
    
    def add_search_history(self, term: str):
        """Add search term to history using ConfigManager"""
        if not term:
            return
        
        search_mode = self.search_mode_var.get()
        current_history = list(self.search_box['values'])
        updated_history = self.config_manager.update_search_history(current_history, term, search_mode)
        self.search_box['values'] = updated_history
    
    def get_selected_translations(self):
        """Get list of selected translations"""
        selected = [code for code, var in self.translation_vars.items() if var.get()]
        if not selected:
            selected = ["KJV"]  # Default fallback
        
        # Sort by order preference
        if self.translation_order_vars:
            selected.sort(key=lambda code: self.translation_order_vars[code].get())
        else:
            selected.sort(key=lambda code: self.search_engine.translation_order.get(code, 999))
        
        return selected
    
    def get_old_testament_books(self):
        """Return list of Old Testament books"""
        return [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
            "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
            "Psalms", "Psalm", "Proverbs", "Ecclesiastes", "Song of Songs", "Song",
            "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
            "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk",
            "Zephaniah", "Haggai", "Zechariah", "Malachi"
        ]
    
    def get_new_testament_books(self):
        """Return list of New Testament books"""
        return [
            "Matthew", "Mark", "Luke", "John", "Acts",
            "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
            "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
            "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
            "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
        ]
    
    def perform_search(self):
        """Perform search using SearchEngine"""
        search_term = self.search_box.get().strip()
        if not search_term or self.placeholder_active:
            self.show_message("Please enter a search term")
            return
        
        # Add to search history
        self.add_search_history(search_term)
        
        # Get search parameters
        selected_translations = self.get_selected_translations()
        ignore_case = self.ignore_case_var.get()
        proximity_window = self.proximity_var.get()
        book = self.book_var.get()
        chapter = self.chapter_var.get()
        bible_scope = self.bible_scope_var.get()
        
        start_time = time.time()
        
        try:
            # Use SearchEngine for the search
            results = self.search_engine.search_bible(
                search_term=search_term,
                selected_translations=selected_translations,
                ignore_case=ignore_case,
                proximity_window=proximity_window,
                book=book,
                chapter=chapter,
                bible_scope=bible_scope,
                old_testament_books=self.get_old_testament_books(),
                new_testament_books=self.get_new_testament_books()
            )
            
            # Store current results
            self.current_results = results
            
            # Update UI with results
            self.display_search_results(results)
            
            search_time = time.time() - start_time
            result_count = len(results)
            self.show_message(f"Found {result_count} results in {search_time:.2f} seconds")
            
        except Exception as e:
            self.log_message(f"Search error: {e}")
            self.show_message(f"Search error: {e}")
    
    def display_search_results(self, results):
        """Display search results in the tree view"""
        # Clear existing results
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # Add new results
        for result in results:
            self.results_tree.insert('', 'end', values=[
                result['Reference'],
                result['Translation'],
                result['Text']
            ])
        
        self.update_search_selection_buttons()
    
    # UI Setup methods would continue here...
    # For brevity, I'm including just the key refactored methods
    # The rest of the UI setup code would remain largely the same
    
    def setup_ui(self):
        """Setup the user interface - simplified version for demonstration"""
        self.root.title("Bible Search - Refactored Version")
        self.root.geometry("1000x700")
        
        # Initialize UI variables
        self.search_mode_var = tk.StringVar(value="word")
        self.ignore_case_var = tk.BooleanVar()
        self.unique_only_var = tk.BooleanVar()
        self.abbreviate_var = tk.BooleanVar()
        self.bible_scope_var = tk.StringVar(value="bible")
        self.proximity_var = tk.IntVar(value=5)
        self.main_font_size_var = tk.IntVar(value=10)
        self.other_font_size_var = tk.IntVar(value=9)
        self.book_var = tk.StringVar(value="All")
        self.chapter_var = tk.IntVar(value=0)
        self.translation_var = tk.StringVar(value="All")
        
        # Translation variables
        self.translation_vars = {}
        self.translation_order_vars = {}
        
        translation_codes = ["KJV", "ASV", "DRB", "DBT", "ERV", "WBT", "WEB", "YLT", "AKJV", "WNT"]
        for i, code in enumerate(translation_codes):
            self.translation_vars[code] = tk.BooleanVar(value=(code == "KJV"))
            self.translation_order_vars[code] = tk.IntVar(value=i+1)
        
        # Height variables
        self.search_height_var = tk.IntVar(value=10)
        self.verse_height_var = tk.IntVar(value=15)
        self.subject_height_var = tk.IntVar(value=10)
        self.comments_height_var = tk.IntVar(value=5)
        
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Search frame
        search_frame = ttk.LabelFrame(main_frame, text="Search")
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Search box
        self.search_box = ttk.Combobox(search_frame, width=50)
        self.search_box.pack(side=tk.LEFT, padx=(5, 0))
        
        # Search button
        search_button = ttk.Button(search_frame, text="Search", command=self.perform_search)
        search_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Results frame
        results_frame = ttk.LabelFrame(main_frame, text="Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Results tree
        columns = ('Reference', 'Translation', 'Text')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.results_tree.heading(col, text=col)
            self.results_tree.column(col, width=200)
        
        self.results_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
    
    def show_message(self, message):
        """Show message in status bar"""
        self.status_label.config(text=message)
        self.log_message(message)
    
    def update_font_size(self):
        """Update font sizes - placeholder method"""
        pass
    
    def update_search_height(self):
        """Update search results height - placeholder method"""
        pass
    
    def update_verse_height(self):
        """Update verse display height - placeholder method"""
        pass
    
    def update_subject_height(self):
        """Update subject tree height - placeholder method"""
        pass
    
    def update_comments_height(self):
        """Update comments area height - placeholder method"""
        pass
    
    def update_search_selection_buttons(self):
        """Update search selection buttons - placeholder method"""
        pass
    
    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except Exception as e:
            self.log_message(f"Application error: {e}")
            messagebox.showerror("Error", f"Application error: {e}")
    
    def on_closing(self):
        """Handle application closing"""
        self.save_config()
        self.root.destroy()


if __name__ == "__main__":
    app = BibleSearchApp()
    app.run()