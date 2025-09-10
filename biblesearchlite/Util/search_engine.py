#!/usr/bin/env python3
"""
Search Engine for Bible Search Application
Handles all search logic, regex building, and result processing
"""

import re
import logging
from typing import List, Dict, Any, Tuple
from itertools import permutations


class SearchEngine:
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.logger = logging.getLogger(__name__)
        
        # Translation column mapping for cleaned database
        self.translation_columns = {
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
            "WNT": "weymouth_new_testament"
        }
        
        # Default translation order
        self.translation_order = {
            "KJV": 1, "ASV": 2, "DRB": 3, "DBT": 4, "ERV": 5,
            "WBT": 6, "WEB": 7, "YLT": 8, "AKJV": 9, "WNT": 10
        }
    
    def parse_search_term(self, search_term: str) -> Tuple[bool, List[str]]:
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
    
    def build_search_patterns(self, terms: List[str], proximity_window: int) -> List[str]:
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
    
    def build_search_regex(self, search_term: str, proximity_window: int, ignore_case: bool) -> str:
        """Build the final search regex from search term"""
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
        
        return search_regex
    
    def build_search_query(self, search_regex: str, selected_translations: List[str], 
                          book: str = "All", chapter: int = 0, bible_scope: str = "bible",
                          old_testament_books: List[str] = None, 
                          new_testament_books: List[str] = None) -> Tuple[str, List[str]]:
        """Build SQL query for bible search"""
        
        # Build UNION query for selected translations
        union_queries = []
        params = []
        
        for trans_code in selected_translations:
            if trans_code in self.translation_columns and trans_code != "All":
                column = self.translation_columns[trans_code]
                # Add order number to the query for sorting
                order_num = self.translation_order.get(trans_code, 999)
                union_queries.append(f"SELECT verse as Reference, '{trans_code}' as Translation, {column} as Text, {order_num} as SortOrder FROM bible_verses WHERE {column} REGEXP ?")
                params.append(search_regex)
        
        if union_queries:
            query = " UNION ALL ".join(union_queries)
        else:
            # Fallback to KJV if no valid translations
            query = "SELECT verse as Reference, 'KJV' as Translation, king_james_bible as Text FROM bible_verses WHERE king_james_bible REGEXP ?"
            params = [search_regex]
        
        # Add filters
        if book != "All" or chapter != 0:
            # Apply book filter
            if book != "All":
                query = query.replace(" REGEXP ?", f" REGEXP ? AND verse LIKE '{book} %'")
            
            # Apply chapter filter
            if chapter != 0:
                if book != "All":
                    query = query.replace(f"verse LIKE '{book} %'", f"verse LIKE '{book} {chapter}:%'")
                else:
                    query = query.replace(" REGEXP ?", f" REGEXP ? AND verse LIKE '% {chapter}:%'")
        
        # Add Bible scope filter (Old Testament, New Testament, or All)
        if bible_scope != "bible":
            if bible_scope == "ot" and old_testament_books:
                # Old Testament filter
                book_conditions = " OR ".join([f"verse LIKE '{book} %'" for book in old_testament_books])
                query = query.replace(" WHERE ", f" WHERE ({book_conditions}) AND ")
            elif bible_scope == "nt" and new_testament_books:
                # New Testament filter
                book_conditions = " OR ".join([f"verse LIKE '{book} %'" for book in new_testament_books])
                query = query.replace(" WHERE ", f" WHERE ({book_conditions}) AND ")
        
        return query, params
    
    def search_bible(self, search_term: str, selected_translations: List[str] = None,
                    ignore_case: bool = False, proximity_window: int = 5, 
                    book: str = "All", chapter: int = 0, bible_scope: str = "bible",
                    old_testament_books: List[str] = None, 
                    new_testament_books: List[str] = None) -> List[Dict[str, Any]]:
        """Search the Bible database using SQLite"""
        
        if not selected_translations:
            selected_translations = ["KJV"]
        
        # Build search regex
        search_regex = self.build_search_regex(search_term, proximity_window, ignore_case)
        
        # Build SQL query
        query, params = self.build_search_query(
            search_regex, selected_translations, book, chapter, bible_scope,
            old_testament_books, new_testament_books
        )
        
        self.logger.info(f"Executing search with regex: {search_regex}")
        
        # Execute search
        results = self.db_manager.search_bible_verses(query, params)
        
        # Convert results to dictionary format
        formatted_results = []
        for result in results:
            formatted_results.append({
                'Reference': result[0],
                'Translation': result[1], 
                'Text': result[2],
                'SortOrder': result[3] if len(result) > 3 else 999
            })
        
        return formatted_results
    
    def get_search_words_for_highlighting(self, search_term: str) -> List[str]:
        """Extract words from search term for highlighting"""
        words = []
        
        # Parse the search term
        is_boolean, terms = self.parse_search_term(search_term)
        
        for term in terms:
            if term.startswith('EXACT:'):
                # For exact phrases, add the whole phrase
                exact_phrase = term[6:]  # Remove 'EXACT:' prefix
                words.append(exact_phrase)
            else:
                # For regular terms, split into individual words
                term_words = re.findall(r'\b\w+\b', term)
                words.extend(term_words)
        
        # Remove duplicates while preserving order
        unique_words = []
        for word in words:
            if word.lower() not in [w.lower() for w in unique_words]:
                unique_words.append(word)
        
        return unique_words
    
    def highlight_text(self, text: str, search_term: str, ignore_case: bool) -> List[Dict[str, str]]:
        """Highlight search terms in text and return formatted segments"""
        search_words = self.get_search_words_for_highlighting(search_term)
        
        if not search_words:
            return [{"text": text, "highlight": False}]
        
        # Create regex pattern for all search words
        escaped_words = [re.escape(word) for word in search_words]
        pattern = '|'.join(escaped_words)
        
        flags = re.IGNORECASE if ignore_case else 0
        
        segments = []
        last_end = 0
        
        for match in re.finditer(pattern, text, flags):
            # Add non-highlighted text before this match
            if match.start() > last_end:
                segments.append({
                    "text": text[last_end:match.start()],
                    "highlight": False
                })
            
            # Add highlighted match
            segments.append({
                "text": match.group(),
                "highlight": True
            })
            
            last_end = match.end()
        
        # Add remaining non-highlighted text
        if last_end < len(text):
            segments.append({
                "text": text[last_end:],
                "highlight": False
            })
        
        return segments
    
    def is_verse_reference(self, text: str) -> bool:
        """Check if text looks like a verse reference"""
        # Simple pattern matching for verse references
        verse_patterns = [
            r'\b\w+\s+\d+:\d+',  # Book Chapter:Verse
            r'\b\d+\s+\w+\s+\d+:\d+',  # Number Book Chapter:Verse
            r'\b\w+\s+\d+:\d+-\d+',  # Book Chapter:Verse-Verse
        ]
        
        for pattern in verse_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False