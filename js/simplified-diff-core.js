// simplified-diff-core.js
// Consolidated core diff functionality

class DiffEngine {
    constructor() {
        // Pre-compile regex patterns for performance
        this.patterns = {
            header: /^(#{1,6})\s+(.+)$/,
            list: /^\s*[\-\*\+]|\d+[.)]\s/,
            code: /```|`[^`]+`/,
            quote: /^>\s/,
            link: /\[([^\]]+)\]\(([^)]+)\)/,
            image: /!\[([^\]]*)\]\(([^)]+)\)/,
            bold: /\*\*([^*]+)\*\*/,
            italic: /\*([^*]+)\*/,
            metric: /\d+%|\$[\d,]+|CTR|CPC|ROAS|CPM|CPA/i
        };
    }

    // Single-pass content analysis
    analyzeContent(text) {
        const lines = text.split('\n');
        const analysis = {
            lines: lines,
            structure: {
                headers: [],
                lists: [],
                codeBlocks: [],
                quotes: []
            },
            normalized: []
        };

        lines.forEach((line, index) => {
            const trimmed = line.trim();
            const lineData = {
                raw: line,
                trimmed: trimmed,
                index: index,
                type: this.getLineType(trimmed),
                normalized: this.normalizeForComparison(trimmed)
            };

            // Collect structural elements
            if (lineData.type === 'header') {
                const match = trimmed.match(this.patterns.header);
                analysis.structure.headers.push({
                    level: match[1].length,
                    text: match[2],
                    index: index
                });
            } else if (lineData.type === 'list') {
                analysis.structure.lists.push({ text: trimmed, index: index });
            } else if (lineData.type === 'code') {
                analysis.structure.codeBlocks.push({ text: trimmed, index: index });
            } else if (lineData.type === 'quote') {
                analysis.structure.quotes.push({ text: trimmed, index: index });
            }

            analysis.normalized.push(lineData);
        });

        return analysis;
    }

    // Efficient line type detection with single regex pass
    getLineType(line) {
        if (this.patterns.header.test(line)) return 'header';
        if (this.patterns.list.test(line)) return 'list';
        if (this.patterns.code.test(line)) return 'code';
        if (this.patterns.quote.test(line)) return 'quote';
        if (this.patterns.image.test(line)) return 'image';
        if (!line) return 'empty';
        return 'text';
    }

    // Optimized text normalization
    normalizeForComparison(text) {
        return text
            .replace(this.patterns.header, '$2')
            .replace(this.patterns.list, '')
            .replace(this.patterns.bold, '$1')
            .replace(this.patterns.italic, '$1')
            .replace(this.patterns.code, '$1')
            .replace(this.patterns.link, '$1')
            .replace(this.patterns.image, '$1')
            .replace(/\s+/g, ' ')
            .trim();
    }

    // Fast similarity calculation using pre-normalized text
    calculateSimilarity(norm1, norm2, type1, type2) {
        // Quick structural check
        if (type1 !== type2 && type1 !== 'text' && type2 !== 'text') return 0;
        
        if (norm1 === norm2) return 1;
        if (!norm1 || !norm2) return 0;

        // Use Jaccard similarity for performance
        const set1 = new Set(norm1.split(/\s+/));
        const set2 = new Set(norm2.split(/\s+/));
        const intersection = new Set([...set1].filter(x => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        
        return intersection.size / union.size;
    }

    // Simplified line-level diff
    computeLineDiff(analysis1, analysis2) {
        const diff = [];
        let i = 0, j = 0;
        const norm1 = analysis1.normalized;
        const norm2 = analysis2.normalized;

        while (i < norm1.length || j < norm2.length) {
            if (i >= norm1.length) {
                diff.push({ type: 'added', line2: norm2[j].raw });
                j++;
            } else if (j >= norm2.length) {
                diff.push({ type: 'removed', line1: norm1[i].raw });
                i++;
            } else {
                const similarity = this.calculateSimilarity(
                    norm1[i].normalized,
                    norm2[j].normalized,
                    norm1[i].type,
                    norm2[j].type
                );

                if (similarity > 0.8) {
                    diff.push({
                        type: 'unchanged',
                        line1: norm1[i].raw,
                        line2: norm2[j].raw
                    });
                    i++; j++;
                } else if (similarity > 0.3) {
                    // Compute word diff only for similar lines
                    const wordDiff = this.computeWordDiff(norm1[i].raw, norm2[j].raw);
                    diff.push({
                        type: 'modified',
                        line1: norm1[i].raw,
                        line2: norm2[j].raw,
                        leftDiff: wordDiff.left,
                        rightDiff: wordDiff.right
                    });
                    i++; j++;
                } else {
                    // Check for insertions/deletions by looking ahead
                    const insertionSim = j + 1 < norm2.length ? 
                        this.calculateSimilarity(norm1[i].normalized, norm2[j + 1].normalized, norm1[i].type, norm2[j + 1].type) : 0;
                    const deletionSim = i + 1 < norm1.length ? 
                        this.calculateSimilarity(norm1[i + 1].normalized, norm2[j].normalized, norm1[i + 1].type, norm2[j].type) : 0;

                    if (insertionSim > 0.7) {
                        diff.push({ type: 'added', line2: norm2[j].raw });
                        j++;
                    } else if (deletionSim > 0.7) {
                        diff.push({ type: 'removed', line1: norm1[i].raw });
                        i++;
                    } else {
                        diff.push({ type: 'removed', line1: norm1[i].raw });
                        diff.push({ type: 'added', line2: norm2[j].raw });
                        i++; j++;
                    }
                }
            }
        }

        return diff;
    }

    // Optimized word diff using dynamic programming
    computeWordDiff(line1, line2) {
        const words1 = line1.split(/(\s+)/);
        const words2 = line2.split(/(\s+)/);
        
        if (words1.length <= 6 && words2.length <= 6) {
            // Use character diff for short lines
            return this.computeCharDiff(line1, line2);
        }

        const dp = Array(words1.length + 1).fill(null).map(() => Array(words2.length + 1).fill(0));
        
        // Initialize
        for (let i = 0; i <= words1.length; i++) dp[i][0] = i;
        for (let j = 0; j <= words2.length; j++) dp[0][j] = j;
        
        // Fill DP table
        for (let i = 1; i <= words1.length; i++) {
            for (let j = 1; j <= words2.length; j++) {
                if (words1[i-1] === words2[j-1]) {
                    dp[i][j] = dp[i-1][j-1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
                }
            }
        }

        // Backtrack to build result
        let leftResult = '';
        let rightResult = '';
        let i = words1.length, j = words2.length;

        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && words1[i-1] === words2[j-1]) {
                leftResult = words1[i-1] + leftResult;
                rightResult = words2[j-1] + rightResult;
                i--; j--;
            } else if (j > 0 && (i === 0 || dp[i][j-1] <= dp[i-1][j])) {
                rightResult = `<span class="word-added">${words2[j-1]}</span>` + rightResult;
                j--;
            } else if (i > 0) {
                leftResult = `<span class="word-removed">${words1[i-1]}</span>` + leftResult;
                i--;
            }
        }

        return { left: leftResult, right: rightResult };
    }

    // Character-level diff implementation
    computeCharDiff(line1, line2) {
        // Simplified character diff for short strings
        if (line1 === line2) return { left: line1, right: line2 };
        
        const len1 = line1.length;
        const len2 = line2.length;
        const maxLen = Math.max(len1, len2);
        
        // For very short strings, return as completely different
        if (maxLen < 10) {
            return {
                left: len1 > 0 ? `<span class="char-removed">${line1}</span>` : '',
                right: len2 > 0 ? `<span class="char-added">${line2}</span>` : ''
            };
        }

        // Use standard DP algorithm for longer strings
        const dp = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));
        
        for (let i = 0; i <= len1; i++) dp[i][0] = i;
        for (let j = 0; j <= len2; j++) dp[0][j] = j;
        
        for (let i = 1; i <= len1; i++) {
            for (let j = 1; j <= len2; j++) {
                if (line1[i-1] === line2[j-1]) {
                    dp[i][j] = dp[i-1][j-1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
                }
            }
        }

        // Build result
        let leftParts = [];
        let rightParts = [];
        let i = len1, j = len2;

        while (i > 0 || j > 0) {
            if (i > 0 && j > 0 && line1[i-1] === line2[j-1]) {
                leftParts.unshift({ type: 'unchanged', char: line1[i-1] });
                rightParts.unshift({ type: 'unchanged', char: line2[j-1] });
                i--; j--;
            } else if (j > 0 && (i === 0 || dp[i][j-1] <= dp[i-1][j])) {
                rightParts.unshift({ type: 'added', char: line2[j-1] });
                j--;
            } else if (i > 0) {
                leftParts.unshift({ type: 'removed', char: line1[i-1] });
                i--;
            }
        }

        const combineParts = (parts) => {
            let result = '';
            let currentBlock = null;

            for (const part of parts) {
                if (currentBlock && currentBlock.type === part.type) {
                    currentBlock.text += part.char;
                } else {
                    if (currentBlock) {
                        result += currentBlock.type === 'unchanged' ? 
                            currentBlock.text : 
                            `<span class="char-${currentBlock.type}">${currentBlock.text}</span>`;
                    }
                    currentBlock = { type: part.type, text: part.char };
                }
            }

            if (currentBlock) {
                result += currentBlock.type === 'unchanged' ? 
                    currentBlock.text : 
                    `<span class="char-${currentBlock.type}">${currentBlock.text}</span>`;
            }

            return result;
        };

        return { left: combineParts(leftParts), right: combineParts(rightParts) };
    }

    // Compare structural elements efficiently
    compareStructure(struct1, struct2) {
        const changes = {
            headers: this.compareElements(struct1.headers, struct2.headers),
            lists: this.compareElements(struct1.lists, struct2.lists),
            codeBlocks: this.compareElements(struct1.codeBlocks, struct2.codeBlocks),
            quotes: this.compareElements(struct1.quotes, struct2.quotes)
        };

        return {
            ...changes,
            overall: {
                headerChanges: changes.headers.filter(h => h.type !== 'unchanged').length,
                listChanges: changes.lists.filter(l => l.type !== 'unchanged').length,
                codeChanges: changes.codeBlocks.filter(c => c.type !== 'unchanged').length
            }
        };
    }

    compareElements(elements1, elements2) {
        const result = [];
        const used2 = new Set();

        // Find exact matches first
        elements1.forEach((elem1, i) => {
            const match = elements2.find((elem2, j) => 
                !used2.has(j) && 
                JSON.stringify(elem1) === JSON.stringify(elem2)
            );

            if (match) {
                const matchIndex = elements2.indexOf(match);
                used2.add(matchIndex);
                result.push({ type: 'unchanged', element: elem1 });
            } else {
                result.push({ type: 'removed', element: elem1 });
            }
        });

        // Find additions
        elements2.forEach((elem2, j) => {
            if (!used2.has(j)) {
                result.push({ type: 'added', element: elem2 });
            }
        });

        return result;
    }

    // Main diff function - simplified pipeline
    diff(text1, text2) {
        // Single-pass analysis of both texts
        const analysis1 = this.analyzeContent(text1);
        const analysis2 = this.analyzeContent(text2);

        // Compute line-level diff with word-level details
        const diff = this.computeLineDiff(analysis1, analysis2);

        // Compare structural elements
        const structuralChanges = this.compareStructure(analysis1.structure, analysis2.structure);

        return { diff, structuralChanges };
    }
}

// Export the simplified engine
window.SimplifiedDiffEngine = DiffEngine;