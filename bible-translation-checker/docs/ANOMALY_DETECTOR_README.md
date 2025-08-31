# Bible JSON Anomaly Detection Utility

A comprehensive Python utility to detect and log anomalies in JSON Bible files converted from OSIS XML format.

## Features

✅ **Text Content Validation:**
- Detects numbers in verse text (0-9) - should not exist in Bible text
- Finds invalid characters (only allows: a-z, A-Z, space, standard punctuation)
- Identifies multiple consecutive spaces ("  " or more)
- Flags suspiciously short (< 3 chars) or long (> 500 chars) verses
- Detects XML/HTML tags that weren't properly cleaned

✅ **Verse Reference Sequence Validation:**
- Verifies logical verse progression within chapters (1, 2, 3... no gaps or duplicates)
- Checks chapter sequence within books (1, 2, 3... no gaps or duplicates)
- Flags missing verses in standard chapters
- Detects non-integer verse/chapter numbers

✅ **Structure Validation:**
- Ensures all 66 expected books are present with correct 3-letter abbreviations
- Verifies translation abbreviation is exactly 3 uppercase letters
- Checks for empty verses, chapters, or books
- Validates JSON structure integrity

✅ **Advanced Checks:**
- Flags verses with unusual encoding issues (strange unicode characters)
- Detects verses that start/end with whitespace
- Finds verses with unusual capitalization patterns
- Checks for repeated identical verses (possible duplication errors)
- Color-coded console output (red for errors, yellow for warnings, green for clean)

## Requirements

```bash
pip install colorama
```

## Installation

The utility uses only built-in Python libraries plus colorama for colored output. No additional installation required.

## Usage

### Basic Usage

```bash
# Analyze all JSON files in current directory
python3 bible_anomaly_detector.py

# Analyze files in specific directory
python3 bible_anomaly_detector.py --dir /path/to/json/files

# Specify custom log directory
python3 bible_anomaly_detector.py --log-dir ./my_logs
```

### Configuration

```bash
# Create sample configuration file
python3 bible_anomaly_detector.py --create-config --config my_config.json

# Use custom configuration
python3 bible_anomaly_detector.py --config my_config.json
```

### Command Line Options

```
--dir PATH          Directory containing JSON files (default: current directory)
--config PATH       Configuration file path
--create-config     Create sample configuration file
--log-dir PATH      Directory for log files (default: ./anomaly_logs)
```

## Configuration Options

The utility is highly configurable via JSON config file:

```json
{
  "check_text_content": true,      // Enable text content validation
  "check_sequences": true,         // Enable sequence validation
  "check_structure": true,         // Enable structure validation
  "check_encoding": true,          // Enable encoding checks
  "min_verse_length": 3,          // Minimum verse length
  "max_verse_length": 500,        // Maximum verse length
  "allowed_chars_pattern": "...",  // Regex for allowed characters
  "skip_books": ["Psa", "Pro"]    // Books to skip during analysis
}
```

## Output Files

### Individual Translation Logs
- **Format:** `[ABBREV]_anomalies.log` (e.g., `KJV_anomalies.log`, `ASV_anomalies.log`)
- **Content:** Detailed anomaly reports grouped by severity and category
- **Example:**
```
ANOMALY DETECTION REPORT FOR KJV
Source file: KJV.json
Analysis complete
================================================================================

ERRORS (0):
----------------------------------------

WARNINGS (278):
----------------------------------------

  TEXT_CONTENT (271):
    1. Exo:13:1: Duplicate verse content
       Details: Same as Exo:6:10: And the LORD spake unto Moses, saying,...
    2. Gen:1:5: Multiple consecutive spaces
       Details: Found in: And God called the light  Day...
```

### Summary Report
- **File:** `anomaly_summary.txt`
- **Content:** Overall statistics, file-by-file summary, top issues
- **Example:**
```
BIBLE JSON ANOMALY DETECTION SUMMARY REPORT
============================================================

Files processed: 38
Total anomalies found: 105068

GLOBAL STATISTICS BY SEVERITY:
------------------------------
   ERROR:  73488
 WARNING:  31580

FILE-BY-FILE SUMMARY:
------------------------------
KJV:   0 errors, 278 warnings (KJV.json)
ASV: 1778 errors, 545 warnings (ASV.json)
```

## Anomaly Categories

