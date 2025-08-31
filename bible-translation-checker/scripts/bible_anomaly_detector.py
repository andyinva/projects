#!/usr/bin/env python3
"""
Bible JSON Anomaly Detection Utility

Detects and logs anomalies in JSON Bible files converted from OSIS XML.
Performs comprehensive validation of text content, verse sequences, and structure.

Requirements:
- pip install colorama

Usage:
    python3 bible_anomaly_detector.py [--config config.json] [--dir path/to/json/files]
"""

import json
import re
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict, Counter
import unicodedata

try:
    from colorama import Fore, Back, Style, init
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback color constants
    class Fore:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = RESET = ""
    class Back:
        RED = GREEN = YELLOW = BLUE = CYAN = MAGENTA = WHITE = BLACK = RESET = ""
    class Style:
        DIM = NORMAL = BRIGHT = RESET_ALL = ""

# Expected 66 books in correct order
EXPECTED_BOOKS = [
    'Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', 'Rut', '1Sa', '2Sa',
    '1Ki', '2Ki', '1Ch', '2Ch', 'Ezr', 'Neh', 'Est', 'Job', 'Psa', 'Pro',
    'Ecc', 'Son', 'Isa', 'Jer', 'Lam', 'Eze', 'Dan', 'Hos', 'Joe', 'Amo',
    'Oba', 'Jon', 'Mic', 'Nah', 'Hab', 'Zep', 'Hag', 'Zec', 'Mal', 'Mat',
    'Mar', 'Luk', 'Joh', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph', 'Phi',
    'Col', '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas', '1Pe',
    '2Pe', '1Jo', '2Jo', '3Jo', 'Jde', 'Rev'
]

# Book names mapping
BOOK_NAMES = {
    'Gen': 'Genesis', 'Exo': 'Exodus', 'Lev': 'Leviticus', 'Num': 'Numbers', 'Deu': 'Deuteronomy',
    'Jos': 'Joshua', 'Jdg': 'Judges', 'Rut': 'Ruth', '1Sa': '1 Samuel', '2Sa': '2 Samuel',
    '1Ki': '1 Kings', '2Ki': '2 Kings', '1Ch': '1 Chronicles', '2Ch': '2 Chronicles',
    'Ezr': 'Ezra', 'Neh': 'Nehemiah', 'Est': 'Esther', 'Job': 'Job', 'Psa': 'Psalms',
    'Pro': 'Proverbs', 'Ecc': 'Ecclesiastes', 'Son': 'Song of Songs', 'Isa': 'Isaiah',
    'Jer': 'Jeremiah', 'Lam': 'Lamentations', 'Eze': 'Ezekiel', 'Dan': 'Daniel',
    'Hos': 'Hosea', 'Joe': 'Joel', 'Amo': 'Amos', 'Oba': 'Obadiah', 'Jon': 'Jonah',
    'Mic': 'Micah', 'Nah': 'Nahum', 'Hab': 'Habakkuk', 'Zep': 'Zephaniah', 'Hag': 'Haggai',
    'Zec': 'Zechariah', 'Mal': 'Malachi', 'Mat': 'Matthew', 'Mar': 'Mark', 'Luk': 'Luke',
    'Joh': 'John', 'Act': 'Acts', 'Rom': 'Romans', '1Co': '1 Corinthians', '2Co': '2 Corinthians',
    'Gal': 'Galatians', 'Eph': 'Ephesians', 'Phi': 'Philippians', 'Col': 'Colossians',
    '1Th': '1 Thessalonians', '2Th': '2 Thessalonians', '1Ti': '1 Timothy', '2Ti': '2 Timothy',
    'Tit': 'Titus', 'Phm': 'Philemon', 'Heb': 'Hebrews', 'Jas': 'James', '1Pe': '1 Peter',
    '2Pe': '2 Peter', '1Jo': '1 John', '2Jo': '2 John', '3Jo': '3 John', 'Jde': 'Jude', 'Rev': 'Revelation'
}

@dataclass
class Anomaly:
    """Represents a detected anomaly"""
    severity: str  # ERROR, WARNING, INFO
    category: str  # TEXT_CONTENT, SEQUENCE, STRUCTURE, ENCODING
    description: str
    location: str  # book:chapter:verse or similar
    details: str = ""

