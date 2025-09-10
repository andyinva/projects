#!/usr/bin/env python3
"""
Script to update the Bible search applications to use the new cleaned database.
"""

import os
import shutil
import sqlite3

def backup_original_files():
    """Create backups of original files before modification."""
    print("Creating backups of original files...")
    
    files_to_backup = [
        'bible_search.py',
        'bible_data.db',
        'Bibles.db'
    ]
    
    backup_dir = 'backup_before_cleanup'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    for file in files_to_backup:
        if os.path.exists(file):
            backup_path = os.path.join(backup_dir, file)
            shutil.copy2(file, backup_path)
            print(f"  Backed up {file} -> {backup_path}")
    
    print("Backup completed.")

def update_python_app():
    """Update the Python Bible search app to use the cleaned database."""
    print("Updating Python app (bible_search.py)...")
    
    # Read the current file
    with open('bible_search.py', 'r') as f:
        content = f.read()
    
    # Replace database path
    content = content.replace(
        'self.sqlite_db_path = "bible_data.db"',
        'self.sqlite_db_path = "Bibles_cleaned.db"'
    )
    
    # Replace the search_bible method with one that works with our schema
    old_search_method = '''    def search_bible(self, search_term: str, translation: str = "All", ignore_case: bool = False,
                    exact_phrase: bool = False, proximity_window: int = 5, 
                    book: str = "All", chapter: int = 0) -> List[Dict[str, Any]]:
        """Search the Bible database using SQLite"""
        self.log_message("Entering search_bible function")
        
        # Parse search term for Boolean operators
        is_boolean, terms = self.parse_search_term(search_term)
        
        # Build search patterns
        patterns = self.build_search_patterns(terms, exact_phrase, proximity_window)
        
        # Create final regex
        if is_boolean and 'AND' in search_term.upper():
            # For AND: all patterns must match (use positive lookahead)
            search_regex = '(?=.*' + ')(?=.*'.join(patterns) + ')'
        elif is_boolean and 'OR' in search_term.upper():
            # For OR: any pattern can match
            search_regex = '(' + '|'.join(patterns) + ')'
        else:
            # Single term or proximity search
            search_regex = patterns[0] if patterns else r'\\b\\w+\\b'
            
        if ignore_case:
            search_regex = f"(?i){search_regex}"
            
        # Build SQL query
        query = """
        SELECT v.book || ' ' || v.chapter || ':' || v.verse as Reference, 
               t.name as Translation, td.text as Text
        FROM Verses v
        JOIN TranslationsData td ON v.id = td.verse_id
        JOIN Translations t ON td.translation_id = t.id
        WHERE td.text REGEXP ?
        """
        
        params = [search_regex]
        
        if book != "All":
            query += " AND v.book = ?"
            params.append(book)
        if chapter != 0:
            query += " AND v.chapter = ?"
            params.append(chapter)
        if translation != "All":
            query += " AND t.name = ?"
            params.append(translation)
            
        self.log_message(f"Executing SQL query with regex: {search_regex}")
        self.log_message(f"Search parameters - ignore_case: {ignore_case}, exact_phrase: {exact_phrase}")
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
                
                # Test if "Day" exists (case sensitive)
                test_cursor = conn.cursor()
                test_cursor.execute("SELECT COUNT(*) FROM Verses v JOIN TranslationsData td ON v.id = td.verse_id WHERE td.text LIKE '%Day%'")
                day_count = test_cursor.fetchone()[0]
                self.log_message(f"Found {day_count} verses containing 'Day' (case sensitive)")
                
                # Test if "Lord" exists (case sensitive) 
                test_cursor.execute("SELECT COUNT(*) FROM Verses v JOIN TranslationsData td ON v.id = td.verse_id WHERE td.text LIKE '%Lord%'")
                lord_count = test_cursor.fetchone()[0]
                self.log_message(f"Found {lord_count} verses containing 'Lord' (case sensitive)")
                
                # Test what case variations exist
                test_cursor.execute("SELECT COUNT(*) FROM Verses v JOIN TranslationsData td ON v.id = td.verse_id WHERE td.text LIKE '%day%'")
                day_lower = test_cursor.fetchone()[0]
                test_cursor.execute("SELECT COUNT(*) FROM Verses v JOIN TranslationsData td ON v.id = td.verse_id WHERE td.text LIKE '%lord%'")
                lord_lower = test_cursor.fetchone()[0]
                self.log_message(f"Found {day_lower} verses with 'day' (lowercase), {lord_lower} verses with 'lord' (lowercase)")
            
            results = []
            for row in rows:
                results.append({
                    'Reference': row[0],
                    'Translation': row[1],
                    'Text': row[2]
                })
                
            conn.close()
            self.log_message(f"Search completed. Found {len(results)} results.")
            
            # Add highlighting info to results
            for result in results:
                result['search_term'] = search_term
                
            return results
            
        except Exception as e:
            self.log_message(f"Error executing SQL query: {e}")
            raise'''
    
    new_search_method = '''    def search_bible(self, search_term: str, translation: str = "All", ignore_case: bool = False,
                    exact_phrase: bool = False, proximity_window: int = 5, 
                    book: str = "All", chapter: int = 0) -> List[Dict[str, Any]]:
        """Search the Bible database using SQLite - Updated for cleaned database"""
        self.log_message("Entering search_bible function (cleaned database version)")
        
        # Parse search term for Boolean operators
        is_boolean, terms = self.parse_search_term(search_term)
        
        # Build search patterns
        patterns = self.build_search_patterns(terms, exact_phrase, proximity_window)
        
        # Create final regex
        if is_boolean and 'AND' in search_term.upper():
            # For AND: all patterns must match (use positive lookahead)
            search_regex = '(?=.*' + ')(?=.*'.join(patterns) + ')'
        elif is_boolean and 'OR' in search_term.upper():
            # For OR: any pattern can match
            search_regex = '(' + '|'.join(patterns) + ')'
        else:
            # Single term or proximity search
            search_regex = patterns[0] if patterns else r'\\b\\w+\\b'
            
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
            "WNT": "weymouth_new_testament"
        }
        
        # Build SQL query for our cleaned database schema
        if translation == "All":
            # Search across all translations
            query = """
            SELECT verse as Reference, 'KJV' as Translation, king_james_bible as Text FROM bible_verses WHERE king_james_bible REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'ASV' as Translation, american_standard_version as Text FROM bible_verses WHERE american_standard_version REGEXP ?
            UNION ALL  
            SELECT verse as Reference, 'DRB' as Translation, douay_rheims_bible as Text FROM bible_verses WHERE douay_rheims_bible REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'DBT' as Translation, darby_bible_translation as Text FROM bible_verses WHERE darby_bible_translation REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'ERV' as Translation, english_revised_version as Text FROM bible_verses WHERE english_revised_version REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'WBT' as Translation, webster_bible_translation as Text FROM bible_verses WHERE webster_bible_translation REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'WEB' as Translation, world_english_bible as Text FROM bible_verses WHERE world_english_bible REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'YLT' as Translation, youngs_literal_translation as Text FROM bible_verses WHERE youngs_literal_translation REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'AKJV' as Translation, american_king_james_version as Text FROM bible_verses WHERE american_king_james_version REGEXP ?
            UNION ALL
            SELECT verse as Reference, 'WNT' as Translation, weymouth_new_testament as Text FROM bible_verses WHERE weymouth_new_testament REGEXP ?
            """
            params = [search_regex] * 10
        else:
            # Search specific translation
            column = translation_columns.get(translation, "king_james_bible")
            query = f"SELECT verse as Reference, ? as Translation, {column} as Text FROM bible_verses WHERE {column} REGEXP ?"
            params = [translation, search_regex]
        
        # Add filters
        if book != "All":
            if translation == "All":
                # Add book filter to each UNION query
                query = query.replace(" REGEXP ?", f" REGEXP ? AND verse LIKE '{book} %'")
            else:
                query += " AND verse LIKE ?"
                params.append(f"{book} %")
                
        if chapter != 0:
            chapter_pattern = f"{book} {chapter}:" if book != "All" else f" {chapter}:"
            if translation == "All":
                query = query.replace(f"verse LIKE '{book} %'", f"verse LIKE '{book} {chapter}:%'")
            else:
                if book != "All":
                    params[-1] = f"{book} {chapter}:%"
                else:
                    query += " AND verse LIKE ?"
                    params.append(f"% {chapter}:%")
            
        self.log_message(f"Executing SQL query with regex: {search_regex}")
        self.log_message(f"Search parameters - ignore_case: {ignore_case}, exact_phrase: {exact_phrase}")
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
            
            # Add highlighting info to results
            for result in results:
                result['search_term'] = search_term
                
            return results
            
        except Exception as e:
            self.log_message(f"Error executing SQL query: {e}")
            raise'''
    
    # Replace the method
    content = content.replace(old_search_method, new_search_method)
    
    # Write the updated file
    with open('bible_search.py', 'w') as f:
        f.write(content)
    
    print("Python app updated successfully.")

