from html import escape

import bcrypt
import bleach
from flask import request, jsonify
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt
from pyisemail import is_email

from app.models import db, User


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


def validate_registration_data(data):
    """Validate registration data"""
    if not data:
        return "All fields are required.", 400

    # Check if all required fields are present
    required_fields = ["email", "password", "name"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return "All fields are required.", 400

    # Check for null/empty fields
    if not all(data.values()):
        return "No empty fields allowed.", 400

    # Validate email format
    if not is_email(data["email"]):
        return f"Invalid email: {data['email']}", 400

    # Check if email already exists
    email = data["email"].lower().strip()
    if User.query.filter_by(email=email).first():
        return "Email already exists.", 400

    return None, None


def create_user(data):
    """Create a new user from validated data"""
    hashed_password = generate_hashed_password(data["password"])
    return User(
        email=data["email"].lower().strip(),
        name=data["name"],
        hashed_password=hashed_password,
        balance=0.0,
    )


def create_registration_response(user, hashed_password):
    """Create standardized registration response"""
    return {
        "name": user.name,
        "hashedPassword": hashed_password,
        "email": user.email,
    }


def handle_auth_operation(operation_func):
    """Generic error handler for auth operations"""
    try:
        return operation_func()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


def validate_login_data(data):
    """Validate login credentials"""
    if not data or not all(field in data and data[field] for field in ["email", "password"]):
        return "Bad credentials.", None, 401

    user = User.query.filter_by(email=data["email"]).first()
    if not user:
        return f"User not found for the given email: {data['email']}", None, 400

    if not password_matches(data["password"], user.hashed_password):
        return "Bad credentials.", None, 401

    return None, user, 200


def create():
    raw_data = request.get_json()
    data = sanitize_registration_data(raw_data)

    error, code = validate_registration_data(data)
    if error:
        return error, code

    new_user = create_user(data)
    db.session.add(new_user)
    db.session.commit()

    response = create_registration_response(new_user, new_user.hashed_password)
    return jsonify(response), 201


def authenticate():
    data = request.get_json()

    error, user, code = validate_login_data(data)
    if error:
        return error, code

    access_token = create_access_token(
        identity="user_identity",
        additional_claims={"user_id": user.id},
    )

    return jsonify({"token": access_token}), code
