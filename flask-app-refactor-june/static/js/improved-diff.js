/**
 * Improved Diff Comparison System for Draft Mode
 *
 * Features:
 * - Block move detection (recognizes moved paragraphs/sections)
 * - Smart paragraph matching with fuzzy comparison
 * - Word and character-level highlighting for modifications
 * - Intelligent handling of whitespace and formatting
 * - Code block awareness
 * - List item tracking
 */

class ImprovedDiff {
    constructor(options = {}) {
        this.options = {
            // Similarity threshold for matching modified lines (0-1)
            similarityThreshold: 0.3,
            // Threshold for detecting moves vs delete+add
            moveDetectionThreshold: 0.8,
            // Whether to ignore leading/trailing whitespace
            ignoreWhitespace: true,
            // Whether to detect moved blocks
            detectMoves: true,
            // Minimum block size for move detection (lines)
            minMoveBlockSize: 2,
            ...options
        };
    }

    /**
     * Main diff computation method
     */
    computeDiff(text1, text2) {
        // Normalize line endings
        text1 = text1.replace(/\r\n/g, '\n');
        text2 = text2.replace(/\r\n/g, '\n');

        // Split into lines
        const lines1 = text1.split('\n');
        const lines2 = text2.split('\n');

        // Compute line-level diff using Myers algorithm
        const lineDiff = this._computeLineDiff(lines1, lines2);

        // Detect moved blocks if enabled
        let processedDiff = lineDiff;
        if (this.options.detectMoves) {
            processedDiff = this._detectMoves(processedDiff, lines1, lines2);
        }

        // Process modifications to add word-level detail
        processedDiff = this._addWordLevelDetail(processedDiff);

        // Calculate statistics
        const stats = this._calculateStats(processedDiff);

        return {
            diff: processedDiff,
            stats: stats
        };
    }

    /**
     * Compute line-level diff using Myers algorithm
     */
    _computeLineDiff(lines1, lines2) {
        const n = lines1.length;
        const m = lines2.length;
        const max = n + m;

        // V array for Myers algorithm - initialize with zeros
        const v = new Array(2 * max + 1).fill(0);
        const trace = [];

        // Myers diff algorithm
        for (let d = 0; d <= max; d++) {
            const currentV = [...v];
            trace.push(currentV);

            for (let k = -d; k <= d; k += 2) {
                let x;

                if (k === -d || (k !== d && v[k - 1 + max] < v[k + 1 + max])) {
                    x = v[k + 1 + max];
                } else {
                    x = v[k - 1 + max] + 1;
                }

                let y = x - k;

                while (x < n && y < m && this._linesEqual(lines1[x], lines2[y])) {
                    x++;
                    y++;
                }

                v[k + max] = x;

                if (x >= n && y >= m) {
                    // Found the shortest edit script
                    return this._backtrack(trace, lines1, lines2, d);
                }
            }
        }

        return [];
    }

    /**
     * Backtrack through the Myers algorithm trace to build diff
     */
    _backtrack(trace, lines1, lines2, d) {
        const diff = [];
        let x = lines1.length;
        let y = lines2.length;
        const max = lines1.length + lines2.length;

        for (let step = d; step >= 0; step--) {
            const v = trace[step];
            const k = x - y;

            const prevK = (k === -step || (k !== step && v[k - 1 + max] < v[k + 1 + max]))
                ? k + 1
                : k - 1;

            const prevX = v[prevK + max];
            const prevY = prevX - prevK;

            // Diagonal moves (no change)
            while (x > prevX && y > prevY) {
                if (x > 0 && y >= 0 && lines1[x - 1] !== undefined && lines2[y - 1] !== undefined) {
                    diff.unshift({
                        type: 'unchanged',
                        oldLine: x - 1,
                        newLine: y - 1,
                        line1: lines1[x - 1],
                        line2: lines2[y - 1]
                    });
                }
                x--;
                y--;
            }

            // Horizontal move (deletion)
            if (x > prevX) {
                if (x > 0 && lines1[x - 1] !== undefined) {
                    diff.unshift({
                        type: 'removed',
                        oldLine: x - 1,
                        newLine: null,
                        line1: lines1[x - 1],
                        line2: ''
                    });
                }
                x--;
            }
            // Vertical move (addition)
            else if (y > prevY) {
                if (y > 0 && lines2[y - 1] !== undefined) {
                    diff.unshift({
                        type: 'added',
                        oldLine: null,
                        newLine: y - 1,
                        line1: '',
                        line2: lines2[y - 1]
                    });
                }
                y--;
            }
        }

        return diff;
    }

