// diff-algorithms.js
// Core diff algorithms: Myers, character-level, and word-level diffs

// Compute word-level differences within a line, returning separate left and right views
function computeWordDiffSeparate(line1, line2) {
    if (!line1 && !line2) return { left: '', right: '' };
    if (!line1) return { left: '', right: `<span class="word-added">${line2}</span>` };
    if (!line2) return { left: `<span class="word-removed">${line1}</span>`, right: '' };
    
    // Split into words but preserve whitespace
    const words1 = line1.split(/(\s+)/);
    const words2 = line2.split(/(\s+)/);
    
    // If lines are identical, return as is
    if (line1 === line2) return { left: line1, right: line2 };
    
    // Use character-level diff for short lines or very different lines
    if (words1.length < 3 || words2.length < 3 || 
        Math.abs(words1.length - words2.length) > Math.max(words1.length, words2.length) * 0.5) {
        return computeCharDiffSeparate(line1, line2);
    }
    
    // Compute word-level diff using LCS
    const dp = [];
    for (let i = 0; i <= words1.length; i++) {
        dp[i] = [];
        for (let j = 0; j <= words2.length; j++) {
            if (i === 0) dp[i][j] = j;
            else if (j === 0) dp[i][j] = i;
            else if (words1[i-1] === words2[j-1]) dp[i][j] = dp[i-1][j-1];
            else dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
        }
    }
    
    // Backtrack to find the word diff, creating separate left and right views
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

// Compute character-level differences within a line, returning separate left and right views
function computeCharDiffSeparate(line1, line2) {
    const dp = [];
    const len1 = line1.length;
    const len2 = line2.length;
    
    // Initialize DP table
    for (let i = 0; i <= len1; i++) {
        dp[i] = [];
        for (let j = 0; j <= len2; j++) {
            if (i === 0) dp[i][j] = j;
            else if (j === 0) dp[i][j] = i;
            else if (line1[i-1] === line2[j-1]) dp[i][j] = dp[i-1][j-1];
            else dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
        }
    }
    
    // Backtrack to find character diff, creating separate left and right views
    const leftParts = [];
    const rightParts = [];
    let i = len1, j = len2;
    
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && line1[i-1] === line2[j-1]) {
            leftParts.unshift({type: 'unchanged', char: line1[i-1]});
            rightParts.unshift({type: 'unchanged', char: line2[j-1]});
            i--; j--;
        } else if (j > 0 && (i === 0 || dp[i][j-1] <= dp[i-1][j])) {
            rightParts.unshift({type: 'added', char: line2[j-1]});
            j--;
        } else if (i > 0) {
            leftParts.unshift({type: 'removed', char: line1[i-1]});
            i--;
        }
    }
    
    // Combine consecutive changes into blocks
    const combineChanges = (parts) => {
        let result = '';
        let currentBlock = null;
        
        for (const part of parts) {
            if (currentBlock && currentBlock.type === part.type) {
                // Extend current block
                currentBlock.text += part.char;
            } else {
                // Finish previous block
                if (currentBlock) {
                    if (currentBlock.type === 'unchanged') {
                        result += currentBlock.text;
                    } else {
                        const spanClass = currentBlock.type === 'added' ? 'char-added' : 'char-removed';
                        result += `<span class="${spanClass}">${currentBlock.text}</span>`;
                    }
                }
                // Start new block
                currentBlock = {type: part.type, text: part.char};
            }
        }
        
        // Finish final block
        if (currentBlock) {
            if (currentBlock.type === 'unchanged') {
                result += currentBlock.text;
            } else {
                const spanClass = currentBlock.type === 'added' ? 'char-added' : 'char-removed';
                result += `<span class="${spanClass}">${currentBlock.text}</span>`;
            }
        }
        
        return result;
    };
    
    return { 
        left: combineChanges(leftParts), 
        right: combineChanges(rightParts) 
    };
}

// Basic Myers diff algorithm for line-level comparison
function myersDiff(lines1, lines2) {
    const dp = [];
    for (let i = 0; i <= lines1.length; i++) {
        dp[i] = [];
        for (let j = 0; j <= lines2.length; j++) {
            if (i === 0) dp[i][j] = j;
            else if (j === 0) dp[i][j] = i;
            else if (lines1[i-1] === lines2[j-1]) dp[i][j] = dp[i-1][j-1];
            else dp[i][j] = 1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
        }
    }
    
    // Backtrack to find the actual diff
    const diff = [];
    let i = lines1.length, j = lines2.length;
    
    while (i > 0 || j > 0) {
        if (i > 0 && j > 0 && lines1[i-1] === lines2[j-1]) {
            diff.unshift({type: 'unchanged', line1: lines1[i-1], line2: lines2[j-1]});
            i--; j--;
        } else if (j > 0 && (i === 0 || dp[i][j-1] <= dp[i-1][j])) {
            diff.unshift({type: 'added', line1: '', line2: lines2[j-1]});
            j--;
        } else if (i > 0) {
            diff.unshift({type: 'removed', line1: lines1[i-1], line2: ''});
            i--;
        }
    }
    
    return diff;
}