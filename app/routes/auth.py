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


def validate_registration_data(data):
    # Check required fields and empty values
    required_fields = ["email", "password", "name"]
    if not all(field in data and data[field] for field in required_fields):
        return "All fields are required.", 400

    email = data["email"].lower().strip()
    if not is_email(email):
        return f"Invalid email: {email}", 400

    if User.query.filter_by(email=email).first():
        return "Email already exists.", 400

    return None


@bp.route("/register", methods=["POST"])
def register():
    raw_data = request.get_json()
    data = sanitize_registration_data(raw_data)

    validation_error = validate_registration_data(data)
    if validation_error:
        return validation_error

    # Create and save new user
    try:
        hashed_password = generate_hashed_password(data["password"])
        new_user = User(
            email=data["email"].lower().strip(),
            name=data["name"],
            hashed_password=hashed_password,
            balance=0.0,
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"name": data["name"], "hashedPassword": hashed_password, "email": data["email"].lower().strip()}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    # Validate required fields
    if not data or not all(field in data and data[field] for field in ["email", "password"]):
        return "Bad credentials.", 401

    # Find and validate user
    user = User.query.filter_by(email=data["email"]).first()
    if not user or not password_matches(data["password"], user.hashed_password):
        return "Bad credentials.", 401

    # Create and return JWT token
    access_token = create_access_token(
        identity="user_identity",
        additional_claims={"user_id": user.id},
    )

    return jsonify({"token": access_token}), 200


# endregion
