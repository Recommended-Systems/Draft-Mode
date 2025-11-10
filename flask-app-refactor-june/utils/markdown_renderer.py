"""Safe markdown rendering with XSS protection"""
import markdown
import bleach
from markupsafe import Markup


# Allowed HTML tags in rendered markdown
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'del', 'ins',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre',
    'ul', 'ol', 'li',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'hr', 'div', 'span',
    'sup', 'sub'
]

# Allowed HTML attributes for specific tags
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'code': ['class'],  # For syntax highlighting
    'pre': ['class'],
    'div': ['class'],
    'span': ['class'],
    'table': ['class'],
    'th': ['align'],
    'td': ['align']
}

# Allowed URL protocols
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def render_markdown_safe(content, extensions=None):
    """
    Render markdown content safely with XSS protection

    Args:
        content (str): Markdown content to render
        extensions (list): Optional list of markdown extensions

    Returns:
        Markup: Safe HTML content
    """
    if not content:
        return Markup('')

    # Default extensions
    if extensions is None:
        extensions = ['extra', 'codehilite', 'fenced_code', 'tables']

    try:
        # Render markdown to HTML
        html_content = markdown.markdown(
            content,
            extensions=extensions,
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False
                }
            }
        )
    except Exception:
        # Fallback to basic markdown if extensions fail
        html_content = markdown.markdown(content)

    # Sanitize the HTML to prevent XSS
    safe_html = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # Strip disallowed tags instead of escaping
    )

    # Linkify URLs (but safely)
    safe_html = bleach.linkify(
        safe_html,
        callbacks=[],
        skip_tags=['pre', 'code']  # Don't linkify inside code blocks
    )

    return Markup(safe_html)


def preview_markdown(content):
    """
    Preview markdown with syntax highlighting

    Args:
        content (str): Markdown content to preview

    Returns:
        Markup: Safe HTML preview
    """
    return render_markdown_safe(content)


def sanitize_user_input(text, allow_tags=False):
    """
    Sanitize user input to prevent XSS

    Args:
        text (str): User input text
        allow_tags (bool): Whether to allow any HTML tags

    Returns:
        str: Sanitized text
    """
    if not text:
        return ''

    if allow_tags:
        # Allow some basic formatting tags
        return bleach.clean(
            text,
            tags=['b', 'i', 'u', 'em', 'strong'],
            strip=True
        )
    else:
        # Strip all HTML tags
        return bleach.clean(text, tags=[], strip=True)
