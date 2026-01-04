#!/usr/bin/env python3
"""
Test script to demonstrate two-word search functionality
"""

# Simulate the old vs new SQL query generation

def old_query_logic(words):
    """Old logic - could match words split between filename and content"""
    conditions = []
    params = []

    for word in words:
        search_pattern = f"%{word}%"
        conditions.append("(content LIKE ? OR filename LIKE ?)")
        params.extend([search_pattern, search_pattern])

    sql = f"WHERE {' AND '.join(conditions)}"
    return sql, params

def new_query_logic(words):
    """New logic - ALL words must be in content OR ALL in filename"""
    content_conditions = []
    filename_conditions = []
    params = []

    for word in words:
        search_pattern = f"%{word}%"
        content_conditions.append("content LIKE ?")
        filename_conditions.append("filename LIKE ?")
        params.append(search_pattern)  # for content

    # Duplicate params for filename search
    for word in words:
        search_pattern = f"%{word}%"
        params.append(search_pattern)  # for filename

    # Match if ALL words are in content OR ALL words are in filename
    sql = f"WHERE (({' AND '.join(content_conditions)}) OR ({' AND '.join(filename_conditions)}))"
    return sql, params

# Test with two words
test_words = ["Abraham", "prophecy"]

print("=" * 70)
print("Testing two-word search: 'Abraham prophecy'")
print("=" * 70)
print()

print("OLD LOGIC (INCORRECT):")
print("-" * 70)
old_sql, old_params = old_query_logic(test_words)
print(f"SQL: {old_sql}")
print(f"Params: {old_params}")
print()
print("Problem: This would match a file named 'Abraham.docx' that contains")
print("         'prophecy' in content, even though 'Abraham' isn't in the content!")
print()

print("NEW LOGIC (CORRECT):")
print("-" * 70)
new_sql, new_params = new_query_logic(test_words)
print(f"SQL: {new_sql}")
print(f"Params: {new_params}")
print()
print("Solution: Now ALL words must appear together - either ALL in content")
print("          OR ALL in filename. This correctly finds documents containing")
print("          both 'Abraham' AND 'prophecy' in the same field.")
print()

print("=" * 70)
print("EXAMPLES:")
print("=" * 70)
print()
print("✓ WILL MATCH:")
print("  - Content: 'The Abraham prophecy was...'  (both in content)")
print("  - Filename: 'Abraham prophecy.docx'       (both in filename)")
print()
print("✗ WILL NOT MATCH:")
print("  - Content: 'The prophecy was...'")
print("    Filename: 'Abraham.docx'                (split between fields)")
print()
