"""Password validation utilities"""
import re


# Common passwords to reject (minimal list - in production, use a larger list)
COMMON_PASSWORDS = {
    'password', 'password123', '123456', '12345678', 'qwerty', 'abc123',
    'monkey', '1234567', 'letmein', 'trustno1', 'dragon', 'baseball',
    'iloveyou', 'master', 'sunshine', 'ashley', 'bailey', 'passw0rd',
    'shadow', '123123', '654321', 'superman', 'qazwsx', 'michael',
    'football', 'welcome', 'jesus', 'ninja', 'mustang', 'password1'
}


def validate_password_strength(password):
    """
    Validate password meets security requirements

    Args:
        password (str): The password to validate

    Returns:
        tuple: (is_valid: bool, errors: list of str)
    """
    errors = []

    if not password:
        return False, ["Password is required"]

    # Check minimum length
    if len(password) < 12:
        errors.append("Password must be at least 12 characters long")

    # Check for lowercase letters
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    # Check for uppercase letters
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    # Check for numbers
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")

    # Check for special characters
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]", password):
        errors.append("Password must contain at least one special character (!@#$%^&*...)")

    # Check against common passwords (case-insensitive)
    if password.lower() in COMMON_PASSWORDS:
        errors.append("This password is too common. Please choose a stronger one")

    # Check for sequential characters
    if has_sequential_characters(password):
        errors.append("Password should not contain simple sequential patterns")

    return len(errors) == 0, errors


def has_sequential_characters(password, min_length=3):
    """
    Check if password contains sequential characters like '123', 'abc', etc.

    Args:
        password (str): The password to check
        min_length (int): Minimum length of sequential pattern to detect

    Returns:
        bool: True if sequential characters found
    """
    password_lower = password.lower()

    # Check for sequential numbers
    for i in range(len(password_lower) - min_length + 1):
        try:
            # Check if min_length consecutive characters are sequential numbers
            chars = password_lower[i:i + min_length]
            if chars.isdigit():
                nums = [int(c) for c in chars]
                if all(nums[j] + 1 == nums[j + 1] for j in range(len(nums) - 1)):
                    return True
                # Check reverse sequence
                if all(nums[j] - 1 == nums[j + 1] for j in range(len(nums) - 1)):
                    return True
        except (ValueError, IndexError):
            continue

    # Check for sequential letters
    for i in range(len(password_lower) - min_length + 1):
        chars = password_lower[i:i + min_length]
        if chars.isalpha():
            # Check if consecutive letters in alphabet
            if all(ord(chars[j]) + 1 == ord(chars[j + 1]) for j in range(len(chars) - 1)):
                return True
            # Check reverse alphabetical sequence
            if all(ord(chars[j]) - 1 == ord(chars[j + 1]) for j in range(len(chars) - 1)):
                return True

    return False


def get_password_strength(password):
    """
    Calculate password strength score

    Args:
        password (str): The password to evaluate

    Returns:
        dict: {
            'score': int (0-100),
            'strength': str ('weak', 'fair', 'good', 'strong', 'very strong'),
            'feedback': list of str
        }
    """
    score = 0
    feedback = []

    if not password:
        return {'score': 0, 'strength': 'weak', 'feedback': ['Password is empty']}

    # Length scoring
    length = len(password)
    if length >= 12:
        score += 20
        if length >= 16:
            score += 10
            feedback.append("Good length")
        if length >= 20:
            score += 10
    else:
        feedback.append(f"Too short (minimum 12 characters, you have {length})")

    # Character variety scoring
    has_lower = bool(re.search(r"[a-z]", password))
    has_upper = bool(re.search(r"[A-Z]", password))
    has_digit = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=\[\]\\\/;'`~]", password))

    variety_count = sum([has_lower, has_upper, has_digit, has_special])

    if variety_count == 4:
        score += 30
        feedback.append("Good character variety")
    elif variety_count == 3:
        score += 20
    elif variety_count == 2:
        score += 10
        feedback.append("Add more character types for better security")
    else:
        feedback.append("Use a mix of letters, numbers, and symbols")

    # Check for common passwords
    if password.lower() not in COMMON_PASSWORDS:
        score += 15
    else:
        feedback.append("This is a commonly used password")

    # Check for sequential patterns
    if not has_sequential_characters(password):
        score += 15
    else:
        feedback.append("Avoid sequential patterns")

    # Entropy check (unique characters)
    unique_chars = len(set(password))
    if unique_chars / length > 0.7:  # High uniqueness
        score += 10
    elif unique_chars / length < 0.4:  # Low uniqueness (too much repetition)
        feedback.append("Try using more varied characters")

    # Determine strength label
    if score >= 80:
        strength = 'very strong'
    elif score >= 65:
        strength = 'strong'
    elif score >= 50:
        strength = 'good'
    elif score >= 30:
        strength = 'fair'
    else:
        strength = 'weak'

    return {
        'score': min(score, 100),
        'strength': strength,
        'feedback': feedback
    }
