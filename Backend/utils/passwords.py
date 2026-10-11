import hashlib
import hmac
import os
import secrets

# PBKDF2-HMAC-SHA256 iteration count. 600,000 is OWASP's current Password
# Storage Cheat Sheet recommendation for this algorithm. The count is stored
# inside each hash (see hash_password), so raising it here only affects
# passwords hashed from now on; existing hashes keep verifying against their
# own stored iteration count (see needs_rehash / authenticate()).
_PREFIX = "pbkdf2_sha256"
_ITERATIONS = 600000


def generate_temp_password():
    return f"Tp@{secrets.token_hex(6)}A1"


def hash_password(password):
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), _ITERATIONS
    ).hex()
    return f"{_PREFIX}${_ITERATIONS}${salt}${digest}"


def is_password_hash(value):
    return isinstance(value, str) and value.startswith(f"{_PREFIX}$")


def needs_rehash(stored):
    """True if `stored` was hashed with fewer iterations than the current
    target, so authenticate() can transparently upgrade it on next login
    without forcing a password reset."""
    if not is_password_hash(stored):
        return True
    try:
        iterations = int(stored.split("$", 2)[1])
    except (ValueError, IndexError):
        return True
    return iterations < _ITERATIONS


def verify_password(password, stored):
    if not is_password_hash(stored):
        return hmac.compare_digest(stored, password)
    try:
        _, iterations, salt, digest = stored.split("$", 3)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except ValueError:
        return False


def validate_password_complexity(password):
    checks = [
        len(password) >= 8,
        any(char.isupper() for char in password),
        any(char.islower() for char in password),
        any(char.isdigit() for char in password),
        any(not char.isalnum() for char in password),
    ]
    return all(checks)
