from passlib.hash import pbkdf2_sha256
from pyisemail import is_email

# from app.blueprints.api.is_valid_email import is_valid_email

from app.models import User


def generate_hashed_password(password: str) -> str:
    # Using pbkdf2_sha256 with high rounds (100000) for better security
    # pbkdf2_sha256 automatically generates and handles the salt
    # This is considered one of the best options in passlib for password hashing
    hashed_password = pbkdf2_sha256.using(rounds=100000).hash(password)
    return hashed_password


def password_matches(password: str, hashed_password: str) -> bool:
    """
    Verify if the provided password matches the hashed password.
    The method extracts the salt from the hashed password automatically.
    """
    return pbkdf2_sha256.verify(password, hashed_password)


def validate_registration_data(data: dict) -> tuple[dict, bool, int]:
    status = False
    code = 400
    # Check if all required fields are present
    if not all(key in data for key in ["email", "password", "name"]):
        return {"msg": "All fields are required."}, status, code

    # Check for null/empty fields
    if not all(data.values()):
        return {"msg": "No empty fields allowed."}, status, code

    email = data["email"]
    password = data["password"]
    name = data["name"]

    # Validate email format
    # if not is_email(email):
    #     return {"msg": f"Invalid email: {email}"}, status, code

    # Clean email by converting to lowercase and stripping whitespace
    email = email.lower().strip()

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return {"msg": "Email already exists."}, status, code

    status = True
    code = 200
    return {"email": email, "password": password, "name": name}, status, code
