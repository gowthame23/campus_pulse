import re

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_non_empty(value):
    return bool(str(value).strip())


def validate_email(email):
    return bool(EMAIL_PATTERN.match(email.strip()))


def validate_password(password):
    return len(password) >= 6


def require_non_empty(prompt):
    while True:
        value = input(prompt).strip()
        if is_non_empty(value):
            return value
        print("Value cannot be empty.")


def require_password(prompt="Password: "):
    while True:
        password = input(prompt).strip()
        if validate_password(password):
            return password
        print("Password must contain at least 6 characters.")
