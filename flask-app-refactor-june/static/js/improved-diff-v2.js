/**
 * Hierarchical Diff Algorithm V2
 *
 * A smarter diff system designed specifically for document/draft comparison.
 * Uses a three-level hierarchical approach:
 *
 * Level 1: Structural/Paragraph Matching
 * - Parse documents into semantic units (paragraphs, headers, lists, code blocks)
 * - Find best matches between units using similarity scoring
 * - Detect moves, additions, and deletions at the structural level
 *
 * Level 2: Word-Level Comparison
 * - For matched units with <100% similarity, compare word-by-word
 * - Identify word additions, deletions, and substitutions
 *
 * Level 3: Character-Level Refinement
 * - For substituted words, show exact character changes
 * - Useful for typo fixes and minor edits
 */

class ImprovedDiffV2 {
    constructor(options = {}) {
        this.options = {
            // Similarity threshold for matching structural units (0-1)
            structuralMatchThreshold: options.structuralMatchThreshold || 0.5,

            // Similarity threshold for word matching (0-1)
            wordMatchThreshold: options.wordMatchThreshold || 0.6,

            // Detect moved blocks
            detectMoves: options.detectMoves !== undefined ? options.detectMoves : true,

            // Minimum block size for move detection (in words)
            minMoveBlockSize: options.minMoveBlockSize || 5,

            // Whether to ignore case in comparisons
            ignoreCase: options.ignoreCase !== undefined ? options.ignoreCase : false
        };
    }

    /**
     * Main diff computation method
     */
    computeDiff(text1, text2) {
        // Level 1: Parse into structural units
        const blocks1 = this._parseIntoBlocks(text1);
        const blocks2 = this._parseIntoBlocks(text2);

        // Level 1: Match structural units
        const structuralMatches = this._matchStructuralUnits(blocks1, blocks2);

        // Level 2 & 3: For each matched pair, compute word and character diffs
        const detailedDiff = this._addDetailedComparisons(structuralMatches, blocks1, blocks2);

        // Calculate statistics
        const stats = this._calculateStats(detailedDiff);

        return {
            diff: detailedDiff,
            stats: stats,
            blocks1: blocks1,
            blocks2: blocks2
        };
    }

    /**
     * Level 1: Parse text into structural blocks
     * Recognizes: paragraphs, headers, lists, code blocks, blockquotes
     */
    _parseIntoBlocks(text) {
        const lines = text.split('\n');
        const blocks = [];
        let currentBlock = null;
        let blockStartLine = 0;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmed = line.trim();

            // Determine block type
            let blockType = null;
            if (trimmed === '') {
                // Empty line - might be paragraph separator
                if (currentBlock && currentBlock.type === 'paragraph') {
                    // End current paragraph
                    blocks.push(currentBlock);
                    currentBlock = null;
                }
                continue;
            } else if (trimmed.startsWith('#')) {
                blockType = 'header';
            } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.match(/^\d+\.\s/)) {
                blockType = 'list';
            } else if (trimmed.startsWith('```')) {
                blockType = 'code';
            } else if (trimmed.startsWith('>')) {
                blockType = 'blockquote';
            } else {
                blockType = 'paragraph';
            }

