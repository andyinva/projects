# Bible Search Lite - Search Operators Reference

## Wildcard Operators

### Asterisk (*) - Multiple Characters Wildcard
Matches any number of characters (0 or more). **Automatically includes possessive forms.**

**Examples:**
- `"love*"` → love, loved, loving, lover, loves, loveth, love's
- `"bless*"` → bless, blessed, blessing, blessings, blessedness, blessing's
- `"*ness"` → righteousness, holiness, goodness, kindness
- `"father*"` → father, fathers, father's, fathers'

**Note:** Possessive forms (with apostrophes like 's or s') are automatically matched

### Percent Sign (%) - Stem/Root Wildcard
Same as asterisk (*), matches word stems and variations. **Automatically includes possessive forms.**

**Examples:**
- `"believ%"` → believe, believed, believer, believing, believeth, believer's
- `"lov%"` → love, loved, loves, lover, loving, loveth, lover's
- `"pray%"` → pray, prayed, prayer, prayers, praying, prayer's

**Note:** * and % work identically - use whichever you prefer. Both automatically match possessive forms.

### Question Mark (?) - Single Character Wildcard
Matches exactly one character.

**Examples:**
- `l?ve` → love, live (not leave or believe)
- `m?n` → man, men, min, mon

## Special Operators

### Ampersand (&) - Word Placeholder
Matches any single word. Use for patterns where you want exactly one word between search terms.

**Examples:**
- `who & sent` → "who had sent", "who hath sent", "who will send"
- `I & you` → "I tell you", "I command you", "I say you"
- `who & & sent` → "who will then send" (two words between)
- `love & & God` → "love dwelleth in God", "love is of God"

**Tip:** Combine with wildcards: `who & sen*` → "who had sent", "who will send"

### Greater Than (>) - Ordered Words
Ensures words appear in the specified order (but not necessarily consecutive).

**Examples:**
- `love > neighbour` → "love thy neighbour" (love before neighbour)
- `faith > works` → verses where "faith" comes before "works"
- `God > love > man` → three words in sequence
- `lov% > God` → "love the Lord thy God" (with wildcard)

**Note:** Order matters! "love > God" gives different results than "God > love"

### Tilde (~N) - Proximity Operator
Finds words within N words or less of each other. The number specifies the maximum word distance (range: 0 to N).

**Examples:**
- `love ~0 God` → "love God" (adjacent words only) - 5 results
- `love ~2 God` → "love of God", "love the God" (0-2 words between) - 26 results
- `love ~4 God` → "love the Lord thy God" (0-4 words between) - 44 results
- `faith ~5 works` → "faith" and "works" within 5 words - 8 results
- `believ% ~3 Jesus` → any "believe" form within 3 words of "Jesus" - 15 results

**Tip:** Smaller numbers give more precise matches. ~0 means adjacent, ~10 allows wide spacing.

## Boolean Operators

### AND
Both terms must appear in the verse (in any order).

**Examples:**
- `faith AND works` → verses containing both words
- `prayer AND fasting` → both terms present

**Note:** Use CAPITAL letters for AND/OR operators

### OR
Either term (or both) must appear.

**Examples:**
- `peace OR joy` → verses with either or both
- `angel OR messenger` → either term

### Parentheses ( ) - Control Operator Precedence
Use parentheses to control the order of operations when mixing AND and OR.

**Why you need them:**
- Without parentheses: `"sleep*" OR "slep*" AND father`
  - Evaluated as: `"sleep*" OR ("slep*" AND father)` due to AND having higher precedence
  - Returns: verses with sleep*, OR verses with BOTH slep* and father

- With parentheses: `("sleep*" OR "slep*") AND father`
  - Evaluated as: `("sleep*" OR "slep*") AND father`
  - Returns: verses with father AND (sleep* OR slep*)

**Examples:**
- `("faith" OR "belief") AND works` → verses with works AND either faith or belief
- `("Holy Spirit" OR "Spirit of God") AND power` → verses with power AND either phrase
- `("love*" OR "lov%") AND "one another"` → verses with "one another" AND any love form

