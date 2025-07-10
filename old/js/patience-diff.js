// patience-diff.js
// Implementation of the patience diff algorithm

// Find unique lines that appear only once in each text
function findUniqueMatches(lines1, lines2) {
    const count1 = {};
    const count2 = {};
    
    // Count occurrences in each text
    lines1.forEach(line => count1[line] = (count1[line] || 0) + 1);
    lines2.forEach(line => count2[line] = (count2[line] || 0) + 1);
    
    // Find lines that appear exactly once in both texts
    const uniqueMatches = [];
    lines1.forEach((line, i) => {
        if (count1[line] === 1 && count2[line] === 1) {
            const j = lines2.indexOf(line);
            if (j !== -1) {
                uniqueMatches.push({
                    line: line,
                    index1: i,
                    index2: j
                });
            }
        }
    });
    
    // Sort by position in first text to maintain order
    return uniqueMatches.sort((a, b) => a.index1 - b.index1);
}

// Patience diff implementation
function patienceDiff(lines1, lines2) {
    const uniqueMatches = findUniqueMatches(lines1, lines2);
    
    if (uniqueMatches.length === 0) {
        // No unique matches, fall back to Myers
        return myersDiff(lines1, lines2);
    }
    
    const result = [];
    let last1 = 0;
    let last2 = 0;
    
    // Process segments between unique matches
    for (const match of uniqueMatches) {
        // Diff the segment before this match
        if (last1 < match.index1 || last2 < match.index2) {
            const segment1 = lines1.slice(last1, match.index1);
            const segment2 = lines2.slice(last2, match.index2);
            const segmentDiff = patienceDiff(segment1, segment2); // Recursive
            result.push(...segmentDiff);
        }
        
        // Add the unique match as unchanged
        result.push({
            type: 'unchanged',
            line1: match.line,
            line2: match.line
        });
        
        last1 = match.index1 + 1;
        last2 = match.index2 + 1;
    }
    
    // Process remaining lines after last match
    if (last1 < lines1.length || last2 < lines2.length) {
        const segment1 = lines1.slice(last1);
        const segment2 = lines2.slice(last2);
        const segmentDiff = patienceDiff(segment1, segment2);
        result.push(...segmentDiff);
    }
    
    return result;
}

// Enhanced unique line detection for blog content
function findBlogAnchors(lines1, lines2) {
    const uniqueMatches = [];
    
    // Look for headers (strong anchors)
    lines1.forEach((line, i) => {
        if (/^#{1,6}\s/.test(line.trim())) {
            const j = lines2.findIndex(l => l.trim() === line.trim());
            if (j !== -1) {
                uniqueMatches.push({
                    line: line,
                    index1: i,
                    index2: j,
                    priority: 'high', // Headers are strong anchors
                    type: 'header'
                });
            }
        }
    });
    
    // Look for code blocks
    lines1.forEach((line, i) => {
        if (/^```/.test(line.trim())) {
            const j = lines2.findIndex(l => l.trim() === line.trim());
            if (j !== -1) {
                uniqueMatches.push({
                    line: line,
                    index1: i,
                    index2: j,
                    priority: 'medium',
                    type: 'codeblock'
                });
            }
        }
    });
    
    // Look for unique long words/phrases
    lines1.forEach((line, i) => {
        const uniqueWords = line.match(/\b\w{8,}\b/g);
        if (uniqueWords) {
            uniqueWords.forEach(word => {
                // Check if this word is unique enough
                const count1 = lines1.filter(l => l.includes(word)).length;
                const count2 = lines2.filter(l => l.includes(word)).length;
                
                if (count1 === 1 && count2 === 1) {
                    const j = lines2.findIndex(l => l.includes(word) && l === line);
                    if (j !== -1) {
                        uniqueMatches.push({
                            line: line,
                            index1: i,
                            index2: j,
                            priority: 'low',
                            type: 'unique-word',
                            word: word
                        });
                    }
                }
            });
        }
    });
    
    // Sort by priority, then by position
    return uniqueMatches.sort((a, b) => {
        const priorityOrder = { high: 0, medium: 1, low: 2 };
        if (a.priority !== b.priority) {
            return priorityOrder[a.priority] - priorityOrder[b.priority];
        }
        return a.index1 - b.index1;
    });
}

// Blog-optimized patience diff
function blogPatienceDiff(lines1, lines2) {
    const anchors = findBlogAnchors(lines1, lines2);
    
    if (anchors.length === 0) {
        return myersDiff(lines1, lines2);
    }
    
    const result = [];
    let last1 = 0;
    let last2 = 0;
    
    // Process segments between anchors
    for (const anchor of anchors) {
        // Skip if this anchor would create non-monotonic sequence
        if (anchor.index1 < last1 || anchor.index2 < last2) {
            continue;
        }
        
        // Diff the segment before this anchor
        if (last1 < anchor.index1 || last2 < anchor.index2) {
            const segment1 = lines1.slice(last1, anchor.index1);
            const segment2 = lines2.slice(last2, anchor.index2);
            
            // Use patience recursively for larger segments, Myers for small ones
            const segmentDiff = segment1.length > 3 || segment2.length > 3 
                ? blogPatienceDiff(segment1, segment2)
                : myersDiff(segment1, segment2);
            result.push(...segmentDiff);
        }
        
        // Add the anchor as unchanged (or moved)
        if (anchor.index1 === last1 && anchor.index2 === last2) {
            result.push({
                type: 'unchanged',
                line1: anchor.line,
                line2: anchor.line
            });
        } else {
            result.push({
                type: 'moved',
                line1: anchor.line,
                line2: anchor.line,
                from: anchor.index1,
                to: anchor.index2,
                moveType: anchor.type
            });
        }
        
        last1 = anchor.index1 + 1;
        last2 = anchor.index2 + 1;
    }
    
    // Process remaining lines
    if (last1 < lines1.length || last2 < lines2.length) {
        const segment1 = lines1.slice(last1);
        const segment2 = lines2.slice(last2);
        const segmentDiff = segment1.length > 3 || segment2.length > 3
            ? blogPatienceDiff(segment1, segment2)
            : myersDiff(segment1, segment2);
        result.push(...segmentDiff);
    }
    
    return result;
}