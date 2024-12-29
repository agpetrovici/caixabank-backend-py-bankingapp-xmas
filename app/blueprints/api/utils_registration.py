import hashlib

from pyisemail import is_email

# from app.blueprints.api.is_valid_email import is_valid_email

from app.models import User


def generate_hashed_password(password: str) -> str:
    salt = "3fe58cd8-aa3e-4c43-81a3-451972d4c9af"
    password_salted = password + salt
    # SHA512 produces a 128-character hexadecimal string
    hashed_password = hashlib.sha512(password_salted.encode()).hexdigest()
    return hashed_password


def validate_registration_data(data: dict) -> tuple[dict, bool, int]:
    status = False
    code = 400
    # Check if all required fields are present
    if not all(key in data for key in ["email", "password", "name"]):
        return {"error": "All fields are required."}, status, code

    # Check for null/empty fields
    if not all(data.values()):
        return {"error": "No empty fields allowed."}, status, code

    email = data["email"]
    password = data["password"]
    name = data["name"]

    # Validate email format
    if not is_email(email):
        return {"error": f"Invalid email: {email}"}, status, code

    # Clean email by converting to lowercase and stripping whitespace
    email = email.lower().strip()

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return {"error": "Email already exists."}, status, code

    status = True
    code = 200
    return {"email": email, "password": password, "name": name}, status, code