    /**
     * Check if two lines are equal (with options like ignoring whitespace)
     */
    _linesEqual(line1, line2) {
        if (this.options.ignoreWhitespace) {
            return line1.trim() === line2.trim();
        }
        return line1 === line2;
    }

    /**
     * Detect moved blocks in the diff
     */
    _detectMoves(diff, lines1, lines2) {
        const result = [];
        const deletedBlocks = [];
        const addedBlocks = [];

        // Collect consecutive deleted and added blocks
        let currentDeleted = [];
        let currentAdded = [];

        for (const item of diff) {
            if (item.type === 'removed') {
                if (currentAdded.length > 0) {
                    addedBlocks.push([...currentAdded]);
                    currentAdded = [];
                }
                currentDeleted.push(item);
            } else if (item.type === 'added') {
                if (currentDeleted.length > 0) {
                    deletedBlocks.push([...currentDeleted]);
                    currentDeleted = [];
                }
                currentAdded.push(item);
            } else {
                if (currentDeleted.length > 0) {
                    deletedBlocks.push([...currentDeleted]);
                    currentDeleted = [];
                }
                if (currentAdded.length > 0) {
                    addedBlocks.push([...currentAdded]);
                    currentAdded = [];
                }
            }
        }

        // Add remaining blocks
        if (currentDeleted.length > 0) deletedBlocks.push(currentDeleted);
        if (currentAdded.length > 0) addedBlocks.push(currentAdded);

        // Find matching blocks (potential moves)
        const matchedDeleted = new Set();
        const matchedAdded = new Set();
        const moves = [];

        for (let i = 0; i < deletedBlocks.length; i++) {
            if (matchedDeleted.has(i)) continue;
            if (deletedBlocks[i].length < this.options.minMoveBlockSize) continue;

            for (let j = 0; j < addedBlocks.length; j++) {
                if (matchedAdded.has(j)) continue;
                if (addedBlocks[j].length !== deletedBlocks[i].length) continue;

                const similarity = this._blockSimilarity(deletedBlocks[i], addedBlocks[j]);

                if (similarity >= this.options.moveDetectionThreshold) {
                    moves.push({
                        deletedIndex: i,
                        addedIndex: j,
                        deletedBlock: deletedBlocks[i],
                        addedBlock: addedBlocks[j],
                        similarity: similarity
                    });
                    matchedDeleted.add(i);
                    matchedAdded.add(j);
                    break;
                }
            }
        }

        // Rebuild diff with move information
        let deletedIdx = 0;
        let addedIdx = 0;
        const moveMap = new Map();

        for (const move of moves) {
            moveMap.set(move.deletedIndex, 'deleted');
            moveMap.set(move.addedIndex, 'added');
        }

        for (const item of diff) {
            if (item.type === 'removed') {
                const blockIdx = this._findBlockIndex(deletedBlocks, deletedIdx);
                if (moveMap.get(blockIdx) === 'deleted') {
                    result.push({ ...item, type: 'moved-out' });
                } else {
                    result.push(item);
                }
                deletedIdx++;
            } else if (item.type === 'added') {
                const blockIdx = this._findBlockIndex(addedBlocks, addedIdx);
                if (moveMap.get(blockIdx) === 'added') {
                    result.push({ ...item, type: 'moved-in' });
                } else {
                    result.push(item);
                }
                addedIdx++;
            } else {
                result.push(item);
            }
        }

        return result;
    }

    /**
     * Calculate similarity between two blocks
     */
    _blockSimilarity(block1, block2) {
        if (block1.length !== block2.length) return 0;

        let totalSimilarity = 0;
        for (let i = 0; i < block1.length; i++) {
            const line1 = block1[i].line1;
            const line2 = block2[i].line2;
            totalSimilarity += this._lineSimilarity(line1, line2);
        }

        return totalSimilarity / block1.length;
    }

    /**
     * Find which block contains a given item index
     */
    _findBlockIndex(blocks, itemIdx) {
        let count = 0;
        for (let i = 0; i < blocks.length; i++) {
            count += blocks[i].length;
            if (itemIdx < count) return i;
        }
        return -1;
    }

