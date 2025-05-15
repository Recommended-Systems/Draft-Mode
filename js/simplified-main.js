// simplified-main.js
// Simplified main application logic

class BlogDiffApp {
    constructor() {
        this.engine = new SimplifiedDiffEngine();
        this.debounceTimeout = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.render();
    }

    bindEvents() {
        const draft1 = document.getElementById('draft1');
        const draft2 = document.getElementById('draft2');
        const markdownToggle = document.getElementById('markdownToggle');

        // Debounced input handler
        const handleInput = () => {
            clearTimeout(this.debounceTimeout);
            this.debounceTimeout = setTimeout(() => this.updateDiff(), 300);
        };

        // Immediate update on blur for better responsiveness
        const handleBlur = () => {
            clearTimeout(this.debounceTimeout);
            this.updateDiff();
        };

        draft1.addEventListener('input', handleInput);
        draft1.addEventListener('blur', handleBlur);
        draft2.addEventListener('input', handleInput);
        draft2.addEventListener('blur', handleBlur);
        markdownToggle.addEventListener('change', () => this.updateDiff());
    }

    updateDiff() {
        const draft1 = document.getElementById('draft1').value.trim();
        const draft2 = document.getElementById('draft2').value.trim();
        const diffContainer = document.getElementById('diffContainer');

        if (!draft1 && !draft2) {
            diffContainer.style.display = 'none';
            return;
        }

        diffContainer.style.display = 'block';

        if (!draft1 || !draft2) {
            this.showPlaceholder();
            return;
        }

        // Show loading briefly for better UX
        this.showLoading();

        // Use setTimeout to avoid blocking UI
        setTimeout(() => {
            const result = this.engine.diff(draft1, draft2);
            this.render(result);
        }, 50);
    }

    showPlaceholder() {
        const content = document.getElementById('diffContent');
        const stats = document.getElementById('diffStats');
        
        content.innerHTML = '<div class="diff-placeholder">Please paste both drafts to see differences</div>';
        stats.textContent = 'No differences';
    }

    showLoading() {
        const content = document.getElementById('diffContent');
        content.innerHTML = '<div class="loading">Computing differences...</div>';
    }

    render(result) {
        if (!result) return;

        const { diff, structuralChanges } = result;
        this.renderDiff(diff);
        this.updateStats(diff);
        
        if (structuralChanges) {
            this.renderStructuralSummary(structuralChanges);
        }
    }

