# Bible Search Lite - Search Operators Reference

Complete guide to search operators and syntax for Bible Search Lite v1.0.

---

## Table of Contents

1. [Basic Search](#basic-search)
2. [Wildcard Operators](#wildcard-operators)
3. [Boolean Operators](#boolean-operators)
4. [Advanced Operators](#advanced-operators)
5. [Combining Operators](#combining-operators)
6. [Search Options](#search-options)
7. [Examples](#examples)

---

## Basic Search

### Simple Word Search
```
love
```
Finds all verses containing the word "love" (case-insensitive by default).

### Exact Phrase Search
```
"in the beginning"
```
Finds the exact phrase "in the beginning" - words must appear in this exact order.

---

## Wildcard Operators

### Asterisk Wildcard (`*`)
Matches zero or more characters at the end of a word.

**Examples:**
```
love*       → love, loved, lover, loving, loveliness
faith*      → faith, faithful, faithfulness, faithfully
believ*     → believe, believed, believer, believing
```

**Use case:** Finding all variations of a root word.

### Percent Wildcard (`%`)
Stem matching - finds words with the same root (advanced stemming).

**Examples:**
```
believ%     → believe, believed, believer, believing, belief
run%        → run, ran, running, runner, runs
```

**Use case:** More intelligent word variation matching.

---

## Boolean Operators

### AND Operator
Both words must appear in the verse (order doesn't matter).

**Syntax:**
```
faith AND works
```

**Results:** Verses containing both "faith" AND "works"
- ✅ "faith without works is dead"
- ✅ "works demonstrate your faith"
- ❌ "have faith in God" (no "works")

### OR Operator
Either word must appear in the verse.

**Syntax:**
```
love OR charity
```

**Results:** Verses with either "love" OR "charity" (or both)
- ✅ "God is love"
- ✅ "charity never faileth"
- ✅ "faith, hope, and charity"

---

## Advanced Operators

### Word Placeholder (`&`)
Matches patterns with one word between two search terms.

**Syntax:**
```
who & sent
```

**Matches:**
- "who **had** sent"
- "who **hath** sent"
- "who **has** sent"

**Does NOT match:**
- "who sent" (no word between)
- "who had already sent" (more than one word between)

### Ordered Words (`>`)
Ensures first word appears before second word in the verse.

**Syntax:**
```
love > God
```

**Matches:**
- ✅ "**love** the Lord your **God**"
- ✅ "those who **love God**"

**Does NOT match:**
- ❌ "**God** is **love**" (wrong order)

### Proximity Search (`~N`)
Finds words within N words of each other (in any order).

**Syntax:**
```
love ~4 God
```

**Explanation:** Find "love" and "God" within 4 words of each other.

**Matches:**
- ✅ "**love** the Lord your **God**" (3 words apart)
- ✅ "those who **love God**" (1 word apart)
- ✅ "**God** demonstrates His **love**" (3 words apart)

**Does NOT match:**
- ❌ "love... [5+ words] ...God" (too far apart)

---

## Combining Operators

### Complex Queries
You can combine multiple operators for sophisticated searches.

**Example 1: Wildcards + Boolean**
```
faith* AND work*
```
Finds verses with variations of both "faith" and "work".

**Example 2: Phrase + Boolean**
```
"love the Lord" OR "love God"
```
Finds either exact phrase.

**Example 3: Multiple Conditions**
```
(faith OR believe*) AND (works OR deeds)
```
Finds verses about faith/belief AND works/deeds.

**Example 4: Proximity + Wildcards**
```
believ* ~3 salvat*
```
Finds belief-related words near salvation-related words.

---

## Search Options

### Case Sensitive Search
**Checkbox:** "Case Sensitive"

When enabled:
- `Lord` ≠ `lord`
- `God` ≠ `god`

**Use case:** Distinguishing "LORD" (YHWH) from "Lord".

### Unique Verses
**Checkbox:** "Unique Verses"

Shows each verse reference only once, even when searching multiple translations.

**Example:** Instead of showing John 3:16 from KJV, NIV, ESV separately, shows it once.

### Translation Selection
**Button:** "Translations"

Choose which Bible versions to search:
- Single translation: Fast, focused
- Multiple translations: Comprehensive comparison

---

## Examples

### Finding Word Variations

**Goal:** All forms of "believe"
```
believ*
```

**Results:**
- believe, believed, believer, believing, believes

---

### Finding Themes

**Goal:** Verses about faith and works together
```
faith AND works
```

**Results:** Only verses containing both concepts.

---

### Finding Specific Patterns

**Goal:** Phrases like "who had sent" or "who hath sent"
```
who & sent
```

**Results:**
- "who **had** sent"
- "who **hath** sent"
- "who **has** sent"

---

### Finding Word Order

**Goal:** "Love" mentioned before "neighbor"
```
love > neighbor
```

**Results:**
- ✅ "**love** your **neighbor**"
- ❌ "**neighbor** whom you **love**"

---

### Finding Proximity

**Goal:** "Love" and "God" close together
```
love ~4 God
```

**Results:** Verses where these words appear within 4 words of each other.

---

### Complex Searches

**Goal:** Verses about believing leading to salvation
```
believ* ~5 salv*
```

**Goal:** Faith or belief with works or deeds
```
(faith OR believ*) AND (works OR deeds)
```

**Goal:** Specific phrase in Old Testament
```
"I am the Lord"
```
Then use Book Filter → "Old Testament"

---

## Search Tips

### 1. Start Simple
Begin with basic searches, then add operators as needed.

### 2. Use Filters
Combine search operators with Book Filters for targeted results:
- Gospels only
- Pauline Epistles
- Old Testament

### 3. Search History
Successful searches are saved in the dropdown - reuse effective queries.

### 4. Wildcards are Powerful
`*` and `%` help find all word forms without knowing every variation.

### 5. Test Proximity Distance
If `~4` gives too many results, try `~3`. If too few, try `~5`.

---

## Operator Quick Reference

| Operator | Syntax | Example | Finds |
|----------|--------|---------|-------|
| Wildcard | `*` | `love*` | love, loved, loving |
| Stem | `%` | `believ%` | believe, belief, believed |
| AND | `AND` | `faith AND works` | Both words present |
| OR | `OR` | `love OR charity` | Either word present |
| Placeholder | `&` | `who & sent` | Words with 1 between |
| Ordered | `>` | `love > God` | First before second |
| Proximity | `~N` | `love ~4 God` | Within N words |
| Phrase | `"..."` | `"in the beginning"` | Exact phrase |

---

## Performance Notes

- **Simple searches** (single word): Very fast (<0.3s)
- **Wildcard searches**: Fast (<0.5s)
- **Complex boolean**: Moderate (0.5-1s)
- **Multiple translations**: Slower but thorough (1-3s)

Use filters to narrow large result sets.

---

## Common Issues

### Too Many Results
**Solution:** Add more specific terms with AND, or use Book Filter.

### No Results
**Solutions:**
- Check spelling
- Try wildcards (`*` or `%`)
- Use OR for synonyms
- Check translation selection
- Disable "Case Sensitive"

### Unexpected Results
**Solutions:**
- Use exact phrase search (`"..."`)
- Check operator syntax
- Use ordered words (`>`) to control sequence

---

**For more help, see the in-app Help menu or README.md**
