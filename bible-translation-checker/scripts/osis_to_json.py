#!/usr/bin/env python3
"""
OSIS XML to JSON Bible Converter

Converts OSIS XML Bible files to JSON format with strict 3-letter naming conventions.
Handles the standard 66 books of the Bible with consistent abbreviations.

Requirements:
- Python 3.6+ (uses built-in xml.etree.ElementTree)

Usage:
    python osis_to_json.py
"""

import os
import json
import re
import logging
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Complete book mapping from OSIS names to 3-letter abbreviations
BOOK_MAPPING = {
    # Old Testament
    'Gen': {'abbrev': 'Gen', 'name': 'Genesis'},
    'Exod': {'abbrev': 'Exo', 'name': 'Exodus'},
    'Lev': {'abbrev': 'Lev', 'name': 'Leviticus'},
    'Num': {'abbrev': 'Num', 'name': 'Numbers'},
    'Deut': {'abbrev': 'Deu', 'name': 'Deuteronomy'},
    'Josh': {'abbrev': 'Jos', 'name': 'Joshua'},
    'Judg': {'abbrev': 'Jdg', 'name': 'Judges'},
    'Ruth': {'abbrev': 'Rut', 'name': 'Ruth'},
    '1Sam': {'abbrev': '1Sa', 'name': '1 Samuel'},
    '2Sam': {'abbrev': '2Sa', 'name': '2 Samuel'},
    '1Kgs': {'abbrev': '1Ki', 'name': '1 Kings'},
    '2Kgs': {'abbrev': '2Ki', 'name': '2 Kings'},
    '1Chr': {'abbrev': '1Ch', 'name': '1 Chronicles'},
    '2Chr': {'abbrev': '2Ch', 'name': '2 Chronicles'},
    'Ezra': {'abbrev': 'Ezr', 'name': 'Ezra'},
    'Neh': {'abbrev': 'Neh', 'name': 'Nehemiah'},
    'Esth': {'abbrev': 'Est', 'name': 'Esther'},
    'Job': {'abbrev': 'Job', 'name': 'Job'},
    'Ps': {'abbrev': 'Psa', 'name': 'Psalms'},
    'Prov': {'abbrev': 'Pro', 'name': 'Proverbs'},
    'Eccl': {'abbrev': 'Ecc', 'name': 'Ecclesiastes'},
    'Song': {'abbrev': 'Son', 'name': 'Song of Songs'},
    'Isa': {'abbrev': 'Isa', 'name': 'Isaiah'},
    'Jer': {'abbrev': 'Jer', 'name': 'Jeremiah'},
    'Lam': {'abbrev': 'Lam', 'name': 'Lamentations'},
    'Ezek': {'abbrev': 'Eze', 'name': 'Ezekiel'},
    'Dan': {'abbrev': 'Dan', 'name': 'Daniel'},
    'Hos': {'abbrev': 'Hos', 'name': 'Hosea'},
    'Joel': {'abbrev': 'Joe', 'name': 'Joel'},
    'Amos': {'abbrev': 'Amo', 'name': 'Amos'},
    'Obad': {'abbrev': 'Oba', 'name': 'Obadiah'},
    'Jonah': {'abbrev': 'Jon', 'name': 'Jonah'},
    'Mic': {'abbrev': 'Mic', 'name': 'Micah'},
    'Nah': {'abbrev': 'Nah', 'name': 'Nahum'},
    'Hab': {'abbrev': 'Hab', 'name': 'Habakkuk'},
    'Zeph': {'abbrev': 'Zep', 'name': 'Zephaniah'},
    'Hag': {'abbrev': 'Hag', 'name': 'Haggai'},
    'Zech': {'abbrev': 'Zec', 'name': 'Zechariah'},
    'Mal': {'abbrev': 'Mal', 'name': 'Malachi'},
    
    # New Testament
    'Matt': {'abbrev': 'Mat', 'name': 'Matthew'},
    'Mark': {'abbrev': 'Mar', 'name': 'Mark'},
    'Luke': {'abbrev': 'Luk', 'name': 'Luke'},
    'John': {'abbrev': 'Joh', 'name': 'John'},
    'Acts': {'abbrev': 'Act', 'name': 'Acts'},
    'Rom': {'abbrev': 'Rom', 'name': 'Romans'},
    '1Cor': {'abbrev': '1Co', 'name': '1 Corinthians'},
    '2Cor': {'abbrev': '2Co', 'name': '2 Corinthians'},
    'Gal': {'abbrev': 'Gal', 'name': 'Galatians'},
    'Eph': {'abbrev': 'Eph', 'name': 'Ephesians'},
    'Phil': {'abbrev': 'Phi', 'name': 'Philippians'},
    'Col': {'abbrev': 'Col', 'name': 'Colossians'},
    '1Thess': {'abbrev': '1Th', 'name': '1 Thessalonians'},
    '2Thess': {'abbrev': '2Th', 'name': '2 Thessalonians'},
    '1Tim': {'abbrev': '1Ti', 'name': '1 Timothy'},
    '2Tim': {'abbrev': '2Ti', 'name': '2 Timothy'},
    'Titus': {'abbrev': 'Tit', 'name': 'Titus'},
    'Phlm': {'abbrev': 'Phm', 'name': 'Philemon'},
    'Heb': {'abbrev': 'Heb', 'name': 'Hebrews'},
    'Jas': {'abbrev': 'Jas', 'name': 'James'},
    '1Pet': {'abbrev': '1Pe', 'name': '1 Peter'},
    '2Pet': {'abbrev': '2Pe', 'name': '2 Peter'},
    '1John': {'abbrev': '1Jo', 'name': '1 John'},
    '2John': {'abbrev': '2Jo', 'name': '2 John'},
    '3John': {'abbrev': '3Jo', 'name': '3 John'},
    'Jude': {'abbrev': 'Jde', 'name': 'Jude'},
    'Rev': {'abbrev': 'Rev', 'name': 'Revelation'}
}

# Expected 66 books in order
EXPECTED_BOOKS = [
    'Gen', 'Exo', 'Lev', 'Num', 'Deu', 'Jos', 'Jdg', 'Rut', '1Sa', '2Sa',
    '1Ki', '2Ki', '1Ch', '2Ch', 'Ezr', 'Neh', 'Est', 'Job', 'Psa', 'Pro',
    'Ecc', 'Son', 'Isa', 'Jer', 'Lam', 'Eze', 'Dan', 'Hos', 'Joe', 'Amo',
    'Oba', 'Jon', 'Mic', 'Nah', 'Hab', 'Zep', 'Hag', 'Zec', 'Mal', 'Mat',
    'Mar', 'Luk', 'Joh', 'Act', 'Rom', '1Co', '2Co', 'Gal', 'Eph', 'Phi',
    'Col', '1Th', '2Th', '1Ti', '2Ti', 'Tit', 'Phm', 'Heb', 'Jas', '1Pe',
    '2Pe', '1Jo', '2Jo', '3Jo', 'Jde', 'Rev'
]

def extract_translation_info(root) -> Dict[str, str]:
    """Extract translation abbreviation and name from OSIS XML."""
    try:
        # Define namespace
        ns = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}
        
        # Try to get from osisIDWork attribute
        osistext = root.find('.//osis:osisText', ns)
        if osistext is not None:
            abbrev = osistext.get('osisIDWork', '').upper()
            
            # Get name from title in work element
            work = root.find('.//osis:work', ns)
            name = ""
            if work is not None:
                title_elem = work.find('.//osis:title', ns)
                if title_elem is not None and title_elem.text:
                    name = title_elem.text.strip()
            
            # Ensure abbreviation is exactly 3 letters
            if len(abbrev) == 3 and abbrev.isalpha():
                return {"abbrev": abbrev, "name": name}
            elif len(abbrev) > 3:
                # Try to truncate to 3 letters
                abbrev = abbrev[:3]
                return {"abbrev": abbrev, "name": name}
                
    except Exception as e:
        logger.warning(f"Could not extract translation info: {e}")
    
    return {"abbrev": "UNK", "name": "Unknown Translation"}

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace and newlines."""
    if not text:
        return ""
    # Remove extra whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', text.strip())
    return cleaned

def convert_osis_to_json(xml_file: Path) -> Optional[Dict]:
    """Convert a single OSIS XML file to JSON format."""
    try:
        logger.info(f"Processing {xml_file.name}...")
        
        # Parse XML
        try:
            tree = ET.parse(str(xml_file))
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"XML syntax error in {xml_file.name}: {e}")
            return None
        
        # Extract translation info
        translation_info = extract_translation_info(root)
        
        # Initialize JSON structure
        bible_json = {
            "translation_info": translation_info,
            "books": {}
        }
        
        # Define namespace for cleaner code
        ns = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}
        
        # Find all book divs
        book_divs = root.findall('.//osis:div[@type="book"]', ns)
        
        books_found = set()
        
        for book_div in book_divs:
            osis_book_id = book_div.get('osisID')
            if not osis_book_id:
                continue
                
            # Map OSIS book ID to our 3-letter abbreviation
            if osis_book_id not in BOOK_MAPPING:
                logger.warning(f"Skipping unknown book: {osis_book_id}")
                continue
                
            book_info = BOOK_MAPPING[osis_book_id]
            book_abbrev = book_info['abbrev']
            book_name = book_info['name']
            
            books_found.add(book_abbrev)
            
            # Initialize book structure
            bible_json["books"][book_abbrev] = {
                "name": book_name,
                "chapters": {}
            }
            
            # Find all chapters in this book
            chapters = book_div.findall('.//osis:chapter', ns)
            
            for chapter in chapters:
                chapter_id = chapter.get('osisID')
                if not chapter_id:
                    continue
                    
                # Extract chapter number from osisID (e.g., "Gen.1" -> "1")
                chapter_match = re.match(rf'{re.escape(osis_book_id)}\.(\d+)', chapter_id)
                if not chapter_match:
                    continue
                    
                chapter_num = chapter_match.group(1)
                bible_json["books"][book_abbrev]["chapters"][chapter_num] = {}
                
                # Find all verses in this chapter
                verses = chapter.findall('.//osis:verse', ns)
                
                for verse in verses:
                    verse_id = verse.get('osisID')
                    if not verse_id:
                        continue
                        
                    # Extract verse number from osisID (e.g., "Gen.1.1" -> "1")
                    verse_match = re.match(rf'{re.escape(osis_book_id)}\.{re.escape(chapter_num)}\.(\d+)', verse_id)
                    if not verse_match:
                        continue
                        
                    verse_num = verse_match.group(1)
                    
                    # Get verse text and clean it
                    verse_text = ""
                    if verse.text:
                        verse_text = verse.text
                    
                    # Also get text from any child elements
                    for elem in verse.iter():
                        if elem.text and elem.tag != verse.tag:
                            verse_text += elem.text
                        if elem.tail:
                            verse_text += elem.tail
                    
                    verse_text = clean_text(verse_text)
                    bible_json["books"][book_abbrev]["chapters"][chapter_num][verse_num] = verse_text
        
        # Validate that we have some books
        if not books_found:
            logger.error(f"No valid books found in {xml_file.name}")
            return None
            
        logger.info(f"Found {len(books_found)} books in {xml_file.name}: {sorted(books_found)}")
        
        return bible_json
        
    except Exception as e:
        logger.error(f"Error processing {xml_file.name}: {e}")
        return None

def validate_json_structure(bible_json: Dict, filename: str) -> bool:
    """Validate the JSON structure meets requirements."""
    try:
        # Check translation_info
        if "translation_info" not in bible_json:
            logger.error(f"{filename}: Missing translation_info")
            return False
            
        trans_info = bible_json["translation_info"]
        if "abbrev" not in trans_info or "name" not in trans_info:
            logger.error(f"{filename}: Missing abbrev or name in translation_info")
            return False
            
        if len(trans_info["abbrev"]) != 3:
            logger.error(f"{filename}: Translation abbreviation must be exactly 3 letters")
            return False
            
        # Check books structure
        if "books" not in bible_json:
            logger.error(f"{filename}: Missing books")
            return False
            
        books = bible_json["books"]
        
        # Validate book abbreviations are 3 letters
        for book_abbrev in books:
            if len(book_abbrev) != 3:
                logger.error(f"{filename}: Book abbreviation '{book_abbrev}' is not 3 letters")
                return False
                
            if book_abbrev not in EXPECTED_BOOKS:
                logger.warning(f"{filename}: Unexpected book abbreviation '{book_abbrev}'")
        
        logger.info(f"{filename}: Validation passed")
        return True
        
    except Exception as e:
        logger.error(f"{filename}: Validation error: {e}")
        return False

def main():
    """Main conversion function."""
    # Set up paths
    xml_dir = Path("/home/ajhinva/my-project/bible_stats/BiblesXML")
    
    if not xml_dir.exists():
        logger.error(f"Directory not found: {xml_dir}")
        return
        
    # Find all XML files
    xml_files = list(xml_dir.glob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML files")
    
    successful_conversions = 0
    failed_conversions = 0
    
    for xml_file in xml_files:
        # Skip Zone.Identifier files
        if xml_file.name.endswith('.xml:Zone.Identifier'):
            continue
            
        try:
            # Convert to JSON
            bible_json = convert_osis_to_json(xml_file)
            
            if bible_json is None:
                failed_conversions += 1
                continue
                
            # Validate structure
            if not validate_json_structure(bible_json, xml_file.name):
                failed_conversions += 1
                continue
                
            # Generate output filename
            trans_abbrev = bible_json["translation_info"]["abbrev"]
            output_file = xml_dir / f"{trans_abbrev}.json"
            
            # Write JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(bible_json, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Successfully converted {xml_file.name} -> {output_file.name}")
            successful_conversions += 1
            
        except Exception as e:
            logger.error(f"Failed to process {xml_file.name}: {e}")
            failed_conversions += 1
    
    logger.info(f"Conversion complete: {successful_conversions} successful, {failed_conversions} failed")

if __name__ == "__main__":
    main()