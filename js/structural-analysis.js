// structural-analysis.js
// Analyzes and compares structural elements of blog posts

// Blog-specific content analysis
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

// Calculate enhanced similarity with blog-specific rules
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

// Extract structural elements from text
function extractStructuralElements(text) {
    const lines = text.split('\n');
    const structural = {
        headers: [],
        lists: [],
        codeBlocks: [],
        quotes: [],
        images: []
    };
    
    lines.forEach((line, index) => {
        const analysis = analyzeContentStructure(line);
        
        if (analysis.isHeader) {
            structural.headers.push({
                level: analysis.headerLevel,
                text: line.trim(),
                index: index
            });
        }
        
        if (analysis.isList) {
            structural.lists.push({
                text: line.trim(),
                index: index,
                type: /^\d+[.)]\s/.test(line.trim()) ? 'ordered' : 'unordered'
            });
        }
        
        if (analysis.isCode && line.trim().startsWith('```')) {
            structural.codeBlocks.push({
                text: line.trim(),
                index: index,
                language: line.trim().replace(/^```/, '')
            });
        }
        
        if (analysis.isQuote) {
            structural.quotes.push({
                text: line.trim(),
                index: index
            });
        }
        
        if (analysis.isImageRef) {
            structural.images.push({
                text: line.trim(),
                index: index
            });
        }
    });
    
    return structural;
}

// Compare structural elements between two texts
function compareStructuralElements(struct1, struct2) {
    const comparison = {
        headers: compareHeaders(struct1.headers, struct2.headers),
        lists: compareLists(struct1.lists, struct2.lists),
        codeBlocks: compareCodeBlocks(struct1.codeBlocks, struct2.codeBlocks),
        overall: {}
    };
    
    // Calculate overall structural changes
    comparison.overall.headerChanges = comparison.headers.filter(h => h.type !== 'unchanged').length;
    comparison.overall.listChanges = comparison.lists.filter(l => l.type !== 'unchanged').length;
    comparison.overall.codeChanges = comparison.codeBlocks.filter(c => c.type !== 'unchanged').length;
    
    return comparison;
}

// Compare headers between two structures
function compareHeaders(headers1, headers2) {
    const result = [];
    const used2 = new Set();
    
    headers1.forEach(h1 => {
        const match = headers2.find((h2, i) => 
            !used2.has(i) && 
            h1.text === h2.text
        );
        
        if (match) {
            const matchIndex = headers2.indexOf(match);
            used2.add(matchIndex);
            
            if (h1.level === match.level && h1.index === match.index) {
                result.push({
                    type: 'unchanged',
                    header: h1.text,
                    level: h1.level
                });
            } else {
                result.push({
                    type: 'moved',
                    header: h1.text,
                    from: h1.index,
                    to: match.index,
                    levelChanged: h1.level !== match.level
                });
            }
        } else {
            result.push({
                type: 'removed',
                header: h1.text,
                level: h1.level,
                index: h1.index
            });
        }
    });
    
    // Find added headers
    headers2.forEach((h2, i) => {
        if (!used2.has(i)) {
            result.push({
                type: 'added',
                header: h2.text,
                level: h2.level,
                index: h2.index
            });
        }
    });
    
    return result.sort((a, b) => Math.min(a.index || 0, a.from || 0) - Math.min(b.index || 0, b.from || 0));
}

// Compare lists between two structures
function compareLists(lists1, lists2) {
    // Similar logic to headers but for lists
    const result = [];
    const used2 = new Set();
    
    lists1.forEach(l1 => {
        const match = lists2.find((l2, i) => 
            !used2.has(i) && 
            l1.text === l2.text &&
            l1.type === l2.type
        );
        
        if (match) {
            const matchIndex = lists2.indexOf(match);
            used2.add(matchIndex);
            result.push({
                type: 'unchanged',
                list: l1.text,
                listType: l1.type
            });
        } else {
            result.push({
                type: 'removed',
                list: l1.text,
                listType: l1.type,
                index: l1.index
            });
        }
    });
    
    lists2.forEach((l2, i) => {
        if (!used2.has(i)) {
            result.push({
                type: 'added',
                list: l2.text,
                listType: l2.type,
                index: l2.index
            });
        }
    });
    
    return result;
}

// Compare code blocks between two structures
function compareCodeBlocks(blocks1, blocks2) {
    const result = [];
    const used2 = new Set();
    
    blocks1.forEach(b1 => {
        const match = blocks2.find((b2, i) => 
            !used2.has(i) && 
            b1.text === b2.text
        );
        
        if (match) {
            const matchIndex = blocks2.indexOf(match);
            used2.add(matchIndex);
            result.push({
                type: 'unchanged',
                codeBlock: b1.text,
                language: b1.language
            });
        } else {
            result.push({
                type: 'removed',
                codeBlock: b1.text,
                language: b1.language,
                index: b1.index
            });
        }
    });
    
    blocks2.forEach((b2, i) => {
        if (!used2.has(i)) {
            result.push({
                type: 'added',
                codeBlock: b2.text,
                language: b2.language,
                index: b2.index
            });
        }
    });
    
    return result;
}

// Join consecutive lines that might have been split, with structural awareness
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