"""Input validation utilities"""
import re
import bleach


def sanitize_text_input(text, max_length=None):
    """
    Sanitize text input by stripping whitespace and removing null bytes

    Args:
        text (str): Input text
        max_length (int): Optional maximum length

    Returns:
        str: Sanitized text
    """
    if not text:
        return ''

    # Strip whitespace
    text = text.strip()

    # Remove null bytes
    text = text.replace('\x00', '')

    # Remove other control characters except newlines and tabs
    text = ''.join(char for char in text if char == '\n' or char == '\t' or not (0 <= ord(char) < 32))

    # Limit length if specified
    if max_length:
        text = text[:max_length]

    return text


def sanitize_html_input(text):
    """
    Remove all HTML tags from input

    Args:
        text (str): Input text that may contain HTML

    Returns:
        str: Text with all HTML removed
    """
    if not text:
        return ''

    return bleach.clean(text, tags=[], strip=True)


def validate_email(email):
    """
    Validate email format

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if email is valid format
    """
    if not email:
        return False

    # Basic email regex pattern
    # This is a simple pattern - for production, consider using email-validator library
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    return bool(re.match(pattern, email))


def validate_name(name):
    """
    Validate user name

    Args:
        name (str): Name to validate

    Returns:
        tuple: (is_valid: bool, error: str or None)
    """
    if not name:
        return False, "Name is required"

    name = sanitize_text_input(name)

    if len(name) < 2:
        return False, "Name must be at least 2 characters"

    if len(name) > 100:
        return False, "Name must be less than 100 characters"

    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"

    return True, None


def validate_draft_title(title):
    """
    Validate draft title

    Args:
        title (str): Draft title to validate

    Returns:
        tuple: (is_valid: bool, error: str or None)
    """
    if not title:
        return False, "Title is required"

    title = sanitize_text_input(title)

    if len(title) < 1:
        return False, "Title cannot be empty"

    if len(title) > 200:
        return False, "Title must be less than 200 characters"

    return True, None


def validate_version_name(version_name):
    """
    Validate version name

    Args:
        version_name (str): Version name to validate

    Returns:
        tuple: (is_valid: bool, error: str or None)
    """
    if not version_name:
        return False, "Version name is required"

    version_name = sanitize_text_input(version_name)

    if len(version_name) < 1:
        return False, "Version name cannot be empty"

    if len(version_name) > 100:
        return False, "Version name must be less than 100 characters"

    return True, None


def validate_description(description, max_length=500):
    """
    Validate description text

    Args:
        description (str): Description to validate
        max_length (int): Maximum allowed length

    Returns:
        tuple: (is_valid: bool, error: str or None)
    """
    if not description:
        return True, None  # Description is optional

    description = sanitize_text_input(description)

    if len(description) > max_length:
        return False, f"Description must be less than {max_length} characters"

    return True, None


def validate_url(url):
    """
    Validate URL format

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid format
    """
    if not url:
        return False

    # Basic URL pattern
    pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=]+$'

    return bool(re.match(pattern, url))


def sanitize_filename(filename):
    """
    Sanitize filename to prevent directory traversal

    Args:
        filename (str): Filename to sanitize

    Returns:
        str: Sanitized filename
    """
    if not filename:
        return ''

    # Remove any directory components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove any non-alphanumeric characters except dot, dash, underscore
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def validate_json_input(data, required_fields):
    """
    Validate JSON input has required fields

    Args:
        data (dict): JSON data to validate
        required_fields (list): List of required field names

    Returns:
        tuple: (is_valid: bool, missing_fields: list)
    """
    if not data:
        return False, required_fields

    missing_fields = [field for field in required_fields if field not in data]

    return len(missing_fields) == 0, missing_fields
