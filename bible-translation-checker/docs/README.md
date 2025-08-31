# OSIS XML to JSON Bible Converter

This script converts OSIS XML Bible files to JSON format with strict 3-letter naming conventions.

## Features

- ✅ Parses OSIS XML format with proper namespace handling
- ✅ Extracts Bible text from `<verse>`, `<chapter>`, and `<div type="book">` tags
- ✅ Converts to JSON structure: `{"translation_info": {"abbrev": "KJV", "name": "King James Version"}, "books": {"Gen": {"name": "Genesis", "chapters": {"1": {"1": "In the beginning..."}}}}}`
- ✅ Handles OSIS tags like `<verse osisID="Gen.1.1">`, `<chapter>`, `<div type="book">`
- ✅ Cleans text by removing XML markup while preserving Bible content
- ✅ Translation abbreviations are exactly 3 letters and UPPERCASE (e.g., "KJV", "ASV", "ESV")
- ✅ Book abbreviations are exactly 3 letters (e.g., "Gen", "Exo", "Mat", "Mar", "Joh")
- ✅ Includes both abbreviation and full name for translations and books
- ✅ Only includes standard 66 books with exact 3-letter abbreviations
- ✅ Skips non-canonical books and content that don't match expected abbreviations
- ✅ Maps OSIS book IDs to required 3-letter format
- ✅ Saves each Bible as [3-LETTER-ABBREV].json
- ✅ Includes error handling for malformed XML and missing books
- ✅ Progress indicators and logging
- ✅ Validates JSON contains expected book abbreviations

## Requirements

- Python 3.6+ (uses built-in xml.etree.ElementTree)

## Usage

```bash
python3 osis_to_json.py
```

## Output Format

The script generates JSON files with this exact structure:

```json
{
  "translation_info": {
    "abbrev": "KJV",
    "name": "King James Version"
  },
  "books": {
    "Gen": {
      "name": "Genesis",
      "chapters": {
        "1": {
          "1": "In the beginning God created the heaven and the earth.",
          "2": "And the earth was without form, and void..."
        }
      }
    }
  }
}
```

## Book Abbreviation Mapping

The script uses this exact mapping for the standard 66 books:

### Old Testament (39 books)
- Genesis=Gen, Exodus=Exo, Leviticus=Lev, Numbers=Num, Deuteronomy=Deu
- Joshua=Jos, Judges=Jdg, Ruth=Rut, 1Samuel=1Sa, 2Samuel=2Sa
- 1Kings=1Ki, 2Kings=2Ki, 1Chronicles=1Ch, 2Chronicles=2Ch
- Ezra=Ezr, Nehemiah=Neh, Esther=Est, Job=Job, Psalms=Psa
- Proverbs=Pro, Ecclesiastes=Ecc, SongofSongs=Son, Isaiah=Isa
- Jeremiah=Jer, Lamentations=Lam, Ezekiel=Eze, Daniel=Dan
- Hosea=Hos, Joel=Joe, Amos=Amo, Obadiah=Oba, Jonah=Jon
- Micah=Mic, Nahum=Nah, Habakkuk=Hab, Zephaniah=Zep, Haggai=Hag
- Zechariah=Zec, Malachi=Mal

### New Testament (27 books)
- Matthew=Mat, Mark=Mar, Luke=Luk, John=Joh, Acts=Act
- Romans=Rom, 1Corinthians=1Co, 2Corinthians=2Co, Galatians=Gal
- Ephesians=Eph, Philippians=Phi, Colossians=Col
- 1Thessalonians=1Th, 2Thessalonians=2Th, 1Timothy=1Ti, 2Timothy=2Ti
- Titus=Tit, Philemon=Phm, Hebrews=Heb, James=Jas
- 1Peter=1Pe, 2Peter=2Pe, 1John=1Jo, 2John=2Jo, 3John=3Jo
- Jude=Jde, Revelation=Rev

## Example Usage

The JSON format enables table queries like:

```python
import json
data = json.load(open('KJV.json'))
verse = data['books']['Gen']['chapters']['1']['1']
print(f"KJV Gen 1:1 {verse}")
# Output: KJV Gen 1:1 In the beginning God created the heaven and the earth.
```

## Conversion Results

Successfully converted 41 out of 43 XML files:
- Generated JSON files with 3-letter abbreviations (KJV.json, ASV.json, etc.)
- Properly handled complete Bibles (66 books), New Testament only (27 books), and Old Testament only (39 books)
- Skipped non-canonical books (Apocrypha) while preserving the standard 66 books
- 2 files failed due to XML parsing errors in source files