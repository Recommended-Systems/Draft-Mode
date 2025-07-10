// main.js
// Main UI controller and event handlers

/**
 * Render the diff in the UI using a table for proper alignment
 */
function renderDiff(diff) {
    const diffContent = document.getElementById('diffContent');
    const statsDiv = document.getElementById('diffStats');
    const isMarkdown = document.getElementById('markdownToggle').checked;
    
    if (!diff || diff.length === 0) {
        diffContent.innerHTML = '<div class="diff-placeholder">No differences found</div>';
        return;
    }
    
    let addedCount = 0;
    let removedCount = 0;
    let modifiedCount = 0;
    let movedCount = 0;
    let leftLineNum = 1;
    let rightLineNum = 1;
    
    // Create table for proper alignment
    const table = document.createElement('table');
    table.className = 'diff-table';
    
    // Add header row
    const headerRow = document.createElement('tr');
    headerRow.className = 'diff-header-row';
    headerRow.innerHTML = `
        <th class="diff-header-cell" colspan="2">Original</th>
        <th class="diff-header-cell" colspan="2">Updated</th>
    `;
    table.appendChild(headerRow);
    
    diff.forEach(item => {
        const row = document.createElement('tr');
        row.className = 'diff-row';
        
        // Create cells
        const leftLineNumCell = document.createElement('td');
        const leftContentCell = document.createElement('td');
        const rightLineNumCell = document.createElement('td');
        const rightContentCell = document.createElement('td');
        
        leftLineNumCell.className = 'diff-line-cell line-number';
        leftContentCell.className = 'diff-line-cell line-content';
        rightLineNumCell.className = 'diff-line-cell line-number';
        rightContentCell.className = 'diff-line-cell line-content';
        
        if (item.type === 'unchanged') {
            leftLineNumCell.textContent = leftLineNum++;
            rightLineNumCell.textContent = rightLineNum++;
            
            leftContentCell.innerHTML = processContentForDisplay(item.line1, isMarkdown);
            rightContentCell.innerHTML = processContentForDisplay(item.line2, isMarkdown);
            
            leftLineNumCell.classList.add('diff-unchanged');
            leftContentCell.classList.add('diff-unchanged');
            rightLineNumCell.classList.add('diff-unchanged');
            rightContentCell.classList.add('diff-unchanged');
            
            if (isMarkdown) {
                leftContentCell.classList.add('markdown-rendered');
                rightContentCell.classList.add('markdown-rendered');
            }
        } else if (item.type === 'removed') {
            leftLineNumCell.textContent = leftLineNum++;
            rightLineNumCell.innerHTML = '&nbsp;';
            
            leftContentCell.innerHTML = processContentForDisplay(item.line1, isMarkdown);
            rightContentCell.innerHTML = '&nbsp;';
            
            leftLineNumCell.classList.add('diff-removed');
            leftContentCell.classList.add('diff-removed');
            rightLineNumCell.classList.add('diff-unchanged');
            rightContentCell.classList.add('diff-unchanged');
            
            if (isMarkdown) {
                leftContentCell.classList.add('markdown-rendered');
            }
            
            removedCount++;
        } else if (item.type === 'added') {
            leftLineNumCell.innerHTML = '&nbsp;';
            rightLineNumCell.textContent = rightLineNum++;
            
            leftContentCell.innerHTML = '&nbsp;';
            rightContentCell.innerHTML = processContentForDisplay(item.line2, isMarkdown);
            
            leftLineNumCell.classList.add('diff-unchanged');
            leftContentCell.classList.add('diff-unchanged');
            rightLineNumCell.classList.add('diff-added');
            rightContentCell.classList.add('diff-added');
            
            if (isMarkdown) {
                rightContentCell.classList.add('markdown-rendered');
            }
            
            addedCount++;
        } else if (item.type === 'modified') {
            leftLineNumCell.textContent = leftLineNum++;
            rightLineNumCell.textContent = rightLineNum++;
            
            // For modified lines, always show word-level differences
            leftContentCell.innerHTML = processContentForDisplay(item.leftDiff, isMarkdown, true);
            rightContentCell.innerHTML = processContentForDisplay(item.rightDiff, isMarkdown, true);
            
            leftLineNumCell.classList.add('diff-modified');
            leftContentCell.classList.add('diff-modified');
            rightLineNumCell.classList.add('diff-modified');
            rightContentCell.classList.add('diff-modified');
            
            if (isMarkdown) {
                leftContentCell.classList.add('markdown-rendered');
                rightContentCell.classList.add('markdown-rendered');
            }
            
            modifiedCount++;
        } else if (item.type === 'moved-from') {
            leftLineNumCell.textContent = leftLineNum++;
            rightLineNumCell.innerHTML = '&nbsp;';
            
            leftContentCell.innerHTML = `
                <div class="move-indicator">↓ Moved to line ${item.moveTo + 1}</div>
                ${processContentForDisplay(item.line1, isMarkdown)}
            `;
            rightContentCell.innerHTML = '&nbsp;';
            
            leftLineNumCell.classList.add('diff-moved');
            leftContentCell.classList.add('diff-moved');
            rightLineNumCell.classList.add('diff-unchanged');
            rightContentCell.classList.add('diff-unchanged');
            
            if (isMarkdown) {
                leftContentCell.classList.add('markdown-rendered');
            }
            
            movedCount++;
        } else if (item.type === 'moved-to') {
            leftLineNumCell.innerHTML = '&nbsp;';
            rightLineNumCell.textContent = rightLineNum++;
            
            leftContentCell.innerHTML = '&nbsp;';
            rightContentCell.innerHTML = `
                <div class="move-indicator">↑ Moved from line ${item.moveFrom + 1}</div>
                ${processContentForDisplay(item.line2, isMarkdown)}
            `;
            
            leftLineNumCell.classList.add('diff-unchanged');
            leftContentCell.classList.add('diff-unchanged');
            rightLineNumCell.classList.add('diff-moved');
            rightContentCell.classList.add('diff-moved');
            
            if (isMarkdown) {
                rightContentCell.classList.add('markdown-rendered');
            }
            
            // Don't increment movedCount again since we counted in moved-from
        }
        
        row.appendChild(leftLineNumCell);
        row.appendChild(leftContentCell);
        row.appendChild(rightLineNumCell);
        row.appendChild(rightContentCell);
        table.appendChild(row);
    });
    
    diffContent.innerHTML = '';
    diffContent.appendChild(table);
    
    // Update stats
    let statsText = '';
    if (addedCount > 0) statsText += `${addedCount} additions`;
    if (removedCount > 0) {
        if (statsText) statsText += ', ';
        statsText += `${removedCount} deletions`;
    }
    if (modifiedCount > 0) {
        if (statsText) statsText += ', ';
        statsText += `${modifiedCount} modifications`;
    }
    if (movedCount > 0) {
        if (statsText) statsText += ', ';
        statsText += `${movedCount} moves`;
    }
    if (!statsText) statsText = 'No changes';
    
    statsDiv.textContent = statsText;
}

/**
 * Update the diff display based on current input
 */
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
        // Use hybrid diff that combines structural analysis with patience algorithm
        const diff = hybridDiff(draft1, draft2);
        renderDiff(diff);
    }, 100);
}

/**
 * Debounced update function for input events
 */
let timeoutId;
function debouncedUpdate() {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(updateDiff, 1000);
}

/**
 * Initialize event listeners when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners for input changes
    document.getElementById('draft1').addEventListener('blur', updateDiff);
    document.getElementById('draft2').addEventListener('blur', updateDiff);
    
    // Add markdown toggle listener
    document.getElementById('markdownToggle').addEventListener('change', updateDiff);
    
    // Add debounced input listeners for better UX
    document.getElementById('draft1').addEventListener('input', debouncedUpdate);
    document.getElementById('draft2').addEventListener('input', debouncedUpdate);
});