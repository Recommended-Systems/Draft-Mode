// blog-analysis.js
// Blog-specific content analysis and similarity functions

/**
 * Analyze the structure and content of a blog line
 */
function analyzeContentStructure(line) {
    const trimmed = line.trim();
    return {
        isHeader: /^#{1,6}\s/.test(trimmed),
        headerLevel: (() => {
            const match = trimmed.match(/^(#{1,6})\s/);
            return match ? match[1].length : 0;
        })(),
        isList: /^\s*[\-\*\+]|\d+\.|\d+\)/.test(trimmed),
        isBold: /\*\*[^*]+\*\*/.test(trimmed),
        isItalic: /\*[^*]+\*(?!\*)/.test(trimmed),
        isCode: /`[^`]+`/.test(trimmed) || /```/.test(trimmed),
        isQuote: /^>\s/.test(trimmed),
        hasLinks: /\[.*\]\(.*\)/.test(trimmed),
        isHorizontalRule: /^[-*_]{3,}$/.test(trimmed),
        // Blog-specific patterns
        isMetric: /\d+%|\$[\d,]+|CTR|CPC|ROAS|CPM|CPA/i.test(trimmed),
        isConclusion: /verdict|conclusion|takeaway|summary|findings|results/i.test(trimmed),
        isMethodology: /method|data|prompt|model|approach|experiment/i.test(trimmed),
        isCallout: /\*\*[^*]+:\*\*/.test(trimmed), // **Label:** pattern
        hasEmphasis: /\*\*[^*]+\*\*|\*[^*]+\*(?!\*)/g.test(trimmed),
        // Structure analysis
        isEmpty: trimmed.length === 0,
        isImageRef: /!\[.*\]\(.*\)/.test(trimmed)
    };
}

/**
 * Calculate similarity between two lines with blog-specific rules
 */
