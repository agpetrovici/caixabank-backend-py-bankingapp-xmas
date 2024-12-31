from html import escape

import bcrypt
import bleach
from flask_jwt_extended import get_jwt


def get_current_user_id():
    return get_jwt()["user_id"]


def generate_hashed_password(password: str) -> str:
    """
    Generate a hashed password using bcrypt.
    bcrypt automatically generates a salt and embeds it in the hash.
    """
    # bcrypt requires the password to be encoded as bytes
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed_password.decode("utf-8")  # Decode to return as a string


def password_matches(password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the bcrypt hashed password.
    The method extracts the salt from the hashed password automatically.
    """
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def sanitize_input(data: str) -> str:
    """
    Sanitize input string to prevent XSS attacks.
    - Escapes HTML special characters
    - Removes potentially dangerous HTML tags and attributes
    """
    if not isinstance(data, str):
        return data

    # First escape HTML special characters
    escaped = escape(data)

    # Then clean any remaining HTML tags
    cleaned = bleach.clean(
        escaped,
        tags=[],  # No HTML tags allowed
        attributes={},  # No attributes allowed
        strip=True,  # Strip disallowed tags
    )

    return cleaned.strip()


def sanitize_registration_data(data: dict) -> dict:
    """Sanitize all registration input fields"""
    output = dict()
    for key, value in data.items():
        if key == "password":
            # Don't sanitize password
            output[key] = value
        else:
            output[key] = sanitize_input(value)
    return output
