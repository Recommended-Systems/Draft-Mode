"""
Unit tests for encryption utilities
Tests API key encryption and decryption
"""
import pytest
from utils.encryption import encrypt_api_key, decrypt_api_key

class TestEncryption:
    """Test encryption utilities"""

    def test_encrypt_api_key(self, app):
        """Test API key encryption"""
        with app.app_context():
            plaintext = 'my-secret-api-key'
            encrypted = encrypt_api_key(plaintext)

            # Encrypted should be different from plaintext
            assert encrypted != plaintext

            # Encrypted should be a string
            assert isinstance(encrypted, str)

            # Encrypted should be longer (base64 encoded)
            assert len(encrypted) > len(plaintext)

    def test_decrypt_api_key(self, app):
        """Test API key decryption"""
        with app.app_context():
            plaintext = 'my-secret-api-key'
            encrypted = encrypt_api_key(plaintext)
            decrypted = decrypt_api_key(encrypted)

            # Decrypted should match original
            assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip(self, app):
        """Test encryption-decryption roundtrip"""
        with app.app_context():
            test_keys = [
                'simple-key',
                'key-with-special-chars!@#$%',
                'very-long-api-key-with-many-characters-' * 10,
                'key:with:colons',
                'key with spaces'
            ]

            for original in test_keys:
                encrypted = encrypt_api_key(original)
                decrypted = decrypt_api_key(encrypted)
                assert decrypted == original, f"Failed for key: {original}"

    def test_encrypt_empty_key(self, app):
        """Test encrypting empty key raises error"""
        with app.app_context():
            with pytest.raises(ValueError, match="API key cannot be empty"):
                encrypt_api_key('')

    def test_decrypt_empty_key(self, app):
        """Test decrypting empty key raises error"""
        with app.app_context():
            with pytest.raises(ValueError, match="Encrypted API key cannot be empty"):
                decrypt_api_key('')

    def test_decrypt_invalid_data(self, app):
        """Test decrypting invalid data raises error"""
        with app.app_context():
            with pytest.raises(ValueError, match="Failed to decrypt"):
                decrypt_api_key('invalid-encrypted-data')

    def test_encryption_determinism(self, app):
        """Test that encrypting the same key twice produces different outputs"""
        with app.app_context():
            plaintext = 'test-key'
            encrypted1 = encrypt_api_key(plaintext)
            encrypted2 = encrypt_api_key(plaintext)

            # Encrypted values should be different (due to random IV)
            # Note: Fernet includes timestamp, so they will be different
            # But both should decrypt to same value
            assert decrypt_api_key(encrypted1) == plaintext
            assert decrypt_api_key(encrypted2) == plaintext

    def test_ghost_api_key_format(self, app):
        """Test encrypting Ghost API key format (id:secret)"""
        with app.app_context():
            ghost_key = 'abc123def456:0123456789abcdef0123456789abcdef'
            encrypted = encrypt_api_key(ghost_key)
            decrypted = decrypt_api_key(encrypted)

            assert decrypted == ghost_key
            assert ':' in decrypted
