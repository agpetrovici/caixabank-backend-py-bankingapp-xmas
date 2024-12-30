import bcrypt
from pyisemail import is_email
import bleach
from html import escape
import re

# from app.blueprints.api.is_valid_email import is_valid_email

from app.models import User


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


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, error_message)

    Rules:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"

    return True, ""


def validate_registration_data(data: dict) -> tuple[dict, bool, int]:
    status = False
    code = 400
    # Check if all required fields are present
    required_fields = ["email", "password", "name"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return {"msg": "All fields are required."}, status, code

    # Check for null/empty fields
    if not all(data.values()):
        return {"msg": "No empty fields allowed."}, status, code

    email = data["email"]
    password = data["password"]
    name = data["name"]

    # Validate password strength
    # is_valid_password, password_error = validate_password(password)
    # if not is_valid_password:
    #     return {"msg": password_error}, status, code

    # Validate email format
    if not is_email(email):
        return {"msg": f"Invalid email: {email}"}, status, code

    # Clean email by converting to lowercase and stripping whitespace
    email = email.lower().strip()

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return {"msg": "Email already exists."}, status, code

    status = True
    code = 200
    return {"email": email, "password": password, "name": name}, status, code


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
    return {
        "email": sanitize_input(data.get("email", "")),
        "name": sanitize_input(data.get("name", "")),
        "password": data.get("password", ""),  # Don't sanitize password
    }
