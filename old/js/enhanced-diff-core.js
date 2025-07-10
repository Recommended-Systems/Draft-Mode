// enhanced-diff-core.js
// Balanced solution that addresses issues without excessive complexity

class EnhancedDiffEngine {
    constructor() {
        // Pre-compile regex patterns for performance
        this.patterns = {
            header: /^(#{1,6})\s+(.+)$/,
            listUnordered: /^\s*([\-\*\+])\s+(.+)$/,
            listOrdered: /^\s*(\d+)[.)]\s+(.+)$/,
            code: /```|`[^`]+`/,
            quote: /^>\s/,
            link: /\[([^\]]+)\]\(([^)]+)\)/,
            image: /!\[([^\]]*)\]\(([^)]+)\)/,
            boldStrong: /\*\*([^*]+)\*\*/,
            italic: /\*([^*]+)\*/,
            strikethrough: /~~([^~]+)~~/,
            codeInline: /`([^`]+)`/
        };
        
        // Threshold values for different comparison scenarios
        this.thresholds = {
            exactMatch: 1.0,
            highSimilarity: 0.8,
            moderateSimilarity: 0.3,
            minMoveSimilarity: 0.85
        };
    }

    // Enhanced content analysis with better structure preservation
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
            normalized: [],
            fingerprints: [] // For move detection
        };

        let inCodeBlock = false;
        let codeBlockStart = -1;

        lines.forEach((line, index) => {
            const trimmed = line.trim();
            
            // Handle code blocks
            if (trimmed.startsWith('```')) {
                if (!inCodeBlock) {
                    inCodeBlock = true;
                    codeBlockStart = index;
                } else {
                    inCodeBlock = false;
                    analysis.structure.codeBlocks.push({
                        start: codeBlockStart,
                        end: index,
                        type: 'multiline'
                    });
                }
                return;
            }

            const lineData = {
                raw: line,
                trimmed: trimmed,
                index: index,
                type: this.getLineType(trimmed),
                normalized: this.normalizeForComparison(trimmed),
                lightNormalized: this.lightNormalize(trimmed), // Preserve formatting differences
                inCodeBlock: inCodeBlock
            };

            // Create fingerprint for move detection
            lineData.fingerprint = this.createFingerprint(lineData);

            // Collect structural elements
            if (lineData.type === 'header') {
                const match = trimmed.match(this.patterns.header);
                analysis.structure.headers.push({
                    level: match[1].length,
                    text: match[2],
                    index: index
                });
            } else if (lineData.type === 'list') {
                const listInfo = this.parseListItem(trimmed);
                analysis.structure.lists.push({ 
                    ...listInfo,
                    index: index
                });
            } else if (lineData.type === 'quote') {
                analysis.structure.quotes.push({ text: trimmed, index: index });
            }

            analysis.normalized.push(lineData);
            analysis.fingerprints.push(lineData.fingerprint);
        });

        return analysis;
    }

    // Light normalization that preserves formatting differences
    lightNormalize(text) {
        // Only normalize spacing and basic punctuation
        return text
            .replace(/\s+/g, ' ')
            .trim()
            .toLowerCase();
    }

    // Create fingerprint for move detection
    createFingerprint(lineData) {
        // Create a unique signature based on content words
        const words = lineData.normalized.split(/\s+/).filter(w => w.length > 3);
        return {
            words: words,
            wordSet: new Set(words),
            signature: words.slice(0, 5).join('|'), // First 5 significant words
            length: lineData.normalized.length,
            type: lineData.type
        };
    }

    // Parse list items while preserving the list marker type
    parseListItem(line) {
        const unorderedMatch = line.match(this.patterns.listUnordered);
        if (unorderedMatch) {
            return {
                type: 'unordered',
                marker: unorderedMatch[1],
                text: unorderedMatch[2]
            };
        }
        
        const orderedMatch = line.match(this.patterns.listOrdered);
        if (orderedMatch) {
            return {
                type: 'ordered',
                number: parseInt(orderedMatch[1]),
                text: orderedMatch[2]
            };
        }
        
        return { type: 'unknown', text: line };
    }

    // Enhanced line type detection
    getLineType(line) {
        if (!line) return 'empty';
        if (this.patterns.header.test(line)) return 'header';
        if (this.patterns.listUnordered.test(line) || this.patterns.listOrdered.test(line)) return 'list';
        if (this.patterns.quote.test(line)) return 'quote';
        if (this.patterns.image.test(line)) return 'image';
        if (line.startsWith('```')) return 'codeblock';
        if (line.match(/^[-*_]{3,}$/)) return 'divider';
        return 'text';
    }

    // Enhanced normalization for comparison
    normalizeForComparison(text) {
        return text
            .replace(this.patterns.header, '$2')
            .replace(this.patterns.listUnordered, '$2')
            .replace(this.patterns.listOrdered, '$2')
            .replace(this.patterns.boldStrong, '$1')
            .replace(this.patterns.italic, '$1')
            .replace(this.patterns.codeInline, '$1')
            .replace(this.patterns.link, '$1')
            .replace(this.patterns.image, '$1')
            .replace(/\s+/g, ' ')
            .trim()
            .toLowerCase();
    }

    // Calculate similarity with different levels of strictness
    calculateSimilarity(line1, line2, strict = false) {
        const norm1 = strict ? line1.lightNormalized : line1.normalized;
        const norm2 = strict ? line2.lightNormalized : line2.normalized;
        
        // Quick structural check
        if (line1.type !== line2.type && line1.type !== 'text' && line2.type !== 'text') {
            return 0;
        }
        
        if (norm1 === norm2) return 1.0;
        if (!norm1 || !norm2) return 0;

        // Use Jaccard similarity for speed
        const words1 = norm1.split(/\s+/);
        const words2 = norm2.split(/\s+/);
        const set1 = new Set(words1);
        const set2 = new Set(words2);
        
        const intersection = new Set([...set1].filter(x => set2.has(x)));
        const union = new Set([...set1, ...set2]);
        
        return intersection.size / union.size;
    }

    // Detect moved content blocks
    detectMoves(analysis1, analysis2) {
        const moves = [];
        const used1 = new Set();
        const used2 = new Set();
        
        // Look for high-similarity fingerprints that appear in different positions
        analysis1.fingerprints.forEach((fp1, i) => {
            if (used1.has(i) || fp1.type === 'empty') return;
            
            analysis2.fingerprints.forEach((fp2, j) => {
                if (used2.has(j) || used1.has(i)) return;
                
                // Check if fingerprints match well
                if (fp1.signature === fp2.signature && 
                    Math.abs(i - j) > 3 && // Moved more than 3 lines
                    fp1.type === fp2.type) {
                    
                    // Verify with full line comparison
                    const similarity = this.calculateSimilarity(
                        analysis1.normalized[i], 
                        analysis2.normalized[j]
                    );
                    
                    if (similarity >= this.thresholds.minMoveSimilarity) {
                        moves.push({
                            from: i,
                            to: j,
                            similarity: similarity,
                            type: 'move',
                            line1: analysis1.lines[i],
                            line2: analysis2.lines[j]
                        });
                        used1.add(i);
                        used2.add(j);
                    }
                }
            });
        });
        
        return moves;
    }

    // Enhanced diff computation with move detection
    computeLineDiff(analysis1, analysis2) {
        const moves = this.detectMoves(analysis1, analysis2);
        const moveMap1 = new Map(moves.map(m => [m.from, m]));
        const moveMap2 = new Map(moves.map(m => [m.to, m]));
        
        const diff = [];
        let i = 0, j = 0;
        const norm1 = analysis1.normalized;
        const norm2 = analysis2.normalized;

        while (i < norm1.length || j < norm2.length) {
            // Check if current line is part of a move
            if (moveMap1.has(i)) {
                const move = moveMap1.get(i);
                diff.push({
                    type: 'moved',
                    line1: move.line1,
                    line2: move.line2,
                    from: move.from,
                    to: move.to
                });
                i++;
                continue;
            }
            
            if (moveMap2.has(j) && i > 0) {
                // This line was moved from elsewhere, skip it here
                j++;
                continue;
            }

            if (i >= norm1.length) {
                diff.push({ type: 'added', line2: norm2[j].raw });
                j++;
            } else if (j >= norm2.length) {
                diff.push({ type: 'removed', line1: norm1[i].raw });
                i++;
            } else {
                const exactSim = this.calculateSimilarity(norm1[i], norm2[j], false);
                const strictSim = this.calculateSimilarity(norm1[i], norm2[j], true);
                
                if (exactSim >= this.thresholds.exactMatch) {
                    diff.push({
                        type: 'unchanged',
                        line1: norm1[i].raw,
                        line2: norm2[j].raw
                    });
                    i++; j++;
                } else if (strictSim >= this.thresholds.highSimilarity) {
                    // High similarity with strict normalization suggests formatting change
                    const wordDiff = this.computeWordDiff(norm1[i].raw, norm2[j].raw);
                    diff.push({
                        type: 'modified',
                        line1: norm1[i].raw,
                        line2: norm2[j].raw,
                        leftDiff: wordDiff.left,
                        rightDiff: wordDiff.right,
                        changeType: 'formatting'
                    });
                    i++; j++;
                } else if (exactSim >= this.thresholds.moderateSimilarity) {
                    // Moderate similarity suggests content change
                    const wordDiff = this.computeWordDiff(norm1[i].raw, norm2[j].raw);
                    diff.push({
                        type: 'modified',
                        line1: norm1[i].raw,
                        line2: norm2[j].raw,
                        leftDiff: wordDiff.left,
                        rightDiff: wordDiff.right,
                        changeType: 'content'
                    });
                    i++; j++;
                } else {
                    // Check for insertions/deletions by looking ahead
                    const insertionSim = j + 1 < norm2.length ? 
                        this.calculateSimilarity(norm1[i], norm2[j + 1]) : 0;
                    const deletionSim = i + 1 < norm1.length ? 
                        this.calculateSimilarity(norm1[i + 1], norm2[j]) : 0;

                    if (insertionSim > this.thresholds.highSimilarity) {
                        diff.push({ type: 'added', line2: norm2[j].raw });
                        j++;
                    } else if (deletionSim > this.thresholds.highSimilarity) {
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

    // Optimized word diff
    computeWordDiff(line1, line2) {
        const words1 = line1.split(/(\s+)/);
        const words2 = line2.split(/(\s+)/);
        
        // Use character diff for very short lines
        if ((words1.length <= 6 && words2.length <= 6) || 
            (line1.length < 30 && line2.length < 30)) {
            return this.computeCharDiff(line1, line2);
        }

        const dp = Array(words1.length + 1).fill(null).map(() => Array(words2.length + 1).fill(0));
        
        // Initialize DP table
        for (let i = 0; i <= words1.length; i++) dp[i][0] = i;
        for (let j = 0; j <= words2.length; j++) dp[0][j] = j;
        
        // Fill DP table with word comparison
        for (let i = 1; i <= words1.length; i++) {
            for (let j = 1; j <= words2.length; j++) {
                if (words1[i-1] === words2[j-1]) {
                    dp[i][j] = dp[i-1][j-1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
                }
            }
        }

        // Backtrack
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

    // Character-level diff for fine-grained comparison
    computeCharDiff(line1, line2) {
        if (line1 === line2) return { left: line1, right: line2 };
        
        const len1 = line1.length;
        const len2 = line2.length;
        
        // Skip char diff for very long lines to avoid performance issues
        if (Math.max(len1, len2) > 500) {
            return {
                left: len1 > 0 ? `<span class="char-removed">${line1}</span>` : '',
                right: len2 > 0 ? `<span class="char-added">${line2}</span>` : ''
            };
        }

        const dp = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));
        
        // Initialize DP table
        for (let i = 0; i <= len1; i++) dp[i][0] = i;
        for (let j = 0; j <= len2; j++) dp[0][j] = j;
        
        // Fill DP table
        for (let i = 1; i <= len1; i++) {
            for (let j = 1; j <= len2; j++) {
                if (line1[i-1] === line2[j-1]) {
                    dp[i][j] = dp[i-1][j-1];
                } else {
                    dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
                }
            }
        }

        // Backtrack to build result
        const leftParts = [];
        const rightParts = [];
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

        // Combine parts
        const combineParts = (parts) => {
            let result = '';
            let currentBlock = null;

            for (const part of parts) {
                if (currentBlock && currentBlock.type === part.type) {
                    currentBlock.text += part.char;
                } else {
                    if (currentBlock) {
                        if (currentBlock.type === 'unchanged') {
                            result += currentBlock.text;
                        } else {
                            const className = currentBlock.type === 'added' ? 'char-added' : 'char-removed';
                            result += `<span class="${className}">${currentBlock.text}</span>`;
                        }
                    }
                    currentBlock = { type: part.type, text: part.char };
                }
            }

            if (currentBlock) {
                if (currentBlock.type === 'unchanged') {
                    result += currentBlock.text;
                } else {
                    const className = currentBlock.type === 'added' ? 'char-added' : 'char-removed';
                    result += `<span class="${className}">${currentBlock.text}</span>`;
                }
            }

            return result;
        };

        return { left: combineParts(leftParts), right: combineParts(rightParts) };
    }

    // Compare structures with better handling
    compareStructure(struct1, struct2) {
        const changes = {
            headers: this.compareElements(struct1.headers, struct2.headers, 'header'),
            lists: this.compareElements(struct1.lists, struct2.lists, 'list'),
            codeBlocks: this.compareElements(struct1.codeBlocks, struct2.codeBlocks, 'code'),
            quotes: this.compareElements(struct1.quotes, struct2.quotes, 'quote')
        };

        return {
            ...changes,
            overall: {
                headerChanges: changes.headers.filter(h => h.type !== 'unchanged').length,
                listChanges: changes.lists.filter(l => l.type !== 'unchanged').length,
                codeChanges: changes.codeBlocks.filter(c => c.type !== 'unchanged').length,
                quoteChanges: changes.quotes.filter(q => q.type !== 'unchanged').length
            }
        };
    }

    // Compare structural elements
    compareElements(elements1, elements2, elementType) {
        const result = [];
        const used2 = new Set();

        // Find matches
        elements1.forEach((elem1, i) => {
            let bestMatch = null;
            let bestSimilarity = 0;

            elements2.forEach((elem2, j) => {
                if (used2.has(j)) return;

                let similarity = 0;
                if (elementType === 'header') {
                    similarity = (elem1.level === elem2.level && elem1.text === elem2.text) ? 1 : 0;
                } else if (elementType === 'list') {
                    similarity = (elem1.type === elem2.type && elem1.text === elem2.text) ? 1 : 0;
                } else {
                    similarity = elem1.text === elem2.text ? 1 : 0;
                }

                if (similarity > bestSimilarity) {
                    bestSimilarity = similarity;
                    bestMatch = { element: elem2, index: j };
                }
            });

            if (bestMatch && bestSimilarity >= 0.8) {
                used2.add(bestMatch.index);
                if (bestSimilarity === 1 && elem1.index === bestMatch.element.index) {
                    result.push({ type: 'unchanged', element: elem1 });
                } else {
                    result.push({ 
                        type: 'moved', 
                        element: elem1,
                        from: elem1.index,
                        to: bestMatch.element.index
                    });
                }
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

    // Main diff function
    diff(text1, text2) {
        // Analyze both texts
        const analysis1 = this.analyzeContent(text1);
        const analysis2 = this.analyzeContent(text2);

        // Compute enhanced diff
        const diff = this.computeLineDiff(analysis1, analysis2);

        // Compare structures
        const structuralChanges = this.compareStructure(analysis1.structure, analysis2.structure);

        return { diff, structuralChanges };
    }
}

// Export the enhanced engine
window.EnhancedDiffEngine = EnhancedDiffEngine;