# Diff Test Samples

This directory contains test samples for evaluating and improving the diff comparison system.

## Test Pairs

### 1. Technical Blog Post (technical_v1.md → technical_v2.md)

**Tests the following change types:**
- ✅ Typo fixes ("challanging" → "challenging", "develpoers" → "developers")
- ✅ Section reordering (Monitoring moved from end to beginning)
- ✅ Content additions (new introduction paragraph, new subsection "Query Optimization")
- ✅ Minor text modifications ("accross" → "across", "requiers" → "requires")
- ✅ List expansions (adding items to existing lists)
- ✅ Formatting changes (enhanced list item descriptions)
- ✅ Paragraph expansion (adding more detail to existing content)

**Key challenges:**
- Should recognize moved sections (not just delete + add)
- Should highlight individual typos within unchanged content
- Should show inline modifications to list items

### 2. Creative Writing (creative_v1.md → creative_v2.md)

**Tests the following change types:**
- ✅ Sentence merging (combining two sentences into one)
- ✅ Word substitutions ("nearly empty" → "nearly deserted")
- ✅ Paragraph splitting (breaking one paragraph into two)
- ✅ Sentence reordering (wind description moved)
- ✅ Minor stylistic changes ("She had been" → "She'd been")
- ✅ Deletions (removed a sentence about the metal bench)
- ✅ Tone adjustments (subtle word choice changes)
- ✅ Paragraph restructuring (merging related content)

**Key challenges:**
- Should handle merged/split paragraphs gracefully
- Should highlight subtle word substitutions
- Should recognize moved sentences within paragraphs
- Should not mark entire paragraphs as changed when only minor edits occurred

### 3. Documentation (documentation_v1.md → documentation_v2.md)

**Tests the following change types:**
- ✅ Section reordering (Rate Limiting moved up)
- ✅ Structural additions (new sections: Changelog, enhanced Best Practices)
- ✅ Format changes (PUT → PATCH, enhanced code examples)
- ✅ Content expansion (more detailed descriptions)
- ✅ New fields in JSON examples
- ✅ Enhanced error response format
- ✅ Code block additions (Python example)
- ✅ List reorganization (error codes expanded)

**Key challenges:**
- Should handle code block comparisons intelligently
- Should recognize structural changes (endpoint method changes)
- Should handle JSON diff appropriately
- Should recognize section reordering in documentation structure

## Expected Diff Capabilities

A good diff system for a text editor should:

1. **Detect moved content** - Not mark moved paragraphs/sections as delete+add
2. **Inline word changes** - Highlight specific word changes within a line
3. **Handle whitespace intelligently** - Ignore insignificant whitespace changes
4. **Smart paragraph matching** - Match paragraphs even with moderate changes
5. **List handling** - Detect reordered list items vs modified items
6. **Code block awareness** - Handle code blocks as semantic units
7. **Formatting preservation** - Maintain markdown formatting in diff view
8. **Change granularity** - Show character-level changes for small edits, line-level for larger changes

## Evaluation Criteria

When testing diff algorithms, evaluate on:

- **Accuracy**: Does it correctly identify what changed?
- **Granularity**: Is the change highlighted at the right level (char/word/line/block)?
- **Readability**: Can users quickly understand what changed?
- **Performance**: Does it handle large documents efficiently?
- **Move detection**: Does it recognize moved content?
- **False positives**: Does it minimize noise from insignificant changes?
