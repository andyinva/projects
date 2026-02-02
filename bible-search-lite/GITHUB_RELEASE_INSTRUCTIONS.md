# GitHub Release v1.1.4 - Instructions

## Quick Release Checklist

### Files to Upload to GitHub Release
✅ Ready in `data/` directory:
- [ ] `bible_data.sql.gz` (81 MB)
- [ ] `checksums.txt` (173 bytes)

### Steps to Create Release

1. **Go to GitHub Releases**
   ```
   https://github.com/andyinva/bible-search-lite/releases
   ```

2. **Click "Draft a new release"**

3. **Fill in Release Details:**
   - **Tag:** `v1.1.4`
   - **Target:** `main` branch
   - **Release title:** `Bible Search Lite v1.1.4`
   - **Description:** Copy from RELEASE_NOTES_v1.1.4.md

4. **Upload Files:**
   - Drag and drop `data/bible_data.sql.gz`
   - Drag and drop `data/checksums.txt`

5. **Publish Release**

### After Publishing

Users can install with:
```bash
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py
```

---

## Release Summary

### Version: v1.1.4
### Release Date: February 2, 2026
### Database: 415 MB (compressed to 81 MB)
### Translations: 39 Bible translations

### Major Features:
- ✨ Two-color highlighting (green base + blue variations)
- ✨ Enhanced possessive form matching
- ✨ Smart filter re-highlighting
- ✨ Translation selector with old English grouping
- ✨ Contraction search support
- 🐛 Database cleaned of pre-existing brackets
- 🐛 Fixed apostrophe handling in wildcards

---

## Verification

After creating the release, verify it works:

```bash
# Test in a clean directory
mkdir test-v1.1.4
cd test-v1.1.4
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py
```

Should download and install successfully.

---

## Distribution URLs

After publishing release `v1.1.4`, files will be available at:

**Database:**
```
https://github.com/andyinva/bible-search-lite/releases/download/v1.1.4/bible_data.sql.gz
```

**Checksums:**
```
https://github.com/andyinva/bible-search-lite/releases/download/v1.1.4/checksums.txt
```

**Setup Script:**
```
https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
```

---

## Files Modified This Release

### Core Files
- `VERSION.txt` → v1.1.4
- `setup.py` → Updated RELEASE_VERSION
- `bible_search.py` → Two-color highlighting, possessive matching
- `bible_search_lite.py` → Filter re-highlighting, word patterns
- `bible_search_ui/ui/widgets.py` → HTML rendering for two colors
- `bible_search_ui/ui/dialogs.py` → Translation grouping

### Documentation
- `RELEASE_NOTES_v1.1.4.md` → Complete release notes
- `SEARCH_OPERATORS.md` → Possessive matching docs

### Database
- `database/bibles.db` → Cleaned all verses (415 MB)
- 39 translations, 31,102+ verses

---

## Commit Messages for Git

Before creating the release, commit all changes:

```bash
git add -A
git commit -m "Release v1.1.4: Two-color highlighting and enhanced search features

- Add two-color highlighting (green base + blue variations)
- Enhance possessive form matching for wildcards
- Implement smart filter re-highlighting
- Group old English translations in selector
- Add contraction search support
- Clean database of pre-existing brackets
- Fix apostrophe handling in wildcard patterns
- Update to 39 Bible translations

See RELEASE_NOTES_v1.1.4.md for full details"

git tag v1.1.4
git push origin main
git push origin v1.1.4
```

---

## Announcement Template

Post this to discussions/social media:

```
🎉 Bible Search Lite v1.1.4 Released!

New Features:
✨ Two-color highlighting (base in green, variations in blue)
✨ Smart filter re-highlighting
✨ Enhanced possessive form matching
✨ Translation selector improvements
✨ Contraction search support

Install with one command:
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py && python3 setup.py

Full release notes:
https://github.com/andyinva/bible-search-lite/releases/tag/v1.1.4

39 Bible translations | 31,000+ verses | Free & Open Source
```

---

## Rollback Plan

If issues are found after release:

1. **Don't delete the release** - it may already be downloaded
2. **Create a hotfix release** (v1.1.5) with fixes
3. **Update setup.py** to point to new version
4. **Announce the hotfix**

---

## Success Metrics

After release, monitor:
- [ ] Download count on GitHub
- [ ] Issues reported
- [ ] User feedback
- [ ] Installation success rate

---

## Next Steps

After this release:
1. Monitor for user feedback
2. Address any issues promptly
3. Plan next feature set
4. Consider documentation improvements

---

**Release prepared by:** Claude Code Assistant
**Date:** February 2, 2026
**Version:** v1.1.4
