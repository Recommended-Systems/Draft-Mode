// Text Selection Toolbar for Draft Mode Editor
class TextSelectionToolbar {
    constructor(textareaSelector = '#contentEditor') {
        this.textarea = document.querySelector(textareaSelector);
        this.toolbar = null;
        this.isVisible = false;
        this.selectionStart = 0;
        this.selectionEnd = 0;
        this.selectedText = '';
        
        this.init();
    }
    
    init() {
        if (!this.textarea) {
            console.warn('TextSelectionToolbar: Textarea not found');
            return;
        }
        
        this.createToolbar();
        this.attachEventListeners();
    }
    
    createToolbar() {
        this.toolbar = document.createElement('div');
        this.toolbar.id = 'textSelectionToolbar';
        this.toolbar.className = 'text-selection-toolbar';
        this.toolbar.style.display = 'none';
        
        const buttons = [
            { id: 'bold', icon: '𝐁', title: 'Bold (Ctrl+B)', action: () => this.formatText('bold') },
            { id: 'italic', icon: '𝐼', title: 'Italic (Ctrl+I)', action: () => this.formatText('italic') },
            { id: 'code', icon: '&lt;/&gt;', title: 'Inline Code', action: () => this.formatText('code') },
            { id: 'separator1', type: 'separator' },
            { id: 'h1', icon: 'H1', title: 'Heading 1', action: () => this.formatText('h1') },
            { id: 'h2', icon: 'H2', title: 'Heading 2', action: () => this.formatText('h2') },
            { id: 'h3', icon: 'H3', title: 'Heading 3', action: () => this.formatText('h3') },
            { id: 'separator2', type: 'separator' },
            { id: 'bullet', icon: '•', title: 'Bullet List', action: () => this.formatText('bullet') },
            { id: 'number', icon: '1.', title: 'Numbered List', action: () => this.formatText('number') },
            { id: 'quote', icon: '❝', title: 'Quote', action: () => this.formatText('quote') },
            { id: 'separator3', type: 'separator' },
            { id: 'link', icon: '🔗', title: 'Link', action: () => this.formatText('link') },
            { id: 'codeblock', icon: '{ }', title: 'Code Block', action: () => this.formatText('codeblock') }
        ];
        
        buttons.forEach(button => {
            if (button.type === 'separator') {
                const separator = document.createElement('div');
                separator.className = 'toolbar-separator';
                this.toolbar.appendChild(separator);
            } else {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'toolbar-btn';
                btn.title = button.title;
                btn.innerHTML = button.icon;
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    button.action();
                });
                this.toolbar.appendChild(btn);
            }
        });
        
        // Add styles
        this.addStyles();
        
        // Add to body
        document.body.appendChild(this.toolbar);
    }
    
    addStyles() {
        const styleId = 'textSelectionToolbarStyles';
        if (document.getElementById(styleId)) return;
        
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
            .text-selection-toolbar {
                position: absolute;
                z-index: 10000;
                background: var(--bg-secondary);
                border: 2px solid var(--border-primary);
                border-radius: 0;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                display: flex;
                align-items: center;
                gap: 2px;
                padding: 4px;
                font-family: 'JetBrains Mono', monospace;
                user-select: none;
                backdrop-filter: blur(10px);
                animation: toolbarFadeIn 0.2s ease-out;
            }
            
            [data-theme="dark"] .text-selection-toolbar {
                box-shadow: 0 4px 12px rgba(0, 255, 65, 0.2), 
                           inset 0 1px 0 var(--border-secondary);
            }
            
            @keyframes toolbarFadeIn {
                from {
                    opacity: 0;
                    transform: translateY(-8px) scale(0.95);
                }
                to {
                    opacity: 1;
                    transform: translateY(0) scale(1);
                }
            }
            
            .toolbar-btn {
                background: var(--bg-tertiary);
                border: 1px solid var(--border-primary);
                color: var(--text-primary);
                padding: 8px 10px;
                font-family: inherit;
                font-size: 11px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.15s ease;
                min-width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                position: relative;
                overflow: hidden;
            }
            
            .toolbar-btn:hover {
                background: var(--accent-green);
                color: var(--bg-primary);
                border-color: var(--accent-green);
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0, 255, 65, 0.3);
            }
            
            [data-theme="light"] .toolbar-btn:hover {
                color: #ffffff;
                box-shadow: 0 2px 4px rgba(40, 167, 69, 0.3);
            }
            
            .toolbar-btn:active {
                transform: translateY(0);
                box-shadow: none;
            }
            
            .toolbar-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s ease;
            }
            
            .toolbar-btn:hover::before {
                left: 100%;
            }
            
            .toolbar-separator {
                width: 1px;
                height: 24px;
                background: var(--border-primary);
                margin: 0 4px;
                opacity: 0.5;
            }
            
            /* Special button styles */
            .toolbar-btn[title*="Heading"] {
                font-family: inherit;
                font-weight: 700;
                font-size: 9px;
                letter-spacing: 0.5px;
            }
            
            .toolbar-btn[title*="Bold"] {
                font-weight: 900;
            }
            
            .toolbar-btn[title*="Italic"] {
                font-style: italic;
                font-weight: 700;
            }
            
            .toolbar-btn[title*="Code"] {
                font-family: 'JetBrains Mono', monospace;
                font-size: 10px;
            }
            
            /* Responsive adjustments */
            @media (max-width: 768px) {
                .text-selection-toolbar {
                    flex-wrap: wrap;
                    max-width: 280px;
                    padding: 6px;
                }
                
                .toolbar-btn {
                    min-width: 36px;
                    height: 36px;
                    font-size: 12px;
                }
                
                .toolbar-separator {
                    display: none;
                }
            }
        `;
        
        document.head.appendChild(style);
    }
    
    attachEventListeners() {
        // Selection events
        this.textarea.addEventListener('mouseup', (e) => this.handleSelection(e));
        this.textarea.addEventListener('keyup', (e) => this.handleSelection(e));
        this.textarea.addEventListener('touchend', (e) => this.handleSelection(e));
        
        // Hide toolbar when clicking elsewhere
        document.addEventListener('mousedown', (e) => {
            if (!this.toolbar.contains(e.target) && e.target !== this.textarea) {
                this.hideToolbar();
            }
        });
        
        // Hide on scroll
        window.addEventListener('scroll', () => this.hideToolbar());
        
        // Hide on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideToolbar();
            }
        });
        
        // Keyboard shortcuts
        this.textarea.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'b':
                        e.preventDefault();
                        this.formatText('bold');
                        break;
                    case 'i':
                        e.preventDefault();
                        this.formatText('italic');
                        break;
                }
            }
        });
    }
    
    handleSelection(e) {
        setTimeout(() => {
            const start = this.textarea.selectionStart;
            const end = this.textarea.selectionEnd;
            const selectedText = this.textarea.value.substring(start, end);
            
            if (selectedText.length > 0 && selectedText.trim().length > 0) {
                this.selectionStart = start;
                this.selectionEnd = end;
                this.selectedText = selectedText;
                this.showToolbar();
            } else {
                this.hideToolbar();
            }
        }, 10);
    }
    
    showToolbar() {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.toolbar.style.display = 'flex';
        
        // Position the toolbar
        this.positionToolbar();
        
        // Trigger fade-in animation
        this.toolbar.style.animation = 'toolbarFadeIn 0.2s ease-out';
    }
    
    hideToolbar() {
        if (!this.isVisible) return;
        
        this.isVisible = false;
        this.toolbar.style.display = 'none';
    }
    
    positionToolbar() {
        const textareaRect = this.textarea.getBoundingClientRect();
        const toolbarRect = this.toolbar.getBoundingClientRect();
        
        // Calculate position based on selection
        const textMetrics = this.getSelectionCoordinates();
        
        let left = textMetrics.left - (toolbarRect.width / 2);
        let top = textMetrics.top - toolbarRect.height - 10;
        
        // Adjust if toolbar would go outside viewport
        const margin = 10;
        
        if (left < margin) {
            left = margin;
        } else if (left + toolbarRect.width > window.innerWidth - margin) {
            left = window.innerWidth - toolbarRect.width - margin;
        }
        
        if (top < margin) {
            // Show below selection if no room above
            top = textMetrics.bottom + 10;
        }
        
        this.toolbar.style.left = `${left}px`;
        this.toolbar.style.top = `${top}px`;
    }
    
    getSelectionCoordinates() {
        // Create a temporary div to measure text position
        const div = document.createElement('div');
        const style = getComputedStyle(this.textarea);
        
        // Copy textarea styles to div
        div.style.position = 'absolute';
        div.style.visibility = 'hidden';
        div.style.whiteSpace = 'pre-wrap';
        div.style.wordWrap = 'break-word';
        div.style.font = style.font;
        div.style.padding = style.padding;
        div.style.border = style.border;
        div.style.width = style.width;
        div.style.height = style.height;
        div.style.overflow = 'hidden';
        
        document.body.appendChild(div);
        
        const textBeforeSelection = this.textarea.value.substring(0, this.selectionStart);
        const selectedText = this.textarea.value.substring(this.selectionStart, this.selectionEnd);
        
        div.textContent = textBeforeSelection;
        const beforeSpan = document.createElement('span');
        beforeSpan.textContent = selectedText;
        div.appendChild(beforeSpan);
        
        const textareaRect = this.textarea.getBoundingClientRect();
        const spanRect = beforeSpan.getBoundingClientRect();
        const divRect = div.getBoundingClientRect();
        
        const coordinates = {
            left: textareaRect.left + (spanRect.left - divRect.left),
            top: textareaRect.top + (spanRect.top - divRect.top),
            bottom: textareaRect.top + (spanRect.bottom - divRect.top)
        };
        
        document.body.removeChild(div);
        
        return coordinates;
    }
    
    formatText(format) {
        const text = this.selectedText;
        let formattedText = '';
        let newSelectionStart = this.selectionStart;
        let newSelectionEnd = this.selectionEnd;
        
        // Get expanded context around selection for smart formatting
        const fullText = this.textarea.value;
        const contextStart = Math.max(0, this.selectionStart - 10);
        const contextEnd = Math.min(fullText.length, this.selectionEnd + 10);
        const beforeContext = fullText.substring(contextStart, this.selectionStart);
        const afterContext = fullText.substring(this.selectionEnd, contextEnd);
        
        switch (format) {
            case 'bold':
                const result = this.toggleInlineFormat(text, beforeContext, afterContext, '**');
                formattedText = result.text;
                newSelectionStart = this.selectionStart + result.startOffset;
                newSelectionEnd = this.selectionEnd + result.endOffset;
                break;
                
            case 'italic':
                const italicResult = this.toggleInlineFormat(text, beforeContext, afterContext, '*');
                formattedText = italicResult.text;
                newSelectionStart = this.selectionStart + italicResult.startOffset;
                newSelectionEnd = this.selectionEnd + italicResult.endOffset;
                break;
                
            case 'code':
                const codeResult = this.toggleInlineFormat(text, beforeContext, afterContext, '`');
                formattedText = codeResult.text;
                newSelectionStart = this.selectionStart + codeResult.startOffset;
                newSelectionEnd = this.selectionEnd + codeResult.endOffset;
                break;
                
            case 'h1':
                formattedText = this.formatHeading(text, 1);
                break;
                
            case 'h2':
                formattedText = this.formatHeading(text, 2);
                break;
                
            case 'h3':
                formattedText = this.formatHeading(text, 3);
                break;
                
            case 'bullet':
                formattedText = this.formatList(text, '- ');
                break;
                
            case 'number':
                formattedText = this.formatList(text, '1. ');
                break;
                
            case 'quote':
                formattedText = this.formatBlockquote(text);
                break;
                
            case 'link':
                formattedText = this.formatLink(text);
                newSelectionStart = this.selectionStart + text.length + 3;
                newSelectionEnd = newSelectionStart + 3; // Select "url"
                break;
                
            case 'codeblock':
                formattedText = this.formatCodeBlock(text);
                break;
                
            default:
                formattedText = text;
        }
        
        this.replaceSelectionWithUndo(formattedText, newSelectionStart, newSelectionEnd);
        this.hideToolbar();
    }
    
    toggleInlineFormat(text, beforeContext, afterContext, marker) {
        const markerLength = marker.length;
        
        // Check if the selection is already wrapped with this marker
        const isWrapped = beforeContext.endsWith(marker) && afterContext.startsWith(marker);
        
        // Check if the text itself contains the marker at start/end
        const textStartsWithMarker = text.startsWith(marker);
        const textEndsWithMarker = text.endsWith(marker);
        const isSelfWrapped = textStartsWithMarker && textEndsWithMarker && text.length > markerLength * 2;
        
        if (isWrapped) {
            // Remove surrounding markers from context
            return {
                text: text,
                startOffset: -markerLength, // We'll remove marker before selection
                endOffset: -markerLength    // We'll remove marker after selection
            };
        } else if (isSelfWrapped) {
            // Remove markers from the selected text itself
            const unwrapped = text.substring(markerLength, text.length - markerLength);
            return {
                text: unwrapped,
                startOffset: 0,
                endOffset: -(markerLength * 2) // Text got shorter by 2 * marker length
            };
        } else {
            // Add markers
            return {
                text: `${marker}${text}${marker}`,
                startOffset: markerLength,
                endOffset: markerLength
            };
        }
    }
    
    formatHeading(text, level) {
        const prefix = '#'.repeat(level) + ' ';
        const lines = text.split('\n');
        return lines.map(line => {
            const trimmed = line.trim();
            // Remove existing heading markers
            const cleaned = trimmed.replace(/^#+\s*/, '');
            return cleaned ? prefix + cleaned : line;
        }).join('\n');
    }
    
    formatList(text, marker) {
        const lines = text.split('\n');
        return lines.map(line => {
            const trimmed = line.trim();
            if (!trimmed) return line;
            
            // Remove existing list markers
            const cleaned = trimmed.replace(/^(\d+\.\s*|\-\s*|\*\s*|\+\s*)/, '');
            return marker + cleaned;
        }).join('\n');
    }
    
    formatBlockquote(text) {
        const lines = text.split('\n');
        return lines.map(line => {
            const trimmed = line.trim();
            if (!trimmed) return line;
            
            // Remove existing blockquote markers
            const cleaned = trimmed.replace(/^>\s*/, '');
            return '> ' + cleaned;
        }).join('\n');
    }
    
    formatLink(text) {
        // If text looks like a URL, use it as the URL
        const urlPattern = /^https?:\/\//;
        if (urlPattern.test(text)) {
            return `[Link Text](${text})`;
        }
        return `[${text}](url)`;
    }
    
    formatCodeBlock(text) {
        // Detect language from common patterns
        let language = '';
        if (text.includes('function') || text.includes('const') || text.includes('let')) {
            language = 'javascript';
        } else if (text.includes('def ') || text.includes('import ')) {
            language = 'python';
        } else if (text.includes('#include') || text.includes('int main')) {
            language = 'c';
        }
        
        return `\`\`\`${language}\n${text}\n\`\`\``;
    }
    
    replaceSelectionWithUndo(newText, newSelectionStart, newSelectionEnd) {
        const textarea = this.textarea;
        const start = this.selectionStart;
        const end = this.selectionEnd;
        
        // Store current scroll position
        const scrollTop = textarea.scrollTop;
        const scrollLeft = textarea.scrollLeft;
        
        // For undo support, we need to handle context-aware replacements
        const fullText = textarea.value;
        let actualStart = start;
        let actualEnd = end;
        let actualNewText = newText;
        
        // Check if we need to expand the replacement area (for removing surrounding markers)
        const beforeContext = fullText.substring(Math.max(0, start - 10), start);
        const afterContext = fullText.substring(end, Math.min(fullText.length, end + 10));
        
        // Handle marker removal from context
        if (newSelectionStart < start) {
            const markerLength = start - newSelectionStart;
            if (beforeContext.length >= markerLength) {
                actualStart = start - markerLength;
                actualNewText = newText;
            }
        }
        
        if (newSelectionEnd < end) {
            const markerLength = end - newSelectionEnd;
            if (afterContext.length >= markerLength) {
                actualEnd = end + markerLength;
            }
        }
        
        // Use document.execCommand for undo support when possible
        textarea.focus();
        textarea.setSelectionRange(actualStart, actualEnd);
        
        // Try using execCommand for undo support (works in most browsers)
        let useExecCommand = false;
        try {
            // Check if we can use insertText (best for undo)
            if (document.queryCommandSupported && document.queryCommandSupported('insertText')) {
                useExecCommand = document.execCommand('insertText', false, actualNewText);
            }
        } catch (e) {
            useExecCommand = false;
        }
        
        // Fallback to direct value manipulation if execCommand fails
        if (!useExecCommand) {
            const before = textarea.value.substring(0, actualStart);
            const after = textarea.value.substring(actualEnd);
            textarea.value = before + actualNewText + after;
        }
        
        // Restore scroll position
        textarea.scrollTop = scrollTop;
        textarea.scrollLeft = scrollLeft;
        
        // Set final selection
        const finalStart = actualStart + (newSelectionStart - start);
        const finalEnd = actualStart + actualNewText.length - (actualEnd - end) + (newSelectionEnd - end);
        
        if (newSelectionStart !== undefined && newSelectionEnd !== undefined) {
            textarea.setSelectionRange(Math.max(0, finalStart), Math.max(0, finalEnd));
        } else {
            textarea.setSelectionRange(actualStart, actualStart + actualNewText.length);
        }
        
        // Trigger input event for auto-save and other listeners
        const event = new Event('input', { bubbles: true });
        textarea.dispatchEvent(event);
    }
    
    // Public API methods
    destroy() {
        if (this.toolbar) {
            this.toolbar.remove();
        }
        
        const styles = document.getElementById('textSelectionToolbarStyles');
        if (styles) {
            styles.remove();
        }
    }
    
    enable() {
        this.textarea.addEventListener('mouseup', (e) => this.handleSelection(e));
        this.textarea.addEventListener('keyup', (e) => this.handleSelection(e));
        this.textarea.addEventListener('touchend', (e) => this.handleSelection(e));
    }
    
    disable() {
        this.hideToolbar();
        this.textarea.removeEventListener('mouseup', this.handleSelection);
        this.textarea.removeEventListener('keyup', this.handleSelection);
        this.textarea.removeEventListener('touchend', this.handleSelection);
    }
}

// Auto-initialize if contentEditor exists
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('contentEditor')) {
        window.textSelectionToolbar = new TextSelectionToolbar('#contentEditor');
    }
});

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TextSelectionToolbar;
}