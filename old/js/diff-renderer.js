// diff-renderer.js
// Handles rendering of diffs in the UI

function renderDiff(diff, structuralChanges = null) {
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
        } else if (item.type === 'moved') {
            // Handle moved content (from patience diff)
            leftLineNumCell.textContent = leftLineNum++;
            rightLineNumCell.textContent = rightLineNum++;
            
            leftContentCell.innerHTML = processContentForDisplay(item.line1, isMarkdown);
            rightContentCell.innerHTML = processContentForDisplay(item.line2, isMarkdown);
            
            // Special styling for moved content
            leftLineNumCell.classList.add('diff-moved');
            leftContentCell.classList.add('diff-moved');
            rightLineNumCell.classList.add('diff-moved');
            rightContentCell.classList.add('diff-moved');
            
            // Add move indicator
            leftContentCell.setAttribute('data-move-info', `Moved from line ${item.from + 1}`);
            rightContentCell.setAttribute('data-move-info', `Moved to line ${item.to + 1}`);
            
            if (isMarkdown) {
                leftContentCell.classList.add('markdown-rendered');
                rightContentCell.classList.add('markdown-rendered');
            }
            
            movedCount++;
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
        statsText += `${movedCount} moved`;
    }
    if (!statsText) statsText = 'No changes';
    
    statsDiv.textContent = statsText;
    
    // If structural changes exist, show them
    if (structuralChanges) {
        renderStructuralChanges(structuralChanges);
    }
}

function renderStructuralChanges(structuralChanges) {
    const diffContent = document.getElementById('diffContent');
    
    // Create a summary of structural changes above the diff
    const summaryDiv = document.createElement('div');
    summaryDiv.className = 'structural-summary';
    summaryDiv.innerHTML = '<h3>Structural Changes Summary</h3>';
    
    if (structuralChanges.overall.headerChanges > 0) {
        const headerSummary = document.createElement('div');
        headerSummary.className = 'structural-change-summary';
        headerSummary.innerHTML = `<strong>Headers:</strong> ${structuralChanges.overall.headerChanges} changes`;
        summaryDiv.appendChild(headerSummary);
    }
    
    if (structuralChanges.overall.listChanges > 0) {
        const listSummary = document.createElement('div');
        listSummary.className = 'structural-change-summary';
        listSummary.innerHTML = `<strong>Lists:</strong> ${structuralChanges.overall.listChanges} changes`;
        summaryDiv.appendChild(listSummary);
    }
    
    if (structuralChanges.overall.codeChanges > 0) {
        const codeSummary = document.createElement('div');
        codeSummary.className = 'structural-change-summary';
        codeSummary.innerHTML = `<strong>Code blocks:</strong> ${structuralChanges.overall.codeChanges} changes`;
        summaryDiv.appendChild(codeSummary);
    }
    
    // Only show if there are structural changes
    if (structuralChanges.overall.headerChanges > 0 || 
        structuralChanges.overall.listChanges > 0 || 
        structuralChanges.overall.codeChanges > 0) {
        diffContent.insertBefore(summaryDiv, diffContent.firstChild);
    }
}