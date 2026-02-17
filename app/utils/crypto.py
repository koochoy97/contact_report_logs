"""Fernet encryption for storing credentials in the database."""
from cryptography.fernet import Fernet

from app.config import FERNET_KEY

_fernet = Fernet(FERNET_KEY.encode()) if FERNET_KEY else None


def encrypt(plaintext: str) -> str:
    if not _fernet:
        raise RuntimeError("FERNET_KEY no configurada")
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    if not _fernet:
        raise RuntimeError("FERNET_KEY no configurada")
    return _fernet.decrypt(ciphertext.encode()).decode()


def generate_key() -> str:
    """Generate a new Fernet key (use once, save to .env)."""
    return Fernet.generate_key().decode()