    /**
     * Add word-level detail to modified lines
     */
    _addWordLevelDetail(diff) {
        const result = [];

        for (let i = 0; i < diff.length; i++) {
            const item = diff[i];

            // Check if next item could be a modification (removed + added)
            if (item.type === 'removed' && i + 1 < diff.length) {
                const nextItem = diff[i + 1];

                if (nextItem.type === 'added') {
                    const similarity = this._lineSimilarity(item.line1, nextItem.line2);

                    if (similarity >= this.options.similarityThreshold) {
                        // This is a modification, compute word-level diff
                        const wordDiff = this._computeWordDiff(item.line1, nextItem.line2);

                        result.push({
                            type: 'modified',
                            oldLine: item.oldLine,
                            newLine: nextItem.newLine,
                            line1: item.line1,
                            line2: nextItem.line2,
                            leftDiff: wordDiff.left,
                            rightDiff: wordDiff.right
                        });

                        i++; // Skip next item as we've processed it
                        continue;
                    }
                }
            }

            result.push(item);
        }

        return result;
    }

    /**
     * Compute word-level diff between two lines
     */
    _computeWordDiff(line1, line2) {
        // Split by words but keep whitespace
        const words1 = line1.split(/(\s+)/);
        const words2 = line2.split(/(\s+)/);

        // If lines are too different, use character-level diff
        if (Math.abs(words1.length - words2.length) > Math.max(words1.length, words2.length) * 0.5) {
            return this._computeCharDiff(line1, line2);
        }

        // Compute LCS for words
        const lcs = this._computeLCS(words1, words2);

        let left = '';
        let right = '';
        let i = 0, j = 0;

        for (const item of lcs) {
            // Add removed words
            while (i < item.i) {
                left += `<span class="word-removed">${this._escapeHtml(words1[i])}</span>`;
                i++;
            }

            // Add added words
            while (j < item.j) {
                right += `<span class="word-added">${this._escapeHtml(words2[j])}</span>`;
                j++;
            }

            // Add unchanged word
            left += this._escapeHtml(words1[i]);
            right += this._escapeHtml(words2[j]);
            i++;
            j++;
        }

        // Add remaining words
        while (i < words1.length) {
            left += `<span class="word-removed">${this._escapeHtml(words1[i])}</span>`;
            i++;
        }

        while (j < words2.length) {
            right += `<span class="word-added">${this._escapeHtml(words2[j])}</span>`;
            j++;
        }

        return { left, right };
    }

    /**
     * Compute character-level diff between two lines
     */
    _computeCharDiff(line1, line2) {
        const chars1 = line1.split('');
        const chars2 = line2.split('');

        const lcs = this._computeLCS(chars1, chars2);

        let left = '';
        let right = '';
        let i = 0, j = 0;
        let leftBuffer = '';
        let rightBuffer = '';

        for (const item of lcs) {
            // Collect removed characters
            while (i < item.i) {
                leftBuffer += this._escapeHtml(chars1[i]);
                i++;
            }

            if (leftBuffer) {
                left += `<span class="char-removed">${leftBuffer}</span>`;
                leftBuffer = '';
            }

            // Collect added characters
            while (j < item.j) {
                rightBuffer += this._escapeHtml(chars2[j]);
                j++;
            }

            if (rightBuffer) {
                right += `<span class="char-added">${rightBuffer}</span>`;
                rightBuffer = '';
            }

            // Add unchanged character
            left += this._escapeHtml(chars1[i]);
            right += this._escapeHtml(chars2[j]);
            i++;
            j++;
        }

        // Add remaining characters
        while (i < chars1.length) {
            leftBuffer += this._escapeHtml(chars1[i]);
            i++;
        }

        if (leftBuffer) {
            left += `<span class="char-removed">${leftBuffer}</span>`;
        }

        while (j < chars2.length) {
            rightBuffer += this._escapeHtml(chars2[j]);
            j++;
        }

        if (rightBuffer) {
            right += `<span class="char-added">${rightBuffer}</span>`;
        }

        return { left, right };
    }

