import hashlib
from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import create_access_token

# from flask_login import login_required, login_user, logout_user

from app.blueprints.api.is_valid_email import is_valid_email
from app.models import User, db

# from app.login import login_manager


def generate_hashed_password(password: str) -> str:
    salt = "3fe58cd8-aa3e-4c43-81a3-451972d4c9af"
    password_salted = password + salt
    hashed_password = hashlib.sha256(password_salted.encode()).hexdigest()
    return hashed_password


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


@bp.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    # Check if all required fields are present
    if not all(key in data for key in ["email", "password", "name"]):
        return jsonify({"error": "All fields are required."}), 400

    # Check for null/empty fields
    if not all(data.values()):
        return jsonify({"error": "No empty fields allowed."}), 400

    email = data["email"]
    password = data["password"]
    name = data["name"]

    # Validate email format
    if not is_valid_email(email):
        return jsonify({"error": f"Invalid email: {email}"}), 400

    # Clean email by converting to lowercase and stripping whitespace
    email = email.lower().strip()

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists."}), 400

    # Create new user
    hashed_password = generate_hashed_password(password)
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
        return jsonify({"error": "Bad credentials."}), 401

    email = data.get("email")
    password = data.get("password")

    # Check for null/empty fields
    if not email or not password:
        return jsonify({"error": "Bad credentials."}), 401

    # Find user by email
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": f"User not found for the given email: {email}"}), 400

    # Verify password
    hashed_password = generate_hashed_password(password)
    if user.hashed_password != hashed_password:
        return jsonify({"error": "Bad credentials."}), 401

    # Create JWT token
    access_token = create_access_token(identity=user.id)

    return jsonify({"token": access_token}), 200