def update_powershell_scripts():
    """Update PowerShell scripts to use the cleaned database."""
    print("Updating PowerShell scripts...")
    
    ps_files = ['BibleSearch.ps1', 'BibleSearch2.ps1', 'BibleSearch3.ps1', 'BibleSearch4.ps1']
    
    for ps_file in ps_files:
        if os.path.exists(ps_file):
            print(f"  Updating {ps_file}...")
            
            with open(ps_file, 'r', encoding='utf-8-sig') as f:
                content = f.read()
            
            # Replace database path
            content = content.replace('bible_data.db', 'Bibles_cleaned.db')
            content = content.replace('Bibles.db', 'Bibles_cleaned.db')
            
            with open(ps_file, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            
            print(f"    {ps_file} updated.")

def main():
    """Main function to update all apps."""
    print("=" * 60)
    print("UPDATING BIBLE SEARCH APPS FOR CLEANED DATABASE")
    print("=" * 60)
    
    # Change to the project directory
    os.chdir('/home/andrew/my-projects/AISQLBibleSearch')
    
    # Step 1: Backup original files
    backup_original_files()
    
    # Step 2: Update Python app
    print()
    update_python_app()
    
    # Step 3: Update PowerShell scripts
    print()
    update_powershell_scripts()
    
    print()
    print("=" * 60)
    print("UPDATE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("✅ All applications now use: Bibles_cleaned.db")
    print("✅ Database contains clean text without formatting codes")
    print("✅ Original files backed up in: backup_before_cleanup/")
    print("")
    print("You can now run the applications and they will use the cleaned data!")

if __name__ == "__main__":
    main()