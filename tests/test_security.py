"""Test minimal des fonctions de sécurité."""
from backend.security import hash_password, verify_password

def test_password_hash_roundtrip():
    original = "MotDePasse-Test-2026"
    hashed = hash_password(original)
    assert hashed != original
    assert verify_password(original, hashed)
    assert not verify_password("mauvais-mot-de-passe", hashed)
