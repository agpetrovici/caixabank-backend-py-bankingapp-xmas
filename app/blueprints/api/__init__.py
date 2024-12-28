import re

from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import login_required, login_user, logout_user

from app.models import User, db

# from app.login import login_manager

bp = Blueprint(
    "api",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/api",
)


@bp.route("/")
def index():
    return render_template("api/index.html")


def is_valid_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


@bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    # Check if all required fields are present
    if not all(key in data for key in ["email", "password", "name"]):
        return jsonify({"msg": "All fields are required."}), 400

    # Check for null/empty fields
    if not all(data.values()):
        return jsonify({"msg": "No empty fields allowed."}), 400

    email = data["email"]
    password = data["password"]
    name = data["name"]

    # Validate email format
    if not is_valid_email(email):
        return jsonify({"msg": f"Invalid email: {email}"}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "Email already exists."}), 400

    # Create new user

    hashed_password = generate_password_hash(password, salt_length=8)

    new_user = User(
        email=email, name=name, hashed_password=hashed_password, balance=0.0
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify(
        {"name": name, "hashedPassword": hashed_password, "email": email}
    ), 201


@bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()

    # Check if email and password are provided
    if not data or "email" not in data or "password" not in data:
        return jsonify({"msg": "Bad credentials."}), 401

    email = data.get("email")
    password = data.get("password")

    # Check for null/empty fields
    if not email or not password:
        return jsonify({"msg": "Bad credentials."}), 401

    # Find user by email
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"msg": f"User not found for the given email: {email}"}), 400

    # Verify password
    if not check_password_hash(user.hashed_password, password):
        return jsonify({"msg": "Bad credentials."}), 401

    # Create JWT token
    access_token = create_access_token(identity=user.id)

    return jsonify({"token": access_token}), 200
