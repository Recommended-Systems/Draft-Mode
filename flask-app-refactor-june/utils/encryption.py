"""
Encryption utilities for securing sensitive data like API keys
Uses Fernet (symmetric encryption) from cryptography library
"""
from cryptography.fernet import Fernet
from flask import current_app
import base64
import os

def get_encryption_key():
    """
    Get encryption key from environment or config
    Generate one if it doesn't exist (for development)

    IMPORTANT: In production, ENCRYPTION_KEY should be set in environment
    """
    key = current_app.config.get('ENCRYPTION_KEY')

    if not key:
        # Development fallback - generate a key
        # WARNING: This means data encrypted with one key can't be decrypted
        # if the server restarts. For production, ALWAYS set ENCRYPTION_KEY
        key = Fernet.generate_key().decode()
        current_app.logger.warning(
            "ENCRYPTION_KEY not set in config. Using generated key. "
            "Data will be lost on restart. SET ENCRYPTION_KEY in production!"
        )

    if isinstance(key, str):
        key = key.encode()

    return key

def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage

    Args:
        api_key: Plain text API key

    Returns:
        Encrypted API key as string
    """
    if not api_key:
        raise ValueError("API key cannot be empty")

    encryption_key = get_encryption_key()
    f = Fernet(encryption_key)

    # Encrypt and return as string
    encrypted = f.encrypt(api_key.encode())
    return encrypted.decode()

def decrypt_api_key(encrypted_api_key: str) -> str:
    """
    Decrypt an API key for use

    Args:
        encrypted_api_key: Encrypted API key string

    Returns:
        Plain text API key

    Raises:
        ValueError: If decryption fails (wrong key or corrupted data)
    """
    if not encrypted_api_key:
        raise ValueError("Encrypted API key cannot be empty")

    try:
        encryption_key = get_encryption_key()
        f = Fernet(encryption_key)

        # Decrypt and return as string
        decrypted = f.decrypt(encrypted_api_key.encode())
        return decrypted.decode()
    except Exception as e:
        current_app.logger.error(f"Failed to decrypt API key: {e}")
        raise ValueError("Failed to decrypt API key. The encryption key may have changed.")