            // Handle block continuation or creation
            if (!currentBlock) {
                currentBlock = {
                    type: blockType,
                    content: line,
                    startLine: i,
                    endLine: i,
                    lines: [line]
                };
            } else if (currentBlock.type === blockType ||
                       (currentBlock.type === 'paragraph' && blockType === 'paragraph')) {
                // Continue current block
                currentBlock.content += '\n' + line;
                currentBlock.endLine = i;
                currentBlock.lines.push(line);
            } else {
                // Different block type - save current and start new
                blocks.push(currentBlock);
                currentBlock = {
                    type: blockType,
                    content: line,
                    startLine: i,
                    endLine: i,
                    lines: [line]
                };
            }
        }

        // Don't forget the last block
        if (currentBlock) {
            blocks.push(currentBlock);
        }

        return blocks;
    }

    /**
     * Level 1: Match structural units between two documents
     * Returns array of match objects with type: matched/added/removed/moved
     */
    _matchStructuralUnits(blocks1, blocks2) {
        const matches = [];
        const used1 = new Set();
        const used2 = new Set();

        // First pass: Find best matches for each block in blocks2
        for (let j = 0; j < blocks2.length; j++) {
            let bestMatch = null;
            let bestMatchScore = 0;
            let bestChangeScore = 0;
            let bestI = -1;

            for (let i = 0; i < blocks1.length; i++) {
                if (used1.has(i)) continue;

                const scores = this._blockSimilarity(blocks1[i], blocks2[j], true);

                if (scores.matchScore > bestMatchScore && scores.matchScore >= this.options.structuralMatchThreshold) {
                    bestMatchScore = scores.matchScore;
                    bestChangeScore = scores.changeScore;
                    bestMatch = blocks1[i];
                    bestI = i;
                }
            }

            if (bestMatch) {
                // Found a match
                used1.add(bestI);
                used2.add(j);

                // Use changeScore to determine if content actually changed
                // This prevents containment from marking expanded content as "unchanged"
                matches.push({
                    type: bestChangeScore >= 0.99 ? 'unchanged' : 'modified',
                    similarity: bestMatchScore,
                    changeScore: bestChangeScore,
                    oldIndex: bestI,
                    newIndex: j,
                    oldBlock: bestMatch,
                    newBlock: blocks2[j],
                    isMoved: Math.abs(bestI - j) > 1 && this.options.detectMoves
                });
            }
        }

        // Second pass: Check for merged/split paragraphs
        // Look for unmatched v1 blocks that are contained in already-matched v2 blocks
        const mergedBlocks = new Map(); // v2 index -> array of additional v1 blocks

        for (let i = 0; i < blocks1.length; i++) {
            if (used1.has(i)) continue;

            // Check if this unmatched v1 block is contained in any matched v2 block
            let bestMergeTarget = -1;
            let bestMergeSimilarity = 0;

            for (const match of matches) {
                if (match.type === 'modified' || match.type === 'unchanged') {
                    const containment = this._calculateContainment(blocks1[i].content, match.newBlock.content);
                    if (containment >= 0.6 && containment > bestMergeSimilarity) {
                        bestMergeSimilarity = containment;
                        bestMergeTarget = match.newIndex;
                    }
                }
            }

            if (bestMergeTarget >= 0) {
                // This block was merged into an already-matched block
                used1.add(i);
                if (!mergedBlocks.has(bestMergeTarget)) {
                    mergedBlocks.set(bestMergeTarget, []);
                }
                mergedBlocks.get(bestMergeTarget).push({
                    index: i,
                    block: blocks1[i],
                    similarity: bestMergeSimilarity
                });
            }
        }

        // Add merged block info to matches
        for (const match of matches) {
            if (mergedBlocks.has(match.newIndex)) {
                match.mergedFrom = mergedBlocks.get(match.newIndex);
            }
        }

        // Third pass: Mark remaining unmatched blocks as added or removed
        for (let i = 0; i < blocks1.length; i++) {
            if (!used1.has(i)) {
                matches.push({
                    type: 'removed',
                    similarity: 0,
                    oldIndex: i,
                    newIndex: null,
                    oldBlock: blocks1[i],
                    newBlock: null,
                    isMoved: false
                });
            }
        }

        for (let j = 0; j < blocks2.length; j++) {
            if (!used2.has(j)) {
                matches.push({
                    type: 'added',
                    similarity: 0,
                    oldIndex: null,
                    newIndex: j,
                    oldBlock: null,
                    newBlock: blocks2[j],
                    isMoved: false
                });
            }
        }

        // Sort by position in the new document
        matches.sort((a, b) => {
            const aPos = a.newIndex !== null ? a.newIndex : a.oldIndex + 1000;
            const bPos = b.newIndex !== null ? b.newIndex : b.oldIndex + 1000;
            return aPos - bPos;
        });

        return matches;
    }

    /**
     * Calculate similarity between two structural blocks
     * Returns an object with both matchScore (for finding matches) and changeScore (for detecting modifications)
     */
    _blockSimilarity(block1, block2, returnDetails = false) {
        // Must be same type to match (or both be paragraph-like)
        const isParagraphLike1 = block1.type === 'paragraph' || block1.type === 'blockquote';
        const isParagraphLike2 = block2.type === 'paragraph' || block2.type === 'blockquote';

        if (block1.type !== block2.type) {
            // Allow matching between paragraph-like blocks
            if (!isParagraphLike1 || !isParagraphLike2) {
                return returnDetails ? { matchScore: 0, changeScore: 0 } : 0;
            }
        }

        // For headers, require high similarity
        if (block1.type === 'header') {
            const sim = this._textSimilarity(block1.content, block2.content);
            return returnDetails ? { matchScore: sim, changeScore: sim } : sim;
        }

        // For other blocks, calculate both forward similarity and containment
        const forward = this._textSimilarity(block1.content, block2.content);
        const containment = this._calculateContainment(block1.content, block2.content);

        if (returnDetails) {
            return {
                // matchScore: use containment to help find merged/split paragraphs
                matchScore: Math.max(forward, containment),
                // changeScore: use only forward similarity to detect actual changes
                changeScore: forward
            };
        }

        // Default: return matchScore for backward compatibility
        return Math.max(forward, containment);
    }

    /**
     * Calculate how much of the shorter text is contained in the longer text
     * Helps detect merged/split paragraphs
     */
    _calculateContainment(text1, text2) {
        const norm1 = text1.trim().toLowerCase();
        const norm2 = text2.trim().toLowerCase();

        if (!norm1 || !norm2) return 0;

        // Get the shorter and longer texts
        const shorter = norm1.length < norm2.length ? norm1 : norm2;
        const longer = norm1.length < norm2.length ? norm2 : norm1;

        // Count words in common
        const words1 = shorter.split(/\s+/);
        const words2Set = new Set(longer.split(/\s+/));

        let commonWords = 0;
        for (const word of words1) {
            if (words2Set.has(word)) {
                commonWords++;
            }
        }

        // Return ratio of common words to total words in shorter text
        return words1.length > 0 ? commonWords / words1.length : 0;
    }

    /**
     * Calculate text similarity using normalized Levenshtein distance
     */
    _textSimilarity(text1, text2) {
        if (text1 === text2) return 1.0;
        if (!text1 || !text2) return 0;

        // Normalize
        let norm1 = text1.trim();
        let norm2 = text2.trim();

        if (this.options.ignoreCase) {
            norm1 = norm1.toLowerCase();
            norm2 = norm2.toLowerCase();
        }

        const distance = this._levenshteinDistance(norm1, norm2);
        const maxLen = Math.max(norm1.length, norm2.length);

        return maxLen === 0 ? 1.0 : (maxLen - distance) / maxLen;
    }

    /**
     * Levenshtein distance algorithm
     */
    _levenshteinDistance(str1, str2) {
        const m = str1.length;
        const n = str2.length;
        const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

        for (let i = 0; i <= m; i++) dp[i][0] = i;
        for (let j = 0; j <= n; j++) dp[0][j] = j;

        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (str1[i - 1] === str2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = Math.min(
                        dp[i - 1][j] + 1,      // deletion
                        dp[i][j - 1] + 1,      // insertion
                        dp[i - 1][j - 1] + 1   // substitution
                    );
                }
            }
        }

        return dp[m][n];
    }

    /**
     * Level 2 & 3: Add detailed word and character comparisons for modified blocks
     */
    _addDetailedComparisons(matches, blocks1, blocks2) {
        return matches.map(match => {
            if (match.type === 'modified') {
                // Level 2: Word-level diff
                const wordDiff = this._computeWordDiff(match.oldBlock.content, match.newBlock.content);

                return {
                    ...match,
                    wordDiff: wordDiff
                };
            }

            return match;
        });
    }

    /**
     * Level 2: Compute word-level diff between two text blocks
     */
    _computeWordDiff(text1, text2) {
        // Split into words while preserving whitespace
        const words1 = this._splitIntoWords(text1);
        const words2 = this._splitIntoWords(text2);

        // Find LCS of words
        const lcs = this._computeLCS(words1, words2);

        const result = [];
        let i = 0, j = 0;

        for (const match of lcs) {
            // Add removed words
            while (i < match.i) {
                result.push({
                    type: 'removed',
                    word: words1[i],
                    charDiff: null
                });
                i++;
            }

            // Add added words
            while (j < match.j) {
                result.push({
                    type: 'added',
                    word: words2[j],
                    charDiff: null
                });
                j++;
            }

            // Check if "matched" words are actually identical
            if (words1[i].value === words2[j].value) {
                result.push({
                    type: 'unchanged',
                    word: words1[i],
                    charDiff: null
                });
            } else {
                // Words are similar but not identical - Level 3: character diff
                const charDiff = this._computeCharDiff(words1[i].value, words2[j].value);
                result.push({
                    type: 'modified',
                    oldWord: words1[i],
                    newWord: words2[j],
                    charDiff: charDiff
                });
            }

            i++;
            j++;
        }

        // Add remaining words
        while (i < words1.length) {
            result.push({
                type: 'removed',
                word: words1[i],
                charDiff: null
            });
            i++;
        }

        while (j < words2.length) {
            result.push({
                type: 'added',
                word: words2[j],
                charDiff: null
            });
            j++;
        }

        return result;
    }

    /**
     * Split text into words while preserving whitespace info
     * Separates punctuation from words for better matching
     */
    _splitIntoWords(text) {
        const words = [];
        // Split by whitespace AND punctuation, but keep both
        const tokens = text.split(/(\s+|[.,;:!?'"()\[\]{}])/);

        for (const token of tokens) {
            if (token.length > 0) {
                const isPunctuation = /^[.,;:!?'"()\[\]{}]$/.test(token);
                words.push({
                    value: token,
                    isWhitespace: /^\s+$/.test(token),
                    isPunctuation: isPunctuation
                });
            }
        }

        return words;
    }

    /**
     * Compute LCS (Longest Common Subsequence) of two arrays
     * Uses similarity threshold for matching words
     */
    _computeLCS(arr1, arr2) {
        const m = arr1.length;
        const n = arr2.length;
        const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (this._itemsMatch(arr1[i - 1], arr2[j - 1])) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }

        // Backtrack to get actual LCS
        const lcs = [];
        let i = m, j = n;

        while (i > 0 && j > 0) {
            if (this._itemsMatch(arr1[i - 1], arr2[j - 1])) {
                lcs.unshift({ i: i - 1, j: j - 1 });
                i--;
                j--;
            } else if (dp[i - 1][j] > dp[i][j - 1]) {
                i--;
            } else {
                j--;
            }
        }

        return lcs;
    }

    /**
     * Check if two items (words) match
     * Prioritizes exact matches, then case-insensitive, then similarity
     */
    _itemsMatch(item1, item2) {
        if (!item1 || !item2) return false;

        const val1 = item1.value || item1;
        const val2 = item2.value || item2;

        // Exact match - highest priority
        if (val1 === val2) return true;

        // For whitespace and punctuation, must be exact
        const isSpecial1 = /^\s+$/.test(val1) || /^[.,;:!?'"()\[\]{}]$/.test(val1);
        const isSpecial2 = /^\s+$/.test(val2) || /^[.,;:!?'"()\[\]{}]$/.test(val2);

        if (isSpecial1 || isSpecial2) {
            return val1 === val2;
        }

        // Case-insensitive match - second priority
        if (val1.toLowerCase() === val2.toLowerCase()) {
            return true;
        }

        // For words, use similarity threshold - lowest priority
        const similarity = this._textSimilarity(val1, val2);
        return similarity >= this.options.wordMatchThreshold;
    }

    /**
     * Level 3: Compute character-level diff for modified words
     */
    _computeCharDiff(str1, str2) {
        const chars1 = str1.split('');
        const chars2 = str2.split('');
        const lcs = this._computeLCS(chars1, chars2);

        const result = [];
        let i = 0, j = 0;

        for (const match of lcs) {
            // Add removed characters
            while (i < match.i) {
                result.push({ type: 'removed', char: chars1[i] });
                i++;
            }

            // Add added characters
            while (j < match.j) {
                result.push({ type: 'added', char: chars2[j] });
                j++;
            }

            // Add unchanged character
            result.push({ type: 'unchanged', char: chars1[i] });
            i++;
            j++;
        }

        // Add remaining characters
        while (i < chars1.length) {
            result.push({ type: 'removed', char: chars1[i] });
            i++;
        }

        while (j < chars2.length) {
            result.push({ type: 'added', char: chars2[j] });
            j++;
        }

        return result;
    }

    /**
     * Calculate statistics from diff result
     */
    _calculateStats(diff) {
        const stats = {
            blocksAdded: 0,
            blocksRemoved: 0,
            blocksModified: 0,
            blocksMoved: 0,
            blocksUnchanged: 0,
            wordsAdded: 0,
            wordsRemoved: 0,
            wordsModified: 0,
            wordsUnchanged: 0
        };

        for (const item of diff) {
            switch (item.type) {
                case 'added':
                    stats.blocksAdded++;
                    break;
                case 'removed':
                    stats.blocksRemoved++;
                    break;
                case 'modified':
                    stats.blocksModified++;
                    if (item.isMoved) stats.blocksMoved++;

                    // Count word-level changes (exclude whitespace and punctuation)
                    if (item.wordDiff) {
                        for (const word of item.wordDiff) {
                            const isContent = word.word ?
                                (!word.word.isWhitespace && !word.word.isPunctuation) :
                                (!word.oldWord.isWhitespace && !word.oldWord.isPunctuation);

                            if (!isContent) continue;

                            switch (word.type) {
                                case 'added':
                                    stats.wordsAdded++;
                                    break;
                                case 'removed':
                                    stats.wordsRemoved++;
                                    break;
                                case 'modified':
                                    stats.wordsModified++;
                                    break;
                                case 'unchanged':
                                    stats.wordsUnchanged++;
                                    break;
                            }
                        }
                    }
                    break;
                case 'unchanged':
                    stats.blocksUnchanged++;
                    break;
            }
        }

        return stats;
    }

    /**
     * Render diff to HTML
     */
    renderToHTML(diffResult) {
        let leftHTML = '';
        let rightHTML = '';

        for (const item of diffResult.diff) {
            switch (item.type) {
                case 'unchanged':
                    leftHTML += this._renderBlock('unchanged', item.oldBlock, null, 'left', item.mergedFrom);
                    rightHTML += this._renderBlock('unchanged', item.newBlock, null, 'right');
                    break;

                case 'removed':
                    leftHTML += this._renderBlock('removed', item.oldBlock, null, 'left');
                    rightHTML += this._renderBlock('empty', null, null, 'right');
                    break;

                case 'added':
                    leftHTML += this._renderBlock('empty', null, null, 'left');
                    rightHTML += this._renderBlock('added', item.newBlock, null, 'right');
                    break;

                case 'modified':
                    leftHTML += this._renderBlock('modified', item.oldBlock, item.wordDiff, 'left', item.mergedFrom);
                    rightHTML += this._renderBlock('modified', item.newBlock, item.wordDiff, 'right');
                    break;
            }
        }

        return {
            left: leftHTML,
            right: rightHTML,
            stats: diffResult.stats
        };
    }

    /**
     * Render a single block
     */
    _renderBlock(changeType, block, wordDiff, side, mergedBlocks) {
        if (changeType === 'empty') {
            return '<div class="diff-block diff-empty"><div class="block-content">&nbsp;</div></div>\n';
        }

        let content = '';

        if (changeType === 'modified' && wordDiff) {
            // Render with word-level highlighting
            content = this._renderWordDiff(wordDiff, side);
        } else if (block) {
            // Render plain content
            content = this._escapeHtml(block.content);
        }

        // Add merged blocks indicator on left side
        let mergedIndicator = '';
        if (side === 'left' && mergedBlocks && mergedBlocks.length > 0) {
            mergedIndicator = '<div class="merged-indicator">⤴ Merged with content below</div>';
            // Append merged block content
            for (const merged of mergedBlocks) {
                content += '\n\n<div class="merged-content-separator">⤴ Also includes:</div>\n';
                content += this._escapeHtml(merged.block.content);
            }
        }

        const blockClass = `diff-block diff-${changeType} block-${block ? block.type : 'unknown'}`;
        return `<div class="${blockClass}">${mergedIndicator}<div class="block-content">${content}</div></div>\n`;
    }

    /**
     * Render word diff with character-level details
     * Groups consecutive changes together for cleaner visual
     */
    _renderWordDiff(wordDiff, side) {
        let html = '';
        let i = 0;

        while (i < wordDiff.length) {
            const item = wordDiff[i];

            if (item.type === 'unchanged') {
                html += this._escapeHtml(item.word.value);
                i++;
            } else if (item.type === 'removed' && side === 'left') {
                // Group consecutive removed words/punctuation
                let buffer = '';
                let isPunctGroup = false;
                let isContentGroup = false;

                while (i < wordDiff.length &&
                       wordDiff[i].type === 'removed' &&
                       !wordDiff[i].word.isWhitespace) {

                    if (wordDiff[i].word.isPunctuation) {
                        isPunctGroup = true;
                    } else {
                        isContentGroup = true;
                    }
                    buffer += this._escapeHtml(wordDiff[i].word.value);
                    i++;
                }

                if (buffer) {
                    // Use word-removed for content, punct-removed for pure punctuation
                    const className = isContentGroup ? 'word-removed' : 'punct-removed';
                    html += `<span class="${className}">${buffer}</span>`;
                }

                // Handle whitespace separately (not grouped)
                if (i < wordDiff.length && wordDiff[i].type === 'removed' && wordDiff[i].word.isWhitespace) {
                    html += this._escapeHtml(wordDiff[i].word.value);
                    i++;
                }
            } else if (item.type === 'added' && side === 'right') {
                // Group consecutive added words/punctuation
                let buffer = '';
                let isPunctGroup = false;
                let isContentGroup = false;

                while (i < wordDiff.length &&
                       wordDiff[i].type === 'added' &&
                       !wordDiff[i].word.isWhitespace) {

                    if (wordDiff[i].word.isPunctuation) {
                        isPunctGroup = true;
                    } else {
                        isContentGroup = true;
                    }
                    buffer += this._escapeHtml(wordDiff[i].word.value);
                    i++;
                }

                if (buffer) {
                    // Use word-added for content, punct-added for pure punctuation
                    const className = isContentGroup ? 'word-added' : 'punct-added';
                    html += `<span class="${className}">${buffer}</span>`;
                }

                // Handle whitespace separately (not grouped)
                if (i < wordDiff.length && wordDiff[i].type === 'added' && wordDiff[i].word.isWhitespace) {
                    html += this._escapeHtml(wordDiff[i].word.value);
                    i++;
                }
            } else if (item.type === 'modified') {
                // Render with character-level diff (not grouped - each word separate)
                if (side === 'left') {
                    html += this._renderCharDiff(item.charDiff, 'left', item.oldWord.value);
                } else {
                    html += this._renderCharDiff(item.charDiff, 'right', item.newWord.value);
                }
                i++;
            } else if (item.type === 'removed' && side === 'right') {
                // Don't show removed items on right side
                i++;
            } else if (item.type === 'added' && side === 'left') {
                // Don't show added items on left side
                i++;
            } else {
                i++;
            }
        }

        return html;
    }

    /**
     * Render character-level diff
     */
    _renderCharDiff(charDiff, side, fallbackText) {
        if (!charDiff) {
            return this._escapeHtml(fallbackText);
        }

        let html = '';

        for (const item of charDiff) {
            if (item.type === 'unchanged') {
                html += this._escapeHtml(item.char);
            } else if (item.type === 'removed' && side === 'left') {
                html += `<span class="char-removed">${this._escapeHtml(item.char)}</span>`;
            } else if (item.type === 'added' && side === 'right') {
                html += `<span class="char-added">${this._escapeHtml(item.char)}</span>`;
            } else if (item.type === 'removed' && side === 'right') {
                // Don't show removed chars on right side
                continue;
            } else if (item.type === 'added' && side === 'left') {
                // Don't show added chars on left side
                continue;
            }
        }

        return html;
    }

    /**
     * Escape HTML entities
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
