// main.js
// Main application logic for the blog diff tool

// Main diff computation function that uses the new algorithms
function computeDiff(text1, text2) {
    // First, try to reconstruct lines that might have been split/merged
    const [lines1, lines2] = reconstructLines(text1, text2);
    
    // Use patience diff for blog content
    const diff = blogPatienceDiff(lines1, lines2);
    
    // Extract structural elements for analysis
    const struct1 = extractStructuralElements(text1);
    const struct2 = extractStructuralElements(text2);
    const structuralChanges = compareStructuralElements(struct1, struct2);
    
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
    
    return { diff: processedDiff, structuralChanges };
}

function updateDiff() {
    const draft1 = document.getElementById('draft1').value.trim();
    const draft2 = document.getElementById('draft2').value.trim();
    const diffContainer = document.getElementById('diffContainer');
    
    if (!draft1 && !draft2) {
        diffContainer.style.display = 'none';
        return;
    }
    
    diffContainer.style.display = 'block';
    
    if (!draft1 || !draft2) {
        const diffContent = document.getElementById('diffContent');
        const isMarkdown = document.getElementById('markdownToggle').checked;
        
        // Show placeholder for missing content
        if (!draft1 && !draft2) {
            diffContent.innerHTML = '<div class="diff-placeholder">Please paste both drafts to see differences</div>';
        } else if (!draft1) {
            diffContent.innerHTML = '<div class="diff-placeholder">Please paste your original draft</div>';
        } else {
            diffContent.innerHTML = '<div class="diff-placeholder">Please paste your updated draft</div>';
        }
        return;
    }
    
    // Show loading state briefly
    document.getElementById('diffContent').innerHTML = '<div class="loading">Computing differences...</div>';
    
    // Compute diff with a small delay to show loading state
    setTimeout(() => {
        const result = computeDiff(draft1, draft2);
        renderDiff(result.diff, result.structuralChanges);
    }, 100);
}

// Initialize the application
function initializeDiffTool() {
    // Add event listeners
    document.getElementById('draft1').addEventListener('blur', updateDiff);
    document.getElementById('draft2').addEventListener('blur', updateDiff);
    
    // Add markdown toggle listener
    document.getElementById('markdownToggle').addEventListener('change', updateDiff);
    
    // Also update on input for better UX (with debouncing)
    let timeoutId;
    function debouncedUpdate() {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(updateDiff, 1000);
    }
    
    document.getElementById('draft1').addEventListener('input', debouncedUpdate);
    document.getElementById('draft2').addEventListener('input', debouncedUpdate);
}

// Run when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeDiffTool);