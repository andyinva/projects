# Release Checklist - v1.1.4

## Pre-Release
- [x] All features tested and working
- [x] VERSION.txt updated to v1.1.4
- [x] setup.py RELEASE_VERSION updated to v1.1.4
- [x] setup_win11.py RELEASE_VERSION updated to v1.1.4
- [x] Database exported (bible_data.sql.gz - 81 MB)
- [x] Checksums generated (checksums.txt)
- [x] Release notes created (RELEASE_NOTES_v1.1.4.md)
- [x] GitHub release instructions created

## Git Commits
- [ ] Commit all changes to main branch
- [ ] Create git tag: `git tag v1.1.4`
- [ ] Push commits: `git push origin main`
- [ ] Push tag: `git push origin v1.1.4`

## GitHub Release
- [ ] Go to https://github.com/andyinva/bible-search-lite/releases
- [ ] Click "Draft a new release"
- [ ] Set tag: v1.1.4
- [ ] Set title: Bible Search Lite v1.1.4
- [ ] Copy release notes from RELEASE_NOTES_v1.1.4.md
- [ ] Upload `data/bible_data.sql.gz` (81 MB)
- [ ] Upload `data/checksums.txt`
- [ ] Publish release

## Post-Release Testing
- [ ] Test installation in clean directory
- [ ] Verify database downloads correctly
- [ ] Verify checksum validation works
- [ ] Test basic search functionality
- [ ] Test two-color highlighting
- [ ] Test filter window with re-highlighting
- [ ] Test translation selector grouping

## Announcement
- [ ] Post release announcement
- [ ] Update README.md if needed
- [ ] Respond to any user questions

## Files Ready for Upload

Location: `data/` directory

1. **bible_data.sql.gz** (81 MB)
   - Compressed SQLite database dump
   - Contains all 39 translations
   - 31,102+ verses
   - Cleaned of pre-existing brackets

2. **checksums.txt** (173 bytes)
   - SHA256 checksum for verification
   - Used by setup.py to validate download

## Key Features in This Release

1. **Two-Color Highlighting**
   - Base words: Green
   - Variations: Blue
   - Example: "father" (green) + "'s" (blue)

2. **Smart Filter Re-Highlighting**
   - Filter to specific words
   - Only filtered words highlighted
   - Removes confusion from original search

3. **Enhanced Possessive Matching**
   - Wildcards match apostrophes
   - "father*" → father, father's, fathers'
   - Consistent across search and filter

4. **Translation Selector**
   - Old English grouped at bottom
   - "Select All" skips old English
   - Added missing dates (SLT, EDG)

5. **Contraction Search**
   - Pattern "?'*" matches it's, I'm, etc.
   - Single-color highlighting for contractions

6. **Database Cleanup**
   - Removed pre-existing brackets
   - Clean text for accurate highlighting
   - All 31,102+ verses processed

## Installation Command for Users

```bash
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py
```

## Quick Test After Release

```bash
# In a new terminal/directory
mkdir test-release
cd test-release
curl -O https://raw.githubusercontent.com/andyinva/bible-search-lite/main/setup.py
python3 setup.py
# Should complete successfully and create working installation
```

## Success Criteria

Release is successful when:
- ✅ Files upload to GitHub without errors
- ✅ Test installation completes successfully
- ✅ Database imports correctly (415 MB final size)
- ✅ Application launches without errors
- ✅ All 39 translations available
- ✅ Search and highlighting work correctly

## Troubleshooting

If issues occur:

**Problem:** Database download fails
**Solution:** Verify release v1.1.4 exists and files are uploaded

**Problem:** Checksum validation fails
**Solution:** Re-upload bible_data.sql.gz, regenerate checksums.txt

**Problem:** Installation fails
**Solution:** Check setup.py RELEASE_VERSION matches tag (v1.1.4)

## Contact

Report issues at:
https://github.com/andyinva/bible-search-lite/issues

---

**Prepared:** February 2, 2026
**Version:** v1.1.4
**Status:** Ready for Release