@dataclass
class Config:
    """Configuration for anomaly detection"""
    check_text_content: bool = True
    check_sequences: bool = True
    check_structure: bool = True
    check_encoding: bool = True
    min_verse_length: int = 3
    max_verse_length: int = 500
    allowed_chars_pattern: str = r'^[a-zA-Z0-9\s\.,;:!?\'"()\[\]\/\-–—""''…]*$'
    skip_books: Set[str] = None
    
    def __post_init__(self):
        if self.skip_books is None:
            self.skip_books = set()

class BibleAnomalyDetector:
    """Main anomaly detection class"""
    
    def __init__(self, config: Config = None, log_dir: Path = None):
        self.config = config or Config()
        self.log_dir = log_dir or Path.cwd()
        self.log_dir.mkdir(exist_ok=True)
        
        # Statistics tracking
        self.stats = defaultdict(Counter)
        self.global_stats = Counter()
        self.processed_files = []
        self.verse_hashes = defaultdict(list)  # For duplicate detection
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'anomaly_detection.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def colorize(self, text: str, color: str) -> str:
        """Add color to text if colorama is available"""
        if not COLORAMA_AVAILABLE:
            return text
        
        color_map = {
            'red': Fore.RED,
            'yellow': Fore.YELLOW,
            'green': Fore.GREEN,
            'blue': Fore.BLUE,
            'cyan': Fore.CYAN,
            'magenta': Fore.MAGENTA
        }
        return f"{color_map.get(color, '')}{text}{Style.RESET_ALL}"
    
    def print_status(self, message: str, color: str = 'white'):
        """Print colored status message"""
        print(self.colorize(message, color))
    
    def detect_text_anomalies(self, text: str, location: str) -> List[Anomaly]:
        """Detect text content anomalies in verse text"""
        anomalies = []
        
        if not self.config.check_text_content:
            return anomalies
        
        # Check for numbers in text
        if re.search(r'\d', text):
            anomalies.append(Anomaly(
                severity="WARNING",
                category="TEXT_CONTENT",
                description="Contains numeric characters",
                location=location,
                details=f"Found numbers in: {text[:50]}..."
            ))
        
        # Check for invalid characters
        if not re.match(self.config.allowed_chars_pattern, text):
            invalid_chars = set(char for char in text if not re.match(r'[a-zA-Z0-9\s\.,;:!?\'"()\[\]\/\-–—""''…]', char))
            anomalies.append(Anomaly(
                severity="ERROR",
                category="TEXT_CONTENT",
                description="Contains invalid characters",
                location=location,
                details=f"Invalid chars: {list(invalid_chars)} in: {text[:50]}..."
            ))
        
        # Check for multiple consecutive spaces
        if re.search(r'  +', text):
            anomalies.append(Anomaly(
                severity="WARNING",
                category="TEXT_CONTENT",
                description="Multiple consecutive spaces",
                location=location,
                details=f"Found in: {text[:50]}..."
            ))
        
        # Check verse length
        if len(text) < self.config.min_verse_length:
            anomalies.append(Anomaly(
                severity="WARNING",
                category="TEXT_CONTENT",
                description=f"Verse too short ({len(text)} chars)",
                location=location,
                details=f"Text: '{text}'"
            ))
        elif len(text) > self.config.max_verse_length:
            anomalies.append(Anomaly(
                severity="WARNING",
                category="TEXT_CONTENT",
                description=f"Verse too long ({len(text)} chars)",
                location=location,
                details=f"Text: {text[:100]}..."
            ))
        
        # Check for HTML/XML tags
        if re.search(r'<[^>]+>', text) or re.search(r'&[a-zA-Z]+;', text):
            anomalies.append(Anomaly(
                severity="ERROR",
                category="TEXT_CONTENT",
                description="Contains HTML/XML tags or entities",
                location=location,
                details=f"Found in: {text[:50]}..."
            ))
        
        # Check for leading/trailing whitespace
        if text != text.strip():
            anomalies.append(Anomaly(
                severity="WARNING",
                category="TEXT_CONTENT",
                description="Leading or trailing whitespace",
                location=location,
                details=f"Original: '{text}'"
            ))
        
        return anomalies
    
    def detect_encoding_anomalies(self, text: str, location: str) -> List[Anomaly]:
        """Detect encoding and formatting anomalies"""
        anomalies = []
        
        if not self.config.check_encoding:
            return anomalies
        
        # Check for unusual unicode characters
        unusual_chars = []
        for char in text:
            if ord(char) > 127:  # Non-ASCII
                category = unicodedata.category(char)
                name = unicodedata.name(char, "UNKNOWN")
                if category.startswith('C') or 'CONTROL' in name or 'PRIVATE' in name:
                    unusual_chars.append((char, name))
        
        if unusual_chars:
            anomalies.append(Anomaly(
                severity="WARNING",
                category="ENCODING",
                description="Contains unusual unicode characters",
                location=location,
                details=f"Chars: {unusual_chars[:5]}..."  # Limit to first 5
            ))
        
        # Check for unusual capitalization patterns
        words = text.split()
        if len(words) > 1:
            all_caps_count = sum(1 for word in words if word.isupper() and len(word) > 1)
            if all_caps_count > len(words) * 0.3:  # More than 30% all caps
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="ENCODING",
                    description="Unusual capitalization pattern",
                    location=location,
                    details=f"{all_caps_count}/{len(words)} words are all caps"
                ))
        
        return anomalies
    
    def detect_sequence_anomalies(self, chapters: Dict, book_abbrev: str) -> List[Anomaly]:
        """Detect verse and chapter sequence anomalies"""
        anomalies = []
        
        if not self.config.check_sequences:
            return anomalies
        
        # Check chapter sequence
        chapter_nums = []
        for chapter_str in chapters.keys():
            try:
                chapter_num = int(chapter_str)
                chapter_nums.append(chapter_num)
            except ValueError:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="SEQUENCE",
                    description="Non-integer chapter number",
                    location=f"{book_abbrev}:{chapter_str}",
                    details=f"Chapter: '{chapter_str}'"
                ))
        
        # Check for gaps or duplicates in chapter sequence
        if chapter_nums:
            expected_chapters = list(range(1, max(chapter_nums) + 1))
            missing_chapters = set(expected_chapters) - set(chapter_nums)
            duplicate_chapters = [num for num in chapter_nums if chapter_nums.count(num) > 1]
            
            if missing_chapters:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="SEQUENCE",
                    description="Missing chapters",
                    location=f"{book_abbrev}",
                    details=f"Missing: {sorted(missing_chapters)}"
                ))
            
            if duplicate_chapters:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="SEQUENCE",
                    description="Duplicate chapters",
                    location=f"{book_abbrev}",
                    details=f"Duplicates: {sorted(set(duplicate_chapters))}"
                ))
        
        # Check verse sequences within each chapter
        for chapter_str, verses in chapters.items():
            verse_nums = []
            for verse_str in verses.keys():
                try:
                    verse_num = int(verse_str)
                    verse_nums.append(verse_num)
                except ValueError:
                    anomalies.append(Anomaly(
                        severity="ERROR",
                        category="SEQUENCE",
                        description="Non-integer verse number",
                        location=f"{book_abbrev}:{chapter_str}:{verse_str}",
                        details=f"Verse: '{verse_str}'"
                    ))
            
            # Check for gaps or duplicates in verse sequence
            if verse_nums:
                expected_verses = list(range(1, max(verse_nums) + 1))
                missing_verses = set(expected_verses) - set(verse_nums)
                duplicate_verses = [num for num in verse_nums if verse_nums.count(num) > 1]
                
                if missing_verses:
                    anomalies.append(Anomaly(
                        severity="WARNING",
                        category="SEQUENCE",
                        description="Missing verses",
                        location=f"{book_abbrev}:{chapter_str}",
                        details=f"Missing: {sorted(missing_verses)}"
                    ))
                
                if duplicate_verses:
                    anomalies.append(Anomaly(
                        severity="ERROR",
                        category="SEQUENCE",
                        description="Duplicate verses",
                        location=f"{book_abbrev}:{chapter_str}",
                        details=f"Duplicates: {sorted(set(duplicate_verses))}"
                    ))
        
        return anomalies
    
    def detect_structure_anomalies(self, bible_data: Dict, filename: str) -> List[Anomaly]:
        """Detect structural anomalies in the JSON"""
        anomalies = []
        
        if not self.config.check_structure:
            return anomalies
        
        # Check translation_info structure
        if 'translation_info' not in bible_data:
            anomalies.append(Anomaly(
                severity="ERROR",
                category="STRUCTURE",
                description="Missing translation_info",
                location="ROOT",
                details="No translation_info found"
            ))
        else:
            trans_info = bible_data['translation_info']
            
            # Check abbreviation
            if 'abbrev' not in trans_info:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="STRUCTURE",
                    description="Missing translation abbreviation",
                    location="translation_info",
                ))
            elif not isinstance(trans_info['abbrev'], str) or len(trans_info['abbrev']) != 3:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="STRUCTURE",
                    description="Invalid translation abbreviation format",
                    location="translation_info",
                    details=f"Expected 3 chars, got: '{trans_info.get('abbrev')}'"
                ))
            elif not trans_info['abbrev'].isupper():
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="STRUCTURE",
                    description="Translation abbreviation not uppercase",
                    location="translation_info",
                    details=f"Got: '{trans_info['abbrev']}'"
                ))
            
            # Check name
            if 'name' not in trans_info:
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="STRUCTURE",
                    description="Missing translation name",
                    location="translation_info"
                ))
        
        # Check books structure
        if 'books' not in bible_data:
            anomalies.append(Anomaly(
                severity="ERROR",
                category="STRUCTURE",
                description="Missing books section",
                location="ROOT"
            ))
            return anomalies
        
        books = bible_data['books']
        
        # Check for expected books
        present_books = set(books.keys())
        missing_books = set(EXPECTED_BOOKS) - present_books
        unexpected_books = present_books - set(EXPECTED_BOOKS)
        
        if missing_books:
            anomalies.append(Anomaly(
                severity="WARNING",
                category="STRUCTURE",
                description="Missing expected books",
                location="books",
                details=f"Missing: {sorted(missing_books)}"
            ))
        
        if unexpected_books:
            anomalies.append(Anomaly(
                severity="WARNING",
                category="STRUCTURE",
                description="Unexpected books present",
                location="books",
                details=f"Unexpected: {sorted(unexpected_books)}"
            ))
        
        # Check each book structure
        for book_abbrev, book_data in books.items():
            if book_abbrev in self.config.skip_books:
                continue
            
            # Check book structure
            if not isinstance(book_data, dict):
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="STRUCTURE",
                    description="Book data is not a dictionary",
                    location=f"books.{book_abbrev}"
                ))
                continue
            
            # Check book name
            if 'name' not in book_data:
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="STRUCTURE",
                    description="Missing book name",
                    location=f"books.{book_abbrev}"
                ))
            elif book_abbrev in BOOK_NAMES and book_data['name'] != BOOK_NAMES[book_abbrev]:
                anomalies.append(Anomaly(
                    severity="WARNING",
                    category="STRUCTURE",
                    description="Unexpected book name",
                    location=f"books.{book_abbrev}",
                    details=f"Expected: '{BOOK_NAMES[book_abbrev]}', Got: '{book_data['name']}'"
                ))
            
            # Check chapters structure
            if 'chapters' not in book_data:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="STRUCTURE",
                    description="Missing chapters",
                    location=f"books.{book_abbrev}"
                ))
                continue
            
            chapters = book_data['chapters']
            if not chapters:
                anomalies.append(Anomaly(
                    severity="ERROR",
                    category="STRUCTURE",
                    description="Empty chapters",
                    location=f"books.{book_abbrev}.chapters"
                ))
                continue
            
            # Check for empty verses
            for chapter_str, verses in chapters.items():
                if not verses:
                    anomalies.append(Anomaly(
                        severity="ERROR",
                        category="STRUCTURE",
                        description="Empty chapter",
                        location=f"{book_abbrev}:{chapter_str}"
                    ))
                else:
                    for verse_str, verse_text in verses.items():
                        if not verse_text or not verse_text.strip():
                            anomalies.append(Anomaly(
                                severity="ERROR",
                                category="STRUCTURE",
                                description="Empty verse",
                                location=f"{book_abbrev}:{chapter_str}:{verse_str}"
                            ))
        
        return anomalies
    
    def detect_duplicate_verses(self, bible_data: Dict, filename: str) -> List[Anomaly]:
        """Detect duplicate verses across the Bible"""
        anomalies = []
        verse_content = {}
        
        books = bible_data.get('books', {})
        for book_abbrev, book_data in books.items():
            if book_abbrev in self.config.skip_books:
                continue
                
            chapters = book_data.get('chapters', {})
            for chapter_str, verses in chapters.items():
                for verse_str, verse_text in verses.items():
                    if isinstance(verse_text, str) and len(verse_text.strip()) > 10:  # Skip very short verses
                        text_hash = hash(verse_text.strip().lower())
                        location = f"{book_abbrev}:{chapter_str}:{verse_str}"
                        
                        if text_hash in verse_content:
                            # Found duplicate
                            original_location = verse_content[text_hash]
                            anomalies.append(Anomaly(
                                severity="WARNING",
                                category="TEXT_CONTENT",
                                description="Duplicate verse content",
                                location=location,
                                details=f"Same as {original_location}: {verse_text[:50]}..."
                            ))
                        else:
                            verse_content[text_hash] = location
        
        return anomalies
    
    def analyze_file(self, json_file: Path) -> Tuple[List[Anomaly], Dict]:
        """Analyze a single JSON Bible file"""
        anomalies = []
        file_stats = Counter()
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                bible_data = json.load(f)
        except json.JSONDecodeError as e:
            anomalies.append(Anomaly(
                severity="ERROR",
                category="STRUCTURE",
                description="Invalid JSON format",
                location="FILE",
                details=str(e)
            ))
            return anomalies, file_stats
        except Exception as e:
            anomalies.append(Anomaly(
                severity="ERROR",
                category="STRUCTURE",
                description="File read error",
                location="FILE",
                details=str(e)
            ))
            return anomalies, file_stats
        
        # Structure validation
        structure_anomalies = self.detect_structure_anomalies(bible_data, json_file.name)
        anomalies.extend(structure_anomalies)
        
        # Check duplicate verses
        duplicate_anomalies = self.detect_duplicate_verses(bible_data, json_file.name)
        anomalies.extend(duplicate_anomalies)
        
        # Text and sequence validation
        books = bible_data.get('books', {})
        for book_abbrev, book_data in books.items():
            if book_abbrev in self.config.skip_books:
                continue
            
            chapters = book_data.get('chapters', {})
            
            # Check sequence anomalies for this book
            sequence_anomalies = self.detect_sequence_anomalies(chapters, book_abbrev)
            anomalies.extend(sequence_anomalies)
            
            # Check each verse
            for chapter_str, verses in chapters.items():
                for verse_str, verse_text in verses.items():
                    if isinstance(verse_text, str):
                        location = f"{book_abbrev}:{chapter_str}:{verse_str}"
                        
                        # Text content anomalies
                        text_anomalies = self.detect_text_anomalies(verse_text, location)
                        anomalies.extend(text_anomalies)
                        
                        # Encoding anomalies
                        encoding_anomalies = self.detect_encoding_anomalies(verse_text, location)
                        anomalies.extend(encoding_anomalies)
        
        # Count anomalies by category and severity
        for anomaly in anomalies:
            file_stats[f"{anomaly.severity}_{anomaly.category}"] += 1
            file_stats[anomaly.severity] += 1
            file_stats[anomaly.category] += 1
        
        return anomalies, file_stats
    
    def write_log_file(self, anomalies: List[Anomaly], filename: str, translation_abbrev: str):
        """Write detailed log file for a translation"""
        log_file = self.log_dir / f"{translation_abbrev}_anomalies.log"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"ANOMALY DETECTION REPORT FOR {translation_abbrev}\n")
            f.write(f"Source file: {filename}\n")
            f.write(f"Analysis complete\n")
            f.write("=" * 80 + "\n\n")
            
            if not anomalies:
                f.write("✅ NO ANOMALIES DETECTED - FILE IS CLEAN\n")
                return
            
            # Group by severity
            by_severity = defaultdict(list)
            for anomaly in anomalies:
                by_severity[anomaly.severity].append(anomaly)
            
            for severity in ["ERROR", "WARNING", "INFO"]:
                if severity in by_severity:
                    f.write(f"\n{severity}S ({len(by_severity[severity])}):\n")
                    f.write("-" * 40 + "\n")
                    
                    # Group by category
                    by_category = defaultdict(list)
                    for anomaly in by_severity[severity]:
                        by_category[anomaly.category].append(anomaly)
                    
                    for category, cat_anomalies in by_category.items():
                        f.write(f"\n  {category} ({len(cat_anomalies)}):\n")
                        for i, anomaly in enumerate(cat_anomalies, 1):
                            f.write(f"    {i}. {anomaly.location}: {anomaly.description}\n")
                            if anomaly.details:
                                f.write(f"       Details: {anomaly.details}\n")
                        f.write("\n")
    
    def process_directory(self, json_dir: Path) -> Dict:
        """Process all JSON files in directory"""
        json_files = list(json_dir.glob("*.json"))
        
        if not json_files:
            self.print_status("❌ No JSON files found in directory", 'red')
            return {}
        
        self.print_status(f"🔍 Found {len(json_files)} JSON files to analyze", 'blue')
        
        all_results = {}
        
        for i, json_file in enumerate(json_files, 1):
            # Extract translation abbreviation from filename
            translation_abbrev = json_file.stem.upper()
            
            self.print_status(f"[{i}/{len(json_files)}] Analyzing {json_file.name}...", 'cyan')
            
            # Analyze file
            anomalies, file_stats = self.analyze_file(json_file)
            
            # Store results
            all_results[translation_abbrev] = {
                'filename': json_file.name,
                'anomalies': anomalies,
                'stats': file_stats
            }
            
            # Write individual log file
            self.write_log_file(anomalies, json_file.name, translation_abbrev)
            
            # Update global stats
            for key, count in file_stats.items():
                self.global_stats[key] += count
            
            # Print status
            error_count = len([a for a in anomalies if a.severity == "ERROR"])
            warning_count = len([a for a in anomalies if a.severity == "WARNING"])
            
            if error_count > 0:
                self.print_status(f"  ❌ {error_count} errors, {warning_count} warnings", 'red')
            elif warning_count > 0:
                self.print_status(f"  ⚠️  {warning_count} warnings", 'yellow')
            else:
                self.print_status(f"  ✅ Clean - no anomalies found", 'green')
        
        return all_results
    
    def generate_summary_report(self, all_results: Dict):
        """Generate comprehensive summary report"""
        summary_file = self.log_dir / "anomaly_summary.txt"
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("BIBLE JSON ANOMALY DETECTION SUMMARY REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Files processed: {len(all_results)}\n")
            f.write(f"Total anomalies found: {sum(len(r['anomalies']) for r in all_results.values())}\n\n")
            
            # Global statistics
            f.write("GLOBAL STATISTICS BY SEVERITY:\n")
            f.write("-" * 30 + "\n")
            for severity in ["ERROR", "WARNING", "INFO"]:
                count = self.global_stats.get(severity, 0)
                f.write(f"{severity:>8}: {count:>6}\n")
            
            f.write("\nGLOBAL STATISTICS BY CATEGORY:\n")
            f.write("-" * 30 + "\n")
            categories = ["TEXT_CONTENT", "SEQUENCE", "STRUCTURE", "ENCODING"]
            for category in categories:
                count = self.global_stats.get(category, 0)
                f.write(f"{category:>12}: {count:>6}\n")
            
            # File-by-file summary
            f.write("\nFILE-BY-FILE SUMMARY:\n")
            f.write("-" * 30 + "\n")
            
            clean_files = []
            problematic_files = []
            
            for abbrev, result in sorted(all_results.items()):
                anomalies = result['anomalies']
                errors = len([a for a in anomalies if a.severity == "ERROR"])
                warnings = len([a for a in anomalies if a.severity == "WARNING"])
                
                if errors == 0 and warnings == 0:
                    clean_files.append(abbrev)
                else:
                    problematic_files.append((abbrev, errors, warnings))
                    f.write(f"{abbrev:>3}: {errors:>3} errors, {warnings:>3} warnings ({result['filename']})\n")
            
            if clean_files:
                f.write(f"\nCLEAN FILES ({len(clean_files)}):\n")
                f.write("-" * 20 + "\n")
                for abbrev in clean_files:
                    f.write(f"{abbrev:>3}: ✅ No anomalies\n")
            
            # Top issues
            f.write("\nTOP ANOMALY TYPES:\n")
            f.write("-" * 20 + "\n")
            issue_counter = Counter()
            for result in all_results.values():
                for anomaly in result['anomalies']:
                    issue_counter[f"{anomaly.severity}_{anomaly.category}_{anomaly.description}"] += 1
            
            for issue, count in issue_counter.most_common(10):
                f.write(f"{count:>3}x {issue}\n")
        
        self.print_status(f"\n📊 Summary report written to: {summary_file}", 'blue')
        self.print_status(f"📝 Individual logs written to: {self.log_dir}/*_anomalies.log", 'blue')

