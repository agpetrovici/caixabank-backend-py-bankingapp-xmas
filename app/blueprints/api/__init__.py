import hashlib
import re

from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import create_access_token

# from flask_login import login_required, login_user, logout_user

# from app.blueprints.api.is_valid_email import is_valid_email
from app.models import User, db

# from app.login import login_manager

bp = Blueprint(
    "api",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/api",
)

# region task 1


def is_valid_email(email: str) -> bool:
    # Check for basic email format using regex
    if not email or not isinstance(email, str):
        return False

    # Remove any leading/trailing whitespace
    email = email.strip()

    # Check length constraints
    if len(email) > 254:  # Maximum length per RFC 5321
        return False

    # Check for exactly one @ symbol
    if email.count("@") != 1:
        return False

    # Split into local and domain parts
    try:
        local, domain = email.rsplit("@", 1)
    except ValueError:
        return False

    # Check local part has at least one character
    if len(local) < 1:
        return False

    if len(domain) < 1:
        return False

    # Check local part ends with alphanumeric character
    if not local[-1].isalnum():
        return False

    # Check local part only contains alphanumeric chars and underscore
    if not all(c.isalnum() or c == "." or c == "_" or c == "-" for c in local):
        return False

    # Check first character before @ and first character after @ is alphanumeric
    if not local[0].isalnum() or not domain[0].isalnum():
        return False

    # Validate lengths of local and domain parts
    if len(local) > 64 or len(domain) > 255:  # RFC 5321
        return False

    # Check for consecutive dots
    if ".." in email:
        return False

    # Validate local part characters
    local_pattern = r"^[a-zA-Z0-9!#$%&\'*+\-/=?^_`{|}~.]+$"
    if not re.match(local_pattern, local):
        return False

    # Validate domain - must have at least one dot and valid characters
    if "." not in domain:
        return False

    domain_pattern = r"^[a-zA-Z0-9.-]+$"
    if not re.match(domain_pattern, domain):
        return False

    # Domain cannot start/end with hyphen or dot
    if domain[0] in ".-" or domain[-1] in ".-":
        return False

    # Check for invalid hyphen-dot or dot-hyphen sequences in domain
    if "-." in domain or ".-" in domain:
        return False
    return True


def generate_hashed_password(password: str) -> str:
    salt = "3fe58cd8-aa3e-4c43-81a3-451972d4c9af"
    password_salted = password + salt
    # SHA512 produces a 128-character hexadecimal string
    hashed_password = hashlib.sha512(password_salted.encode()).hexdigest()
    return hashed_password


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


# endregion
