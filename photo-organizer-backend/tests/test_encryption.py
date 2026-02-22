import pytest
from app.core.encryption import encrypt_api_key, decrypt_api_key


class TestEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        original = "sk-test-api-key-12345"
        encrypted = encrypt_api_key(original)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original

    def test_encrypted_differs_from_original(self):
        original = "my-secret-key"
        encrypted = encrypt_api_key(original)
        assert encrypted != original

    def test_different_encryptions_differ(self):
        original = "same-key"
        enc1 = encrypt_api_key(original)
        enc2 = encrypt_api_key(original)
        assert enc1 != enc2  # Different nonces

    def test_decrypt_both_produce_same_result(self):
        original = "same-key"
        enc1 = encrypt_api_key(original)
        enc2 = encrypt_api_key(original)
        assert decrypt_api_key(enc1) == decrypt_api_key(enc2) == original

    def test_empty_string(self):
        original = ""
        encrypted = encrypt_api_key(original)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original

    def test_unicode_key(self):
        original = "密钥-测试-🔑"
        encrypted = encrypt_api_key(original)
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original
