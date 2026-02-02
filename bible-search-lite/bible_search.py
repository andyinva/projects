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
        # Known publication dates for translations not in description field
        TRANSLATION_DATES = {
            'DRB': '1582-1610',
            'DBT': '1890',
            'WEB': '2000',
            'WNT': '1903',
            'NET': '2005',
            'ACV': '2008',
            'BSB': '2016',
            'CPD': '2009',
            'DRC': '1749-52',
            'LEB': '2012',
            'LIT': '1985',
            'NHE': '2023',
            'NHJ': '2023',
            'NHM': '2023',
            'OEB': '2010',
            'OEC': '2010',
            'TWE': '1904',
            'MKJ': '1998',
            'BST': '1844',
            'BBE': '1965',
            'JPS': '1917',
            'ROT': '1902',
            'YLT': '1862',
            'JUB': '2000'
        }

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            cursor.execute("SELECT abbreviation, name, description FROM translations ORDER BY id")
            translation_rows = cursor.fetchall()

            for i, (abbrev, name, description) in enumerate(translation_rows):
                # Extract year from description if present
                # Look for patterns like (1611), (1901), (1534), (1568-1611), etc.
                year_match = re.search(r'\((\d{4}(?:-\d{2,4})?)\)', description)

                if year_match:
                    year = year_match.group(1)
                    full_name = f"{name} ({year})"
                elif abbrev in TRANSLATION_DATES:
                    # Use hardcoded date if available
                    full_name = f"{name} ({TRANSLATION_DATES[abbrev]})"
                else:
                    full_name = name

                translation = Translation(
                    abbreviation=abbrev,
                    full_name=full_name,
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
    
    def _build_proximity_query(self, query: str, case_sensitive: bool, not_search: bool) -> Tuple[str, List[str]]:
        """Build query for searches with ~N (proximity operator).

        For example: "love ~4 God" matches if "love" and "God" appear within 4 words or less of each other.
        """
        # Normalize apostrophes: Convert standard apostrophe (U+0027) to right single quotation mark (U+2019)
        # The database uses U+2019 for apostrophes
        query = query.replace("'", "\u2019")

        # Store the original query for later regex matching
        self._proximity_pattern = query
        self._proximity_case_sensitive = case_sensitive

        # Extract the proximity distance and the words
        import re
        proximity_match = re.search(r'(.*?) ~(\d+) (.*)', query)
        if proximity_match:
            word1 = proximity_match.group(1).strip()
            distance = int(proximity_match.group(2))
            word2 = proximity_match.group(3).strip()

            self._proximity_word1 = word1
            self._proximity_word2 = word2
            self._proximity_distance = distance

            # Build SQL condition that requires both words to be present
            # The proximity check will be done in Python
            sql_conditions = []
            search_terms = []

            for word in [word1, word2]:
                # Strip quotes if present (to support "bless*" ~4 fertile syntax)
                clean_word = word.strip('"').strip("'")
                # Convert wildcards in the word
                search_term = self.convert_wildcard_to_sql(clean_word)
                like_pattern = f"%{search_term}%"

                if case_sensitive:
                    condition = "text LIKE ?"
                else:
                    condition = "LOWER(text) LIKE LOWER(?)"

                if not_search:
                    condition = f"NOT ({condition})"

                sql_conditions.append(condition)
                search_terms.append(like_pattern)

            # Combine with AND (both words must be present, proximity will be checked in Python)
            where_clause = " AND ".join(sql_conditions)

            return where_clause, search_terms

        # Fallback if parsing fails
        return "", []

    def _build_ordered_words_query(self, query: str, case_sensitive: bool, not_search: bool) -> Tuple[str, List[str]]:
        """Build query for searches with > (ordered words operator).

        For example: "love > neighbor" matches "love your neighbor", "love one another and your neighbor"
        The words must appear in the specified order but don't need to be consecutive.
        """
        # Normalize apostrophes: Convert standard apostrophe (U+0027) to right single quotation mark (U+2019)
        # The database uses U+2019 for apostrophes
        query = query.replace("'", "\u2019")

        # Store the original query for later regex matching
        self._ordered_words_pattern = query
        self._ordered_words_case_sensitive = case_sensitive

        # Split by > to get the ordered words
        parts = query.split(' > ')
        ordered_words = [part.strip() for part in parts if part.strip()]

        # Build SQL condition that requires all words to be present
        # The order check will be done in Python
        sql_conditions = []
        search_terms = []

        for word in ordered_words:
            # Strip quotes if present (to support "bless*" > fertile syntax)
            clean_word = word.strip('"').strip("'")
            # Convert wildcards in the word
            search_term = self.convert_wildcard_to_sql(clean_word)
            like_pattern = f"%{search_term}%"

            if case_sensitive:
                condition = "text LIKE ?"
            else:
                condition = "LOWER(text) LIKE LOWER(?)"

            if not_search:
                condition = f"NOT ({condition})"

            sql_conditions.append(condition)
            search_terms.append(like_pattern)

        # Combine with AND (all words must be present, order will be checked in Python)
        where_clause = " AND ".join(sql_conditions)

        return where_clause, search_terms

    def _build_word_placeholder_query(self, query: str, case_sensitive: bool, not_search: bool) -> Tuple[str, List[str]]:
        """Build query for searches containing & (word placeholder).

        For example: "who & send" matches "who will send", "who can send", etc.
        """
        # Normalize apostrophes: Convert standard apostrophe (U+0027) to right single quotation mark (U+2019)
        # The database uses U+2019 for apostrophes
        query = query.replace("'", "\u2019")

        # Store the original query for later regex matching
        self._word_placeholder_pattern = query
        self._word_placeholder_case_sensitive = case_sensitive

        # For SQL, we need to find all the actual words (non-& parts)
        parts = query.split()
        actual_words = [part for part in parts if part != '&']

        # Build SQL condition that requires all actual words to be present
        sql_conditions = []
        search_terms = []

        for word in actual_words:
            # Convert wildcards in the word
            search_term = self.convert_wildcard_to_sql(word)
            like_pattern = f"%{search_term}%"

            if case_sensitive:
                condition = "text LIKE ?"
            else:
                condition = "LOWER(text) LIKE LOWER(?)"

            if not_search:
                condition = f"NOT ({condition})"

            sql_conditions.append(condition)
            search_terms.append(like_pattern)

        # Combine with AND (all words must be present, but order/spacing will be checked in Python)
        where_clause = " AND ".join(sql_conditions)

        return where_clause, search_terms

    def _build_query_with_parentheses(self, query: str, case_sensitive: bool, not_search: bool) -> Tuple[str, List[str]]:
        """Build query for searches with parentheses to control operator precedence.

        Example: ("sleep*" OR "slep*") AND father

        For simplicity, we just tell users to write the query with explicit AND for all terms.
        This method will be enhanced in the future.
        """
        # For now, fall back to normal query building but add SQL parentheses
        # This is a simplified implementation - full parentheses support would require
        # a proper expression parser

        # Simple approach: detect pattern (term OR term) AND term
        # and rewrite the WHERE clause with proper parentheses
        import re

        # Remove the ( ) from query and build normally, but track where they were
        query_no_parens = query.replace('(', '').replace(')', '')
        where_clause, search_terms = self.build_word_search_query(query_no_parens, case_sensitive)

        # If query had pattern: (A OR B) AND C
        # The where_clause is: A OR B AND C
        # We need to make it: (A OR B) AND C

        # Find first AND in the where clause and wrap everything before it in parens
        and_pos = where_clause.upper().find(' AND ')
        if and_pos > 0:
            # Wrap the part before AND in parentheses
            where_clause = f"({where_clause[:and_pos]}) {where_clause[and_pos:]}"

        return where_clause, search_terms

    def build_word_search_query(self, query: str, case_sensitive: bool = False) -> Tuple[str, List[str]]:
        """Build SQL query for word search with wildcards and operators.

        Special symbols:
        - * : wildcard for any characters within a word (e.g., "sen*" matches "sent", "send")
        - % : stem/root wildcard, same as * (e.g., "believ%" matches "believe", "believed", "believer")
        - & : placeholder for any single word (e.g., "who & send" matches "who will send")
        - > : ordered words separator (e.g., "love > neighbor" matches "love your neighbor")
        - ~N : proximity operator (e.g., "love ~4 God" matches if words within 4 words or less)
        """
        # Normalize apostrophes: Convert standard apostrophe (U+0027) to right single quotation mark (U+2019)
        # The database uses U+2019 for apostrophes
        query = query.replace("'", "\u2019")

        words = []
        operators = []

        # Handle NOT operator (!)
        if query.startswith('!'):
            query = query[1:].strip()
            not_search = True
        else:
            not_search = False

        # Check if query contains ~N (proximity operator)
        import re
        proximity_match = re.search(r' ~(\d+) ', query)
        if proximity_match:
            # Build query for proximity pattern
            return self._build_proximity_query(query, case_sensitive, not_search)

        # Check if query contains > (ordered words)
        contains_ordered_operator = ' > ' in query

        if contains_ordered_operator:
            # Build query for ordered words pattern
            return self._build_ordered_words_query(query, case_sensitive, not_search)

        # Check if query contains & (word placeholder)
        contains_word_placeholder = '&' in query and ' & ' in query

        if contains_word_placeholder:
            # Build a regex-based search using REGEXP (if supported) or fallback to Python filtering
            # For now, we'll use a single LIKE pattern and filter in Python
            # Convert query like "who & send" to pattern for Python regex matching
            return self._build_word_placeholder_query(query, case_sensitive, not_search)

        # Check for parentheses - if present, handle them first
        if '(' in query or ')' in query:
            return self._build_query_with_parentheses(query, case_sensitive, not_search)

        # Split by AND/OR while preserving quoted phrases
        parts = re.findall(r'"[^"]*"|[^\s]+', query)

        sql_conditions = []
        search_terms = []

        for part in parts:
            if part.upper() in ['AND', 'OR']:
                operators.append(part.upper())
                continue
            
            # Remove quotes from exact phrases
            quoted_wildcard = False  # Track if this is a quoted wildcard term
            if part.startswith('"') and part.endswith('"'):
                search_term = part[1:-1]  # Remove quotes

                # Check if quoted term contains wildcards
                # "sent*" means words starting with "sent" (with word boundaries)
                if '*' in search_term or '%' in search_term or '?' in search_term:
                    # Quoted wildcard - treat as wildcard with word boundaries
                    quoted_term = False
                    quoted_wildcard = True  # Mark as quoted wildcard
                    # Store for word boundary filtering
                    if not hasattr(self, '_wildcard_terms'):
                        self._wildcard_terms = []
                    self._wildcard_terms.append(search_term)
                    self._wildcard_case_sensitive = case_sensitive
                    # Apply wildcard conversion
                    search_term = self.convert_wildcard_to_sql(search_term)
                else:
                    # Quoted exact phrase without wildcards
                    quoted_term = True
            else:
                # Unquoted term - wildcards are NOT supported
                # Treat wildcards as literal characters
                # "sing*" without quotes should search for the literal text "sing*"
                quoted_term = False
                search_term = part  # Use as-is, no wildcard conversion

            if quoted_term:
                # For quoted terms, we'll do a broader search and filter for exact matches in Python
                # This is simpler and more reliable than complex SQL word boundary logic
                like_pattern = f"%{search_term}%"

                if case_sensitive:
                    condition = "text LIKE ?"
                else:
                    condition = "LOWER(text) LIKE LOWER(?)"

                if not_search:
                    condition = f"NOT ({condition})"

                sql_conditions.append(condition)
                search_terms.append(like_pattern)
                # Note: We'll filter for exact word matches in the results processing
            else:
                # Regular wildcard search
                # For quoted wildcards, add % on both sides to find matches anywhere in text
                # The word boundary filtering in Python will ensure precise matching
                if quoted_wildcard:
                    # Quoted wildcard like "sing*" or "father'?" needs % on both sides
                    # to match anywhere in the text, then Python regex will enforce word boundaries
                    like_pattern = f"%{search_term}%"
                else:
                    # Unquoted wildcard or regular term - allow matches anywhere
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
    
    def _highlight_proximity_pattern(self, text: str, query: str) -> str:
        """Highlight proximity pattern.

        For example, for pattern "love ~4 God", highlight both "love" and "God"
        if they appear within 4 words of each other.
        """
        # Extract the words from the proximity query
        proximity_match = re.search(r'(.*?) ~(\d+) (.*)', query)
        if not proximity_match:
            return text

        word1 = proximity_match.group(1).strip()
        word2 = proximity_match.group(3).strip()

        # Strip quotes if present (to support "bless*" ~4 fertile syntax)
        clean_word1 = word1.strip('"').strip("'")
        clean_word2 = word2.strip('"').strip("'")

        # Convert wildcards to regex
        word1_pattern = clean_word1.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
        word2_pattern = clean_word2.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')

        # Build regex patterns
        regex1 = r'\b' + word1_pattern + r'\b'
        regex2 = r'\b' + word2_pattern + r'\b'

        # Find and highlight all occurrences of both words
        highlighted_text = text
        matches_to_highlight = []

        for match in re.finditer(regex1, highlighted_text, flags=re.IGNORECASE):
            matches_to_highlight.append((match.start(), match.end(), match.group(0)))

        for match in re.finditer(regex2, highlighted_text, flags=re.IGNORECASE):
            matches_to_highlight.append((match.start(), match.end(), match.group(0)))

        # Sort by position (reverse order)
        matches_to_highlight.sort(key=lambda x: x[0], reverse=True)

        # Remove duplicates
        seen_positions = set()
        unique_matches = []
        for start, end, text_match in matches_to_highlight:
            if start not in seen_positions:
                unique_matches.append((start, end, text_match))
                seen_positions.add(start)

        # Apply highlights from end to start
        for start, end, matched_text in unique_matches:
            highlighted_text = highlighted_text[:start] + matched_text + highlighted_text[end:]

        return highlighted_text

    def _highlight_ordered_words_pattern(self, text: str, query: str) -> str:
        """Highlight ordered words pattern.

        For example, for pattern "love > neighbor", highlight both "love" and "neighbor"
        wherever they appear in order.
        """
        # Split by > to get ordered words
        ordered_words = [word.strip() for word in query.split(' > ') if word.strip()]

        # Build regex pattern to find all matching words
        regex_parts = []
        for word in ordered_words:
            # Strip quotes if present (to support "bless*" > fertile syntax)
            clean_word = word.strip('"').strip("'")
            # Convert wildcards to regex
            word_pattern = clean_word.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
            regex_parts.append(r'\b' + word_pattern + r'\b')

        # Find each word and highlight it
        highlighted_text = text
        matches_to_highlight = []

        for word_pattern in regex_parts:
            for match in re.finditer(word_pattern, highlighted_text, flags=re.IGNORECASE):
                matches_to_highlight.append((match.start(), match.end(), match.group(0)))

        # Sort by position (reverse order so we can replace from end to start)
        matches_to_highlight.sort(key=lambda x: x[0], reverse=True)

        # Remove duplicates (same position)
        seen_positions = set()
        unique_matches = []
        for start, end, text_match in matches_to_highlight:
            if start not in seen_positions:
                unique_matches.append((start, end, text_match))
                seen_positions.add(start)

        # Apply highlights from end to start (to preserve positions)
        for start, end, matched_text in unique_matches:
            highlighted_text = highlighted_text[:start] + matched_text + highlighted_text[end:]

        return highlighted_text

    def _highlight_word_placeholder_pattern(self, text: str, query: str) -> str:
        """Highlight text that matches a word placeholder pattern.

        For example, for pattern "who & send", highlight "who will send" as "[who] [will] [send]"
        """
        # Build regex pattern from word placeholder query
        regex_parts = []
        parts = query.split()

        for part in parts:
            if part == '&':
                # & matches any single word
                regex_parts.append(r'(\w+)')
            else:
                # Regular word - convert wildcards to regex and capture
                # Both * and % are stem/root wildcards
                word_pattern = part.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
                regex_parts.append(f'({word_pattern})')

        # Join with \s+ (one or more whitespace)
        regex_pattern = r'\b' + r'\s+'.join(regex_parts) + r'\b'

        # Find the match
        match = re.search(regex_pattern, text, flags=re.IGNORECASE)

        if not match:
            return text

        # Build highlighted text by replacing matched portion with highlighted version
        highlighted_match = ""

        # Add each captured group with brackets and preserve whitespace
        for i, group in enumerate(match.groups()):
            if i > 0:
                # Add the whitespace between this group and previous group
                # Get position of current group within the match
                group_start_in_match = match.start(i + 1) - match.start()
                prev_group_end_in_match = match.end(i) - match.start()
                highlighted_match += match.group(0)[prev_group_end_in_match:group_start_in_match]

            highlighted_match += group

        result = text[:match.start()] + highlighted_match + text[match.end():]

        return result

    def highlight_search_terms(self, text: str, query: str) -> str:
        """Highlight search terms in text with [ ] brackets."""
        # Normalize apostrophes: Convert standard apostrophe (U+0027) to right single quotation mark (U+2019)
        # The database uses U+2019 for apostrophes
        query = query.replace("'", "\u2019")

        # Special handling for proximity patterns (~N)
        if re.search(r' ~\d+ ', query):
            return self._highlight_proximity_pattern(text, query)

        # Special handling for ordered words patterns (>)
        if ' > ' in query:
            return self._highlight_ordered_words_pattern(text, query)

        # Special handling for word placeholder patterns (&)
        if '&' in query and ' & ' in query:
            return self._highlight_word_placeholder_pattern(text, query)

        # Extract search terms from query
        terms = re.findall(r'"[^"]*"|[^\s]+', query)

        # Debug: Uncomment the next line to see what terms are being processed
        # print(f"DEBUG: Highlighting query='{query}' in text='{text[:50]}...' with terms={terms}")

        # Collect all matches first to avoid overlapping highlights
        matches_to_highlight = []

        for term in terms:
            if term.upper() in ['AND', 'OR', '!']:
                continue

            # Strip parentheses from terms (they're used for grouping in queries)
            term = term.strip('()')
            
            # Handle quoted phrases
            if term.startswith('"') and term.endswith('"'):
                phrase = term[1:-1]  # Remove quotes
                if phrase:
                    # Check if quoted phrase contains wildcards
                    # "sing*" means words starting with "sing" (with word boundaries)
                    if '*' in phrase or '?' in phrase or '%' in phrase:
                        # Quoted wildcard - build pattern with word boundaries
                        # Track the base pattern (non-wildcard part) for two-color highlighting
                        regex_parts = []
                        starts_with_wildcard = phrase.startswith('*') or phrase.startswith('%') or phrase.startswith('?')

                        if not starts_with_wildcard:
                            regex_parts.append(r'\b')

                        # Build the base pattern (without wildcards) to identify the fixed part
                        # Only use two-color highlighting for patterns like "father*" (letters + wildcard at end)
                        # Don't use it for patterns like "?'*" (wildcard at start)
                        if starts_with_wildcard:
                            # Pattern starts with wildcard - no clear base, use single-color highlighting
                            base_pattern = None
                        else:
                            # Pattern starts with letters - extract base for two-color highlighting
                            base_pattern = phrase.replace('*', '').replace('%', '').replace('?', '')

                        for char in phrase:
                            if char == '*' or char == '%':
                                # Match word characters including apostrophes
                                regex_parts.append(r"[a-zA-Z]*(?:[''][a-zA-Z]*)*")
                            elif char == '?':
                                regex_parts.append(r'\w')
                            else:
                                regex_parts.append(re.escape(char))

                        # Don't add extra possessive pattern - it's already handled in the wildcard match above
                        regex_parts.append(r'\b')
                        wildcard_pattern = ''.join(regex_parts)
                        for match in re.finditer(wildcard_pattern, text, flags=re.IGNORECASE):
                            # Store: (start, end, matched_text, base_pattern_for_coloring)
                            matches_to_highlight.append((match.start(), match.end(), match.group(0), base_pattern))
                    else:
                        # Quoted phrase without wildcards - exact match with word boundaries
                        pattern = r'\b' + re.escape(phrase) + r'\b'
                        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                            # No wildcard - no two-color highlighting needed (None as 4th element)
                            matches_to_highlight.append((match.start(), match.end(), match.group(0), None))
            else:
                # Unquoted term - wildcards are NOT supported
                # Treat *, ?, % as literal characters
                # For unquoted terms, use partial matching (matches "sent" in "presents")
                clean_term = term.strip('"')
                if clean_term:
                    # For unquoted terms, find words containing the search term (like SQL LIKE %term%)
                    # This is more intuitive - unquoted = broader match, quoted = exact match
                    if len(clean_term) <= 2:
                        # For very short terms (1-2 chars), only highlight if they appear at word boundaries
                        # This prevents "I" from highlighting "Israel", "David", etc.
                        boundary_pattern = r'\b' + re.escape(clean_term) + r'(?=\W|$)'
                        for match in re.finditer(boundary_pattern, text, flags=re.IGNORECASE):
                            matches_to_highlight.append((match.start(), match.end(), match.group(0), None))
                    else:
                        # For longer terms, find words containing the search term
                        # Pattern: \b\w*term\w*\b matches whole words containing "term"
                        # Example: "sent" matches "sent", "presents", "sentries", "resent"
                        containing_pattern = r'\b\w*' + re.escape(clean_term) + r'\w*\b'
                        for word_match in re.finditer(containing_pattern, text, flags=re.IGNORECASE):
                            # Highlight the entire word that contains the search term
                            # This ensures "presents" is bracketed as "[presents]" not "pre[sent]s"
                            word_text = word_match.group(0)
                            word_start = word_match.start()
                            word_end = word_match.end()
                            matches_to_highlight.append((word_start, word_end, word_text, None))
        
        # Sort matches by position (reverse order for easier processing)
        matches_to_highlight.sort(key=lambda x: x[0], reverse=True)

        # Remove overlapping matches (keep the first/longest one)
        filtered_matches = []
        for start, end, matched_text, base_pattern in matches_to_highlight:
            # Check if this match overlaps with any already accepted match
            overlaps = False
            for existing_start, existing_end, _, _ in filtered_matches:
                if not (end <= existing_start or start >= existing_end):
                    overlaps = True
                    break

            if not overlaps:
                filtered_matches.append((start, end, matched_text, base_pattern))

        # Apply highlights from right to left (to preserve indices)
        highlighted_text = text
        for start, end, matched_text, base_pattern in filtered_matches:
            # Two-color highlighting for wildcard matches
            if base_pattern:
                # Find where the base pattern ends in the matched text
                base_len = len(base_pattern)
                matched_lower = matched_text.lower()
                base_lower = base_pattern.lower()

                # Find the base in the match (case-insensitive)
                base_start = matched_lower.find(base_lower)
                if base_start != -1:
                    base_end = base_start + base_len
                    base_part = matched_text[base_start:base_end]

                    # Check if there's a variation after the base
                    if base_end < len(matched_text):
                        variation_part = matched_text[base_end:]
                        # Base in brackets, variation in curly braces for blue color
                        highlighted_text = highlighted_text[:start] + '[' + base_part + ']{' + variation_part + '}' + highlighted_text[end:]
                    else:
                        # No variation - just base
                        highlighted_text = highlighted_text[:start] + '[' + matched_text + ']' + highlighted_text[end:]
                else:
                    # Couldn't find base - just use regular brackets
                    highlighted_text = highlighted_text[:start] + '[' + matched_text + ']' + highlighted_text[end:]
            else:
                # No wildcard - regular bracketing
                highlighted_text = highlighted_text[:start] + '[' + matched_text + ']' + highlighted_text[end:]

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
                     abbreviate_results: bool = False, book_filter: List[str] = None) -> List[SearchResult]:
        """Perform verse search based on query type."""
        if not enabled_translations:
            enabled_translations = [t.abbreviation for t in self.translations if t.enabled]

        search_type = self.detect_search_type(query)
        results = []

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            if search_type == "verse_reference":
                results = self._search_verse_reference(cursor, query, enabled_translations, book_filter)
            else:
                results = self._search_words(cursor, query, enabled_translations, case_sensitive, book_filter)

            conn.close()

            # Store total count before filtering for metadata
            total_before_filter = len(results)

            # Apply post-processing
            if unique_verses:
                results = self._filter_unique_verses(results)
                # Store metadata about filtering
                self.last_search_metadata = {
                    'total_count': total_before_filter,
                    'unique_count': len(results),
                    'unique_verses_enabled': True
                }
                print(f"🔍 Unique verses: {total_before_filter} total → {len(results)} unique")
            else:
                self.last_search_metadata = {
                    'total_count': len(results),
                    'unique_count': None,
                    'unique_verses_enabled': False
                }

            if abbreviate_results:
                for result in results:
                    result.text = self.abbreviate_text(result.text)
                    result.highlighted_text = self.abbreviate_text(result.highlighted_text)

            # Sort by biblical book order, then by translation order
            translation_order = {t.abbreviation: t.sort_order for t in self.translations}
            results.sort(key=lambda x: (
                self.book_order.get(x.book, 999),           # Biblical book order first
                x.chapter,                                   # Chapter order second
                x.verse,                                     # Verse order third
                translation_order.get(x.translation, 999)   # Translation order fourth
            ))

        except Exception as e:
            print(f"Search error: {e}")

        return results
    
    def _search_verse_reference(self, cursor, query: str, enabled_translations: List[str],
                               book_filter: List[str] = None) -> List[SearchResult]:
        """Search for specific verse references."""
        verse_ref = self.parse_verse_reference(query)
        if not verse_ref:
            return []

        # Check if the verse reference book is in the filter (if filter is active)
        if book_filter and len(book_filter) > 0:
            if verse_ref['book'] not in book_filter:
                print(f"📚 Book '{verse_ref['book']}' not in filter, skipping")
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
                     case_sensitive: bool, book_filter: List[str] = None) -> List[SearchResult]:
        """Search for words with wildcards and operators."""
        # Clear any previous special patterns
        self._word_placeholder_pattern = None
        self._word_placeholder_case_sensitive = False
        self._ordered_words_pattern = None
        self._ordered_words_case_sensitive = False
        self._proximity_pattern = None
        self._proximity_case_sensitive = False
        self._wildcard_terms = []  # Store wildcard terms for word boundary filtering
        self._wildcard_case_sensitive = False

        where_clause, search_terms = self.build_word_search_query(query, case_sensitive)

        # Store whether query uses OR operator for later filtering
        self._query_uses_or = ' OR ' in query.upper()

        results = []

        for translation in self.translations:
            if translation.abbreviation not in enabled_translations:
                continue

            try:
                # Build SQL with optional book filter
                if book_filter and len(book_filter) > 0:
                    # Add book name filter to WHERE clause
                    book_placeholders = ','.join(['?' for _ in book_filter])
                    sql = f"""
                    SELECT b.abbreviation, v.chapter, v.verse_number, vt.text, b.name
                    FROM books b
                    JOIN verses v ON b.id = v.book_id
                    JOIN verse_texts vt ON v.id = vt.verse_id
                    JOIN translations t ON vt.translation_id = t.id
                    WHERE t.abbreviation = ? AND ({where_clause}) AND b.name IN ({book_placeholders})
                    ORDER BY b.order_index, v.chapter, v.verse_number
                    """
                    params = [translation.abbreviation] + search_terms + book_filter
                else:
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
                    # Filter results to ensure quoted terms are exact word matches
                    if not self._contains_exact_quoted_terms(row[3], query, case_sensitive):
                        continue

                    # Filter results for wildcard terms with word boundaries
                    if not self._matches_wildcard_word_boundaries(row[3]):
                        continue

                    # Filter results for proximity patterns (queries with ~N)
                    if hasattr(self, '_proximity_pattern') and self._proximity_pattern:
                        if not self._matches_proximity_pattern(row[3]):
                            continue

                    # Filter results for ordered words patterns (queries with >)
                    if hasattr(self, '_ordered_words_pattern') and self._ordered_words_pattern:
                        if not self._matches_ordered_words_pattern(row[3]):
                            continue

                    # Filter results for word placeholder patterns (queries with &)
                    if hasattr(self, '_word_placeholder_pattern') and self._word_placeholder_pattern:
                        if not self._matches_word_placeholder_pattern(row[3]):
                            continue

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
    
    def _matches_proximity_pattern(self, text: str) -> bool:
        """Check if text matches a proximity pattern (with ~N).

        For example, pattern "love ~4 God" should match if "love" and "God"
        appear within 4 words or less of each other.
        """
        if not hasattr(self, '_proximity_pattern'):
            return True

        word1 = getattr(self, '_proximity_word1', '')
        word2 = getattr(self, '_proximity_word2', '')
        distance = getattr(self, '_proximity_distance', 0)
        case_sensitive = getattr(self, '_proximity_case_sensitive', False)

        # Strip quotes if present (to support "bless*" ~4 fertile syntax)
        clean_word1 = word1.strip('"').strip("'")
        clean_word2 = word2.strip('"').strip("'")

        # Convert wildcards to regex
        word1_pattern = clean_word1.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
        word2_pattern = clean_word2.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')

        # Build regex patterns for both words
        word1_regex = r'\b' + word1_pattern + r'\b'
        word2_regex = r'\b' + word2_pattern + r'\b'

        flags = 0 if case_sensitive else re.IGNORECASE

        # Find all occurrences of both words
        word1_matches = [(m.start(), m.end()) for m in re.finditer(word1_regex, text, flags)]
        word2_matches = [(m.start(), m.end()) for m in re.finditer(word2_regex, text, flags)]

        if not word1_matches or not word2_matches:
            return False

        # Check if any pair of matches is within the specified distance
        # Split text into words to count distance
        words = re.findall(r'\b\w+\b', text)

        # Build position map: character position -> word index
        word_positions = {}
        pos = 0
        for i, word in enumerate(words):
            match = re.search(r'\b' + re.escape(word) + r'\b', text[pos:], flags)
            if match:
                char_pos = pos + match.start()
                word_positions[char_pos] = i
                pos = pos + match.end()

        # Check each pair of word1 and word2 matches
        for w1_start, w1_end in word1_matches:
            for w2_start, w2_end in word2_matches:
                # Find word indices for these character positions
                w1_idx = None
                w2_idx = None

                # Find closest word index for word1
                for char_pos, word_idx in word_positions.items():
                    if char_pos <= w1_start <= char_pos + len(words[word_idx]):
                        w1_idx = word_idx
                        break

                # Find closest word index for word2
                for char_pos, word_idx in word_positions.items():
                    if char_pos <= w2_start <= char_pos + len(words[word_idx]):
                        w2_idx = word_idx
                        break

                if w1_idx is not None and w2_idx is not None:
                    # Calculate word distance (subtract 1 for the words themselves)
                    word_distance = abs(w2_idx - w1_idx) - 1

                    # Check if within proximity distance (0 to N words between)
                    if word_distance <= distance:
                        return True

        return False

    def _matches_ordered_words_pattern(self, text: str) -> bool:
        """Check if text matches an ordered words pattern (with >).

        For example, pattern "love > neighbor" should match "love your neighbor"
        but not "neighbor whom you love".
        """
        if not hasattr(self, '_ordered_words_pattern'):
            return True

        pattern = self._ordered_words_pattern
        case_sensitive = getattr(self, '_ordered_words_case_sensitive', False)

        # Split by > to get ordered words
        ordered_words = [word.strip() for word in pattern.split(' > ') if word.strip()]

        # Build regex pattern to check order
        # For "love > neighbor", build: \blove\b.*?\bneighbor\b
        regex_parts = []
        for word in ordered_words:
            # Strip quotes if present (to support "bless*" > fertile syntax)
            clean_word = word.strip('"').strip("'")
            # Convert wildcards to regex
            # Both * and % are stem/root wildcards
            word_pattern = clean_word.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
            regex_parts.append(r'\b' + word_pattern + r'\b')

        # Join with .*? (any characters, non-greedy) to allow words in between
        regex_pattern = r'.*?'.join(regex_parts)

        # Compile and match
        flags = 0 if case_sensitive else re.IGNORECASE
        match = re.search(regex_pattern, text, flags)

        return match is not None

    def _matches_word_placeholder_pattern(self, text: str) -> bool:
        """Check if text matches a pattern with word placeholders (&).

        For example, pattern "who & send" should match "who will send", "who can send", etc.
        Pattern "who & & send" should match "who will then send", etc.
        """
        if not hasattr(self, '_word_placeholder_pattern'):
            return True

        pattern = self._word_placeholder_pattern
        case_sensitive = getattr(self, '_word_placeholder_case_sensitive', False)

        # Build regex pattern from word placeholder pattern
        # Convert "who & send" to r'\bwho\s+\w+\s+send\b'
        # Convert "who & & send" to r'\bwho\s+\w+\s+\w+\s+send\b'

        regex_parts = []
        parts = pattern.split()

        for i, part in enumerate(parts):
            if part == '&':
                # & matches any single word: \w+ (one or more word characters)
                regex_parts.append(r'\w+')
            else:
                # Regular word - convert wildcards to regex
                # Both * and % are stem/root wildcards
                word_pattern = part.replace('*', r'\w*').replace('%', r'\w*').replace('?', r'\w')
                regex_parts.append(word_pattern)

        # Join with \s+ (one or more whitespace characters)
        regex_pattern = r'\b' + r'\s+'.join(regex_parts) + r'\b'

        # Compile and match
        flags = 0 if case_sensitive else re.IGNORECASE
        match = re.search(regex_pattern, text, flags)

        return match is not None

    def _matches_wildcard_word_boundaries(self, text: str) -> bool:
        """Check if wildcard terms match with word boundaries.

        For example:
        - sent* should match "sent", "sentence" but NOT "present"
        - *sent should match "sent", "resent" but NOT "sentence"
        - *sent* should match "present", "sentence", "resent"

        For OR queries, returns True if ANY term matches.
        For AND queries, returns True only if ALL terms match.
        """
        if not hasattr(self, '_wildcard_terms') or not self._wildcard_terms:
            return True

        case_sensitive = getattr(self, '_wildcard_case_sensitive', False)
        flags = 0 if case_sensitive else re.IGNORECASE

        # Check if query uses OR operator
        uses_or = getattr(self, '_query_uses_or', False)

        # For OR queries: return True if ANY term matches
        # For AND queries: return True only if ALL terms match
        matches = []

        for term in self._wildcard_terms:
            # Convert wildcard term to regex with word boundaries
            # * and % mean "any word characters" (not any characters)
            # ? means "single word character"

            pattern_parts = []
            i = 0
            starts_with_wildcard = term.startswith('*') or term.startswith('%')
            ends_with_wildcard = term.endswith('*') or term.endswith('%')

            # Add word boundary at start if term doesn't start with wildcard
            if not starts_with_wildcard:
                pattern_parts.append(r'\b')

            # Convert the term character by character
            while i < len(term):
                char = term[i]
                if char in ('*', '%'):
                    # Match any word characters (stays within word boundaries)
                    pattern_parts.append(r'\w*')
                elif char == '?':
                    # Match single word character
                    pattern_parts.append(r'\w')
                else:
                    # Literal character
                    pattern_parts.append(re.escape(char))
                i += 1

            # Always add word boundary at end
            # sent* means "words starting with sent", so we need \bsent\w*\b
            # This ensures "sent" is at a word boundary, and * only matches within the word
            pattern_parts.append(r'\b')

            pattern = ''.join(pattern_parts)

            # Check if this pattern matches in the text
            term_matches = bool(re.search(pattern, text, flags))
            matches.append(term_matches)

            # For OR queries, we can return early if we find a match
            if uses_or and term_matches:
                return True

        # For OR queries: if we got here, no term matched
        if uses_or:
            return False

        # For AND queries: all terms must match
        return all(matches)

    def _contains_exact_quoted_terms(self, text: str, query: str, case_sensitive: bool) -> bool:
        """Check if text contains all quoted terms as exact word matches."""
        # Extract quoted terms from query
        quoted_terms = re.findall(r'"([^"]*)"', query)

        if not quoted_terms:
            # No quoted terms, so no filtering needed
            return True

        # Check each quoted term for exact word match
        for term in quoted_terms:
            if not term.strip():
                continue

            # Skip quoted wildcards - they're handled by _matches_wildcard_word_boundaries
            # "sing*" should be filtered by wildcard matching, not exact matching
            if '*' in term or '%' in term or '?' in term:
                continue

            # Create word boundary pattern for non-wildcard quoted terms
            pattern = r'\b' + re.escape(term) + r'\b'
            flags = 0 if case_sensitive else re.IGNORECASE

            if not re.search(pattern, text, flags):
                return False

        return True
    
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
                             start_verse: int, num_verses: int = None) -> List[SearchResult]:
        """Get continuous verses for reading window. If num_verses is None, loads entire chapter."""
        results = []
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            if num_verses is None:
                # Load entire chapter
                sql = """
                SELECT b.abbreviation, v.chapter, v.verse_number, vt.text 
                FROM books b
                JOIN verses v ON b.id = v.book_id
                JOIN verse_texts vt ON v.id = vt.verse_id
                JOIN translations t ON vt.translation_id = t.id
                WHERE t.abbreviation = ?
                AND b.abbreviation = ?
                AND v.chapter = ?
                ORDER BY v.verse_number
                """
                cursor.execute(sql, (translation, book, chapter))
            else:
                # Load limited verses (existing behavior)
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

    def get_continuous_reading_cross_chapter(self, translation: str, book: str, chapter: int,
                                            start_verse: int, num_verses: int = 50) -> List[SearchResult]:
        """Get continuous verses across chapter boundaries for reading window."""
        results = []

        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()

            # Query to get verses starting from the specified verse, crossing chapter boundaries
            # Uses verse ordering within the book to get continuous reading
            sql = """
            SELECT b.abbreviation, v.chapter, v.verse_number, vt.text
            FROM books b
            JOIN verses v ON b.id = v.book_id
            JOIN verse_texts vt ON v.id = vt.verse_id
            JOIN translations t ON vt.translation_id = t.id
            WHERE t.abbreviation = ?
            AND b.abbreviation = ?
            AND (v.chapter > ? OR (v.chapter = ? AND v.verse_number >= ?))
            ORDER BY v.chapter, v.verse_number
            LIMIT ?
            """
            cursor.execute(sql, (translation, book, chapter, chapter, start_verse, num_verses))
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
            print(f"Error getting continuous reading across chapters: {e}")

        return results