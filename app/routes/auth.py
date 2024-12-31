from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from pyisemail import is_email

from app.utils.utils_auth import (
    generate_hashed_password,
    password_matches,
    sanitize_registration_data,
)
from app.models import db, User


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# region task 1


@bp.route("/register", methods=["POST"])
def register():
    raw_data = request.get_json()

    # Sanitize input data
    data = sanitize_registration_data(raw_data)

    # Validate data

    # Check if all required fields are present
    required_fields = ["email", "password", "name"]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return "All fields are required.", 400

    # Check for null/empty fields
    if not all(data.values()):
        return "No empty fields allowed.", 400

    email = data["email"]

    # Validate email format
    if not is_email(email):
        return f"Invalid email: {email}", 400
    # Clean email by converting to lowercase and stripping whitespace
    email = email.lower().strip()

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return "Email already exists.", 400

    # Create new user with sanitized data
    hashed_password = generate_hashed_password(data["password"])
    new_user = User(
        email=data["email"],
        name=data["name"],
        hashed_password=hashed_password,
        balance=0.0,
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400

    return jsonify(
        {
            "name": data["name"],
            "hashedPassword": hashed_password,
            "email": data["email"],
        }
    ), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # Check if email and password are provided
    if not data or "email" not in data or "password" not in data:
        return "Bad credentials.", 401

    email = data.get("email")
    password = data.get("password")

    # Check for null/empty fields
    if not email or not password:
        return "Bad credentials.", 401

    # Find user by email
    user = User.query.filter_by(email=email).first()

    if not user:
        return f"User not found for the given email: {email}", 400

    # Verify password
    if not password_matches(password, user.hashed_password):
        return "Bad credentials.", 401

    # Create JWT token
    claims = {"user_id": user.id}
    access_token = create_access_token(
        identity="user_identity",
        additional_claims=claims,
    )

    return jsonify({"token": access_token}), 200


# endregion