function calculateBlogSimilarity(line1, line2) {
    if (!line1 || !line2) return 0;
    
    const struct1 = analyzeContentStructure(line1);
    const struct2 = analyzeContentStructure(line2);
    
    // High penalty for different structures
    if (struct1.isHeader !== struct2.isHeader) return 0;
    if (struct1.isHeader && struct1.headerLevel !== struct2.headerLevel) return 0.1;
    if (struct1.isList !== struct2.isList) return 0.1;
    if (struct1.isCode !== struct2.isCode) return 0.1;
    if (struct1.isQuote !== struct2.isQuote) return 0.1;
    
    // Normalize content by removing markdown syntax for comparison
    let norm1 = line1.trim()
        .replace(/^#{1,6}\s/, '') // Remove header markers
        .replace(/^\s*[\-\*\+]|\d+\.|\d+\)\s?/, '') // Remove list markers
        .replace(/\*\*([^*]+)\*\*/g, '$1') // Remove bold
        .replace(/\*([^*]+)\*/g, '$1') // Remove italic
        .replace(/`([^`]+)`/g, '$1') // Remove inline code
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Extract link text
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1') // Extract alt text
        .replace(/\s+/g, ' ');
        
    let norm2 = line2.trim()
        .replace(/^#{1,6}\s/, '')
        .replace(/^\s*[\-\*\+]|\d+\.|\d+\)\s?/, '')
        .replace(/\*\*([^*]+)\*\*/g, '$1')
        .replace(/\*([^*]+)\*/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
        .replace(/!\[([^\]]*)\]\([^)]+\)/g, '$1')
        .replace(/\s+/g, ' ');
    
    if (norm1 === norm2) return 1;
    if (!norm1 || !norm2) return 0;
    
    // Bonus for matching structure types
    let structureBonus = 0;
    if (struct1.isMethodology && struct2.isMethodology) structureBonus += 0.1;
    if (struct1.isConclusion && struct2.isConclusion) structureBonus += 0.1;
    if (struct1.isMetric && struct2.isMetric) structureBonus += 0.05;
    
    // Calculate base similarity
    const len1 = norm1.length;
    const len2 = norm2.length;
    const dp = [];
    
    for (let i = 0; i <= len1; i++) {
        dp[i] = [i];
        for (let j = 1; j <= len2; j++) {
            dp[i][j] = 0;
        }
    }
    for (let j = 0; j <= len2; j++) {
        dp[0][j] = j;
    }
    
    for (let i = 1; i <= len1; i++) {
        for (let j = 1; j <= len2; j++) {
            const cost = norm1[i-1] === norm2[j-1] ? 0 : 1;
            dp[i][j] = Math.min(
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            );
        }
    }
    
    const maxLen = Math.max(len1, len2);
    const baseSimilarity = maxLen === 0 ? 1 : (maxLen - dp[len1][len2]) / maxLen;
    
    return Math.min(1, baseSimilarity + structureBonus);
}

/**
 * Join consecutive lines that might have been split
 */
function reconstructLines(text1, text2) {
    const lines1 = text1.split('\n');
    const lines2 = text2.split('\n');
    
    // Look for cases where lines might have been merged or split
    const reconstructed1 = [];
    const reconstructed2 = [];
    
    let i = 0, j = 0;
    while (i < lines1.length || j < lines2.length) {
        if (i >= lines1.length) {
            // Remaining lines in second text
            reconstructed1.push('');
            reconstructed2.push(lines2[j]);
            j++;
        } else if (j >= lines2.length) {
            // Remaining lines in first text
            reconstructed1.push(lines1[i]);
            reconstructed2.push('');
            i++;
        } else {
            // Check if current lines are similar
            const similarity = calculateBlogSimilarity(lines1[i], lines2[j]);
            
            if (similarity > 0.3) {
                // Lines are similar enough
                reconstructed1.push(lines1[i]);
                reconstructed2.push(lines2[j]);
                i++;
                j++;
            } else {
                // Check if line1[i] matches line2[j+1] (line added)
                if (j + 1 < lines2.length && calculateBlogSimilarity(lines1[i], lines2[j + 1]) > 0.7) {
                    reconstructed1.push('');
                    reconstructed2.push(lines2[j]);
                    j++;
                }
                // Check if line1[i+1] matches line2[j] (line removed)
                else if (i + 1 < lines1.length && calculateBlogSimilarity(lines1[i + 1], lines2[j]) > 0.7) {
                    reconstructed1.push(lines1[i]);
                    reconstructed2.push('');
                    i++;
                }
                // Check if lines might have been merged (line1[i] + line1[i+1] ≈ line2[j])
                else if (i + 1 < lines1.length) {
                    const merged = lines1[i] + ' ' + lines1[i + 1];
                    if (calculateBlogSimilarity(merged, lines2[j]) > 0.7) {
                        reconstructed1.push(merged);
                        reconstructed2.push(lines2[j]);
                        i += 2;
                        j++;
                        continue;
                    }
                }
                // Check if line might have been split (line1[i] ≈ line2[j] + line2[j+1])
                else if (j + 1 < lines2.length) {
                    const merged = lines2[j] + ' ' + lines2[j + 1];
                    if (calculateBlogSimilarity(lines1[i], merged) > 0.7) {
                        reconstructed1.push(lines1[i]);
                        reconstructed2.push(merged);
                        i++;
                        j += 2;
                        continue;
                    }
                }
                
                // Default case: lines are different
                reconstructed1.push(lines1[i]);
                reconstructed2.push(lines2[j]);
                i++;
                j++;
            }
        }
    }
    
    return [reconstructed1, reconstructed2];
}

/**
 * Extract structural elements from text
 */
function extractStructure(text) {
    const lines = text.split('\n');
    const structure = {
        headers: [],
        lists: [],
        codeBlocks: [],
        quotes: [],
        images: [],
        content: []
    };
    
    let inCodeBlock = false;
    
    lines.forEach((line, index) => {
        const trimmed = line.trim();
        
        // Track code blocks
        if (trimmed.startsWith('```')) {
            inCodeBlock = !inCodeBlock;
            structure.codeBlocks.push({
                index: index,
                line: line,
                type: inCodeBlock ? 'start' : 'end'
            });
            return;
        }
        
        if (inCodeBlock) {
            structure.codeBlocks.push({
                index: index,
                line: line,
                type: 'content'
            });
            return;
        }
        
        // Extract different structural elements
        if (trimmed.match(/^#{1,6}\s/)) {
            const match = trimmed.match(/^(#{1,6})\s(.+)$/);
            structure.headers.push({
                index: index,
                level: match[1].length,
                text: match[2],
                line: line
            });
        } else if (trimmed.match(/^\s*[\-\*\+]|\d+\.|\d+\)/)) {
            structure.lists.push({
                index: index,
                line: line,
                type: trimmed.match(/^\s*[\-\*\+]/) ? 'unordered' : 'ordered'
            });
        } else if (trimmed.startsWith('>')) {
            structure.quotes.push({
                index: index,
                line: line
            });
        } else if (trimmed.match(/!\[.*\]\(.*\)/)) {
            structure.images.push({
                index: index,
                line: line
            });
        } else if (trimmed.length > 0) {
            structure.content.push({
                index: index,
                line: line
            });
        }
    });
    
    return structure;
}

/**
 * Compare structural elements between two texts
 */
function compareStructures(structure1, structure2) {
    const structuralChanges = {
        headers: compareElements(structure1.headers, structure2.headers, compareHeaders),
        lists: compareElements(structure1.lists, structure2.lists, compareLists),
        codeBlocks: compareElements(structure1.codeBlocks, structure2.codeBlocks, compareGeneric),
        quotes: compareElements(structure1.quotes, structure2.quotes, compareGeneric),
        images: compareElements(structure1.images, structure2.images, compareGeneric)
    };
    
    return structuralChanges;
}

/**
 * Compare elements using a custom comparison function
 */
function compareElements(elements1, elements2, compareFunc) {
    const changes = [];
    
    // Find matches, additions, and removals
    const matched1 = new Set();
    const matched2 = new Set();
    
    // Find exact matches first
    elements1.forEach((elem1, i) => {
        elements2.forEach((elem2, j) => {
            if (!matched1.has(i) && !matched2.has(j) && compareFunc(elem1, elem2) > 0.9) {
                changes.push({
                    type: 'matched',
                    element1: elem1,
                    element2: elem2,
                    similarity: compareFunc(elem1, elem2)
                });
                matched1.add(i);
                matched2.add(j);
            }
        });
    });
    
    // Find similar elements that might have changed
    elements1.forEach((elem1, i) => {
        if (!matched1.has(i)) {
            elements2.forEach((elem2, j) => {
                if (!matched2.has(j)) {
                    const similarity = compareFunc(elem1, elem2);
                    if (similarity > 0.3) {
                        changes.push({
                            type: 'modified',
                            element1: elem1,
                            element2: elem2,
                            similarity: similarity
                        });
                        matched1.add(i);
                        matched2.add(j);
                    }
                }
            });
        }
    });
    
    // Mark remaining as removed/added
    elements1.forEach((elem1, i) => {
        if (!matched1.has(i)) {
            changes.push({
                type: 'removed',
                element1: elem1,
                element2: null
            });
        }
    });
    
    elements2.forEach((elem2, j) => {
        if (!matched2.has(j)) {
            changes.push({
                type: 'added',
                element1: null,
                element2: elem2
            });
        }
    });
    
    return changes;
}

/**
 * Compare header elements
 */
function compareHeaders(header1, header2) {
    if (header1.level !== header2.level) return 0.1;
    return calculateBlogSimilarity(header1.text, header2.text);
}

/**
 * Compare list elements
 */
function compareLists(list1, list2) {
    if (list1.type !== list2.type) return 0.1;
    return calculateBlogSimilarity(list1.line, list2.line);
}

/**
 * Generic comparison for other elements
 */
function compareGeneric(elem1, elem2) {
    return calculateBlogSimilarity(elem1.line, elem2.line);
}

/**
 * Create a version of text with structure removed for content comparison
 */
function removeStructure(text) {
    const lines = text.split('\n');
    const contentLines = [];
    
    let inCodeBlock = false;
    
    lines.forEach(line => {
        const trimmed = line.trim();
        
        // Track code blocks
        if (trimmed.startsWith('```')) {
            inCodeBlock = !inCodeBlock;
            return;
        }
        
        if (inCodeBlock) return;
        
        // Skip structural elements
        if (trimmed.match(/^#{1,6}\s/) || 
            trimmed.match(/^\s*[\-\*\+]|\d+\.|\d+\)/) ||
            trimmed.startsWith('>') ||
            trimmed.match(/!\[.*\]\(.*\)/) ||
            trimmed.match(/^[-*_]{3,}$/)) {
            return;
        }
        
        if (trimmed.length > 0) {
            contentLines.push(line);
        }
    });
    
    return contentLines;
}

/**
 * Hybrid diff that combines structural and content analysis
 */
function hybridDiff(text1, text2) {
    // For now, let's use a simpler approach that's more reliable
    // We'll improve the structural analysis in future iterations
    
    // First, try to reconstruct lines that might have been split/merged
    const [lines1, lines2] = reconstructLines(text1, text2);
    
    // Use patience diff algorithm which handles moved sections better
    const diff = patienceDiff(lines1, lines2);
    
    // Post-process to identify modified lines and compute word/char diffs
    const processedDiff = [];
    for (let k = 0; k < diff.length; k++) {
        if (diff[k].type === 'removed' && k + 1 < diff.length && diff[k + 1].type === 'added') {
            // Check if these lines are similar enough to be considered a modification
            const similarity = calculateBlogSimilarity(diff[k].line1, diff[k + 1].line2);
            
            if (similarity > 0.3) {
                // This is likely a modified line, compute word-level diff
                const line1 = diff[k].line1;
                const line2 = diff[k + 1].line2;
                const wordDiff = computeWordDiffSeparate(line1, line2);
                
                processedDiff.push({
                    type: 'modified',
                    line1: line1,
                    line2: line2,
                    leftDiff: wordDiff.left,
                    rightDiff: wordDiff.right
                });
                k++; // Skip the next item since we've processed it
            } else {
                // Lines are too different, treat as separate removal and addition
                processedDiff.push(diff[k]);
            }
        } else {
            processedDiff.push(diff[k]);
        }
    }
    
    return processedDiff;
}

/**
 * Check if a line is structural (header, list, etc.)
 */
function isStructuralLine(line) {
    const trimmed = line.trim();
    return trimmed.match(/^#{1,6}\s/) ||
           trimmed.match(/^\s*[\-\*\+]|\d+\.|\d+\)/) ||
           trimmed.startsWith('>') ||
           trimmed.match(/!\[.*\]\(.*\)/) ||
           trimmed.match(/^[-*_]{3,}$/) ||
           trimmed.startsWith('```');
}