    renderDiff(diff) {
        const content = document.getElementById('diffContent');
        const isMarkdown = document.getElementById('markdownToggle').checked;
        
        if (!diff || diff.length === 0) {
            content.innerHTML = '<div class="diff-placeholder">No differences found</div>';
            return;
        }

        const table = document.createElement('table');
        table.className = 'diff-table';

        // Header
        const header = document.createElement('tr');
        header.className = 'diff-header-row';
        header.innerHTML = `
            <th class="diff-header-cell" colspan="2">Original</th>
            <th class="diff-header-cell" colspan="2">Updated</th>
        `;
        table.appendChild(header);

        let leftLineNum = 1;
        let rightLineNum = 1;

        diff.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'diff-row';

            const cells = {
                leftNum: document.createElement('td'),
                leftContent: document.createElement('td'),
                rightNum: document.createElement('td'),
                rightContent: document.createElement('td')
            };

            // Set cell classes
            Object.values(cells).forEach(cell => {
                cell.className = 'diff-line-cell';
            });
            cells.leftNum.classList.add('line-number');
            cells.leftContent.classList.add('line-content');
            cells.rightNum.classList.add('line-number');
            cells.rightContent.classList.add('line-content');

            switch (item.type) {
                case 'unchanged':
                    cells.leftNum.textContent = leftLineNum++;
                    cells.rightNum.textContent = rightLineNum++;
                    cells.leftContent.innerHTML = this.processContent(item.line1, isMarkdown);
                    cells.rightContent.innerHTML = this.processContent(item.line2, isMarkdown);
                    this.addTypeClasses(cells, 'unchanged');
                    break;

                case 'removed':
                    cells.leftNum.textContent = leftLineNum++;
                    cells.rightNum.innerHTML = '&nbsp;';
                    cells.leftContent.innerHTML = this.processContent(item.line1, isMarkdown);
                    cells.rightContent.innerHTML = '&nbsp;';
                    this.addTypeClasses(cells, 'removed');
                    break;

                case 'added':
                    cells.leftNum.innerHTML = '&nbsp;';
                    cells.rightNum.textContent = rightLineNum++;
                    cells.leftContent.innerHTML = '&nbsp;';
                    cells.rightContent.innerHTML = this.processContent(item.line2, isMarkdown);
                    this.addTypeClasses(cells, 'added');
                    break;

                case 'modified':
                    cells.leftNum.textContent = leftLineNum++;
                    cells.rightNum.textContent = rightLineNum++;
                    cells.leftContent.innerHTML = this.processContent(item.leftDiff, isMarkdown, true);
                    cells.rightContent.innerHTML = this.processContent(item.rightDiff, isMarkdown, true);
                    this.addTypeClasses(cells, 'modified');
                    break;
            }

            if (isMarkdown) {
                cells.leftContent.classList.add('markdown-rendered');
                cells.rightContent.classList.add('markdown-rendered');
            }

            row.append(cells.leftNum, cells.leftContent, cells.rightNum, cells.rightContent);
            table.appendChild(row);
        });

        content.innerHTML = '';
        content.appendChild(table);
    }

    addTypeClasses(cells, type) {
        const leftClasses = ['diff-' + type];
        const rightClasses = ['diff-' + (type === 'removed' ? 'unchanged' : type)];

        cells.leftNum.classList.add(...leftClasses);
        cells.leftContent.classList.add(...leftClasses);
        cells.rightNum.classList.add(...rightClasses);
        cells.rightContent.classList.add(...rightClasses);
    }

    processContent(content, isMarkdown, hasHighlights = false) {
        if (!content) return '';

        if (hasHighlights) {
            if (isMarkdown) {
                // Preserve highlights while rendering markdown
                const parts = content.split(/(<span[^>]*>[^<]*<\/span>)/);
                return parts.map(part => 
                    part.startsWith('<span') ? part : this.renderMarkdown(part)
                ).join('');
            }
            return content;
        }

        return isMarkdown ? this.renderMarkdown(content) : content;
    }

    // Lightweight markdown renderer
    renderMarkdown(text) {
        if (!text) return '';
        
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/^(#{1,6})\s+(.+)$/gm, (match, hashes, text) => 
                `<h${hashes.length}>${text}</h${hashes.length}>`)
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/`(.+?)`/g, '<code>$1</code>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>')
            .replace(/!\[(.+?)\]\((.+?)\)/g, '<img src="$2" alt="$1" style="max-width: 100%;">')
            .replace(/^[*+-]\s(.+)$/gm, '<li>$1</li>')
            .replace(/^\d+\.\s(.+)$/gm, '<li>$1</li>')
            .replace(/^>\s(.+)$/gm, '<blockquote>$1</blockquote>')
            .replace(/^[-*_]{3,}$/gm, '<hr>');
    }

    updateStats(diff) {
        const stats = document.getElementById('diffStats');
        const counts = {
            added: 0,
            removed: 0,
            modified: 0
        };

        diff.forEach(item => {
            if (counts.hasOwnProperty(item.type)) {
                counts[item.type]++;
            }
        });

        const parts = [];
        if (counts.added > 0) parts.push(`${counts.added} additions`);
        if (counts.removed > 0) parts.push(`${counts.removed} deletions`);
        if (counts.modified > 0) parts.push(`${counts.modified} modifications`);

        stats.textContent = parts.length > 0 ? parts.join(', ') : 'No changes';
    }

    renderStructuralSummary(changes) {
        const content = document.getElementById('diffContent');
        const { overall } = changes;
        
        if (overall.headerChanges === 0 && overall.listChanges === 0 && overall.codeChanges === 0) {
            return;
        }

        const summary = document.createElement('div');
        summary.className = 'structural-summary';
        summary.innerHTML = '<h3>Structural Changes</h3>';

        if (overall.headerChanges > 0) {
            const div = document.createElement('div');
            div.className = 'structural-change-summary';
            div.innerHTML = `<strong>Headers:</strong> ${overall.headerChanges} changes`;
            summary.appendChild(div);
        }

        if (overall.listChanges > 0) {
            const div = document.createElement('div');
            div.className = 'structural-change-summary';
            div.innerHTML = `<strong>Lists:</strong> ${overall.listChanges} changes`;
            summary.appendChild(div);
        }

        if (overall.codeChanges > 0) {
            const div = document.createElement('div');
            div.className = 'structural-change-summary';
            div.innerHTML = `<strong>Code blocks:</strong> ${overall.codeChanges} changes`;
            summary.appendChild(div);
        }

        content.insertBefore(summary, content.firstChild);
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new BlogDiffApp();
});