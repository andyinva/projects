#!/usr/bin/env python3
"""
Python version of BibleSearch4.ps1 - AI-Assisted Bible Search Program with SQLite
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
        self.sqlite_db_path = "bibles.db"
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
        self.current_bible_translation = "KJV"  # Default translation for Bible Reading View
        
        # Placeholder functionality
        self.placeholder_active = True
        self.word_search_placeholder = 'love AND peace'
        self.verse_search_placeholder = 'John 3:16, Rom 8:28'
        self.subject_placeholder_active = True
        self.subject_placeholder = 'Subject'
        
        self.init_book_abbreviations()
        self.setup_ui()
        self.load_config()
        
        # Ensure Word Search radio button is selected at startup
        self.search_mode_var.set("word")
        self.update_search_placeholder()
        
        # Update Bible Reading View label with default translation
        self.update_bible_reading_view_label(self.current_bible_translation)
        
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
            '1 Kings': '1Ki', '2 Kings': '2Ki', '1 Chronicles': '1Ch', '2 Chronicles': '2Ch', 'Ezra': 'Ezr',
            'Nehemiah': 'Neh', 'Esther': 'Est', 'Job': 'Job', 'Psalm': 'Psa', 'Proverbs': 'Pro',
            'Ecclesiastes': 'Ecc', 'Song': 'Son', 'Isaiah': 'Isa', 'Jeremiah': 'Jer', 'Lamentations': 'Lam',
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
        
        # Create reverse mapping (abbreviations to full names)
        self.abbreviation_to_book = {v: k for k, v in self.book_abbreviations.items()}
        
        # Add alternative abbreviations
        alt_abbrevs = {
            'Cor': '1 Corinthians', '1 Cor': '1 Corinthians', '2 Cor': '2 Corinthians',
            'Thess': '1 Thessalonians', '1 Thess': '1 Thessalonians', '2 Thess': '2 Thessalonians',
            'Tim': '1 Timothy', '1 Tim': '1 Timothy', '2 Tim': '2 Timothy',
            'Pet': '1 Peter', '1 Pet': '1 Peter', '2 Pet': '2 Peter',
            'Sam': '1 Samuel', '1 Sam': '1 Samuel', '2 Sam': '2 Samuel',
            'Chr': '1 Chronicles', '1 Chr': '1 Chronicles', '2 Chr': '2 Chronicles',
            'Kg': '1 Kings', '1 Kg': '1 Kings', '2 Kg': '2 Kings',
            'Jn': 'John', '1 Jn': '1 John', '2 Jn': '2 John', '3 Jn': '3 John'
        }
        self.abbreviation_to_book.update(alt_abbrevs)
    
    def parse_verse_reference(self, reference):
        """Parse a verse reference like 'Matthew 3:7-11' or '1 Cor 3:10,11'"""
        reference = reference.strip()
        
        # Pattern to match book chapter:verse(-verse) or book chapter:verse,verse
        pattern = r'^([0-9]*\s*[A-Za-z]+)\s+(\d+):(\d+)(?:[-,](\d+))?$'
        match = re.match(pattern, reference)
        
        if not match:
            return None
            
        book_part = match.group(1).strip()
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse
        
        # Find the full book name
        full_book_name = self.resolve_book_name(book_part)
        if not full_book_name:
            return None
            
        return {
            'book': full_book_name,
            'chapter': chapter,
            'start_verse': start_verse,
            'end_verse': end_verse
        }
    
    def resolve_book_name(self, book_input):
        """Resolve book name from full name or abbreviation"""
        book_input = book_input.strip()
        
        # Check if it's already a full name
        if book_input in self.book_abbreviations:
            return book_input
            
        # Check abbreviations
        if book_input in self.abbreviation_to_book:
            return self.abbreviation_to_book[book_input]
            
        # Try case-insensitive matching
        for full_name in self.book_abbreviations:
            if full_name.lower() == book_input.lower():
                return full_name
                
        for abbrev, full_name in self.abbreviation_to_book.items():
            if abbrev.lower() == book_input.lower():
                return full_name
                
        return None
    
    def lookup_verses_by_reference(self, reference_string):
        """Lookup verses by reference string (supports multiple references separated by commas)"""
        results = []
        
        # Split by commas, but be smart about it - check if each part is a complete reference
        references = self.smart_split_references(reference_string)
        
        for ref in references:
            if not ref:
                continue
                
            parsed = self.parse_verse_reference(ref)
            if not parsed:
                self.log_message(f"Could not parse reference: {ref}")
                continue
                
            verses = self.get_verses_from_database(parsed)
            if verses:
                results.extend(verses)
            else:
                self.log_message(f"No verses found for: {ref}")
                
        return results
    
    def smart_split_references(self, reference_string):
        """Smart split that handles references like 'Mark 1:3, Dan 12:2' vs '1 Cor 3:10,11'"""
        # Split by comma and analyze each part
        parts = [p.strip() for p in reference_string.split(',')]
        references = []
        i = 0
        
        while i < len(parts):
            current_part = parts[i]
            
            # Check if current part is a complete reference (book + chapter:verse)
            if re.match(r'^[0-9]*\s*[A-Za-z]+\s+\d+:\d+', current_part):
                # Check if next part is just a number (indicating verse continuation)
                if i + 1 < len(parts) and re.match(r'^\d+$', parts[i + 1].strip()):
                    # Combine as verse range: "Book chapter:verse,verse"
                    combined = current_part + ',' + parts[i + 1].strip()
                    references.append(combined)
                    i += 2
                else:
                    # This is a standalone complete reference
                    references.append(current_part)
                    i += 1
            else:
                # If it's not a complete reference, treat as is (might be invalid)
                references.append(current_part)
                i += 1
                
        return references
    
    def get_verses_from_database(self, parsed_ref):
        """Get verses from database based on parsed reference"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            verses = []
            for verse_num in range(parsed_ref['start_verse'], parsed_ref['end_verse'] + 1):
                verse_reference = f"{parsed_ref['book']} {parsed_ref['chapter']}:{verse_num}"
                
                cursor.execute("SELECT * FROM bible_verses WHERE verse = ?", (verse_reference,))
                row = cursor.fetchone()
                
                if row:
                    verses.append(row)
                    
            conn.close()
            return verses
            
        except Exception as e:
            self.log_message(f"Error querying database: {e}")
            return []
    
    def get_selected_translations(self):
        """Get list of selected translation codes"""
        # If translation_vars is empty (dialog not opened yet), use selected_translations
        if not self.translation_vars:
            selected = [code for code, selected in self.selected_translations.items() if selected]
        else:
            selected = [code for code, var in self.translation_vars.items() if var.get()]
        
        if not selected:
            selected = ["KJV"]  # Default fallback
        return selected
    
    def get_translation_column_index(self, translation_code):
        """Get database column index for translation code"""
        translation_mapping = {
            'KJV': 2,  # king_james_bible
            'ASV': 3,  # american_standard_version  
            'DRB': 4,  # douay_rheims_bible
            'DBT': 5,  # darby_bible_translation
            'ERV': 6,  # english_revised_version
            'WBT': 7,  # webster_bible_translation
            'WEB': 8,  # world_english_bible
            'YLT': 9,  # youngs_literal_translation
            'AKJV': 10, # american_king_james_version
            'WNT': 11,  # weymouth_new_testament
            'BISHOPS': 12,  # bishops_bible
            'COVERDALE': 13,  # coverdale_bible
            'GENEVA': 14,  # geneva_bible
            'NET': 15,  # net_bible
            'TYNDALE': 16   # tyndale_bible
        }
        return translation_mapping.get(translation_code)
    
    def abbreviate_verse(self, verse_text):
        """Abbreviate verse text using verse-specific strategies"""
        if len(verse_text) <= 100:  # Don't abbreviate short verses
            return verse_text
            
        # Words to remove (less significant)
        removable_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'for', 'nor', 'so', 'yet',
            'in', 'on', 'at', 'by', 'with', 'from', 'up', 'out', 'off', 'over',
            'to', 'into', 'unto', 'through', 'during', 'before', 'after',
            'that', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'must', 'shall'
        }
        
        # Important words to never abbreviate
        important_words = {
            'god', 'lord', 'jesus', 'christ', 'holy', 'spirit', 'father', 'son',
            'heaven', 'earth', 'love', 'faith', 'hope', 'peace', 'truth', 'life',
            'death', 'sin', 'salvation', 'grace', 'mercy', 'forgiveness'
        }
        
        words = verse_text.split()
        abbreviated_words = []
        removed_count = 0
        
        for i, word in enumerate(words):
            # Clean word for comparison (remove punctuation)
            clean_word = word.lower().strip('.,;:!?"\'')
            
            # Keep important words intact
            if clean_word in important_words:
                abbreviated_words.append(word)
            # Remove less significant words, but not too many consecutively
            elif clean_word in removable_words and removed_count < 2:
                abbreviated_words.append('.')
                removed_count += 1
            else:
                removed_count = 0  # Reset consecutive removal counter
                
                # For longer words (6+ letters), remove vowels but keep readable
                if len(clean_word) >= 6 and clean_word not in important_words:
                    abbreviated_word = self.remove_vowels_smart(word)
                    abbreviated_words.append(abbreviated_word)
                else:
                    abbreviated_words.append(word)
        
        # Join and clean up multiple consecutive periods
        result = ' '.join(abbreviated_words)
        result = re.sub(r'\.(\s+\.)+', '...', result)  # Replace multiple periods with ...
        
        return result
    
    def remove_vowels_smart(self, word):
        """Remove vowels from word while keeping it readable"""
        # Preserve punctuation
        punctuation = ''
        clean_word = word
        if word and word[-1] in '.,;:!?"\'':
            punctuation = word[-1]
            clean_word = word[:-1]
        
        if len(clean_word) <= 4:  # Don't abbreviate very short words
            return word
            
        # Keep first letter, remove some vowels from middle, keep last letter
        if len(clean_word) >= 6:
            first_char = clean_word[0]
            last_char = clean_word[-1]
            middle = clean_word[1:-1]
            
            # Remove vowels from middle, but keep at least one vowel if word would become unreadable
            vowels_removed = re.sub(r'[aeiouAEIOU]', '', middle)
            
            # If removing all vowels makes it too short, keep some vowels
            if len(vowels_removed) < 2:
                # Keep every other vowel
                middle_chars = list(middle)
                for i in range(len(middle_chars)):
                    if middle_chars[i].lower() in 'aeiou' and i % 2 == 0:
                        middle_chars[i] = ''
                vowels_removed = ''.join(middle_chars)
            
            result = first_char + vowels_removed + last_char + punctuation
            return result
        
        return word
    
    def is_verse_reference(self, text):
        """Check if the given text looks like a verse reference"""
        if not text:
            return False
        return self.parse_verse_reference(text) is not None
    
    def update_search_placeholder(self):
        """Update the search box placeholder based on selected mode"""
        current_mode = self.search_mode_var.get()
        
        if current_mode == "verse":
            placeholder_text = self.verse_search_placeholder
        else:
            placeholder_text = self.word_search_placeholder
        
        # Only update if placeholder is active and search box is empty or contains placeholder
        current_text = self.search_var.get()
        if self.placeholder_active or current_text in [self.word_search_placeholder, self.verse_search_placeholder, ""]:
            self.search_var.set(placeholder_text)
            self.search_box.config(foreground='gray')
            self.placeholder_active = True
    
    def on_search_focus_in(self, event=None):
        """Handle search box focus in - remove placeholder"""
        if self.placeholder_active:
            self.search_var.set("")
            self.search_box.config(foreground='black')
            self.placeholder_active = False
    
    def on_search_focus_out(self, event=None):
        """Handle search box focus out - restore placeholder if empty"""
        if not self.search_var.get().strip():
            self.update_search_placeholder()
    
    def on_search_selected(self, event=None):
        """Handle search box dropdown selection"""
        if self.placeholder_active:
            self.search_box.config(foreground='black')
            self.placeholder_active = False
        
        # Get selected value
        selected_value = self.search_var.get()
        if selected_value and '|' in selected_value:
            # Extract term and mode from history entry
            term, mode = selected_value.split('|', 1)
            # Set the radio button to the stored mode first
            self.search_mode_var.set(mode)
            # Update the placeholder to match the mode
            self.update_search_placeholder()
            # Set the search term in the box
            self.search_var.set(term)
            # Ensure the text is black (not placeholder gray)
            self.search_box.config(foreground='black')
            self.placeholder_active = False
            self.log_message(f"Selected from history: {term} (mode: {mode})")
        else:
            # If no mode in history entry, auto-detect based on content
            if selected_value:
                if self.is_verse_reference(selected_value):
                    self.search_mode_var.set("verse")
                else:
                    self.search_mode_var.set("word")
                self.update_search_placeholder()
                self.log_message(f"Auto-detected mode for history selection: {selected_value}")
    
    def on_subject_focus_in(self, event=None):
        """Handle subject box focus in - remove placeholder"""
        if self.subject_placeholder_active:
            self.subject_var.set("")
            self.subject_combobox.config(foreground='black')
            self.subject_placeholder_active = False
    
    def on_subject_focus_out(self, event=None):
        """Handle subject box focus out - restore placeholder if empty"""
        if not self.subject_var.get().strip():
            self.update_subject_placeholder()
    
    def update_subject_placeholder(self):
        """Update the subject box placeholder"""
        current_text = self.subject_var.get()
        
        # Only update if placeholder is active and subject box is empty or contains placeholder
        if self.subject_placeholder_active or current_text in [self.subject_placeholder, ""]:
            self.subject_var.set(self.subject_placeholder)
            self.subject_combobox.config(foreground='gray')
            self.subject_placeholder_active = True
    
    def on_search_mode_change(self):
        """Handle search mode radio button change"""
        # If placeholder is currently showing, update it
        current_text = self.search_var.get()
        if self.placeholder_active or current_text in [self.word_search_placeholder, self.verse_search_placeholder]:
            self.update_search_placeholder()

    def setup_ui(self):
        """Create and setup the user interface"""
        self.log_message("Setting up UI...")
        
        # Initialize height variables first (needed for widget creation)
        self.search_height_var = tk.IntVar(value=12)
        self.verse_height_var = tk.IntVar(value=3)
        self.subject_height_var = tk.IntVar(value=10)
        self.comments_height_var = tk.IntVar(value=6)
        
        self.root.title('Bible Search Lite')
        self.root.geometry('800x700')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        
        
        # Options frame
        # Settings section with border
        settings_frame = ttk.LabelFrame(main_frame, text="Search Settings", padding="5")
        settings_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        # Column 1: Checkboxes (3 vertical)
        self.ignore_case_var = tk.BooleanVar()
        self.unique_only_var = tk.BooleanVar()
        self.abbreviate_var = tk.BooleanVar()
        
        ttk.Checkbutton(settings_frame, text="Ignore case", 
                       variable=self.ignore_case_var).grid(row=0, column=0, sticky=tk.W, padx=(0, 15))
        ttk.Checkbutton(settings_frame, text="Only Unique Verse", 
                       variable=self.unique_only_var).grid(row=1, column=0, sticky=tk.W, padx=(0, 15))
        ttk.Checkbutton(settings_frame, text="Abbreviate Results", 
                       variable=self.abbreviate_var).grid(row=2, column=0, sticky=tk.W, padx=(0, 15))
        
        # Column 2: Bible scope radio buttons (3 vertical)
        self.bible_scope_var = tk.StringVar(value="bible")
        ttk.Radiobutton(settings_frame, text="Bible Search", 
                       variable=self.bible_scope_var, value="bible").grid(row=0, column=1, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(settings_frame, text="New Testament", 
                       variable=self.bible_scope_var, value="nt").grid(row=1, column=1, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(settings_frame, text="Old Testament", 
                       variable=self.bible_scope_var, value="ot").grid(row=2, column=1, sticky=tk.W, padx=(0, 15))
        
        # Column 3: Search mode radio buttons (2 vertical)
        self.search_mode_var = tk.StringVar(value="word")
        ttk.Radiobutton(settings_frame, text="Word Search", 
                       variable=self.search_mode_var, value="word", 
                       command=self.on_search_mode_change).grid(row=0, column=2, sticky=tk.W, padx=(0, 15))
        ttk.Radiobutton(settings_frame, text="Verse Search", 
                       variable=self.search_mode_var, value="verse", 
                       command=self.on_search_mode_change).grid(row=1, column=2, sticky=tk.W, padx=(0, 15))
        
        # Proximity
        proximity_frame = ttk.Frame(settings_frame)
        proximity_frame.grid(row=0, column=3, sticky=tk.W)
        ttk.Label(proximity_frame, text="Proximity:").grid(row=0, column=0, sticky=tk.W)
        self.proximity_var = tk.IntVar(value=5)
        proximity_spin = tk.Spinbox(proximity_frame, from_=1, to=50, width=5, 
                                   textvariable=self.proximity_var)
        proximity_spin.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Initialize font size variables
        self.main_font_size_var = tk.IntVar(value=10)  # For Messaging, Search Results, Bible Reading, Subject Verses, Comments
        self.other_font_size_var = tk.IntVar(value=10)  # For everything else
        
        # Settings gear button
        settings_button = ttk.Button(settings_frame, text="⚙", command=self.open_settings_menu, width=3)
        settings_button.grid(row=0, column=4, sticky=tk.E, padx=(10, 0))
        
        # Configure settings frame to push settings button to the right
        settings_frame.columnconfigure(3, weight=1)
        
        # Messaging section (moved from bottom)
        messaging_frame = ttk.LabelFrame(main_frame, text="Messaging", padding="5")
        messaging_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(messaging_frame, textvariable=self.status_var, 
                                     relief="sunken", background="white", 
                                     font=('Arial', self.other_font_size_var.get()))
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=2, pady=2)
        
        # Message history dropdown (read-only)
        history_label = ttk.Label(messaging_frame, text="History:")
        history_label.grid(row=0, column=1, sticky=tk.E, padx=(5, 2), pady=2)
        
        self.message_history_var = tk.StringVar()
        self.message_history_dropdown = ttk.Combobox(messaging_frame, textvariable=self.message_history_var, 
                                                   width=20, state="readonly")
        self.message_history_dropdown.grid(row=0, column=2, sticky=tk.E, padx=(2, 2), pady=2)
        self.message_history_dropdown['values'] = self.message_history[:10]  # Show last 10 messages
        
        # Configure messaging frame to expand
        messaging_frame.columnconfigure(0, weight=1)
        
        # Initialize status message and blinking system
        self.status_var.set("Ready")
        self.previous_status = "Ready"
        self.is_blinking = False
        self.blink_job = None
        
        # Filters frame
        filters_frame = ttk.Frame(main_frame)
        filters_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E))
        
        # Set default book value (no UI element)
        self.book_var = tk.StringVar(value="All")
        
        # Set default chapter value (no UI element)
        self.chapter_var = tk.IntVar(value=0)
        
        # Translation selection - initialize selected translations with order numbers
        self.selected_translations = {"KJV": True, "ASV": False, "DRB": False, "DBT": False, 
                                     "ERV": False, "WBT": False, "WEB": False, "YLT": False, 
                                     "AKJV": False, "WNT": False, "BISHOPS": False, "COVERDALE": False,
                                     "GENEVA": False, "NET": False, "TYNDALE": False}
        # Initialize translation order (1-15, default order)
        self.translation_order = {"KJV": 1, "ASV": 2, "DRB": 3, "DBT": 4, 
                                 "ERV": 5, "WBT": 6, "WEB": 7, "YLT": 8, 
                                 "AKJV": 9, "WNT": 10, "BISHOPS": 11, "COVERDALE": 12,
                                 "GENEVA": 13, "NET": 14, "TYNDALE": 15}
        self.translation_var = tk.StringVar(value="All")
        
        
        # Initialize translation variables for the dialog
        self.translation_vars = {}
        self.translation_order_vars = {}
        
        # Search results section with checkboxes
        search_results_frame = ttk.LabelFrame(main_frame, text="Search Results", padding="5")
        search_results_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Search controls (moved from header)
        search_controls_frame = ttk.Frame(search_results_frame)
        search_controls_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Search term input
        self.search_var = tk.StringVar()
        self.search_box = ttk.Combobox(search_controls_frame, textvariable=self.search_var, width=35)
        self.search_box.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        # Search button
        self.search_button = ttk.Button(search_controls_frame, text="Search", command=self.perform_search)
        self.search_button.grid(row=0, column=1, sticky=tk.W, padx=(0, 5))
        
        # Search Terms help button
        self.search_terms_button = ttk.Button(search_controls_frame, text="Search Terms", command=self.show_search_help)
        self.search_terms_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        
        # Export button (moved from header)
        self.export_button = ttk.Button(search_controls_frame, text="Export Search", command=self.export_results, state=tk.DISABLED)
        self.export_button.grid(row=0, column=4, sticky=tk.E, padx=(10, 0))
        
        # Configure search controls frame for right-justified export
        search_controls_frame.columnconfigure(3, weight=1)
        
        # Search results treeview with checkboxes
        # Create container for treeview and navigation buttons
        tree_frame = ttk.Frame(search_results_frame)
        tree_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Configure treeview columns
        self.results_tree = ttk.Treeview(tree_frame, columns=('reference', 'translation', 'text'), show='tree headings', height=int(self.search_height_var.get() * 1.3))
        
        # Configure column headings and widths
        self.results_tree.heading('#0', text='☐', anchor='center')  # Checkbox column
        self.results_tree.heading('reference', text='Reference', anchor='w')
        self.results_tree.heading('translation', text='', anchor='w')
        self.results_tree.heading('text', text='Verse Text', anchor='w')
        
        # Set column widths
        self.results_tree.column('#0', width=30, minwidth=30, stretch=False)  # Checkbox column
        self.results_tree.column('reference', width=120, minwidth=100, stretch=False)
        self.results_tree.column('translation', width=80, minwidth=60, stretch=False)
        self.results_tree.column('text', width=500, minwidth=300, stretch=True)
        
        # Add scrollbars
        tree_v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.results_tree.yview)
        tree_h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=tree_v_scrollbar.set, xscrollcommand=tree_h_scrollbar.set)
        
        # Grid the treeview and scrollbars
        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_v_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        tree_h_scrollbar.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        
        # Configure grid weights for tree_frame
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Bind treeview events
        self.results_tree.bind('<Button-1>', self.on_treeview_click)
        self.results_tree.bind('<space>', self.on_treeview_space)
        self.results_tree.bind('<<TreeviewSelect>>', self.on_search_results_select)
        
        # Configure treeview fonts and tags
        self.update_font_size()
        
        # Configure basic tags for search results
        self.results_tree.tag_configure('checked', background='lightblue')
        self.results_tree.tag_configure('unchecked', background='white')
        
        # Verse Display Window (Reading Window)
        verse_display_frame = ttk.LabelFrame(main_frame, text="Bible Reading View: King James Version", padding="5")
        self.verse_display_frame = verse_display_frame  # Store reference for label updates
        verse_display_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Add navigation controls
        nav_frame = ttk.Frame(verse_display_frame)
        nav_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        
        # Create verse display treeview with checkboxes and scrollbar
        verse_display_container = ttk.Frame(verse_display_frame)
        verse_display_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=2, pady=2)
        
        self.verse_display_tree = ttk.Treeview(verse_display_container, columns=('reference', 'translation', 'text'), 
                                              show='tree headings', height=int(self.verse_height_var.get() * 1.5))
        
        # Configure columns
        self.verse_display_tree.heading('#0', text='✓', anchor='center')
        self.verse_display_tree.heading('reference', text='Reference')
        self.verse_display_tree.heading('translation', text='Translation')
        self.verse_display_tree.heading('text', text='Verse Text')
        
        self.verse_display_tree.column('#0', width=30, minwidth=30, stretch=False)
        self.verse_display_tree.column('reference', width=120, minwidth=100)
        self.verse_display_tree.column('translation', width=80, minwidth=60)
        self.verse_display_tree.column('text', width=400, minwidth=200)
        
        verse_display_scrollbar = ttk.Scrollbar(verse_display_container, orient="vertical", 
                                               command=self.verse_display_tree.yview)
        self.verse_display_tree.configure(yscrollcommand=verse_display_scrollbar.set)
        
        self.verse_display_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        verse_display_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure treeview appearance using style
        try:
            style = ttk.Style()
            style.configure('VerseTree.Treeview', 
                          fieldbackground='white', 
                          background='white',
                          selectbackground='lightblue',
                          selectforeground='black')
            self.verse_display_tree.configure(style='VerseTree.Treeview')
        except Exception:
            pass
        
        # Configure tag styles
        self.verse_display_tree.tag_configure('checked', background='lightgreen')
        self.verse_display_tree.tag_configure('unchecked', background='white')
        
        # Initialize Bible Reading View data structures
        self.current_bible_verses = []  # Store currently displayed verses
        self.selected_bible_verses = set()  # Track selected verse indices
        
        # Bind keyboard events for navigation and clicking
        self.verse_display_tree.bind('<Key-Up>', lambda e: self.scroll_bible_up())
        self.verse_display_tree.bind('<Key-Down>', lambda e: self.scroll_bible_down())
        self.verse_display_tree.bind('<Button-1>', self.on_bible_verse_click)
        
        # Configure verse display frame
        verse_display_frame.columnconfigure(0, weight=1)
        verse_display_container.columnconfigure(0, weight=1)
        verse_display_container.rowconfigure(0, weight=1)
        verse_display_frame.rowconfigure(1, weight=1)
        
        # Subject verses display and controls
        subject_verses_frame = ttk.LabelFrame(main_frame, text="Subject Verses", padding="5")
        subject_verses_frame.grid(row=5, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Subject control buttons
        subject_controls_frame = ttk.Frame(subject_verses_frame)
        subject_controls_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Subject controls in logical order
        # Subject selector (moved from search results)
        self.subject_var = tk.StringVar()
        self.subject_combobox = ttk.Combobox(subject_controls_frame, textvariable=self.subject_var, width=35)
        self.subject_combobox.grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.subject_combobox.bind('<<ComboboxSelected>>', self.on_subject_selected)
        self.subject_combobox.bind('<Return>', self.on_subject_return)
        self.subject_combobox.bind('<FocusIn>', self.on_subject_focus_in)
        self.subject_combobox.bind('<FocusOut>', self.on_subject_focus_out)
        self.subject_combobox.config(state="normal")  # Start as normal to show placeholder
        
        # Try to set white background explicitly
        try:
            style = ttk.Style()
            style.configure('Subject.TCombobox', fieldbackground='white')
            self.subject_combobox.configure(style='Subject.TCombobox')
        except Exception:
            pass
        
        
        self.create_subject_button = ttk.Button(subject_controls_frame, text="Create Subject", 
                                               command=self.enable_subject_creation, state=tk.NORMAL)
        self.create_subject_button.grid(row=0, column=1, padx=(0, 5))
        
        self.move_to_subject_button = ttk.Button(subject_controls_frame, text="Move to Subject", 
                                                command=self.move_to_current_subject, state=tk.DISABLED)
        self.move_to_subject_button.grid(row=0, column=2, padx=(0, 5))
        
        self.delete_button = ttk.Button(subject_controls_frame, text="Delete", 
                                       command=self.show_delete_dialog, state=tk.DISABLED)
        self.delete_button.grid(row=0, column=3, padx=(0, 5))
        
        self.export_subject_button = ttk.Button(subject_controls_frame, text="Export Subject", 
                                               command=self.export_current_subject, state=tk.DISABLED)
        self.export_subject_button.grid(row=0, column=6, sticky=tk.E, padx=(10, 0))
        
        # Configure subject controls frame for right-justified export
        subject_controls_frame.columnconfigure(5, weight=1)
        
        # Create container for treeview and navigation buttons
        text_container = ttk.Frame(subject_verses_frame)
        text_container.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Subject verses treeview
        self.subject_tree = ttk.Treeview(text_container, columns=('reference', 'translation', 'text'), show='tree headings', height=int(self.subject_height_var.get() * 1.3))
        
        # Configure subject tree appearance to have white background
        try:
            # Method 1: Direct treeview configuration
            self.subject_tree.configure(selectbackground='lightblue', selectforeground='black')
            
            # Method 2: Style configuration for better background control
            style = ttk.Style()
            style.configure('SubjectTree.Treeview', 
                          fieldbackground='white', 
                          background='white',
                          borderwidth=1,
                          relief='solid')
            self.subject_tree.configure(style='SubjectTree.Treeview')
            
            # Method 3: Add an empty item to force white background display, then remove it
            temp_item = self.subject_tree.insert('', 'end', text='', values=('', '', ''))
            self.subject_tree.delete(temp_item)
        except Exception as e:
            self.log_message(f"Warning: Could not set subject tree background: {e}")
        
        # Configure column headings and widths for subject tree
        self.subject_tree.heading('#0', text='☐', anchor='center')  # Checkbox column
        self.subject_tree.heading('reference', text='Reference', anchor='w')
        self.subject_tree.heading('translation', text='', anchor='w')
        self.subject_tree.heading('text', text='Verse Text', anchor='w')
        
        # Set column widths for subject tree
        self.subject_tree.column('#0', width=30, minwidth=30, stretch=False)  # Checkbox column
        self.subject_tree.column('reference', width=120, minwidth=100, stretch=False)
        self.subject_tree.column('translation', width=80, minwidth=60, stretch=False)
        self.subject_tree.column('text', width=500, minwidth=300, stretch=True)
        
        # Add scrollbars for subject tree
        subject_v_scrollbar = ttk.Scrollbar(text_container, orient='vertical', command=self.subject_tree.yview)
        subject_h_scrollbar = ttk.Scrollbar(text_container, orient='horizontal', command=self.subject_tree.xview)
        self.subject_tree.configure(yscrollcommand=subject_v_scrollbar.set, xscrollcommand=subject_h_scrollbar.set)
        
        # Grid the subject treeview and scrollbars
        self.subject_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        subject_v_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        subject_h_scrollbar.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        
        # Bind subject tree events
        self.subject_tree.bind('<Button-1>', self.on_subject_treeview_click)
        self.subject_tree.bind('<space>', self.on_subject_treeview_space)
        self.subject_tree.bind('<<TreeviewSelect>>', self.on_subject_tree_selection)
        
        # Configure subject tree tags
        self.subject_tree.tag_configure('checked', background='lightblue')
        self.subject_tree.tag_configure('unchecked', background='white')
        self.subject_tree.tag_configure('placeholder', background='white', foreground='gray')
        
        # Insert a placeholder item to ensure white background is visible at startup
        self.subject_tree.insert('', 'end', text='', values=('Subject', '', ''), tags=('placeholder',))
        
        # Comments display area below the subject treeview
        comments_frame = ttk.LabelFrame(subject_verses_frame, text="Subject Verse Comments", padding="5")
        comments_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        # Comment control buttons
        comment_controls_frame = ttk.Frame(comments_frame)
        comment_controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.create_comment_button = ttk.Button(comment_controls_frame, text="Create Comment", 
                                               command=self.create_comment, state=tk.DISABLED)
        self.create_comment_button.grid(row=0, column=0, padx=(0, 5))
        
        self.edit_comment_button = ttk.Button(comment_controls_frame, text="Edit Comment", 
                                             command=self.edit_comment, state=tk.DISABLED)
        self.edit_comment_button.grid(row=0, column=1, padx=(0, 5))
        
        self.delete_comment_button = ttk.Button(comment_controls_frame, text="Delete Comment", 
                                               command=self.delete_comment, state=tk.DISABLED)
        self.delete_comment_button.grid(row=0, column=2, padx=(0, 5))
        
        self.save_comment_button = ttk.Button(comment_controls_frame, text="Save Comment", 
                                             command=self.save_comment, state=tk.DISABLED)
        self.save_comment_button.grid(row=0, column=3, padx=(0, 5))
        
        # Comments text widget with scrollbar
        comments_container = ttk.Frame(comments_frame)
        comments_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.comments_text = tk.Text(comments_container, height=int(self.comments_height_var.get() * 1.5), wrap=tk.WORD, 
                                   font=('Arial', self.main_font_size_var.get()), state=tk.DISABLED)
        self.comments_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        comments_scrollbar = ttk.Scrollbar(comments_container, orient='vertical', 
                                         command=self.comments_text.yview)
        self.comments_text.configure(yscrollcommand=comments_scrollbar.set)
        comments_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure comments frame to expand
        comments_frame.columnconfigure(0, weight=1)
        comments_frame.rowconfigure(1, weight=1)
        comments_container.columnconfigure(0, weight=1)
        comments_container.rowconfigure(0, weight=1)
        
        # (Messaging section moved above - see row 1)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)  # Search results
        main_frame.rowconfigure(4, weight=1)  # Bible Reading View  
        main_frame.rowconfigure(5, weight=2)  # Subject verses + Comments (double weight since it contains 2 expandable areas)
        
        # Configure search results frame
        search_results_frame.columnconfigure(0, weight=1)
        search_results_frame.rowconfigure(1, weight=1)
        
        # Configure verse display frame (Bible Reading View)
        verse_display_frame.columnconfigure(0, weight=1)
        verse_display_frame.rowconfigure(1, weight=1)
        
        # Configure subject verses frame
        subject_verses_frame.columnconfigure(0, weight=1)
        subject_verses_frame.rowconfigure(1, weight=1)  # Subject tree
        subject_verses_frame.rowconfigure(2, weight=1)  # Comments
        
        # Configure text container
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)
        
        # Bind events
        self.search_box.bind('<Return>', lambda e: self.perform_search())
        self.search_box.bind('<FocusIn>', self.on_search_focus_in)
        self.search_box.bind('<FocusOut>', self.on_search_focus_out)
        self.search_box.bind('<<ComboboxSelected>>', self.on_search_selected)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize subjects
        self.load_subjects()
        
        # Initialize placeholders
        self.update_search_placeholder()
        self.update_subject_placeholder()
        
        # Note: Translation button is now accessed via Settings gear button
        
        # Update font sizes for all widgets now that they're all created
        self.update_font_size()
        
        self.log_message("UI setup completed successfully")
        
    def show_blinking_status(self, message, duration=3000):
        """Show a blinking status message for specified duration (in milliseconds)"""
        if self.is_blinking and self.blink_job:
            # Cancel any existing blink job
            self.root.after_cancel(self.blink_job)
        
        # Store current status if not already blinking
        if not self.is_blinking:
            self.previous_status = self.status_var.get()
        
        # Add message to history (keep last 10)
        self.add_message_to_history(message)
        
        self.is_blinking = True
        self.blink_count = 0
        self.blink_message = message
        
        # Start blinking
        self._blink_status()
        
        # Schedule restoration after duration
        self.blink_job = self.root.after(duration, self._restore_status)
    
    def _blink_status(self):
        """Internal method to handle the blinking effect - blinks twice in yellow"""
        if not self.is_blinking:
            return
            
        # Show message with yellow background, then white background (2 blinks = 4 state changes)
        if self.blink_count % 2 == 0:
            self.status_var.set(self.blink_message)
            self.status_label.configure(background="yellow")
        else:
            self.status_var.set(self.blink_message)
            self.status_label.configure(background="white")
        
        self.blink_count += 1
        
        # Blink twice (4 state changes) with 300ms intervals
        if self.blink_count < 4:
            self.root.after(300, self._blink_status)
        else:
            # After blinking, keep message visible for remaining time
            self.status_var.set(self.blink_message)
            self.status_label.configure(background="white")
    
    def _restore_status(self):
        """Stop blinking and keep the current message displayed"""
        self.is_blinking = False
        self.blink_job = None
        # Keep the current message (blink_message) instead of reverting to previous
        self.status_var.set(self.blink_message)
        self.status_label.configure(background="white")
        # Update previous_status to the current message for future reference
        self.previous_status = self.blink_message
    
    def add_message_to_history(self, message):
        """Add message to history and update dropdown"""
        if message and message not in self.message_history:
            self.message_history.insert(0, message)  # Add to beginning
            self.message_history = self.message_history[:10]  # Keep only last 10
            
            # Update dropdown values
            if hasattr(self, 'message_history_dropdown'):
                self.message_history_dropdown['values'] = self.message_history
    
    def update_status(self, message):
        """Update status message (stores as previous for blinking system)"""
        if not self.is_blinking:
            # Add to history for regular status updates too
            self.add_message_to_history(message)
            self.status_var.set(message)
            self.previous_status = message
    
    def show_message(self, message):
        """Show a new message with yellow blinking effect"""
        self.show_blinking_status(message)
    
    def update_font_size(self):
        """Update the font size for all UI elements"""
        main_font_size = self.main_font_size_var.get()
        other_font_size = self.other_font_size_var.get()
        
        # Group 1: Messaging, Search Results, Bible Reading View, Subject Verses, Comments
        # Update treeview fonts (both search results and subject verses)
        if hasattr(self, 'results_tree'):
            style = ttk.Style()
            style.configure('Treeview', font=('Arial', main_font_size), fieldbackground='white', background='white')
            style.configure('Treeview.Heading', font=('Arial', main_font_size, 'bold'))
            # Also configure the custom subject tree style
            style.configure('SubjectTree.Treeview', 
                          font=('Arial', main_font_size), 
                          fieldbackground='white', 
                          background='white',
                          borderwidth=1,
                          relief='solid')
        
        # Update comments text widget font
        if hasattr(self, 'comments_text'):
            self.comments_text.configure(font=('Arial', main_font_size))
        
        # Update verse display font (Bible Reading View)
        if hasattr(self, 'verse_display_tree'):
            # Bible Reading View treeview already gets styled by the general Treeview style above
            pass
        
        # Group 2: Everything else (status line, etc.)
        # Update status line font
        if hasattr(self, 'status_label'):
            self.status_label.configure(font=('Arial', other_font_size))
    
    def open_font_size_dialog(self):
        """Open font size configuration dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Font Size Settings")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Group 1: Main windows font size
        group1_frame = ttk.LabelFrame(main_frame, text="Main Windows (Messaging, Search Results, Bible Reading, Subject Verses, Comments)", padding="10")
        group1_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(group1_frame, text="Font Size:").grid(row=0, column=0, sticky=tk.W)
        main_font_spin = tk.Spinbox(group1_frame, from_=8, to=20, width=5, 
                                   textvariable=self.main_font_size_var,
                                   command=lambda: (self.update_font_size(), self.log_message(f"Main font changed to: {self.main_font_size_var.get()}")))
        main_font_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        main_font_spin.bind('<KeyRelease>', lambda e: self.root.after(100, lambda: (self.update_font_size(), self.log_message(f"Main font changed to: {self.main_font_size_var.get()}"))))
        
        # Group 2: Other elements font size  
        group2_frame = ttk.LabelFrame(main_frame, text="Other Elements", padding="10")
        group2_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(group2_frame, text="Font Size:").grid(row=0, column=0, sticky=tk.W)
        other_font_spin = tk.Spinbox(group2_frame, from_=8, to=20, width=5, 
                                    textvariable=self.other_font_size_var,
                                    command=lambda: (self.update_font_size(), self.log_message(f"Other font changed to: {self.other_font_size_var.get()}")))
        other_font_spin.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        other_font_spin.bind('<KeyRelease>', lambda e: self.root.after(100, lambda: (self.update_font_size(), self.log_message(f"Other font changed to: {self.other_font_size_var.get()}"))))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT)
        
        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        group1_frame.columnconfigure(1, weight=1)
        group2_frame.columnconfigure(1, weight=1)

    def update_search_height(self):
        """Update the height of the search results treeview"""
        if hasattr(self, 'results_tree'):
            height = int(self.search_height_var.get() * 1.3)
            self.results_tree.configure(height=height)
    
    def update_verse_height(self):
        """Update the height of the verse display treeview widget"""
        if hasattr(self, 'verse_display_tree'):
            height = int(self.verse_height_var.get() * 1.5)
            self.verse_display_tree.configure(height=height)
    
    def update_subject_height(self):
        """Update the height of the subject verses treeview"""
        if hasattr(self, 'subject_tree'):
            height = int(self.subject_height_var.get() * 1.3)
            self.subject_tree.configure(height=height)
    
    def update_comments_height(self):
        """Update the height of the comments text widget"""
        if hasattr(self, 'comments_text'):
            height = int(self.comments_height_var.get() * 1.5)
            self.comments_text.configure(height=height)
        
    def load_config(self):
        """Load configuration from JSON file"""
        self.log_message("Loading configuration...")
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                # Load search history (handle both old and new formats)
                if 'SearchHistory' in config:
                    history = config['SearchHistory']
                    # Convert all entries to new format
                    converted_history = []
                    for entry in history:
                        if '|' not in entry:
                            # Old format - auto-detect mode
                            if self.is_verse_reference(entry):
                                converted_history.append(f"{entry}|verse")
                            else:
                                converted_history.append(f"{entry}|word")
                        else:
                            # New format - use as is
                            converted_history.append(entry)
                    self.search_box['values'] = converted_history
                
                # Load other settings
                if 'IgnoreCase' in config:
                    self.ignore_case_var.set(config['IgnoreCase'])
                if 'UniqueOnly' in config:
                    self.unique_only_var.set(config['UniqueOnly'])
                if 'Abbreviate' in config:
                    self.abbreviate_var.set(config['Abbreviate'])
                if 'BibleScope' in config:
                    self.bible_scope_var.set(config['BibleScope'])
                if 'ProximityWindow' in config:
                    self.proximity_var.set(config['ProximityWindow'])
                if 'MainFontSize' in config:
                    self.main_font_size_var.set(config['MainFontSize'])
                    self.log_message(f"Loaded MainFontSize: {config['MainFontSize']}")
                if 'OtherFontSize' in config:
                    self.other_font_size_var.set(config['OtherFontSize'])
                    self.log_message(f"Loaded OtherFontSize: {config['OtherFontSize']}")
                # Legacy support for old FontSize setting
                if 'FontSize' in config and 'MainFontSize' not in config:
                    self.main_font_size_var.set(config['FontSize'])
                    self.other_font_size_var.set(config['FontSize'])
                if 'Book' in config:
                    self.book_var.set(config['Book'])
                if 'Chapter' in config:
                    self.chapter_var.set(config['Chapter'])
                if 'Translation' in config:
                    self.translation_var.set(config['Translation'] if config['Translation'] else "All")
                # Load translation selections
                if 'SelectedTranslations' in config:
                    for code, selected in config['SelectedTranslations'].items():
                        if code in self.translation_vars:
                            self.translation_vars[code].set(selected)
                if 'TranslationOrder' in config:
                    for code, order in config['TranslationOrder'].items():
                        if code in self.translation_order_vars:
                            self.translation_order_vars[code].set(order)
                if 'TranslationOrder' in config:
                    self.translation_order.update(config['TranslationOrder'])
                
                # Load window heights
                if 'SearchHeight' in config:
                    self.search_height_var.set(config['SearchHeight'])
                if 'VerseHeight' in config:
                    self.verse_height_var.set(config['VerseHeight'])
                if 'SubjectHeight' in config:
                    self.subject_height_var.set(config['SubjectHeight'])
                if 'CommentsHeight' in config:
                    self.comments_height_var.set(config['CommentsHeight'])
                
                # Restore window size and position
                if 'WindowGeometry' in config:
                    try:
                        self.root.geometry(config['WindowGeometry'])
                        self.log_message(f"Restored window geometry: {config['WindowGeometry']}")
                    except Exception as e:
                        self.log_message(f"Error restoring window geometry: {e}")
                
                # Update window heights after loading configuration
                if hasattr(self, 'results_tree'):
                    self.update_search_height()
                if hasattr(self, 'verse_display_tree'):
                    self.update_verse_height()
                if hasattr(self, 'subject_tree'):
                    self.update_subject_height()
                if hasattr(self, 'comments_text'):
                    self.update_comments_height()
                
                # Update font sizes after loading configuration
                self.update_font_size()
                
                self.log_message("Configuration loaded successfully")
            else:
                self.log_message("Configuration file not found")
            
            # Initialize Bible view after configuration is loaded
            self.display_bible_view()
        except Exception as e:
            self.log_message(f"Error loading configuration: {e}")
            
    def save_config(self):
        """Save configuration to JSON file"""
        self.log_message("Saving configuration...")
        try:
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
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.log_message("Configuration saved successfully")
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}")
            
    def add_search_history(self, term: str):
        """Add search term to history with search mode"""
        if not term:
            return
            
        # Get current search mode
        search_mode = self.search_mode_var.get()
        
        # Create history entry with mode
        history_entry = f"{term}|{search_mode}"
        
        # Check if this exact entry already exists
        current_values = list(self.search_box['values'])
        if history_entry not in current_values:
            current_values.insert(0, history_entry)
            if len(current_values) > 50:
                current_values = current_values[:50]
            self.search_box['values'] = current_values
            self.log_message(f"Added to search history: {term} (mode: {search_mode})")
            
    def parse_search_term(self, search_term: str) -> tuple:
        """Parse search term for Boolean operators and exact phrases (quoted strings)"""
        # First, extract quoted phrases and replace them with placeholders
        quoted_phrases = []
        placeholder_pattern = "QUOTED_PHRASE_{}"
        
        # Find all quoted strings
        quote_pattern = r'"([^"]*)"'
        matches = re.finditer(quote_pattern, search_term)
        
        processed_term = search_term
        for i, match in enumerate(matches):
            quoted_text = match.group(1)  # Text inside quotes
            quoted_phrases.append(quoted_text)
            placeholder = placeholder_pattern.format(i)
            processed_term = processed_term.replace(match.group(0), placeholder)
        
        # Now check for AND/OR operators in the processed term
        if ' AND ' in processed_term.upper():
            terms = [term.strip() for term in re.split(r'\s+AND\s+', processed_term, flags=re.IGNORECASE)]
            is_boolean = True
        elif ' OR ' in processed_term.upper():
            terms = [term.strip() for term in re.split(r'\s+OR\s+', processed_term, flags=re.IGNORECASE)]
            is_boolean = True
        else:
            terms = [processed_term.strip()]
            is_boolean = False
        
        # Replace placeholders back with quoted phrases
        final_terms = []
        for term in terms:
            if "QUOTED_PHRASE_" in term:
                # Replace placeholders with the actual quoted phrases
                for i, phrase in enumerate(quoted_phrases):
                    placeholder = placeholder_pattern.format(i)
                    if placeholder in term:
                        term = term.replace(placeholder, phrase)
                        # Mark this term as an exact phrase
                        term = f'EXACT:{phrase}'
                        break
            final_terms.append(term)
        
        return is_boolean, final_terms
    
    def convert_wildcards_to_regex(self, term: str) -> str:
        """Convert wildcard patterns (* and ?) to regex"""
        # Escape special regex characters except * and ?
        term = re.escape(term)
        # Convert escaped wildcards back to regex equivalents
        term = term.replace(r'\*', '.*')  # * becomes .*
        term = term.replace(r'\?', '.')   # ? becomes .
        return term
    
    def build_search_patterns(self, terms: list, proximity_window: int) -> list:
        """Build regex patterns for search terms"""
        patterns = []
        
        for term in terms:
            # Check if this is an exact phrase (marked with EXACT:)
            if term.startswith('EXACT:'):
                # Extract the exact phrase
                exact_phrase = term[6:]  # Remove 'EXACT:' prefix
                words = exact_phrase.split()
                regex_words = [self.convert_wildcards_to_regex(word) for word in words]
                # For exact phrases, words must appear in exact order with only whitespace between
                pattern = r'\b' + r'\s+'.join(regex_words) + r'\b'
            else:
                # Regular proximity search
                words = term.split()
                regex_words = [self.convert_wildcards_to_regex(word) for word in words]
                
                # Create bidirectional proximity search
                if len(regex_words) == 1:
                    pattern = r'\b' + regex_words[0] + r'\b'
                elif len(regex_words) == 2:
                    # For two words, create pattern that matches either order
                    word1, word2 = regex_words
                    pattern1 = rf'\b{word1}.{{0,{proximity_window}}}\b{word2}\b'
                    pattern2 = rf'\b{word2}.{{0,{proximity_window}}}\b{word1}\b'
                    pattern = f'({pattern1}|{pattern2})'
                else:
                    # For multiple words, use all permutations within proximity
                    perm_patterns = []
                    for perm in permutations(regex_words):
                        perm_pattern = r'\b' + f'.{{0,{proximity_window}}}'.join(perm) + r'\b'
                        perm_patterns.append(perm_pattern)
                    pattern = '(' + '|'.join(perm_patterns) + ')'
            
            patterns.append(pattern)
        
        return patterns

    def get_biblical_book_order(self):
        """Return the proper Biblical book order for sorting"""
        return [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
            "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
            "Psalms", "Psalm", "Proverbs", "Ecclesiastes", "Song of Songs", "Song",
            "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
            "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", 
            "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
            "Matthew", "Mark", "Luke", "John", "Acts", "Romans", 
            "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", 
            "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
            "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
            "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
        ]

    def get_old_testament_books(self):
        """Return list of Old Testament book names"""
        return [
            "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
            "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
            "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
            "Psalms", "Psalm", "Proverbs", "Ecclesiastes", "Song of Songs", "Song",
            "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
            "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", 
            "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi"
        ]

    def get_new_testament_books(self):
        """Return list of New Testament book names"""
        return [
            "Matthew", "Mark", "Luke", "John", "Acts", "Romans", 
            "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", 
            "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
            "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
            "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
        ]

    def search_bible(self, search_term: str, translation: str = "All", ignore_case: bool = False,
                    proximity_window: int = 5, book: str = "All", chapter: int = 0) -> List[Dict[str, Any]]:
        """Search the Bible database using SQLite - Updated for cleaned database"""
        self.log_message("Entering search_bible function (cleaned database version)")
        
        # Parse search term for Boolean operators and quoted phrases
        is_boolean, terms = self.parse_search_term(search_term)
        
        # Build search patterns
        patterns = self.build_search_patterns(terms, proximity_window)
        
        # Create final regex
        if is_boolean and 'AND' in search_term.upper():
            # For AND: all patterns must match (use positive lookahead)
            search_regex = '(?=.*' + ')(?=.*'.join(patterns) + ')'
        elif is_boolean and 'OR' in search_term.upper():
            # For OR: any pattern can match
            search_regex = '(' + '|'.join(patterns) + ')'
        else:
            # Single term or proximity search
            search_regex = patterns[0] if patterns else r'\b\w+\b'
            
        if ignore_case:
            search_regex = f"(?i){search_regex}"
        
        # Map translation names to column names in our cleaned database
        translation_columns = {
            "All": "*",
            "KJV": "king_james_bible",
            "ASV": "american_standard_version", 
            "DRB": "douay_rheims_bible",
            "DBT": "darby_bible_translation",
            "ERV": "english_revised_version",
            "WBT": "webster_bible_translation",
            "WEB": "world_english_bible",
            "YLT": "youngs_literal_translation",
            "AKJV": "american_king_james_version",
            "WNT": "weymouth_new_testament",
            "BISHOPS": "bishops_bible",
            "COVERDALE": "coverdale_bible",
            "GENEVA": "geneva_bible",
            "NET": "net_bible",
            "TYNDALE": "tyndale_bible"
        }
        
        # Build SQL query for our cleaned database schema
        if translation == "All" or hasattr(self, 'selected_translations'):
            # Determine which translations to search
            if translation == "All":
                # Search all translations when "All" is selected, use custom ordering
                selected_translations = list(translation_columns.keys())[1:]  # All except "All"
                selected_translations.sort(key=lambda code: self.translation_order.get(code, 999))
            else:
                # Get selected translations from checkboxes
                selected_translations = [code for code, var in self.translation_vars.items() if var.get()]
                if not selected_translations:
                    selected_translations = ["KJV"]  # Default fallback
                
                # Sort by order preference
                if self.translation_order_vars:
                    # Use order from dialog variables if available
                    selected_translations.sort(key=lambda code: self.translation_order_vars[code].get())
                else:
                    # Use default order from self.translation_order if dialog not opened yet
                    selected_translations.sort(key=lambda code: self.translation_order.get(code, 999))
            
            # Build UNION query for selected translations
            union_queries = []
            params = []
            
            for trans_code in selected_translations:
                if trans_code in translation_columns and trans_code != "All":
                    column = translation_columns[trans_code]
                    # Add order number to the query for sorting
                    order_num = self.translation_order.get(trans_code, 999)
                    union_queries.append(f"SELECT verse as Reference, '{trans_code}' as Translation, {column} as Text, {order_num} as SortOrder FROM bible_verses WHERE {column} REGEXP ?")
                    params.append(search_regex)
            
            if union_queries:
                query = " UNION ALL ".join(union_queries)
                # Note: Removed ORDER BY - we'll sort in Python for proper Biblical order
            else:
                # Fallback to KJV if no valid translations
                query = "SELECT verse as Reference, 'KJV' as Translation, king_james_bible as Text FROM bible_verses WHERE king_james_bible REGEXP ?"
                params = [search_regex]
        else:
            # Search specific translation (legacy compatibility)
            column = translation_columns.get(translation, "king_james_bible")
            query = f"SELECT verse as Reference, ? as Translation, {column} as Text FROM bible_verses WHERE {column} REGEXP ?"
            params = [translation, search_regex]
        
        # Add filters
        if book != "All" or chapter != 0:
            # Apply book filter
            if book != "All":
                if translation == "All" or hasattr(self, 'selected_translations'):
                    # Add book filter to each UNION query
                    query = query.replace(" REGEXP ?", f" REGEXP ? AND verse LIKE '{book} %'")
                else:
                    query += f" AND verse LIKE ?"
                    params.append(f"{book} %")
            
            # Apply chapter filter
            if chapter != 0:
                chapter_pattern = f"{book} {chapter}:" if book != "All" else f" {chapter}:"
                if translation == "All" or hasattr(self, 'selected_translations'):
                    if book != "All":
                        query = query.replace(f"verse LIKE '{book} %'", f"verse LIKE '{book} {chapter}:%'")
                    else:
                        query = query.replace(" REGEXP ?", f" REGEXP ? AND verse LIKE '% {chapter}:%'")
                else:
                    if book != "All":
                        # Update the last parameter
                        if params and params[-1].startswith(f"{book} "):
                            params[-1] = f"{book} {chapter}:%"
                        else:
                            params.append(f"{book} {chapter}:%")
                            query += " AND verse LIKE ?"
                    else:
                        query += " AND verse LIKE ?"
                        params.append(f"% {chapter}:%")
        
        # Add Bible scope filter (Old Testament, New Testament, or All)
        bible_scope = getattr(self, 'bible_scope_var', None)
        if bible_scope and bible_scope.get() != "bible":
            if bible_scope.get() == "ot":
                # Old Testament filter
                ot_books = self.get_old_testament_books()
                book_conditions = " OR ".join([f"verse LIKE '{book} %'" for book in ot_books])
                if translation == "All" or hasattr(self, 'selected_translations'):
                    # For UNION queries, wrap in parentheses and add to each query
                    query = query.replace(" WHERE ", f" WHERE ({book_conditions}) AND ")
                else:
                    query += f" AND ({book_conditions})"
            elif bible_scope.get() == "nt":
                # New Testament filter
                nt_books = self.get_new_testament_books()
                book_conditions = " OR ".join([f"verse LIKE '{book} %'" for book in nt_books])
                if translation == "All" or hasattr(self, 'selected_translations'):
                    # For UNION queries, wrap in parentheses and add to each query
                    query = query.replace(" WHERE ", f" WHERE ({book_conditions}) AND ")
                else:
                    query += f" AND ({book_conditions})"
            
        self.log_message(f"Executing SQL query with regex: {search_regex}")
        self.log_message(f"Search parameters - ignore_case: {ignore_case}, proximity_window: {proximity_window}")
        self.log_message(f"Boolean analysis - is_boolean: {is_boolean}, terms: {terms}")
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            
            # Add REGEXP function to SQLite that properly handles flags
            def regexp(expr, item):
                if item is None:
                    return False
                try:
                    # Check if the regex starts with case-insensitive flag
                    if expr.startswith('(?i)'):
                        return re.search(expr, item, re.IGNORECASE) is not None
                    else:
                        return re.search(expr, item) is not None
                except re.error:
                    return False
                
            conn.create_function("REGEXP", 2, regexp)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Debug: Let's also try a simple test query to see what's in the database
            if len(rows) == 0:
                self.log_message("No results found. Testing with simpler queries...")
                
                # Test if "light" exists (case sensitive)
                test_cursor = conn.cursor()
                test_cursor.execute("SELECT COUNT(*) FROM bible_verses WHERE king_james_bible LIKE '%light%'")
                count = test_cursor.fetchone()[0]
                self.log_message(f"Found {count} verses containing 'light' in KJV")
            
            results = []
            for row in rows:
                results.append({
                    'Reference': row[0],
                    'Translation': row[1],
                    'Text': row[2]
                })
                
            conn.close()
            self.log_message(f"Search completed. Found {len(results)} results.")
            
            # Sort results by proper Biblical book order instead of alphabetical
            book_order = self.get_biblical_book_order()
            book_order_dict = {book: i for i, book in enumerate(book_order)}
            
            def get_sort_key(result):
                verse_ref = result['Reference']
                # Extract book name (everything before the first space and number)
                parts = verse_ref.split(' ')
                if len(parts) >= 2:
                    # Handle books like "1 Samuel", "2 Kings", etc.
                    if parts[0].isdigit():
                        book_name = f"{parts[0]} {parts[1]}"
                        chapter_verse = ' '.join(parts[2:])
                    else:
                        book_name = parts[0]
                        chapter_verse = ' '.join(parts[1:])
                    
                    # Get book order (default to 999 for unknown books)
                    book_order_num = book_order_dict.get(book_name, 999)
                    
                    # Extract chapter and verse numbers for proper numerical sorting
                    try:
                        if ':' in chapter_verse:
                            chapter_str, verse_str = chapter_verse.split(':', 1)
                            chapter_num = int(chapter_str)
                            verse_num = int(verse_str)
                        else:
                            chapter_num = int(chapter_verse) if chapter_verse.isdigit() else 0
                            verse_num = 0
                    except (ValueError, IndexError):
                        chapter_num = 0
                        verse_num = 0
                    
                    return (book_order_num, chapter_num, verse_num)
                else:
                    return (999, 0, 0)  # Default for malformed references
            
            # Sort by Biblical order, then by translation order if multiple translations
            results = sorted(results, key=lambda x: (get_sort_key(x), self.translation_order.get(x['Translation'], 999)))
            
            # Add highlighting info to results
            for result in results:
                result['search_term'] = search_term
                
            return results
            
        except Exception as e:
            self.log_message(f"Error executing SQL query: {e}")
            raise
            
    def get_search_words_for_highlighting(self, search_term: str) -> list:
        """Extract terms for highlighting - keeping exact phrases intact"""
        # Parse search term for Boolean operators and exact phrases
        is_boolean, terms = self.parse_search_term(search_term)
        
        highlight_patterns = []
        for term in terms:
            if term.startswith('EXACT:'):
                # For exact phrases, create a single pattern for the entire phrase
                exact_phrase = term[6:]  # Remove 'EXACT:' prefix
                words = exact_phrase.split()
                regex_words = [self.convert_wildcards_to_regex(word) for word in words]
                # Create exact phrase pattern
                phrase_pattern = r'\b' + r'\s+'.join(regex_words) + r'\b'
                highlight_patterns.append(phrase_pattern)
            else:
                # For regular terms, extract individual words
                words = term.split()
                for word in words:
                    # Convert wildcards to regex for individual word highlighting
                    word_regex = self.convert_wildcards_to_regex(word)
                    highlight_patterns.append(rf'\b{word_regex}\b')
        
        return highlight_patterns
    
    def abbreviate_text(self, text: str, search_term: str, ignore_case: bool) -> str:
        """Create abbreviated text showing only the matching portion with 8 words before and after"""
        flags = re.IGNORECASE if ignore_case else 0
        
        try:
            # Parse search term to understand if it's a phrase or individual words
            is_boolean, terms = self.parse_search_term(search_term)
            
            # For multi-word searches, try to find the best contiguous match
            if len(terms) == 1 and not terms[0].startswith('EXACT:') and len(terms[0].split()) > 1:
                # This is a multi-word search term (not quoted)
                # Try to find the position where most words appear together
                search_words = terms[0].split()
                words = text.split()
                best_start = -1
                best_end = -1
                best_score = 0
                
                # Look for the position with the highest concentration of search words
                for i in range(len(words)):
                    score = 0
                    consecutive_matches = 0
                    for j in range(min(len(search_words) * 2, len(words) - i)):  # Look ahead reasonable distance
                        word_lower = words[i + j].lower().strip('.,;:!?')
                        for search_word in search_words:
                            if (ignore_case and search_word.lower() in word_lower) or (search_word in words[i + j]):
                                score += 1
                                consecutive_matches += 1
                                break
                        else:
                            if consecutive_matches > 0:
                                score += consecutive_matches * 0.1  # Bonus for consecutive matches
                                consecutive_matches = 0
                    
                    if score > best_score:
                        best_score = score
                        best_start = i
                        # Set end to cover the area where matches were found
                        best_end = min(i + len(search_words) + 2, len(words) - 1)
                
                if best_start != -1:
                    # Extract 8 words before and after the best match area
                    start_word = max(0, best_start - 8)
                    end_word = min(len(words), best_end + 8)
                    
                    # Create abbreviated text
                    abbreviated_words = words[start_word:end_word]
                    
                    # Add ellipsis if we cut off the beginning or end
                    if start_word > 0:
                        abbreviated_words.insert(0, "...")
                    if end_word < len(words):
                        abbreviated_words.append("...")
                    
                    return " ".join(abbreviated_words)
            
            # Fall back to original method for other cases
            # Get patterns to highlight (exact phrases and individual words)
            highlight_patterns = self.get_search_words_for_highlighting(search_term)
            
            if not highlight_patterns:
                return text
            
            # Combine all patterns
            combined_pattern = '|'.join(highlight_patterns)
            
            # Find the first match
            match = re.search(combined_pattern, text, flags)
            
            if not match:
                return text
            
            # Split text into words
            words = text.split()
            
            # Find the word positions that contain the match
            current_pos = 0
            match_word_start = -1
            match_word_end = -1
            
            for i, word in enumerate(words):
                word_start = current_pos
                word_end = current_pos + len(word)
                
                # Check if this word overlaps with the match
                if (match.start() < word_end and match.end() > word_start):
                    if match_word_start == -1:
                        match_word_start = i
                    match_word_end = i
                
                # Move to next word position (including space)
                current_pos = word_end + 1
            
            if match_word_start == -1:
                return text
            
            # Extract 8 words before and after the match
            start_word = max(0, match_word_start - 8)
            end_word = min(len(words), match_word_end + 9)  # +9 because slice end is exclusive
            
            # Create abbreviated text
            abbreviated_words = words[start_word:end_word]
            
            # Add ellipsis if we cut off the beginning or end
            if start_word > 0:
                abbreviated_words.insert(0, "...")
            if end_word < len(words):
                abbreviated_words.append("...")
            
            return " ".join(abbreviated_words)
            
        except re.error:
            return text

    def highlight_text(self, text: str, search_term: str, ignore_case: bool) -> list:
        """Find text segments for highlighting exact phrases and individual words"""
        flags = re.IGNORECASE if ignore_case else 0
        highlighted_segments = []
        
        try:
            # Get patterns to highlight (exact phrases and individual words)
            highlight_patterns = self.get_search_words_for_highlighting(search_term)
            
            if not highlight_patterns:
                return [('normal', text)]
            
            # Combine all patterns
            combined_pattern = '|'.join(highlight_patterns)
            
            # Find all matches (exact phrases and individual words)
            matches = list(re.finditer(combined_pattern, text, flags))
            
            # Debug logging
            self.log_message(f"Highlighting pattern: {combined_pattern}")
            self.log_message(f"Found {len(matches)} matches for highlighting")
            for i, match in enumerate(matches):
                self.log_message(f"Match {i+1}: '{match.group()}' at position {match.start()}-{match.end()}")
            
            # Sort matches by position
            matches.sort(key=lambda x: x.start())
            
            last_end = 0
            for match in matches:
                # Add text before match
                if match.start() > last_end:
                    highlighted_segments.append(('normal', text[last_end:match.start()]))
                
                # Add highlighted word
                highlighted_segments.append(('highlight', text[match.start():match.end()]))
                last_end = match.end()
            
            # Add remaining text
            if last_end < len(text):
                highlighted_segments.append(('normal', text[last_end:]))
                
        except re.error:
            # If regex fails, just return the text as normal
            highlighted_segments = [('normal', text)]
            
        return highlighted_segments
    
    def perform_search(self):
        """Perform the Bible search and display results"""
        self.log_message("Search button clicked")
        start_time = time.time()
        
        try:
            # Clear treeview
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)
            # Clear current results and disable export button when clearing display
            self.current_results = []
            self.selected_search_results = []
            self.export_button.config(state=tk.DISABLED)
            self.update_search_selection_buttons()
            
            # Show "Searching" in status bar
            self.update_status("Searching...")
            self.root.update()
            
            # Get search term and remove mode suffix if present
            raw_search_term = self.search_var.get().strip()
            if '|' in raw_search_term:
                search_term = raw_search_term.split('|')[0].strip()
            else:
                search_term = raw_search_term
            
            # Check if placeholder is active or search term is empty
            if not search_term or self.placeholder_active:
                self.update_status("Please enter a search term or verse reference")
                return
            
            # Auto-detect search mode if it looks like a verse reference
            current_mode = self.search_mode_var.get()
            if self.is_verse_reference(search_term):
                if current_mode != "verse":
                    self.search_mode_var.set("verse")
                    self.update_search_placeholder()
                    self.log_message(f"Auto-detected verse reference, switched to verse search mode")
            else:
                # If it's not a verse reference, ensure word search is selected
                if current_mode != "word":
                    self.search_mode_var.set("word")
                    self.update_search_placeholder()
                    self.log_message(f"Auto-detected word search, switched to word search mode")
            
            # Check search mode
            search_mode = self.search_mode_var.get()
            
            if search_mode == "verse":
                # Handle verse search
                self.update_status("Looking up verses...")
                self.root.update()
                self.perform_verse_search_internal(search_term, start_time)
                return
            else:
                # Handle word search (existing functionality)
                self.add_search_history(search_term)
                
                # Check if database exists
                if not os.path.exists(self.sqlite_db_path):
                    self.update_status("Database not found")
                    return
                
                
                results = self.search_bible(
                    search_term=search_term,
                    translation=self.translation_var.get(),
                    ignore_case=self.ignore_case_var.get(),
                    proximity_window=self.proximity_var.get(),
                    book=self.book_var.get(),
                    chapter=self.chapter_var.get()
                )
            
            # Calculate search time
            search_time = time.time() - start_time
            
            if not results:
                self.update_status(f"No results found. Search completed in {search_time:.2f} seconds.")
                self.log_message(f"No results found for search term: {search_term}")
                self.current_results = []
                self.selected_search_results = []
                self.export_button.config(state=tk.DISABLED)
                self.update_search_selection_buttons()
            else:
                unique_verses = len(set(result['Reference'] for result in results))
                self.show_message(f"{len(results)} finds, {unique_verses} unique finds. Search completed in {search_time:.2f} seconds.")
                
                # Filter results if "Show unique verses only" is checked
                if self.unique_only_var.get():
                    seen_references = set()
                    filtered_results = []
                    for result in results:
                        if result['Reference'] not in seen_references:
                            seen_references.add(result['Reference'])
                            filtered_results.append(result)
                    results_to_display = filtered_results
                else:
                    results_to_display = results
                
                # Store filtered results for export and enable export button
                self.current_results = results_to_display
                self.export_button.config(state=tk.NORMAL)
                
                # Populate treeview with results
                self.log_message(f"About to populate treeview with {len(results_to_display)} results")
                
                for idx, result in enumerate(results_to_display):
                    # Determine the text to display (abbreviated or full)
                    display_text = result['Text']
                    if self.abbreviate_var.get():
                        display_text = self.abbreviate_text(result['Text'], result['search_term'], 
                                                          self.ignore_case_var.get())
                    
                    # Add highlighting to search terms in display text
                    segments = self.highlight_text(display_text, result['search_term'], 
                                                 self.ignore_case_var.get())
                    
                    highlighted_text = ""
                    for segment_type, segment_text in segments:
                        if segment_type == 'highlight':
                            highlighted_text += f"[{segment_text}]"
                        else:
                            highlighted_text += segment_text
                    
                    # Insert item into treeview with unchecked checkbox symbol
                    item_id = self.results_tree.insert('', 'end', 
                                                      text='☐',  # Unchecked checkbox
                                                      values=(result['Reference'], 
                                                             result['Translation'], 
                                                             highlighted_text),
                                                      tags=('unchecked',))
                    
                    self.log_message(f"Inserted treeview item {idx+1}: {result['Reference']} ({result['Translation']})")
                
                self.log_message(f"Treeview population completed. Total items in treeview: {len(self.results_tree.get_children())}")
                self.log_message(f"Found {len(results)} results for search term: {search_term}")
                
        except sqlite3.Error as e:
            search_time = time.time() - start_time
            error_message = f"Database error: {str(e)}"
            self.log_message(f"Database error in perform_search: {error_message}")
            self.update_status(f"Database error occurred. Search time: {search_time:.2f} seconds.")
        except Exception as e:
            search_time = time.time() - start_time
            error_message = str(e)
            import traceback
            traceback_str = traceback.format_exc()
            self.log_message(f"Error in perform_search: {error_message}")
            self.log_message(f"Full traceback: {traceback_str}")
            self.update_status(f"Search error occurred: {error_message}. Search time: {search_time:.2f} seconds.")
            
    
    def perform_verse_search_internal(self, search_term, start_time):
        """Internal verse search method used by perform_search"""
        try:
            # Lookup verses
            verses = self.lookup_verses_by_reference(search_term)
            
            if not verses:
                lookup_time = time.time() - start_time
                self.update_status(f"No verses found for the given reference(s). Time: {lookup_time:.2f} seconds.")
                return
            
            # Get the selected translation columns
            selected_translations = self.get_selected_translations()
            
            # Prepare results for processing (similar to word search structure)
            verse_results = []
            for verse_data in verses:
                verse_reference = verse_data[1]  # verse column
                
                for translation in selected_translations:
                    # Find the column index for this translation
                    translation_column = self.get_translation_column_index(translation)
                    if translation_column and len(verse_data) > translation_column:
                        verse_text = verse_data[translation_column]
                        if verse_text and verse_text.strip():
                            verse_results.append({
                                'Reference': verse_reference,
                                'Translation': translation,
                                'Text': verse_text,
                                'search_term': search_term  # For abbreviation purposes
                            })
            
            # Apply Bible scope filter (Old Testament, New Testament, or All)
            bible_scope = getattr(self, 'bible_scope_var', None)
            if bible_scope and bible_scope.get() != "bible":
                filtered_results = []
                if bible_scope.get() == "ot":
                    ot_books = self.get_old_testament_books()
                    for result in verse_results:
                        verse_book = result['Reference'].split()[0]
                        if len(result['Reference'].split()) > 1 and result['Reference'].split()[1].isdigit():
                            verse_book = f"{result['Reference'].split()[0]} {result['Reference'].split()[1]}"
                        if verse_book in ot_books:
                            filtered_results.append(result)
                elif bible_scope.get() == "nt":
                    nt_books = self.get_new_testament_books()
                    for result in verse_results:
                        verse_book = result['Reference'].split()[0]
                        if len(result['Reference'].split()) > 1 and result['Reference'].split()[1].isdigit():
                            verse_book = f"{result['Reference'].split()[0]} {result['Reference'].split()[1]}"
                        if verse_book in nt_books:
                            filtered_results.append(result)
                verse_results = filtered_results
            
            # Apply "Show unique verses only" filter if enabled
            if self.unique_only_var.get():
                seen_references = set()
                filtered_results = []
                for result in verse_results:
                    if result['Reference'] not in seen_references:
                        seen_references.add(result['Reference'])
                        filtered_results.append(result)
                verse_results = filtered_results
            
            # Display results
            self.current_results = verse_results  # Store processed results for verse display
            for result in verse_results:
                display_text = result['Text']
                
                # Apply abbreviation if enabled
                if self.abbreviate_var.get():
                    display_text = self.abbreviate_verse(display_text)
                
                # Insert into treeview with unchecked checkbox symbol
                item = self.results_tree.insert('', 'end', 
                                               text='☐',  # Unchecked checkbox
                                               values=(result['Reference'], result['Translation'], display_text),
                                               tags=('unchecked',))
            
            lookup_time = time.time() - start_time
            result_count = len(self.results_tree.get_children())
            total_verses = len(verses)
            unique_verses = len(set(result['Reference'] for result in verse_results))
            
            # Update status based on unique verses setting
            if self.unique_only_var.get():
                self.update_status(f"Found {unique_verses} unique verses. Lookup time: {lookup_time:.2f} seconds.")
            else:
                self.update_status(f"Found {result_count} verse translations, {unique_verses} unique verses. Lookup time: {lookup_time:.2f} seconds.")
            
            # Enable export if results found
            if result_count > 0:
                self.export_button.config(state=tk.NORMAL)
                
            # Add to search history (verse search mode)
            self.add_search_history(search_term)
                
        except Exception as e:
            lookup_time = time.time() - start_time
            error_message = str(e)
            self.log_message(f"Error in perform_verse_search_internal: {error_message}")
            self.update_status(f"Verse lookup error occurred. Time: {lookup_time:.2f} seconds.")
            
    def scroll_up(self):
        """Scroll the results treeview up"""
        current_selection = self.results_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            prev_item = self.results_tree.prev(current_item)
            if prev_item:
                self.results_tree.selection_set(prev_item)
                self.results_tree.focus(prev_item)
                self.results_tree.see(prev_item)
        else:
            children = self.results_tree.get_children()
            if children:
                self.results_tree.selection_set(children[-1])
                self.results_tree.focus(children[-1])
                
    def scroll_down(self):
        """Scroll the results treeview down"""
        current_selection = self.results_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            next_item = self.results_tree.next(current_item)
            if next_item:
                self.results_tree.selection_set(next_item)
                self.results_tree.focus(next_item)
                self.results_tree.see(next_item)
        else:
            children = self.results_tree.get_children()
            if children:
                self.results_tree.selection_set(children[0])
                self.results_tree.focus(children[0])
        
    def page_up(self):
        """Scroll the results treeview up by one page"""
        visible_items = int(self.results_tree['height'])
        current_selection = self.results_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            children = self.results_tree.get_children()
            current_index = children.index(current_item)
            new_index = max(0, current_index - visible_items)
            new_item = children[new_index]
            self.results_tree.selection_set(new_item)
            self.results_tree.focus(new_item)
            self.results_tree.see(new_item)
        
    def page_down(self):
        """Scroll the results treeview down by one page"""
        visible_items = int(self.results_tree['height'])
        current_selection = self.results_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            children = self.results_tree.get_children()
            current_index = children.index(current_item)
            new_index = min(len(children) - 1, current_index + visible_items)
            new_item = children[new_index]
            self.results_tree.selection_set(new_item)
            self.results_tree.focus(new_item)
            self.results_tree.see(new_item)

    def export_results(self):
        """Export current search results to a text file"""
        if not self.current_results:
            messagebox.showwarning("No Results", "No search results to export.")
            return
        
        # Get file path from user
        file_path = filedialog.asksaveasfilename(
            title="Export Search Results",
            initialdir=os.path.dirname(os.path.abspath(__file__)),
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # Write header with search information
                search_term = self.search_var.get().strip()
                f.write("Bible Search Results\n")
                f.write("=" * 50 + "\n")
                f.write(f"Search Term: {search_term}\n")
                f.write(f"Search Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Results: {len(self.current_results)}\n")
                
                # Add search settings
                f.write(f"Case Sensitive: {'No' if self.ignore_case_var.get() else 'Yes'}\n")
                f.write(f"Proximity Window: {self.proximity_var.get()} words\n")
                f.write(f"Book Filter: {self.book_var.get()}\n")
                f.write(f"Chapter Filter: {self.chapter_var.get() if self.chapter_var.get() > 0 else 'All'}\n")
                
                # Add selected translations
                selected_translations = [code for code, selected in self.selected_translations.items() if selected]
                if len(selected_translations) == len(self.selected_translations):
                    f.write("Translations: All\n")
                else:
                    f.write(f"Translations: {', '.join(selected_translations)}\n")
                
                f.write("\n" + "=" * 50 + "\n\n")
                
                # Write results
                for i, result in enumerate(self.current_results, 1):
                    f.write(f"{i}. {result['Reference']} ({result['Translation']})\n")
                    f.write(f"{result['Text']}\n\n")
                
            self.log_message(f"Search results exported to: {file_path}")
            self.show_blinking_status(f"Search results exported to {file_path}")
            
        except Exception as e:
            error_msg = f"Error exporting results: {str(e)}"
            self.log_message(error_msg)
            messagebox.showerror("Export Error", error_msg)

    # Subject Management Methods
    
    def load_subjects(self):
        """Load all subjects from database into the combobox"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM subjects ORDER BY name")
            subjects = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            self.subject_combobox['values'] = subjects
            self.log_message(f"Loaded {len(subjects)} subjects")
            
        except Exception as e:
            self.log_message(f"Error loading subjects: {e}")
    
    def move_to_current_subject(self):
        """Move selected verses (from search results or Bible Reading View) to the subject in the dropdown"""
        # Check if we have selections from either source
        has_search_selections = bool(self.selected_search_results)
        has_bible_selections = bool(self.selected_bible_verses)
        
        if not has_search_selections and not has_bible_selections:
            messagebox.showwarning("No Selection", "Please select verses from search results or Bible Reading View first.")
            return
            
        subject_name = self.subject_var.get().strip()
        if not subject_name:
            messagebox.showwarning("No Subject", "Please select a subject from the dropdown.")
            return
        
        # Check if subject exists, create if not
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject_name,))
            subject_row = cursor.fetchone()
            
            if not subject_row:
                # Create new subject
                cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
                subject_id = cursor.lastrowid
                self.load_subjects()  # Refresh combobox
            else:
                subject_id = subject_row[0]
            
            # Get current max order index
            cursor.execute("SELECT MAX(order_index) FROM subject_verses WHERE subject_id = ?", (subject_id,))
            max_order = cursor.fetchone()[0] or 0
            
            # Add selected verses from both sources
            moved_count = 0
            current_max_order = max_order
            
            # Process search results selections
            if has_search_selections:
                for idx, result_idx in enumerate(self.selected_search_results):
                    result = self.current_results[result_idx]
                    cursor.execute("""
                        INSERT INTO subject_verses (subject_id, verse_reference, verse_text, translation, order_index)
                        VALUES (?, ?, ?, ?, ?)
                    """, (subject_id, result['Reference'], result['Text'], result['Translation'], current_max_order + moved_count + 1))
                    moved_count += 1
            
            # Process Bible Reading View selections
            if has_bible_selections:
                for bible_verse_idx in sorted(self.selected_bible_verses):
                    if bible_verse_idx < len(self.current_bible_verses):
                        verse_data = self.current_bible_verses[bible_verse_idx]
                        cursor.execute("""
                            INSERT INTO subject_verses (subject_id, verse_reference, verse_text, translation, order_index)
                            VALUES (?, ?, ?, ?, ?)
                        """, (subject_id, verse_data['reference'], verse_data['text'], verse_data['translation'], current_max_order + moved_count + 1))
                        moved_count += 1
            
            conn.commit()
            conn.close()
            
            # Set as current subject and refresh display
            self.current_subject = subject_name
            self.load_subject_verses(subject_name)
            
            # Uncheck and clear moved verses from both sources
            if has_search_selections:
                self.uncheck_moved_verses(self.selected_search_results.copy())
                self.selected_search_results = []
                self.update_search_selection_buttons()
            
            if has_bible_selections:
                self.uncheck_moved_bible_verses(self.selected_bible_verses.copy())
                self.selected_bible_verses = set()
                self.update_move_button_state()
            
            self.log_message(f"Moved {moved_count} verses to subject: {subject_name}")
            
        except Exception as e:
            self.log_message(f"Error moving verses to subject: {e}")
            messagebox.showerror("Error", f"Error moving verses: {e}")
    
    def uncheck_moved_verses(self, moved_indices):
        """Uncheck verses in search results treeview after they've been moved"""
        try:
            children = self.results_tree.get_children()
            for result_index in moved_indices:
                if result_index < len(children):
                    item = children[result_index]
                    # Set to unchecked state
                    self.results_tree.item(item, text='☐')  # Unchecked checkbox
                    self.results_tree.item(item, tags=('unchecked',))
            
            self.log_message(f"Unchecked {len(moved_indices)} moved verses in search results")
            
        except Exception as e:
            self.log_message(f"Error unchecking moved verses: {e}")
    
    def uncheck_moved_bible_verses(self, moved_indices):
        """Uncheck verses in Bible Reading View treeview after they've been moved"""
        try:
            children = self.verse_display_tree.get_children()
            for bible_verse_index in moved_indices:
                if bible_verse_index < len(children):
                    item = children[bible_verse_index]
                    # Set to unchecked state
                    self.verse_display_tree.item(item, text='☐', tags=('unchecked',))
            
            self.log_message(f"Unchecked {len(moved_indices)} moved verses in Bible Reading View")
            
        except Exception as e:
            self.log_message(f"Error unchecking moved Bible verses: {e}")
    
    def on_subject_selected(self, event=None):
        """Handle subject selection from combobox"""
        # Handle placeholder state
        if self.subject_placeholder_active:
            self.subject_combobox.config(foreground='black')
            self.subject_placeholder_active = False
        
        subject_name = self.subject_var.get().strip()
        if subject_name and subject_name != self.subject_placeholder:
            # Check if this is a new subject (not in current values)
            current_values = list(self.subject_combobox['values']) if self.subject_combobox['values'] else []
            if subject_name not in current_values:
                self.create_subject_from_dropdown(subject_name)
            else:
                # Selected existing subject - reset dropdown to readonly and load subject
                # self.subject_combobox.config(state="readonly")  # Keep as normal to maintain white background
                self.current_subject = subject_name
                self.load_subject_verses(subject_name)
    
    def on_subject_return(self, event=None):
        """Handle Enter key press in subject combobox"""
        # Handle placeholder state
        if self.subject_placeholder_active:
            self.subject_combobox.config(foreground='black')
            self.subject_placeholder_active = False
            
        subject_name = self.subject_var.get().strip()
        if subject_name and subject_name != self.subject_placeholder:
            current_values = list(self.subject_combobox['values']) if self.subject_combobox['values'] else []
            if subject_name not in current_values:
                self.create_subject_from_dropdown(subject_name)
            else:
                # Selected existing subject - reset dropdown to readonly and load subject
                # self.subject_combobox.config(state="readonly")  # Keep as normal to maintain white background
                self.current_subject = subject_name
                self.load_subject_verses(subject_name)
    
    def enable_subject_creation(self):
        """Enable the dropdown for subject creation and focus on it"""
        # Auto-close current subject if one is open
        if self.current_subject:
            self.current_subject = None
            self.subject_text.delete(1.0, tk.END)
            self.enable_subject_controls(False)
            # Clear subject treeview
            for item in self.subject_tree.get_children():
                self.subject_tree.delete(item)
            self.selected_subject_verses.clear()
            self.update_subject_selection_buttons()
        
        # Enable the combobox for input
        self.subject_combobox.config(state="normal")
        # Clear any existing text
        self.subject_var.set("")
        # Focus on the combobox
        self.subject_combobox.focus()
        # Note: We don't disable the create button anymore since it should always be available
    
    def create_subject_from_dropdown(self, subject_name):
        """Create a new subject from dropdown entry"""
        # Auto-close current subject if one is open
        if self.current_subject:
            self.current_subject = None
            self.subject_text.delete(1.0, tk.END)
            self.enable_subject_controls(False)
            
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Create subject
            cursor.execute("INSERT INTO subjects (name) VALUES (?)", (subject_name,))
            subject_id = cursor.lastrowid
            
            # Add selected verses to subject (if any are selected)
            if self.selected_search_results:
                for idx, result_idx in enumerate(self.selected_search_results):
                    result = self.current_results[result_idx]
                    cursor.execute("""
                        INSERT INTO subject_verses (subject_id, verse_reference, verse_text, translation, order_index)
                        VALUES (?, ?, ?, ?, ?)
                    """, (subject_id, result['Reference'], result['Text'], result['Translation'], idx))
            
            conn.commit()
            conn.close()
            
            # Refresh subjects list and select new subject
            self.load_subjects()
            self.subject_var.set(subject_name)
            self.current_subject = subject_name
            self.load_subject_verses(subject_name)
            
            # Uncheck the moved verses in the search results treeview (if any were selected)
            if self.selected_search_results:
                self.uncheck_moved_verses(self.selected_search_results.copy())
                # Clear selection
                self.selected_search_results = []
                self.update_search_selection_buttons()
            
            # Reset dropdown to readonly state
            # self.subject_combobox.config(state="readonly")  # Keep as normal to maintain white background
            
            self.log_message(f"Created new subject from dropdown: {subject_name}")
            self.show_blinking_status(f"Subject '{subject_name}' created successfully!")
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Subject name already exists. Please choose a different name.")
            self.subject_var.set("")  # Clear the invalid entry
            # self.subject_combobox.config(state="readonly")  # Keep as normal to maintain white background  # Reset to readonly
        except Exception as e:
            self.log_message(f"Error creating subject from dropdown: {e}")
            messagebox.showerror("Error", f"Error creating subject: {e}")
            self.subject_var.set("")  # Clear the invalid entry
            # self.subject_combobox.config(state="readonly")  # Keep as normal to maintain white background  # Reset to readonly
    
    def load_subject_verses(self, subject_name):
        """Load verses for the selected subject"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sv.verse_reference, sv.verse_text, sv.translation, sv.comments, sv.id
                FROM subject_verses sv
                JOIN subjects s ON sv.subject_id = s.id
                WHERE s.name = ?
                ORDER BY sv.order_index
            """, (subject_name,))
            
            verses = cursor.fetchall()
            conn.close()
            
            self.subject_verses = verses
            self.display_subject_verses()
            
            # Enable subject controls
            self.enable_subject_controls(True)
            
        except Exception as e:
            self.log_message(f"Error loading subject verses: {e}")
            messagebox.showerror("Error", f"Error loading verses: {e}")
    
    def display_subject_verses(self):
        """Display subject verses in the treeview"""
        # Clear treeview
        for item in self.subject_tree.get_children():
            self.subject_tree.delete(item)
        
        # Clear selected verses list
        self.selected_subject_verses = []
        
        if self.current_subject is None:
            # Insert placeholder when no subject is selected
            self.subject_tree.insert('', 'end', text='', values=('Subject', '', ''), tags=('placeholder',))
            return
        elif not self.subject_verses:
            # Insert a placeholder item when subject is selected but has no verses
            self.subject_tree.insert('', 'end', text='', values=('', '', 'No verses in this subject.'), tags=('unchecked',))
            return
        
        for i, (reference, text, translation, comments, verse_id) in enumerate(self.subject_verses):
            # Apply abbreviation to subject verses display
            display_text = self.abbreviate_verse(text)
            
            # Insert item into subject treeview with unchecked checkbox (no comments column)
            item_id = self.subject_tree.insert('', 'end', 
                                              text='☐',  # Unchecked checkbox
                                              values=(reference, translation, display_text),
                                              tags=('unchecked',))
        
        # Update button states
        self.update_subject_selection_buttons()
    
    def get_verse_comments(self, reference, translation):
        """Get comments for a specific verse from the database"""
        try:
            if not hasattr(self, 'current_subject') or not self.current_subject:
                return ""
                
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sv.comments
                FROM subject_verses sv
                JOIN subjects s ON sv.subject_id = s.id
                WHERE s.name = ? AND sv.verse_reference = ? AND sv.translation = ?
            """, (self.current_subject, reference, translation))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else ""
            
        except Exception as e:
            self.log_message(f"Error getting verse comments: {e}")
            return ""
    
    def create_comment(self):
        """Create a comment for the currently selected verse"""
        try:
            selection = self.subject_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a verse to add a comment to.")
                return
                
            # Enable text widget for editing
            self.comments_text.config(state=tk.NORMAL)
            self.comments_text.focus()
            
            # Enable save button, disable create button
            self.save_comment_button.config(state=tk.NORMAL)
            self.create_comment_button.config(state=tk.DISABLED)
            
        except Exception as e:
            self.log_message(f"Error creating comment: {e}")
            messagebox.showerror("Error", f"Error creating comment: {e}")
    
    def edit_comment(self):
        """Edit the comment for the currently selected verse"""
        try:
            selection = self.subject_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a verse to edit comment.")
                return
                
            # Enable text widget for editing
            self.comments_text.config(state=tk.NORMAL)
            self.comments_text.focus()
            
            # Enable save button, disable edit button
            self.save_comment_button.config(state=tk.NORMAL)
            self.edit_comment_button.config(state=tk.DISABLED)
            
        except Exception as e:
            self.log_message(f"Error editing comment: {e}")
            messagebox.showerror("Error", f"Error editing comment: {e}")
    
    def save_comment(self):
        """Save the comment for the currently selected verse"""
        try:
            selection = self.subject_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a verse to save comment.")
                return
                
            item = selection[0]
            values = self.subject_tree.item(item, 'values')
            if len(values) >= 3:
                reference = values[0]
                translation = values[1]
                
                # Get comment text
                comment_text = self.comments_text.get(1.0, tk.END).strip()
                
                # Update database
                conn = sqlite3.connect(self.sqlite_db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE subject_verses 
                    SET comments = ?
                    WHERE verse_reference = ? AND translation = ? AND subject_id IN (
                        SELECT id FROM subjects WHERE name = ?
                    )
                """, (comment_text if comment_text else None, reference, translation, self.current_subject))
                
                conn.commit()
                conn.close()
                
                # Disable text widget and reset buttons
                self.comments_text.config(state=tk.DISABLED)
                self.save_comment_button.config(state=tk.DISABLED)
                self.create_comment_button.config(state=tk.NORMAL)
                self.edit_comment_button.config(state=tk.NORMAL)
                
                self.show_blinking_status("Comment saved successfully.")
                
        except Exception as e:
            self.log_message(f"Error saving comment: {e}")
            messagebox.showerror("Error", f"Error saving comment: {e}")
    
    def delete_comment(self):
        """Delete the comment for the currently selected verse"""
        try:
            selection = self.subject_tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a verse to delete comment.")
                return
                
            # Confirm deletion
            result = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this comment?")
            if not result:
                return
                
            item = selection[0]
            values = self.subject_tree.item(item, 'values')
            if len(values) >= 3:
                reference = values[0]
                translation = values[1]
                
                # Update database
                conn = sqlite3.connect(self.sqlite_db_path)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE subject_verses 
                    SET comments = NULL
                    WHERE verse_reference = ? AND translation = ? AND subject_id IN (
                        SELECT id FROM subjects WHERE name = ?
                    )
                """, (reference, translation, self.current_subject))
                
                conn.commit()
                conn.close()
                
                # Clear comments text widget
                self.comments_text.config(state=tk.NORMAL)
                self.comments_text.delete(1.0, tk.END)
                self.comments_text.config(state=tk.DISABLED)
                
                self.show_blinking_status("Comment deleted successfully.")
                
        except Exception as e:
            self.log_message(f"Error deleting comment: {e}")
            messagebox.showerror("Error", f"Error deleting comment: {e}")
    
    def enable_subject_controls(self, enable=True):
        """Enable or disable subject control buttons"""
        state = tk.NORMAL if enable else tk.DISABLED
        
        # Delete button is now controlled by verse selection, not subject loading
        # self.delete_button.config(state=state)  # Managed by update_subject_selection_buttons()
        self.export_subject_button.config(state=state)
        
        # Enable comment controls only when a subject is loaded
        comment_state = tk.NORMAL if enable else tk.DISABLED
        self.create_comment_button.config(state=comment_state)
        # Edit/Delete comment buttons will be enabled only when verse is selected
    
    def update_search_selection_buttons(self):
        """Update state of search result selection buttons"""
        has_selection = len(self.selected_search_results) > 0
        state = tk.NORMAL if has_selection else tk.DISABLED
        
        # Create Subject button is always enabled
        # self.create_subject_button.config(state=tk.NORMAL)  # Always enabled
        self.move_to_subject_button.config(state=state)
    
    def on_treeview_click(self, event):
        """Handle treeview click events for checkbox toggling"""
        region = self.results_tree.identify("region", event.x, event.y)
        if region == "tree":
            item = self.results_tree.identify_row(event.y)
            if item:
                self.toggle_treeview_checkbox(item)
    
    def on_treeview_space(self, event):
        """Handle space key press for checkbox toggling"""
        selection = self.results_tree.selection()
        if selection:
            self.toggle_treeview_checkbox(selection[0])
    
    def toggle_treeview_checkbox(self, item):
        """Toggle checkbox state for a treeview item"""
        try:
            # Get current checkbox state
            current_checkbox = self.results_tree.item(item, 'text')
            
            # Get the item index from the treeview
            children = self.results_tree.get_children()
            item_index = children.index(item)
            
            if current_checkbox == '☐':  # Unchecked
                # Check the item
                self.results_tree.item(item, text='☑')  # Checked checkbox
                self.results_tree.item(item, tags=('checked',))
                if item_index not in self.selected_search_results:
                    self.selected_search_results.append(item_index)
            else:  # Checked
                # Uncheck the item
                self.results_tree.item(item, text='☐')  # Unchecked checkbox
                self.results_tree.item(item, tags=('unchecked',))
                if item_index in self.selected_search_results:
                    self.selected_search_results.remove(item_index)
            
            # Update button states
            self.update_search_selection_buttons()
            
        except Exception as e:
            self.log_message(f"Error toggling checkbox: {e}")
    
    def toggle_search_result_selection(self, index):
        """Legacy method for compatibility - redirects to treeview implementation"""
        children = self.results_tree.get_children()
        if index < len(children):
            self.toggle_treeview_checkbox(children[index])
    
    def on_subject_treeview_click(self, event):
        """Handle subject treeview click events for checkbox toggling"""
        region = self.subject_tree.identify("region", event.x, event.y)
        if region == "tree":
            item = self.subject_tree.identify_row(event.y)
            if item:
                self.toggle_subject_checkbox(item)
    
    def on_subject_treeview_space(self, event):
        """Handle space key press for subject checkbox toggling"""
        selection = self.subject_tree.selection()
        if selection:
            self.toggle_subject_checkbox(selection[0])
    
    def toggle_subject_checkbox(self, item):
        """Toggle checkbox state for a subject treeview item"""
        try:
            # Get current checkbox state
            current_checkbox = self.subject_tree.item(item, 'text')
            
            # Get the item index from the treeview
            children = self.subject_tree.get_children()
            item_index = children.index(item)
            
            if current_checkbox == '☐':  # Unchecked
                # Check the item
                self.subject_tree.item(item, text='☑')  # Checked checkbox
                self.subject_tree.item(item, tags=('checked',))
                if item_index not in self.selected_subject_verses:
                    self.selected_subject_verses.append(item_index)
            else:  # Checked
                # Uncheck the item
                self.subject_tree.item(item, text='☐')  # Unchecked checkbox
                self.subject_tree.item(item, tags=('unchecked',))
                if item_index in self.selected_subject_verses:
                    self.selected_subject_verses.remove(item_index)
            
            # Update button states based on selection
            self.update_subject_selection_buttons()
            
        except Exception as e:
            self.log_message(f"Error toggling subject checkbox: {e}")
    
    def update_subject_selection_buttons(self):
        """Update state of subject verse selection buttons"""
        has_selection = len(self.selected_subject_verses) > 0
        state = tk.NORMAL if has_selection else tk.DISABLED
        
        # Update delete entry button state
        self.delete_button.config(state=state)
    
    def on_subject_tree_selection(self, event):
        """Handle selection changes in subject treeview to update comments display"""
        try:
            selection = self.subject_tree.selection()
            if selection:
                # Get the selected item data
                item = selection[0]
                values = self.subject_tree.item(item, 'values')
                if len(values) >= 3:  # reference, translation, text
                    reference = values[0]
                    translation = values[1]
                    
                    # Get comments from database for this specific verse
                    comments = self.get_verse_comments(reference, translation)
                    
                    # Update the comments text widget
                    self.comments_text.config(state=tk.NORMAL)
                    self.comments_text.delete(1.0, tk.END)
                    self.comments_text.insert(1.0, comments)
                    self.comments_text.config(state=tk.DISABLED)
                    
                    # Enable comment editing buttons when verse is selected
                    if hasattr(self, 'current_subject') and self.current_subject:
                        self.edit_comment_button.config(state=tk.NORMAL)
                        self.delete_comment_button.config(state=tk.NORMAL)
                    
                    # Navigate to the verse in Bible view
                    self.log_message(f"Subject verse selection - navigating to: {reference}")
                    self.navigate_to_verse(reference)
            else:
                # Clear comments if no selection
                self.comments_text.config(state=tk.NORMAL)
                self.comments_text.delete(1.0, tk.END)
                self.comments_text.config(state=tk.DISABLED)
                
                # Disable comment editing buttons when no verse selected
                self.edit_comment_button.config(state=tk.DISABLED)
                self.delete_comment_button.config(state=tk.DISABLED)
        except Exception as e:
            self.log_message(f"Error updating comments display: {e}")
    
    # Subject navigation and control methods
    
    def subject_line_up(self):
        """Move selection up in subject treeview"""
        current_selection = self.subject_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            prev_item = self.subject_tree.prev(current_item)
            if prev_item:
                self.subject_tree.selection_set(prev_item)
                self.subject_tree.focus(prev_item)
                self.subject_tree.see(prev_item)
        else:
            children = self.subject_tree.get_children()
            if children:
                self.subject_tree.selection_set(children[-1])
                self.subject_tree.focus(children[-1])
        
    def subject_line_down(self):
        """Move selection down in subject treeview"""
        current_selection = self.subject_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            next_item = self.subject_tree.next(current_item)
            if next_item:
                self.subject_tree.selection_set(next_item)
                self.subject_tree.focus(next_item)
                self.subject_tree.see(next_item)
        else:
            children = self.subject_tree.get_children()
            if children:
                self.subject_tree.selection_set(children[0])
                self.subject_tree.focus(children[0])
        
    def subject_page_up(self):
        """Move selection up by one page in subject treeview"""
        visible_items = int(self.subject_tree['height'])
        current_selection = self.subject_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            children = self.subject_tree.get_children()
            current_index = children.index(current_item)
            new_index = max(0, current_index - visible_items)
            new_item = children[new_index]
            self.subject_tree.selection_set(new_item)
            self.subject_tree.focus(new_item)
            self.subject_tree.see(new_item)
        
    def subject_page_down(self):
        """Move selection down by one page in subject treeview"""
        visible_items = int(self.subject_tree['height'])
        current_selection = self.subject_tree.selection()
        if current_selection:
            current_item = current_selection[0]
            children = self.subject_tree.get_children()
            current_index = children.index(current_item)
            new_index = min(len(children) - 1, current_index + visible_items)
            new_item = children[new_index]
            self.subject_tree.selection_set(new_item)
            self.subject_tree.focus(new_item)
            self.subject_tree.see(new_item)
    
    def create_new_entry(self):
        """Create a new verse entry in current subject"""
        if not self.current_subject:
            messagebox.showwarning("No Subject", "Please select a subject first.")
            return
            
        # Simple dialog to add verse reference and text
        reference = simpledialog.askstring("New Entry", "Enter verse reference (e.g., John 3:16):")
        if not reference:
            return
            
        text = simpledialog.askstring("New Entry", "Enter verse text:")
        if not text:
            return
            
        translation = simpledialog.askstring("New Entry", "Enter translation (e.g., KJV):", initialvalue="KJV")
        if not translation:
            translation = "KJV"
        
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get subject ID
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (self.current_subject,))
            subject_id = cursor.fetchone()[0]
            
            # Get max order index
            cursor.execute("SELECT MAX(order_index) FROM subject_verses WHERE subject_id = ?", (subject_id,))
            max_order = cursor.fetchone()[0] or 0
            
            # Insert new verse
            cursor.execute("""
                INSERT INTO subject_verses (subject_id, verse_reference, verse_text, translation, order_index)
                VALUES (?, ?, ?, ?, ?)
            """, (subject_id, reference, text, translation, max_order + 1))
            
            conn.commit()
            conn.close()
            
            # Refresh display
            self.load_subject_verses(self.current_subject)
            
        except Exception as e:
            self.log_message(f"Error creating new entry: {e}")
            messagebox.showerror("Error", f"Error creating entry: {e}")
    
    def show_deletion_dialog(self, count):
        """Show dialog to choose deletion type"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Options")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Result variable
        result = {"choice": None}
        
        # Main message
        message = f"You have selected {count} verse(s) to delete.\nWhat would you like to delete?"
        ttk.Label(dialog, text=message, font=('Arial', 10)).pack(pady=20)
        
        # Buttons frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=20)
        
        def delete_comments_only():
            result["choice"] = "comments_only"
            dialog.destroy()
            
        def delete_verse_and_comments():
            result["choice"] = "verse_and_comments"
            dialog.destroy()
            
        def cancel():
            result["choice"] = None
            dialog.destroy()
        
        ttk.Button(button_frame, text="Delete Comments Only", 
                  command=delete_comments_only, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Verse & Comments", 
                  command=delete_verse_and_comments, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", 
                  command=cancel, width=10).pack(side=tk.LEFT, padx=5)
        
        # Wait for dialog to close
        dialog.wait_window()
        
        return result["choice"]
    
    def delete_selected_entries(self):
        """Delete selected entries from current subject"""
        if not self.selected_subject_verses:
            messagebox.showwarning("No Selection", "Please select verses to delete.")
            return
            
        if not self.current_subject:
            messagebox.showwarning("No Subject", "Please select a subject first.")
            return
            
        # Show custom dialog for deletion options
        count = len(self.selected_subject_verses)
        deletion_choice = self.show_deletion_dialog(count)
        if not deletion_choice:
            return
            
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get subject ID
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (self.current_subject,))
            subject_id = cursor.fetchone()[0]
            
            # Handle deletion based on user choice
            deleted_count = 0
            for verse_index in sorted(self.selected_subject_verses, reverse=True):
                if verse_index < len(self.subject_verses):
                    verse_data = self.subject_verses[verse_index]
                    verse_id = verse_data[4]  # verse_id is the 5th element (index 4)
                    
                    if deletion_choice == "comments_only":
                        # Delete only comments, keep the verse
                        cursor.execute("UPDATE subject_verses SET comments = NULL WHERE id = ?", (verse_id,))
                    else:  # deletion_choice == "verse_and_comments"
                        # Delete the entire verse (and its comments)
                        cursor.execute("DELETE FROM subject_verses WHERE id = ?", (verse_id,))
                    deleted_count += 1
            
            conn.commit()
            conn.close()
            
            # Refresh display
            self.load_subject_verses(self.current_subject)
            
            if deletion_choice == "comments_only":
                self.show_blinking_status(f"Successfully deleted comments from {deleted_count} verse(s).")
            else:
                self.show_blinking_status(f"Successfully deleted {deleted_count} verse(s) and their comments.")
            
        except Exception as e:
            self.log_message(f"Error deleting entries: {e}")
            messagebox.showerror("Error", f"Error deleting entries: {e}")
    
    def toggle_edit_mode(self):
        """Toggle edit mode for subject verses"""
        # For now, editing mode is not implemented for treeview
        # This could be expanded to allow inline editing of verse text and comments
        messagebox.showinfo("Edit Mode", "Editing mode for treeview is not yet implemented.\nUse Create New Entry and Delete Entry buttons to manage verses.")
    
    def save_subject_changes(self):
        """Save changes made in edit mode"""
        # With treeview implementation, this is not needed
        messagebox.showinfo("Save", "No changes to save. Use Create New Entry and Delete Entry buttons to manage verses.")
    
    def show_delete_dialog(self):
        """Show dialog with delete options"""
        if not self.current_subject:
            messagebox.showwarning("No Subject", "Please select a subject first.")
            return
        
        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Delete Options")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Add label
        label = ttk.Label(dialog, text=f"What would you like to delete from\n'{self.current_subject}'?")
        label.pack(pady=20)
        
        # Add buttons frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        # Delete comments only button
        ttk.Button(button_frame, text="Delete Comments Only", 
                  command=lambda: self.handle_delete_choice(dialog, "comments")).pack(side=tk.LEFT, padx=5)
        
        # Delete subject and comments button
        ttk.Button(button_frame, text="Delete Subject & Comments", 
                  command=lambda: self.handle_delete_choice(dialog, "subject")).pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        ttk.Button(button_frame, text="Cancel", 
                  command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def handle_delete_choice(self, dialog, choice):
        """Handle the delete choice from dialog"""
        dialog.destroy()
        
        if choice == "comments":
            self.delete_selected_entries()
        elif choice == "subject":
            self.delete_current_subject()
    
    def delete_current_subject(self):
        """Delete the current subject and all its verses"""
        if not self.current_subject:
            messagebox.showwarning("No Subject", "Please select a subject first.")
            return
            
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete the subject '{self.current_subject}' and all its verses?")
        if not result:
            return
            
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Delete subject (cascades to verses due to foreign key)
            cursor.execute("DELETE FROM subjects WHERE name = ?", (self.current_subject,))
            
            conn.commit()
            conn.close()
            
            # Clear display and refresh subjects
            deleted_subject = self.current_subject
            self.current_subject = None
            self.subject_var.set("")
            self.subject_text.delete(1.0, tk.END)
            self.load_subjects()
            self.enable_subject_controls(False)
            
            self.show_blinking_status(f"Subject '{deleted_subject}' deleted successfully.")
            
        except Exception as e:
            self.log_message(f"Error deleting subject: {e}")
            messagebox.showerror("Error", f"Error deleting subject: {e}")
    
    def export_current_subject(self):
        """Export current subject to a text file"""
        if not self.current_subject or not self.subject_verses:
            messagebox.showwarning("No Subject", "Please select a subject with verses first.")
            return
            
        # Get file path from user
        file_path = filedialog.asksaveasfilename(
            title="Export Subject",
            initialdir=os.path.dirname(os.path.abspath(__file__)),
            initialname=f"{self.current_subject}.txt",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Subject: {self.current_subject}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Verses: {len(self.subject_verses)}\n\n")
                
                for i, (reference, text, translation, comments, verse_id) in enumerate(self.subject_verses, 1):
                    f.write(f"{i}. {reference} ({translation})\n")
                    f.write(f"{text}\n")
                    if comments:
                        f.write(f"Comments: {comments}\n")
                    f.write("\n")
                    
            self.show_blinking_status(f"Subject exported to {file_path}")
            
        except Exception as e:
            self.log_message(f"Error exporting subject: {e}")
            messagebox.showerror("Error", f"Error exporting subject: {e}")

    def show_search_help(self):
        """Show search terms help window"""
        help_window = tk.Toplevel(self.root)
        help_window.title("Search Terms Help")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        
        # Make window modal
        help_window.transient(self.root)
        help_window.grab_set()
        
        # Main frame with padding
        help_frame = ttk.Frame(help_window, padding="15")
        help_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(help_frame, text="Search Terms and Examples", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Help text with examples
        help_text = """BASIC SEARCH:
• Simple word: love
• Multiple words: love peace (finds verses with both words nearby)

EXACT PHRASES:
• Use double quotes to search for exact phrases
  Example: "in the beginning" finds only the exact phrase
  Example: "love your neighbor" finds the exact phrase in that order
• Quoted phrases can be combined with other terms
  Example: "the Lord" AND justice

WILDCARDS:
• * (asterisk): Matches any number of characters
  Example: love* finds love, loved, loves, loving
• ? (question mark): Matches exactly one character
  Example: l?ve finds love, live

BOOLEAN OPERATORS:
• AND: Both terms must be present
  Example: love AND peace
  Example: "the Lord" AND mercy
• OR: Either term can be present
  Example: love OR peace
  Example: "Jesus Christ" OR "Christ Jesus"

PROXIMITY SEARCH:
• Set proximity value to find words within a certain distance
• Default is 5 words between search terms
• Works with multiple words automatically (not in quotes)

FILTERS:
• Book: Search within specific Bible book
• Chapter: Search within specific chapter (requires book selection)
• Translation: Search specific Bible translation

EXAMPLES:
• "in the beginning" → finds exact phrase match
• faith* AND hope → finds verses with faith/faithful/faithfulness AND hope
• "Jesus Christ" OR "Christ Jesus" → finds either exact phrase
• peace* → finds peace, peaceful, peaceable, etc.
• love AND neighbor (proximity: 3) → finds love and neighbor within 3 words
• "the day of the Lord" → finds exact phrase match

VERSE SEARCH MODE:
Select "Verse Search" radio button to lookup specific verses by reference.

VERSE REFERENCE FORMATS:
• Single verse: Genesis 1:8, John 3:16
• Verse range: Matthew 3:7-11, Romans 8:28-30
• Verse list: 1 Cor 3:10,11, Psalm 23:1,6
• Multiple references: Mark 1:3, Dan 12:2

BOOK NAME ABBREVIATIONS:
• Full names: Genesis, Matthew, 1 Corinthians, 2 Timothy
• Common abbreviations: Gen, Mat, 1 Cor, 2 Tim
• Alternative forms: Cor (1 Corinthians), Thess (1 Thessalonians)

VERSE SEARCH EXAMPLES:
• Matthew 5:3-8 → Beatitudes verses 3 through 8
• John 3:16 → Single verse lookup
• 1 Cor 13:4,7,13 → Love chapter specific verses
• Gen 1:1, John 1:1, Rev 22:21 → First, middle, and last verses"""
        
        # Text widget with scrollbar
        text_widget = scrolledtext.ScrolledText(help_frame, width=70, height=25, wrap=tk.WORD)
        text_widget.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Close button
        close_button = ttk.Button(help_frame, text="Close", command=help_window.destroy)
        close_button.grid(row=2, column=0, pady=(10, 0))
        
        # Configure grid weights
        help_window.columnconfigure(0, weight=1)
        help_window.rowconfigure(0, weight=1)
        help_frame.columnconfigure(0, weight=1)
        help_frame.rowconfigure(1, weight=1)
        
        # Center the window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (help_window.winfo_width() // 2)
        y = (help_window.winfo_screenheight() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")

    def show_translation_dialog(self):
        """Show translation selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Translations")
        dialog.geometry("450x450")
        dialog.resizable(True, True)
        
        # Make window modal
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main frame with padding
        main_frame = ttk.Frame(dialog, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Select Bible Translations", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(main_frame, text="Check the translations you want to search:", 
                                font=('Arial', 9))
        instructions.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Checkboxes frame with scrollbar
        canvas = tk.Canvas(main_frame, height=250)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        
        # Translation options with descriptions
        translations = [
            ("KJV", "King James Version"),
            ("ASV", "American Standard Version"),
            ("DRB", "Douay-Rheims Bible"),
            ("DBT", "Darby Bible Translation"),
            ("ERV", "English Revised Version"),
            ("WBT", "Webster Bible Translation"),
            ("WEB", "World English Bible"),
            ("YLT", "Young's Literal Translation"),
            ("AKJV", "American King James Version"),
            ("WNT", "Weymouth New Testament"),
            ("BISHOPS", "Bishops Bible (1568)"),
            ("COVERDALE", "Coverdale Bible (1535)"),
            ("GENEVA", "Geneva Bible (1587)"),
            ("NET", "NET Bible"),
            ("TYNDALE", "Tyndale Bible (1534)")
        ]
        
        # Create checkbox and order variables
        self.translation_vars = {}
        self.translation_order_vars = {}
        
        # Add column headers
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5), padx=(10, 0))
        ttk.Label(header_frame, text="Translation", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(header_frame, text="Order", font=('Arial', 9, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=(200, 0))
        
        # Create checkboxes and order inputs
        for i, (code, name) in enumerate(translations):
            row = i + 1  # Start after header
            
            # Checkbox
            var = tk.BooleanVar(value=self.selected_translations[code])
            self.translation_vars[code] = var
            
            checkbox = ttk.Checkbutton(scrollable_frame, text=f"{code} - {name}", 
                                     variable=var)
            checkbox.grid(row=row, column=0, sticky=tk.W, pady=2, padx=(10, 0))
            
            # Order number input
            order_var = tk.IntVar(value=self.translation_order[code])
            self.translation_order_vars[code] = order_var
            
            order_entry = ttk.Entry(scrollable_frame, width=5, 
                                   textvariable=order_var)
            order_entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(20, 0))
        
        # Select All / None buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, pady=(15, 0))
        
        select_all_btn = ttk.Button(buttons_frame, text="Select All", 
                                   command=lambda: self.toggle_all_translations(True))
        select_all_btn.grid(row=0, column=0, padx=(0, 5))
        
        select_none_btn = ttk.Button(buttons_frame, text="Select None", 
                                    command=lambda: self.toggle_all_translations(False))
        select_none_btn.grid(row=0, column=1, padx=(5, 0))
        
        # OK and Cancel buttons
        ok_cancel_frame = ttk.Frame(main_frame)
        ok_cancel_frame.grid(row=4, column=0, pady=(15, 0))
        
        ok_button = ttk.Button(ok_cancel_frame, text="OK", 
                              command=lambda: self.apply_translation_selection(dialog))
        ok_button.grid(row=0, column=0, padx=(0, 5))
        
        cancel_button = ttk.Button(ok_cancel_frame, text="Cancel", 
                                  command=dialog.destroy)
        cancel_button.grid(row=0, column=1, padx=(5, 0))
        
        # Configure grid weights
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=0)  # Scrollbar column
        main_frame.rowconfigure(2, weight=1)
        
        # Center the window
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def toggle_all_translations(self, select_all):
        """Toggle all translation checkboxes"""
        for var in self.translation_vars.values():
            var.set(select_all)

    def apply_translation_selection(self, dialog):
        """Apply the translation selection and close dialog"""
        # Update selected translations
        for code, var in self.translation_vars.items():
            self.selected_translations[code] = var.get()
        
        # Update translation order
        for code, order_var in self.translation_order_vars.items():
            self.translation_order[code] = order_var.get()
        
        # Update translation_var for compatibility with existing code
        selected_count = sum(self.selected_translations.values())
        if selected_count == 0:
            # If none selected, select KJV as default
            self.selected_translations["KJV"] = True
            selected_count = 1
        
        if selected_count == len(self.selected_translations):
            self.translation_var.set("All")
        elif selected_count == 1:
            # Find the single selected translation
            for code, selected in self.selected_translations.items():
                if selected:
                    self.translation_var.set(code)
                    break
        else:
            self.translation_var.set(f"{selected_count} selected")
        
        # Update button text to show selection
        selected_codes = [code for code, selected in self.selected_translations.items() if selected]
        if len(selected_codes) == len(self.selected_translations):
            button_text = "Translations (All)"
        elif len(selected_codes) == 1:
            button_text = f"Translations ({selected_codes[0]})"
        else:
            button_text = f"Translations ({len(selected_codes)})"
        
        # Update translation button in search area if it exists
        if hasattr(self, 'translation_button_search'):
            self.translation_button_search.config(text=button_text)
        dialog.destroy()

    def update_translation_button_text(self):
        """Update the translation button text based on current selection"""
        try:
            selected_codes = [code for code, selected in self.selected_translations.items() if selected]
            if len(selected_codes) == len(self.selected_translations):
                button_text = "Translations (All)"
            elif len(selected_codes) == 1:
                button_text = f"Translations ({selected_codes[0]})"
            elif len(selected_codes) == 0:
                button_text = "Translations (KJV)"  # Default fallback
            else:
                button_text = f"Translations ({len(selected_codes)})"
            
            # Update translation button in search area if it exists
            if hasattr(self, 'translation_button_search'):
                self.translation_button_search.config(text=button_text)
        except Exception as e:
            self.log_message(f"Error updating translation button text: {e}")

    def on_search_results_select(self, event):
        """Handle selection changes in search results treeview to navigate to Bible view"""
        try:
            self.log_message("Search results selection event triggered")
            selection = self.results_tree.selection()
            self.log_message(f"Selection: {selection}")
            if selection:
                # Get the selected item data
                item = selection[0]
                values = self.results_tree.item(item, 'values')
                self.log_message(f"Selected item values: {values}")
                if len(values) >= 3:  # reference, translation, text
                    reference = values[0]
                    translation = values[1]
                    self.log_message(f"Extracted reference: {reference}, translation: {translation}")
                    
                    # Update the current translation for Bible Reading View
                    self.current_bible_translation = translation
                    self.update_bible_reading_view_label(translation)
                    
                    # Navigate to the verse in Bible view (target verse at top)
                    self.navigate_to_verse(reference)
            else:
                # Clear verse display if no selection - for treeview, just clear the treeview
                self.log_message("No selection, clearing verse display")
                if hasattr(self, 'verse_display_tree'):
                    for item in self.verse_display_tree.get_children():
                        self.verse_display_tree.delete(item)
                    self.current_bible_verses = []
                    self.selected_bible_verses = set()
                    self.update_move_button_state()
        except Exception as e:
            self.log_message(f"Error updating verse display from search results: {e}")

    def update_verse_display(self, text):
        """Update the verse display window with the given text (legacy function for backward compatibility)"""
        try:
            # This function is now obsolete since we use display_bible_view() with treeview
            # Clear the treeview if text is empty, otherwise do nothing (display_bible_view handles population)
            if not text and hasattr(self, 'verse_display_tree'):
                for item in self.verse_display_tree.get_children():
                    self.verse_display_tree.delete(item)
                self.current_bible_verses = []
                self.selected_bible_verses = set()
                self.update_move_button_state()
        except Exception as e:
            self.log_message(f"Error updating verse display: {e}")

    def get_verse_by_id(self, verse_id):
        """Get a verse by its ID from the database"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bible_verses WHERE id = ?", (verse_id,))
            result = cursor.fetchone()
            conn.close()
            return result
        except Exception as e:
            self.log_message(f"Error getting verse by ID {verse_id}: {e}")
            return None

    def get_total_verses_count(self):
        """Get the total number of verses in the database"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(id) FROM bible_verses")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else 31102  # Default to typical Bible verse count
        except Exception as e:
            self.log_message(f"Error getting total verses count: {e}")
            return 31102

    def get_verse_id_from_reference(self, reference):
        """Get the verse ID from a verse reference like 'Genesis 1:1'"""
        try:
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM bible_verses WHERE verse = ?", (reference,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except Exception as e:
            self.log_message(f"Error getting verse ID for reference {reference}: {e}")
            return None

    def navigate_to_verse(self, reference):
        """Navigate to a specific verse in the Bible view"""
        self.log_message(f"Navigating to verse: {reference}")
        verse_id = self.get_verse_id_from_reference(reference)
        self.log_message(f"Found verse ID: {verse_id}")
        if verse_id:
            # Start at the target verse (display it at the top)
            start_position = max(1, verse_id)
            self.current_bible_position = start_position
            self.log_message(f"Setting Bible position to: {start_position}")
            self.display_bible_view()
        else:
            self.log_message(f"Could not find verse ID for reference: {reference}")

    def display_bible_view(self):
        """Display the scrollable Bible view starting from current_bible_position"""
        try:
            self.log_message(f"Displaying Bible view from position: {self.current_bible_position}")
            # Get the current translation preference - use the one selected from search results if available
            current_translation = getattr(self, 'current_bible_translation', "KJV")
            if not current_translation or current_translation == "":
                current_translation = "KJV"
            translation_column = self.get_translation_column(current_translation)
            self.log_message(f"Using translation: {current_translation}, column: {translation_column}")
            
            conn = sqlite3.connect(self.sqlite_db_path)
            cursor = conn.cursor()
            
            # Get verses starting from current position
            cursor.execute(f"""
                SELECT verse, {translation_column} 
                FROM bible_verses 
                WHERE id >= ? AND id < ? 
                ORDER BY id
            """, (self.current_bible_position, self.current_bible_position + self.bible_verses_per_view))
            
            verses = cursor.fetchall()
            conn.close()
            
            if verses:
                # Store verses data for checkbox functionality
                self.current_bible_verses = []
                
                # Clear and populate treeview
                if hasattr(self, 'verse_display_tree'):
                    # Clear existing items
                    for item in self.verse_display_tree.get_children():
                        self.verse_display_tree.delete(item)
                    
                    # Add verses to treeview
                    for i, (verse_ref, verse_text) in enumerate(verses):
                        verse_id = self.current_bible_position + i
                        verse_data = {
                            'id': verse_id,
                            'reference': verse_ref,
                            'translation': current_translation,
                            'text': verse_text
                        }
                        self.current_bible_verses.append(verse_data)
                        
                        # Insert into treeview with unchecked state
                        item_id = self.verse_display_tree.insert('', 'end', text='☐', 
                                                               values=(verse_ref, current_translation, verse_text),
                                                               tags=('unchecked',))
                
                # Update Move to Subject button state
                self.update_move_button_state()
                
        except Exception as e:
            self.log_message(f"Error displaying Bible view: {e}")

    def get_translation_column(self, translation_code):
        """Get the database column name for a translation code"""
        translation_map = {
            "All": "king_james_bible",  # Default for "All"
            "KJV": "king_james_bible",
            "ASV": "american_standard_version",
            "DRB": "douay_rheims_bible",
            "DBT": "darby_bible_translation",
            "ERV": "english_revised_version",
            "WBT": "webster_bible_translation",
            "WEB": "world_english_bible",
            "YLT": "youngs_literal_translation",
            "AKJV": "american_king_james_version",
            "WNT": "weymouth_new_testament",
            "BISHOPS": "bishops_bible",
            "COVERDALE": "coverdale_bible",
            "GENEVA": "geneva_bible",
            "NET": "net_bible",
            "TYNDALE": "tyndale_bible"
        }
        return translation_map.get(translation_code, "king_james_bible")

    def get_translation_full_name(self, translation_code):
        """Get the full name for a translation code"""
        translation_names = {
            "KJV": "King James Version",
            "ASV": "American Standard Version",
            "DRB": "Douay-Rheims Bible",
            "DBT": "Darby Bible Translation",
            "ERV": "English Revised Version",
            "WBT": "Webster Bible Translation",
            "WEB": "World English Bible",
            "YLT": "Young's Literal Translation",
            "AKJV": "American King James Version",
            "WNT": "Weymouth New Testament",
            "BISHOPS": "Bishops Bible (1568)",
            "COVERDALE": "Coverdale Bible (1535)",
            "GENEVA": "Geneva Bible (1587)",
            "NET": "NET Bible",
            "TYNDALE": "Tyndale Bible (1534)"
        }
        return translation_names.get(translation_code, "King James Version")

    def update_bible_reading_view_label(self, translation_code):
        """Update the Bible Reading View label to show current translation"""
        try:
            translation_name = self.get_translation_full_name(translation_code)
            if hasattr(self, 'verse_display_frame'):
                self.verse_display_frame.configure(text=f"Bible Reading View: {translation_name}")
        except Exception as e:
            self.log_message(f"Error updating Bible Reading View label: {e}")

    def scroll_bible_up(self):
        """Scroll up in the Bible (toward the beginning)"""
        self.current_bible_position = max(1, self.current_bible_position - 5)
        # Clear selections when scrolling to new verses
        self.selected_bible_verses = set()
        self.display_bible_view()

    def scroll_bible_down(self):
        """Scroll down in the Bible (toward the end)"""
        total_verses = self.get_total_verses_count()
        self.current_bible_position = min(total_verses - self.bible_verses_per_view + 1, 
                                         self.current_bible_position + 5)
        # Clear selections when scrolling to new verses
        self.selected_bible_verses = set()
        self.display_bible_view()

    def on_bible_verse_click(self, event):
        """Handle clicks on verses in the Bible Reading View treeview (checkbox toggle)"""
        try:
            # Identify what was clicked
            region = self.verse_display_tree.identify_region(event.x, event.y)
            item = self.verse_display_tree.identify_row(event.y)
            
            if item and region == "tree":  # Clicked on checkbox area
                self.toggle_bible_verse_checkbox(item)
            elif item and region == "cell":  # Clicked on verse content
                # Navigate to the verse (preserve old functionality)
                verse_ref = self.verse_display_tree.item(item, 'values')[0]
                self.log_message(f"Bible verse click - navigating to: {verse_ref}")
                self.navigate_to_verse(verse_ref)
                
        except Exception as e:
            self.log_message(f"Error handling Bible verse click: {e}")

    def toggle_bible_verse_checkbox(self, item):
        """Toggle the checkbox state of a Bible verse"""
        try:
            current_tags = self.verse_display_tree.item(item, 'tags')
            
            if 'checked' in current_tags:
                # Uncheck the item
                self.verse_display_tree.item(item, text='☐', tags=('unchecked',))
                # Find and remove from selected set
                item_index = self.get_bible_verse_index(item)
                if item_index is not None:
                    self.selected_bible_verses.discard(item_index)
            else:
                # Check the item
                self.verse_display_tree.item(item, text='☑', tags=('checked',))
                # Add to selected set
                item_index = self.get_bible_verse_index(item)
                if item_index is not None:
                    self.selected_bible_verses.add(item_index)
            
            self.update_move_button_state()
            
        except Exception as e:
            self.log_message(f"Error toggling Bible verse checkbox: {e}")

    def get_bible_verse_index(self, item):
        """Get the index of a treeview item in the current_bible_verses list"""
        try:
            children = self.verse_display_tree.get_children()
            return list(children).index(item)
        except (ValueError, AttributeError):
            return None

    def update_move_button_state(self):
        """Enable/disable Move to Subject button based on Bible verse selections"""
        try:
            if hasattr(self, 'move_to_subject_button'):
                if self.selected_bible_verses:
                    self.move_to_subject_button.configure(state=tk.NORMAL)
                else:
                    self.move_to_subject_button.configure(state=tk.DISABLED)
        except Exception as e:
            self.log_message(f"Error updating move button state: {e}")

    def show_heights_dialog(self):
        """Show window heights adjustment dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Adjust Window Heights")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Adjust Window Heights", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Search Results Height
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(search_frame, text="Search Results Height (rows):").grid(row=0, column=0, sticky=tk.W)
        search_spin = tk.Spinbox(search_frame, from_=3, to=30, width=10, 
                                textvariable=self.search_height_var,
                                command=self.update_search_height)
        search_spin.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        # Verse Display Height
        verse_frame = ttk.Frame(main_frame)
        verse_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(verse_frame, text="Verse Display Height (rows):").grid(row=0, column=0, sticky=tk.W)
        verse_spin = tk.Spinbox(verse_frame, from_=2, to=15, width=10, 
                               textvariable=self.verse_height_var,
                               command=self.update_verse_height)
        verse_spin.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        # Subject Verses Height
        subject_frame = ttk.Frame(main_frame)
        subject_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(subject_frame, text="Subject Verses Height (rows):").grid(row=0, column=0, sticky=tk.W)
        subject_spin = tk.Spinbox(subject_frame, from_=3, to=25, width=10, 
                                 textvariable=self.subject_height_var,
                                 command=self.update_subject_height)
        subject_spin.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        # Comments Height
        comments_frame = ttk.Frame(main_frame)
        comments_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(comments_frame, text="Comments Height (rows):").grid(row=0, column=0, sticky=tk.W)
        comments_spin = tk.Spinbox(comments_frame, from_=2, to=15, width=10, 
                                  textvariable=self.comments_height_var,
                                  command=self.update_comments_height)
        comments_spin.grid(row=0, column=1, sticky=tk.E, padx=(20, 0))
        
        # Configure frames to expand properly
        main_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(1, weight=1)
        verse_frame.columnconfigure(1, weight=1)
        subject_frame.columnconfigure(1, weight=1)
        comments_frame.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        
        close_button = ttk.Button(button_frame, text="Close", command=dialog.destroy)
        close_button.grid(row=0, column=0, padx=5)
        
        # Apply button to update all heights at once
        apply_button = ttk.Button(button_frame, text="Apply All", 
                                 command=lambda: self.apply_all_heights())
        apply_button.grid(row=0, column=1, padx=5)
        
        # Center the dialog on the parent window
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def apply_all_heights(self):
        """Apply all height changes at once"""
        self.update_search_height()
        self.update_verse_height()
        self.update_subject_height()
        self.update_comments_height()

    def open_settings_menu(self):
        """Open the settings menu with all configuration options"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Settings", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Settings buttons
        translations_button = ttk.Button(main_frame, text="Select Translations", 
                                       command=lambda: [dialog.destroy(), self.show_translation_dialog()],
                                       width=20)
        translations_button.grid(row=1, column=0, pady=5)
        
        heights_button = ttk.Button(main_frame, text="Adjust Heights", 
                                   command=lambda: [dialog.destroy(), self.show_heights_dialog()],
                                   width=20)
        heights_button.grid(row=2, column=0, pady=5)
        
        font_button = ttk.Button(main_frame, text="Font Size", 
                                command=lambda: [dialog.destroy(), self.open_font_size_dialog()],
                                width=20)
        font_button.grid(row=3, column=0, pady=5)
        
        # Close button
        close_button = ttk.Button(main_frame, text="Close", command=dialog.destroy, width=20)
        close_button.grid(row=4, column=0, pady=(20, 0))
        
        # Center the dialog on the parent window
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

    def on_closing(self):
        """Handle application closing"""
        self.save_config()
        self.log_message("Application closing")
        self.root.destroy()
    
    def exit_application(self):
        """Exit application via Exit button"""
        # Log current font sizes before saving
        self.log_message(f"Saving font sizes - Main: {self.main_font_size_var.get()}, Other: {self.other_font_size_var.get()}")
        self.update_status("Saving current configurations...")
        self.root.update()  # Force GUI update to show message
        self.root.after(2000, self.on_closing)  # Wait 2 seconds before closing
    
    def save_window_size(self):
        """Save current window size and position"""
        try:
            # Get current window geometry
            geometry = self.root.geometry()
            self.log_message(f"Saving window geometry: {geometry}")
            
            # Load existing config if it exists
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update config with window size
            config['WindowGeometry'] = geometry
            
            # Save updated config
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            self.log_message(f"Error saving window size: {e}")
        
    def run(self):
        """Start the application"""
        self.log_message("Starting main application loop")
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = BibleSearchApp()
        app.run()
    except Exception as e:
        logging.error(f"Critical error: {e}")
        messagebox.showerror("Critical Error", f"A critical error occurred:\n{e}")


if __name__ == "__main__":
    main()