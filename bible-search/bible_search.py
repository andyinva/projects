import sqlite3
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Represents a search result with verse information."""
    translation: str
    book: str
    chapter: int
    verse: int
    text: str
    highlighted_text: str = ""

@dataclass
class Translation:
    """Represents a Bible translation."""
    abbreviation: str
    full_name: str
    enabled: bool = True
    sort_order: int = 1

class BibleSearch:
    """Handles all Bible search operations with wildcard and reference search capabilities."""
    
    def __init__(self, database_path: str = None):
        self.database_path = database_path or self._find_database()
        self.book_abbreviations = {}
        self.reverse_book_abbreviations = {}
        self.book_order = {}  # Maps book name to order index
        self.translations = []
        self.load_books()
        self.load_translations()
    
    def _find_database(self, filename: str = "bibles.db") -> str:
        """Find database file, searching current directory first, then subdirectories."""
        # Check current directory first
        if os.path.exists(filename):
            return filename
        
        # Search in common subdirectories
        common_dirs = ['database', 'db', 'data', 'databases']
        for dir_name in common_dirs:
            db_path = os.path.join(dir_name, filename)
            if os.path.exists(db_path):
                return db_path
        
        # Search recursively in all subdirectories (up to 2 levels deep)
        current_dir = os.getcwd()
        for root, dirs, files in os.walk(current_dir):
            # Limit search depth to avoid performance issues
            level = root.replace(current_dir, '').count(os.sep)
            if level < 3:  # Allow up to 2 subdirectory levels
                if filename in files:
                    return os.path.join(root, filename)
        
        # If not found, return default name (will cause error later if file doesn't exist)
        return filename
    
    def load_books(self):
        """Load book names and abbreviations from database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, abbreviation, order_index FROM books ORDER BY order_index")
            book_rows = cursor.fetchall()
            
            for name, abbrev, order_index in book_rows:
                # Create mappings for both directions
                self.book_abbreviations[abbrev.lower()] = name
                self.reverse_book_abbreviations[name.lower()] = abbrev
                
                # Store book order for sorting
                self.book_order[name] = order_index
                self.book_order[abbrev] = order_index  # Also map abbreviation to order
                
                # Also handle common variations
                if name.startswith('1 ') or name.startswith('2 ') or name.startswith('3 '):
                    # Handle "1 Samuel" -> "1samuel", "1sa" etc.
                    compact_name = name.replace(' ', '').lower()
                    self.book_abbreviations[compact_name] = name
                    self.book_order[compact_name] = order_index
            
            conn.close()
        except Exception as e:
            print(f"Error loading books: {e}")
    
    def load_translations(self):
        """Load available translations from database."""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT abbreviation, name FROM translations ORDER BY id")
            translation_rows = cursor.fetchall()
            
            for i, (abbrev, name) in enumerate(translation_rows):
                translation = Translation(
                    abbreviation=abbrev,
                    full_name=name,
                    enabled=True,
                    sort_order=i + 1
                )
                self.translations.append(translation)
            
            conn.close()
        except Exception as e:
            print(f"Error loading translations: {e}")
    
    def detect_search_type(self, query: str) -> str:
        """Detect if search is for words or verse reference."""
        # Remove leading/trailing whitespace
        query = query.strip()
        
        # Check for verse reference patterns
        # Pattern 1: Gen 1:1, Genesis 1:1, etc.
        verse_pattern = r'^([a-zA-Z]+)\s*(\d+):(\d+)(?:-(\d+))?$'
        if re.match(verse_pattern, query):
            return "verse_reference"
        
        # Pattern 2: 1 Samuel 1:1, 2 Kings 3:4, etc.
        verse_pattern_2 = r'^(\d+\s*[a-zA-Z]+)\s*(\d+):(\d+)(?:-(\d+))?$'
        if re.match(verse_pattern_2, query):
            return "verse_reference"
        
        # Otherwise it's a word search
        return "word_search"
    
    def normalize_book_name(self, book_input: str) -> Optional[str]:
        """Convert book name or abbreviation to standard form."""
        book_input = book_input.lower().strip()
        
        # Handle numbered books (1 Samuel, 2 Kings, etc.)
        numbered_book_match = re.match(r'(\d+)\s*(.+)', book_input)
        if numbered_book_match:
            number, book_part = numbered_book_match.groups()
            compact_form = f"{number}{book_part.replace(' ', '')}"
            if compact_form in self.book_abbreviations:
                return self.book_abbreviations[compact_form]
        
        # Direct abbreviation match
        if book_input in self.book_abbreviations:
            return self.book_abbreviations[book_input]
        
        # Try partial matches for full names
        for abbrev, full_name in self.book_abbreviations.items():
            if book_input in full_name.lower() or full_name.lower().startswith(book_input):
                return full_name
        
        return None
    
    def parse_verse_reference(self, query: str) -> Optional[Dict]:
        """Parse verse reference into components."""
        # Pattern for references like "Gen 1:1" or "Gen 1:1-9"
        pattern1 = r'^([a-zA-Z]+)\s*(\d+):(\d+)(?:-(\d+))?$'
        match = re.match(pattern1, query.strip())
        
        if match:
            book_part, chapter, start_verse, end_verse = match.groups()
            book = self.normalize_book_name(book_part)
            if book:
                return {
                    'book': book,
                    'chapter': int(chapter),
                    'start_verse': int(start_verse),
                    'end_verse': int(end_verse) if end_verse else int(start_verse)
                }
        
        # Pattern for numbered books like "1 Samuel 1:1"
        pattern2 = r'^(\d+\s*[a-zA-Z]+)\s*(\d+):(\d+)(?:-(\d+))?$'
        match = re.match(pattern2, query.strip())
        
        if match:
            book_part, chapter, start_verse, end_verse = match.groups()
            book = self.normalize_book_name(book_part)
            if book:
                return {
                    'book': book,
                    'chapter': int(chapter),
                    'start_verse': int(start_verse),
                    'end_verse': int(end_verse) if end_verse else int(start_verse)
                }
        
        return None
    
    def convert_wildcard_to_sql(self, word: str) -> str:
        """Convert wildcard patterns to SQL LIKE patterns."""
        # Replace * with % (any characters)
        word = word.replace('*', '%')
        # Replace ? with _ (single character)
        word = word.replace('?', '_')
        return word
    
    def build_word_search_query(self, query: str, case_sensitive: bool = False) -> Tuple[str, List[str]]:
        """Build SQL query for word search with wildcards and operators."""
        words = []
        operators = []
        
        # Handle NOT operator (!)
        if query.startswith('!'):
            query = query[1:].strip()
            not_search = True
        else:
            not_search = False
        
        # Split by AND/OR while preserving quoted phrases
        parts = re.findall(r'"[^"]*"|[^\s]+', query)
        
        sql_conditions = []
        search_terms = []
        
        for part in parts:
            if part.upper() in ['AND', 'OR']:
                operators.append(part.upper())
                continue
            
            # Remove quotes from exact phrases
            if part.startswith('"') and part.endswith('"'):
                search_term = part[1:-1]
                like_pattern = f"%{search_term}%"
            else:
                # Apply wildcard conversion
                search_term = self.convert_wildcard_to_sql(part)
                like_pattern = f"%{search_term}%"
            
            if case_sensitive:
                condition = "text LIKE ?"
            else:
                condition = "LOWER(text) LIKE LOWER(?)"
            
            if not_search:
                condition = f"NOT ({condition})"
            
            sql_conditions.append(condition)
            search_terms.append(like_pattern)
        
        # Combine conditions with operators
        if not operators:
            # Default to AND if no operators specified
            where_clause = " AND ".join(sql_conditions)
        else:
            where_clause = sql_conditions[0]
            for i, operator in enumerate(operators):
                if i + 1 < len(sql_conditions):
                    where_clause += f" {operator} {sql_conditions[i + 1]}"
        
        return where_clause, search_terms
    
    def highlight_search_terms(self, text: str, query: str) -> str:
        """Highlight search terms in text with [ ] brackets."""
        # Extract search terms from query
        terms = re.findall(r'"[^"]*"|[^\s]+', query)
        
        # Debug: Uncomment the next line to see what terms are being processed
        # print(f"DEBUG: Highlighting query='{query}' in text='{text[:50]}...' with terms={terms}")
        
        # Collect all matches first to avoid overlapping highlights
        matches_to_highlight = []
        
        for term in terms:
            if term.upper() in ['AND', 'OR', '!']:
                continue
            
            # Handle quoted phrases
            if term.startswith('"') and term.endswith('"'):
                phrase = term[1:-1]  # Remove quotes
                if phrase:
                    # Find exact phrase matches
                    pattern = re.escape(phrase)
                    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                        matches_to_highlight.append((match.start(), match.end(), match.group(0)))
            else:
                # Handle wildcard terms
                if '*' in term or '?' in term:
                    # Convert wildcard pattern to regex to match SQL behavior exactly
                    # SQL _ matches ANY single character including spaces
                    # SQL % matches any sequence of characters including spaces
                    
                    # For highlighting, we need to match patterns that can span across words
                    # but still highlight individual words that are part of the match
                    
                    # Build regex pattern character by character  
                    regex_parts = []
                    for char in term:
                        if char == '*':
                            regex_parts.append(r'.*?')     # Match any characters including spaces (non-greedy)
                        elif char == '?':
                            regex_parts.append(r'.')       # Match any single character including space
                        else:
                            regex_parts.append(re.escape(char))
                    
                    wildcard_pattern = ''.join(regex_parts)
                    
                    # Find matches that can span across word boundaries
                    for match in re.finditer(wildcard_pattern, text, flags=re.IGNORECASE):
                        matched_text = match.group(0)
                        
                        # For patterns with ?, we need to highlight meaningful words involved
                        if '?' in term and not '*' in term:
                            # Extract individual words from the match that are substantial (2+ chars)
                            words_in_match = re.findall(r'\b\w{2,}(?:\'[ts])?\b', matched_text)
                            
                            # Find position of each word and add to highlights
                            search_pos = match.start()
                            remaining_text = text[search_pos:]
                            
                            for word in words_in_match:
                                word_match = re.search(r'\b' + re.escape(word) + r'\b', remaining_text)
                                if word_match:
                                    word_start = search_pos + word_match.start()
                                    word_end = search_pos + word_match.end()
                                    matches_to_highlight.append((word_start, word_end, word))
                                    # Update search position to after this word
                                    search_pos += word_match.end()
                        else:
                            # For * patterns or mixed patterns, highlight the whole match
                            matches_to_highlight.append((match.start(), match.end(), matched_text))
                else:
                    # Regular term without wildcards
                    clean_term = term.strip('"')
                    if clean_term:
                        # First try exact word matches
                        exact_pattern = r'\b' + re.escape(clean_term) + r'\b'
                        exact_matches = list(re.finditer(exact_pattern, text, flags=re.IGNORECASE))
                        
                        if exact_matches:
                            # Use exact matches if found
                            for match in exact_matches:
                                matches_to_highlight.append((match.start(), match.end(), match.group(0)))
                        else:
                            # If no exact matches, find words containing the search term (like SQL LIKE %term%)
                            # But be more restrictive with short terms to avoid false matches
                            if len(clean_term) <= 2:
                                # For very short terms (1-2 chars), only highlight if they appear at word boundaries
                                # This prevents "I" from highlighting "Israel", "David", etc.
                                boundary_pattern = r'\b' + re.escape(clean_term) + r'(?=\W|$)'
                                for match in re.finditer(boundary_pattern, text, flags=re.IGNORECASE):
                                    matches_to_highlight.append((match.start(), match.end(), match.group(0)))
                            else:
                                # For longer terms, find words containing the search term
                                containing_pattern = r'\b\w*' + re.escape(clean_term) + r'\w*\b'
                                for match in re.finditer(containing_pattern, text, flags=re.IGNORECASE):
                                    matches_to_highlight.append((match.start(), match.end(), match.group(0)))
        
        # Sort matches by position (reverse order for easier processing)
        matches_to_highlight.sort(key=lambda x: x[0], reverse=True)
        
        # Remove overlapping matches (keep the first/longest one)
        filtered_matches = []
        for start, end, matched_text in matches_to_highlight:
            # Check if this match overlaps with any already accepted match
            overlaps = False
            for existing_start, existing_end, _ in filtered_matches:
                if not (end <= existing_start or start >= existing_end):
                    overlaps = True
                    break
            
            if not overlaps:
                filtered_matches.append((start, end, matched_text))
        
        # Apply highlights from right to left (to preserve indices)
        highlighted_text = text
        for start, end, matched_text in filtered_matches:
            highlighted_text = highlighted_text[:start] + f'[{matched_text}]' + highlighted_text[end:]
        
        return highlighted_text
    
    def _wildcard_length_matches(self, pattern: str, text: str) -> bool:
        """Check if the matched text has the correct length for the wildcard pattern."""
        # Count expected length based on pattern
        expected_length = 0
        for char in pattern:
            if char == '*':
                # * can match any length, so we can't do exact length checking for it
                return True  # Allow * patterns (they match any length)
            elif char == '?':
                expected_length += 1  # ? matches exactly 1 character
            else:
                expected_length += 1  # Literal character
        
        # For patterns with only ? wildcards (no *), check exact length
        return len(text) == expected_length
    
    def abbreviate_text(self, text: str) -> str:
        """Abbreviate text by replacing unnecessary words with '..'."""
        # Common words to abbreviate
        abbreviations = {
            'and': '..',
            'the': '..',
            'that': '..',
            'unto': '..',
            'upon': '..',
            'which': '..',
            'shall': '..',
            'with': '..',
            'from': '..',
            'they': '..',
            'them': '..',
            'their': '..',
            'there': '..',
            'where': '..',
            'when': '..',
            'what': '..',
            'will': '..',
            'said': '..',
            'came': '..',
            'come': '..',
            'went': '..',
            'were': '..',
            'been': '..',
            'have': '..',
            'has': '..',
            'had': '..'
        }
        
        words = text.split()
        abbreviated_words = []
        
        for word in words:
            # Remove punctuation for comparison
            clean_word = re.sub(r'[^\w]', '', word.lower())
            if clean_word in abbreviations:
                abbreviated_words.append(abbreviations[clean_word])
            else:
                abbreviated_words.append(word)
        
        # Join words but don't add spaces around ".." abbreviations
        result_parts = []
        for i, word in enumerate(abbreviated_words):
            if word == '..':
                result_parts.append(word)  # Add ".." with no spaces
            else:
                if i > 0:  # Add space before regular words (except first word)
                    result_parts.append(' ')
                result_parts.append(word)
        
        # Clean up any double spaces and spaces around ".."
        result_text = ''.join(result_parts)
        # Remove spaces before and after ".."
        result_text = result_text.replace(' ..', '..')
        result_text = result_text.replace('.. ', '..')
        # Remove spaces after commas to save more space
        result_text = result_text.replace(', ', ',')
        
        return result_text
    
    def search_verses(self, query: str, enabled_translations: List[str] = None, 
                     case_sensitive: bool = False, unique_verses: bool = False,
                     abbreviate_results: bool = False) -> List[SearchResult]:
        """Perform verse search based on query type."""
        if not enabled_translations:
            enabled_translations = [t.abbreviation for t in self.translations if t.enabled]
        
        search_type = self.detect_search_type(query)
        results = []
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            if search_type == "verse_reference":
                results = self._search_verse_reference(cursor, query, enabled_translations)
            else:
                results = self._search_words(cursor, query, enabled_translations, case_sensitive)
            
            conn.close()
            
            # Apply post-processing
            if unique_verses:
                results = self._filter_unique_verses(results)
            
            if abbreviate_results:
                for result in results:
                    result.text = self.abbreviate_text(result.text)
                    result.highlighted_text = self.abbreviate_text(result.highlighted_text)
            
            # Sort by translation order, then by biblical book order
            translation_order = {t.abbreviation: t.sort_order for t in self.translations}
            results.sort(key=lambda x: (
                translation_order.get(x.translation, 999),  # Translation order first
                self.book_order.get(x.book, 999),           # Biblical book order second
                x.chapter,                                   # Chapter order third
                x.verse                                      # Verse order fourth
            ))
            
        except Exception as e:
            print(f"Search error: {e}")
        
        return results
    
    def _search_verse_reference(self, cursor, query: str, enabled_translations: List[str]) -> List[SearchResult]:
        """Search for specific verse references."""
        verse_ref = self.parse_verse_reference(query)
        if not verse_ref:
            return []
        
        results = []
        
        for translation in self.translations:
            if translation.abbreviation not in enabled_translations:
                continue
            
            try:
                # Query using normalized database structure
                sql = """
                SELECT b.abbreviation, v.chapter, v.verse_number, vt.text 
                FROM books b
                JOIN verses v ON b.id = v.book_id
                JOIN verse_texts vt ON v.id = vt.verse_id
                JOIN translations t ON vt.translation_id = t.id
                WHERE LOWER(b.name) = LOWER(?) 
                AND t.abbreviation = ?
                AND v.chapter = ? 
                AND v.verse_number BETWEEN ? AND ?
                ORDER BY v.verse_number
                """
                
                cursor.execute(sql, (
                    verse_ref['book'],
                    translation.abbreviation,
                    verse_ref['chapter'],
                    verse_ref['start_verse'],
                    verse_ref['end_verse']
                ))
                
                rows = cursor.fetchall()
                for row in rows:
                    result = SearchResult(
                        translation=translation.abbreviation,
                        book=row[0],
                        chapter=row[1],
                        verse=row[2],
                        text=row[3],
                        highlighted_text=row[3]
                    )
                    results.append(result)
            
            except sqlite3.Error as e:
                print(f"Error searching verse reference for {translation.abbreviation}: {e}")
                continue
        
        return results
    
    def _search_words(self, cursor, query: str, enabled_translations: List[str], 
                     case_sensitive: bool) -> List[SearchResult]:
        """Search for words with wildcards and operators."""
        where_clause, search_terms = self.build_word_search_query(query, case_sensitive)
        results = []
        
        for translation in self.translations:
            if translation.abbreviation not in enabled_translations:
                continue
            
            try:
                sql = f"""
                SELECT b.abbreviation, v.chapter, v.verse_number, vt.text 
                FROM books b
                JOIN verses v ON b.id = v.book_id
                JOIN verse_texts vt ON v.id = vt.verse_id
                JOIN translations t ON vt.translation_id = t.id
                WHERE t.abbreviation = ? AND ({where_clause})
                ORDER BY b.order_index, v.chapter, v.verse_number
                """
                
                params = [translation.abbreviation] + search_terms
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                for row in rows:
                    highlighted_text = self.highlight_search_terms(row[3], query)
                    
                    result = SearchResult(
                        translation=translation.abbreviation,
                        book=row[0],
                        chapter=row[1],
                        verse=row[2],
                        text=row[3],
                        highlighted_text=highlighted_text
                    )
                    results.append(result)
            
            except sqlite3.Error as e:
                print(f"Error searching words for {translation.abbreviation}: {e}")
                continue
        
        return results
    
    def _filter_unique_verses(self, results: List[SearchResult]) -> List[SearchResult]:
        """Filter to show only unique verses (highest priority translation)."""
        unique_results = {}
        
        for result in results:
            verse_key = f"{result.book}_{result.chapter}_{result.verse}"
            
            if verse_key not in unique_results:
                unique_results[verse_key] = result
            else:
                # Keep the one with better sort order
                current_translation = next((t for t in self.translations if t.abbreviation == result.translation), None)
                existing_translation = next((t for t in self.translations if t.abbreviation == unique_results[verse_key].translation), None)
                
                if current_translation and existing_translation:
                    if current_translation.sort_order < existing_translation.sort_order:
                        unique_results[verse_key] = result
        
        return list(unique_results.values())
    
    def get_continuous_reading(self, translation: str, book: str, chapter: int, 
                             start_verse: int, num_verses: int = 10) -> List[SearchResult]:
        """Get continuous verses for reading window."""
        results = []
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Use normalized database structure
            sql = """
            SELECT b.abbreviation, v.chapter, v.verse_number, vt.text 
            FROM books b
            JOIN verses v ON b.id = v.book_id
            JOIN verse_texts vt ON v.id = vt.verse_id
            JOIN translations t ON vt.translation_id = t.id
            WHERE t.abbreviation = ?
            AND b.abbreviation = ?
            AND v.chapter = ? 
            AND v.verse_number >= ?
            ORDER BY v.verse_number
            LIMIT ?
            """
            
            cursor.execute(sql, (translation, book, chapter, start_verse, num_verses))
            rows = cursor.fetchall()
            
            for row in rows:
                result = SearchResult(
                    translation=translation,
                    book=row[0],
                    chapter=row[1],
                    verse=row[2],
                    text=row[3],
                    highlighted_text=row[3]
                )
                results.append(result)
            
            conn.close()
        
        except Exception as e:
            print(f"Error getting continuous reading: {e}")
        
        return results