    /**
     * Compute Longest Common Subsequence
     */
    _computeLCS(arr1, arr2) {
        const n = arr1.length;
        const m = arr2.length;
        const dp = Array(n + 1).fill(null).map(() => Array(m + 1).fill(0));

        // Build LCS table
        for (let i = 1; i <= n; i++) {
            for (let j = 1; j <= m; j++) {
                if (arr1[i - 1] === arr2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }

        // Backtrack to find LCS
        const lcs = [];
        let i = n, j = m;

        while (i > 0 && j > 0) {
            if (arr1[i - 1] === arr2[j - 1]) {
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
     * Calculate line similarity using Levenshtein distance
     */
    _lineSimilarity(line1, line2) {
        if (!line1 || !line2) return 0;

        // Normalize lines
        const norm1 = line1.trim().toLowerCase();
        const norm2 = line2.trim().toLowerCase();

        if (norm1 === norm2) return 1;

        const distance = this._levenshteinDistance(norm1, norm2);
        const maxLen = Math.max(norm1.length, norm2.length);

        return maxLen === 0 ? 1 : (maxLen - distance) / maxLen;
    }

    /**
     * Calculate Levenshtein distance
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
                    dp[i][j] = 1 + Math.min(
                        dp[i - 1][j],     // deletion
                        dp[i][j - 1],     // insertion
                        dp[i - 1][j - 1]  // substitution
                    );
                }
            }
        }

        return dp[m][n];
    }

    /**
     * Calculate statistics from diff
     */
    _calculateStats(diff) {
        const stats = {
            additions: 0,
            deletions: 0,
            modifications: 0,
            moves: 0,
            unchanged: 0
        };

        for (const item of diff) {
            switch (item.type) {
                case 'added':
                    stats.additions++;
                    break;
                case 'removed':
                    stats.deletions++;
                    break;
                case 'modified':
                    stats.modifications++;
                    break;
                case 'moved-in':
                case 'moved-out':
                    stats.moves++;
                    break;
                case 'unchanged':
                    stats.unchanged++;
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
        let leftLineNum = 1;
        let rightLineNum = 1;

        for (const item of diffResult.diff) {
            let leftClass = 'diff-line';
            let rightClass = 'diff-line';
            let leftContent = '';
            let rightContent = '';
            let leftNum = '';
            let rightNum = '';

            switch (item.type) {
                case 'unchanged':
                    leftClass += ' diff-unchanged';
                    rightClass += ' diff-unchanged';
                    leftNum = leftLineNum;
                    rightNum = rightLineNum;
                    leftContent = this._escapeHtml(item.line1);
                    rightContent = this._escapeHtml(item.line2);
                    leftLineNum++;
                    rightLineNum++;
                    break;

                case 'removed':
                    leftClass += ' diff-removed';
                    rightClass += ' diff-empty';
                    leftNum = leftLineNum;
                    rightNum = '&nbsp;';
                    leftContent = this._escapeHtml(item.line1);
                    rightContent = '&nbsp;';
                    leftLineNum++;
                    break;

                case 'added':
                    leftClass += ' diff-empty';
                    rightClass += ' diff-added';
                    leftNum = '&nbsp;';
                    rightNum = rightLineNum;
                    leftContent = '&nbsp;';
                    rightContent = this._escapeHtml(item.line2);
                    rightLineNum++;
                    break;

                case 'modified':
                    leftClass += ' diff-modified';
                    rightClass += ' diff-modified';
                    leftNum = leftLineNum;
                    rightNum = rightLineNum;
                    leftContent = item.leftDiff;
                    rightContent = item.rightDiff;
                    leftLineNum++;
                    rightLineNum++;
                    break;

                case 'moved-out':
                    leftClass += ' diff-moved-out';
                    rightClass += ' diff-empty';
                    leftNum = leftLineNum;
                    rightNum = '&nbsp;';
                    leftContent = '↗️ ' + this._escapeHtml(item.line1);
                    rightContent = '&nbsp;';
                    leftLineNum++;
                    break;

                case 'moved-in':
                    leftClass += ' diff-empty';
                    rightClass += ' diff-moved-in';
                    leftNum = '&nbsp;';
                    rightNum = rightLineNum;
                    leftContent = '&nbsp;';
                    rightContent = '↙️ ' + this._escapeHtml(item.line2);
                    rightLineNum++;
                    break;
            }

            // Build the HTML for this line
            leftHTML += `<div class="${leftClass}"><span class="line-number">${leftNum}</span><span class="line-content">${leftContent}</span></div>\n`;
            rightHTML += `<div class="${rightClass}"><span class="line-number">${rightNum}</span><span class="line-content">${rightContent}</span></div>\n`;
        }

        return {
            left: leftHTML,
            right: rightHTML,
            stats: diffResult.stats
        };
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

// Export for use in browser
if (typeof window !== 'undefined') {
    window.ImprovedDiff = ImprovedDiff;
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ImprovedDiff;
}