**Note:** Parentheses only work with AND/OR operators, not with special operators like `>`, `~`, or `&`

## Exact Phrases

Use quotation marks for exact word order.

**Examples:**
- `"in the beginning"` → exact phrase only
- `"love the Lord"` → exact phrase in this order
- `"I am"` → exact two-word phrase

## Combining Operators

Mix different operators for powerful searches:

- `"faith without" AND works` → exact phrase plus word
- `love* AND neighbor` → any form of "love" with "neighbor"
- `"Holy Spirit" OR "Spirit of God"` → either phrase
- `("love*" OR "charity") AND neighbor` → verses with neighbor AND either love or charity
- `believ% > Jesus` → any "believe" form before "Jesus"
- `I & lov% > God` → "I [word] love/loved God"
- `believ% ~3 Jesus` → any "believe" form within 3 words of "Jesus"
- `pray% ~5 faith` → any "pray" form within 5 words of "faith"
- `("faith" OR "belief") AND ("works" OR "deeds")` → complex AND/OR combinations

## Important Limitations

### Wildcard Requirements
**Wildcards (`*`, `?`) REQUIRE quotes for precision:**
- ✅ `"sing*"` → finds singing, singer, singers (wildcard works)
- ✅ `sing` → finds words containing "sing" (partial match)
- ❌ `sing*` → treats asterisk as literal character (finds nothing)

**This rule creates clear behavior:**
- **Unquoted terms** = simple and forgiving (partial matching)
- **Quoted terms** = precision and control (exact matching + wildcards)

### Wildcards with Relationship Operators
Wildcards work with `>`, `~`, and `&` operators when quoted:
- ✅ `"bless*" > fertile` → blessed/blessing before fertile
- ✅ `"love*" ~4 God` → love/loved/loving within 4 words of God
- ✅ `who & "sen*"` → who [word] sent/send/sending

### Operator Mixing Limitations
**You CANNOT mix `>` (ordered) and `~` (proximity) in the same query:**
- ✅ `"bless*" > fertile > increase` → multiple ordered words
- ✅ `fertile ~4 increase` → proximity search
- ❌ `"bless*" > fertile ~4 increase` → NOT supported (mixing operators)

**Why this limitation exists:**
The search parser processes each operator type independently. When it detects `~N`, it uses proximity logic for the entire query. When it detects `>`, it uses ordered-words logic. Mixing them would require a more complex query parser.

**Workaround:**
Break complex queries into multiple simpler searches:
1. First search: `"bless*" > fertile`
2. Then search within results: `fertile ~4 increase`

## Quick Reference Table

| Operator | Purpose | Example |
|----------|---------|---------|
| `*` | Multiple characters wildcard | `love*` → loved, loving |
| `%` | Stem/root wildcard (same as *) | `believ%` → believe, believed |
| `?` | Single character wildcard | `m?n` → man, men |
| `&` | Word placeholder (exactly one word) | `who & sent` → "who had sent" |
| `>` | Ordered words (must be in sequence) | `love > God` → love before God |
| `~N` | Proximity (words within N words) | `love ~4 God` → within 4 words |
| `AND` | Both terms required | `faith AND works` |
| `OR` | Either term (or both) | `peace OR joy` |
| `( )` | Control operator precedence | `("A" OR "B") AND C` |
| `" "` | Exact phrase | `"in the beginning"` |

## Test Files

The following test files demonstrate each operator:

- `test_stem_wildcard.py` - Tests for % operator
- `test_word_placeholder.py` - Tests for & operator
- `test_ordered_words.py` - Tests for > operator
- `test_proximity.py` - Tests for ~N operator
- `test_filter_pattern.py` - Tests for pattern filtering
- `test_filter_who_sen.py` - Tests for filter with wildcards
- `test_filter_with_placeholder.py` - Tests for filter with placeholders
- `test_book_filter.py` - Tests for book filtering
- `test_load_more.py` - Tests for load more functionality

Run any test file with: `python3 test_<name>.py`
