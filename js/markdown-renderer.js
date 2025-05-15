// markdown-renderer.js
// Simple markdown renderer that safely handles HTML entities

// Simple markdown renderer
function renderMarkdown(text) {
    if (!text) return '';
    
    // First, escape any existing HTML to prevent double-rendering
    text = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    return text
        // Headers
        .replace(/^(#{6})\s(.+)$/gm, '<h6>$2</h6>')
        .replace(/^(#{5})\s(.+)$/gm, '<h5>$2</h5>')
        .replace(/^(#{4})\s(.+)$/gm, '<h4>$2</h4>')
        .replace(/^(#{3})\s(.+)$/gm, '<h3>$2</h3>')
        .replace(/^(#{2})\s(.+)$/gm, '<h2>$2</h2>')
        .replace(/^(#{1})\s(.+)$/gm, '<h1>$2</h1>')
        // Bold and italic
        .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Code blocks - handle these before inline code
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        // Inline code
        .replace(/`(.+?)`/g, '<code>$1</code>')
        // Links
        .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2">$1</a>')
        // Images
        .replace(/!\[(.+?)\]\((.+?)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; height: auto;">')
        // Lists - basic support
        .replace(/^\* (.+)$/gm, '<li>$1</li>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        .replace(/^\+ (.+)$/gm, '<li>$1</li>')
        .replace(/^(\d+)\. (.+)$/gm, '<li>$1. $2</li>')
        // Quotes
        .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
        // Horizontal rules
        .replace(/^[-*_]{3,}$/gm, '<hr>');
}

// Process content for display with or without markdown
function processContentForDisplay(content, isMarkdown, hasHighlights = false) {
    if (!content) return '';
    
    // If we have highlights (word/char diffs), we need to preserve them
    if (hasHighlights) {
        if (isMarkdown) {
            // For markdown with highlights, we need to be more careful
            // Split by spans to preserve them while rendering markdown in between
            const parts = content.split(/(<span[^>]*>[^<]*<\/span>)/);
            return parts.map(part => {
                if (part.startsWith('<span')) {
                    return part; // Keep spans as-is
                } else {
                    return renderMarkdown(part);
                }
            }).join('');
        } else {
            return content; // Return as-is with highlights
        }
    }
    
    // No highlights - safe to render markdown if requested
    return isMarkdown ? renderMarkdown(content) : content;
}