def load_config(config_path: Path) -> Config:
    """Load configuration from JSON file"""
    if not config_path.exists():
        return Config()
    
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        
        return Config(
            check_text_content=config_data.get('check_text_content', True),
            check_sequences=config_data.get('check_sequences', True),
            check_structure=config_data.get('check_structure', True),
            check_encoding=config_data.get('check_encoding', True),
            min_verse_length=config_data.get('min_verse_length', 3),
            max_verse_length=config_data.get('max_verse_length', 500),
            allowed_chars_pattern=config_data.get('allowed_chars_pattern', r'^[a-zA-Z0-9\s\.,;:!?\'"()\[\]\/\-–—""''…]*$'),
            skip_books=set(config_data.get('skip_books', []))
        )
    except Exception as e:
        print(f"Warning: Could not load config file {config_path}: {e}")
        return Config()

def create_sample_config(config_path: Path):
    """Create a sample configuration file"""
    sample_config = {
        "check_text_content": True,
        "check_sequences": True,
        "check_structure": True,
        "check_encoding": True,
        "min_verse_length": 3,
        "max_verse_length": 500,
        "allowed_chars_pattern": "^[a-zA-Z0-9\\s\\.,;:!?\\'\"()\\[\\]\\/\\-–—\"\"''…]*$",
        "skip_books": []
    }
    
    with open(config_path, 'w') as f:
        json.dump(sample_config, f, indent=2)
    
    print(f"Sample config created at: {config_path}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Bible JSON Anomaly Detection Utility")
    parser.add_argument('--dir', type=Path, default=Path('/home/ajhinva/my-project/bible_stats/BiblesXML'),
                       help='Directory containing JSON files')
    parser.add_argument('--config', type=Path, help='Configuration file path')
    parser.add_argument('--create-config', action='store_true',
                       help='Create sample configuration file')
    parser.add_argument('--log-dir', type=Path, help='Directory for log files')
    
    args = parser.parse_args()
    
    if args.create_config:
        config_path = args.config or Path('anomaly_config.json')
        create_sample_config(config_path)
        return
    
    # Load configuration
    config = load_config(args.config) if args.config else Config()
    
    # Setup detector
    log_dir = args.log_dir or args.dir / 'anomaly_logs'
    detector = BibleAnomalyDetector(config, log_dir)
    
    # Process files
    print("🔍 Bible JSON Anomaly Detection Utility")
    print("=" * 50)
    
    if not args.dir.exists():
        detector.print_status(f"❌ Directory not found: {args.dir}", 'red')
        sys.exit(1)
    
    all_results = detector.process_directory(args.dir)
    
    if all_results:
        detector.generate_summary_report(all_results)
        
        # Final summary
        total_files = len(all_results)
        clean_files = len([r for r in all_results.values() if not r['anomalies']])
        total_anomalies = sum(len(r['anomalies']) for r in all_results.values())
        
        print("\n" + "=" * 50)
        detector.print_status(f"📈 FINAL SUMMARY:", 'blue')
        detector.print_status(f"   Files processed: {total_files}", 'white')
        detector.print_status(f"   Clean files: {clean_files}", 'green' if clean_files > 0 else 'white')
        detector.print_status(f"   Files with issues: {total_files - clean_files}", 'yellow' if total_files - clean_files > 0 else 'white')
        detector.print_status(f"   Total anomalies: {total_anomalies}", 'red' if total_anomalies > 0 else 'green')
        print("=" * 50)

if __name__ == "__main__":
    main()