### 1. TEXT_CONTENT
- **Numbers in text:** `Gen:1:1: Contains numeric characters`
- **Invalid characters:** `Mat:5:3: Contains invalid characters`
- **Multiple spaces:** `Joh:3:16: Multiple consecutive spaces`
- **Verse length:** `Psa:119:1: Verse too long (645 chars)`
- **HTML/XML remnants:** `Rom:8:28: Contains HTML/XML tags`
- **Whitespace issues:** `1Co:13:4: Leading or trailing whitespace`
- **Duplicate verses:** `Exo:13:1: Duplicate verse content`

### 2. SEQUENCE
- **Missing chapters:** `Gen: Missing chapters [5, 12]`
- **Duplicate chapters:** `Exo: Duplicate chapters [3]`
- **Missing verses:** `Gen:1: Missing verses [15, 23]`
- **Non-integer references:** `Mat:5:abc: Non-integer verse number`

### 3. STRUCTURE
- **Missing books:** `books: Missing expected books [Rev]`
- **Invalid abbreviations:** `translation_info: Expected 3 chars, got: 'KJVA'`
- **Empty content:** `Gen:1:1: Empty verse`
- **JSON integrity:** `FILE: Invalid JSON format`

### 4. ENCODING
- **Unicode issues:** `Joh:1:1: Contains unusual unicode characters`
- **Capitalization:** `Rom:1:16: Unusual capitalization pattern`

## Severity Levels

- **🔴 ERROR:** Critical issues that need immediate fixing
  - Invalid JSON structure
  - Missing required fields
  - Duplicate verses/chapters
  - Invalid character encoding

- **🟡 WARNING:** Issues that should be reviewed
  - Duplicate verse content
  - Unusual verse lengths
  - Missing expected books
  - Formatting inconsistencies

- **🔵 INFO:** Informational notices
  - Statistics and counts
  - Analysis completion status

## Color-Coded Console Output

- **🔴 Red:** Files with errors
- **🟡 Yellow:** Files with warnings only
- **🟢 Green:** Clean files (no anomalies)
- **🔵 Blue:** Progress and summary information
- **🔵 Cyan:** File processing status

## Example Analysis Results

Based on testing 38 JSON Bible files:

```
📈 FINAL SUMMARY:
   Files processed: 38
   Clean files: 0
   Files with issues: 38
   Total anomalies: 105,068

Top Issues Found:
- 91,380 text content issues (duplicate verses, formatting)
- 13,306 encoding issues (unusual characters)
- 261 structure issues (missing books/fields)
- 121 sequence issues (gaps in verses/chapters)
```

## Common Issues Found

1. **Duplicate Introductory Phrases:** Many translations repeat "And the LORD spake unto Moses, saying" 
2. **Encoding Problems:** Special characters not properly converted
3. **Missing Books:** Some translations only contain NT (27 books) or OT (39 books)
4. **Formatting Issues:** Extra spaces, inconsistent punctuation
5. **XML Remnants:** Occasional HTML/XML tags not cleaned

## Integration with Other Tools

The utility generates structured logs that can be:
- Imported into databases for analysis
- Processed by other scripts for automated fixing
- Used to generate quality metrics
- Integrated into CI/CD pipelines for Bible data validation

## Performance

- **Speed:** ~1-3 seconds per Bible translation
- **Memory:** Low memory footprint, processes files individually
- **Scalability:** Can handle hundreds of Bible translations
- **Output:** Detailed logs without overwhelming the console

## Best Practices

1. **Run regularly** after converting new OSIS files
2. **Review warnings** - many are legitimate formatting choices
3. **Focus on errors first** - these indicate data integrity issues
4. **Use configuration** to skip books or checks not relevant to your use case
5. **Archive logs** for historical comparison and quality tracking

## Troubleshooting

### Common Issues

1. **"No JSON files found"**
   - Check directory path
   - Ensure files have .json extension

2. **"Invalid JSON format"**
   - Files may be corrupted
   - Check original OSIS conversion process

3. **High anomaly counts**
   - Review allowed character patterns in config
   - Consider if warnings are acceptable for your use case

4. **Missing colorama**
   - Install: `pip install colorama`
   - Utility works without it (fallback mode)

### Configuration Tips

- Adjust `min_verse_length` and `max_verse_length` based on your Bible versions
- Modify `allowed_chars_pattern` to include language-specific characters
- Use `skip_books` to ignore books with known formatting differences
- Disable specific check types if not relevant to your validation needs