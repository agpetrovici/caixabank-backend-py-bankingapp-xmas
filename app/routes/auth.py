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
        return "Bad credentials.", 401

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not password_matches(data["password"], user.hashed_password):
        return "Bad credentials.", 401

    return None, user


@bp.route("/register", methods=["POST"])
def register():
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

    return handle_auth_operation(create)


@bp.route("/login", methods=["POST"])
def login():
    def authenticate():
        data = request.get_json()

        error, user = validate_login_data(data)
        if error:
            return error, 401

        access_token = create_access_token(
            identity="user_identity",
            additional_claims={"user_id": user.id},
        )

        return jsonify({"token": access_token}), 200

    return handle_auth_operation(authenticate)
