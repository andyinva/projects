# Bible Search Database Specification

## Overview

The Bible Search application uses a SQLite database (`database/bibles.db`) to store biblical texts, translations, books, verses, and subject categorizations. The database is **627.52 MB** in size with **160,644 pages** (4,096 bytes per page).

## Database Statistics

| Table | Record Count | Description |
|-------|--------------|-------------|
| `books` | 66 | Biblical books (Old and New Testament) |
| `translations` | 17 | Bible translations/versions |
| `verses` | 32,584 | Unique verse references (book, chapter, verse) |
| `verse_texts` | 475,055 | Actual verse text for each translation |
| `subjects` | 2 | Subject categories for verse categorization |
| `subject_verses` | 24 | Verses assigned to specific subjects |

**Total Records**: 507,748

## Table Schemas

### books
Stores the 66 biblical books with ordering information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Unique book identifier |
| `name` | TEXT | NOT NULL | Full book name (e.g., "Genesis") |
| `abbreviation` | TEXT | NOT NULL | Book abbreviation (e.g., "Gen") |
| `testament` | TEXT | NOT NULL | "Old" or "New" Testament |
| `order_index` | INTEGER | NOT NULL | Canonical book order (1-66) |

**Sample Data**: Genesis (Gen, Old), Exodus (Exo, Old), Leviticus (Lev, Old), Numbers (Num, Old), Deuteronomy (Deu, Old)

### translations
Contains Bible translation information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Unique translation identifier |
| `name` | TEXT | NOT NULL | Full translation name |
| `abbreviation` | TEXT | NOT NULL | Translation abbreviation |
| `description` | TEXT | | Translation description |
| `created_date` | TIMESTAMP | | Creation timestamp |

**Sample Translations**: 
- King James Bible (KJV)
- American Standard Version (ASV)
- Douay-Rheims Bible (DRB)
- Darby Bible Translation (DBT)
- English Revised Version (ERV)
- Webster Bible Translation (WBT)
- World English Bible (WEB)
- Young's Literal Translation (YLT)
- American King James Version (AKJ)
- Weymouth New Testament (WNT)

### verses
Defines unique verse references without text content.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Unique verse identifier |
| `book_id` | INTEGER | NOT NULL, FK → books.id | Reference to book |
| `chapter` | INTEGER | NOT NULL | Chapter number |
| `verse_number` | INTEGER | NOT NULL | Verse number within chapter |

### verse_texts
Contains the actual text content for each verse in each translation.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Unique record identifier |
| `verse_id` | INTEGER | NOT NULL, FK → verses.id | Reference to verse |
| `translation_id` | INTEGER | NOT NULL, FK → translations.id | Reference to translation |
| `text` | TEXT | NOT NULL | Actual verse text content |

**Data Volume**: 475,055 records (average ~14.6 translations per verse)

### subjects
Subject categories for topical verse organization.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Unique subject identifier |
| `name` | TEXT | NOT NULL | Subject name |
| `created_date` | TEXT | | Creation date |

**Current Subjects**: "Darkness in Heavens", "Job"

### subject_verses
Links verses to subjects with additional metadata.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Unique record identifier |
| `subject_id` | INTEGER | NOT NULL, FK → subjects.id | Reference to subject |
| `verse_reference` | TEXT | NOT NULL | Human-readable verse reference |
| `translation` | TEXT | NOT NULL | Translation used |
| `verse_text` | TEXT | NOT NULL | Cached verse text |
| `comments` | TEXT | | Optional comments |
| `order_index` | INTEGER | | Display order within subject |
| `created_date` | TEXT | | Creation date |

## Database Relationships

```
books (1) ←→ (many) verses (1) ←→ (many) verse_texts (many) ←→ (1) translations
                                       ↓
subjects (1) ←→ (many) subject_verses
```

### Foreign Key Relationships
- `verses.book_id` → `books.id`
- `verse_texts.verse_id` → `verses.id`
- `verse_texts.translation_id` → `translations.id`
- `subject_verses.subject_id` → `subjects.id`

**Note**: Foreign key constraints are **disabled** in the current database configuration.

## Indexes

The database includes several performance-optimized indexes:

| Index Name | Table | Columns | Purpose |
|------------|-------|---------|---------|
| `idx_verses_book_chapter` | verses | book_id, chapter | Fast chapter lookups |
| `idx_verse_texts_verse` | verse_texts | verse_id | Verse text retrieval |
| `idx_verse_texts_translation` | verse_texts | translation_id | Translation-specific queries |
| `idx_verse_texts_composite` | verse_texts | translation_id, verse_id | Composite lookups |
| `idx_translations_abbr` | translations | abbreviation | Translation lookup by abbreviation |
| `idx_books_abbr` | books | abbreviation | Book lookup by abbreviation |

## Data Distribution

- **Average verses per book**: ~494 verses
- **Average translations per verse**: ~14.6 translations
- **Testament distribution**: 39 Old Testament books, 27 New Testament books
- **Storage efficiency**: ~1.32 KB per verse text record

## System Tables

- `sqlite_sequence`: Auto-increment sequence tracking
- `sqlite_stat1`: Query optimizer statistics

## Technical Notes

- Database file: `database/bibles.db`
- SQLite version: Compatible with SQLite3
- Page size: 4,096 bytes
- Total pages: 160,644
- Encoding: UTF-8 (inferred from text content)
- Journal mode: Default (DELETE)
- Foreign keys: Disabled

---
*Generated: September 3, 2025*