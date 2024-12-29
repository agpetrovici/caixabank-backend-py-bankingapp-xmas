import hashlib
from flask import Blueprint, render_template, request, jsonify
from flask_jwt_extended import create_access_token

# from flask_login import login_required, login_user, logout_user


from app.blueprints.api.register_utils import validate_registration_data
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

    validated_data, error = validate_registration_data(data)
    if error:
        return jsonify(error[0]), error[1]

    # Create new user
    hashed_password = generate_hashed_password(validated_data["password"])
    new_user = User(
        email=validated_data["email"],
        name=validated_data["name"],
        hashed_password=hashed_password,
        balance=0.0,
    )

    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

    return jsonify(
        {
            "name": validated_data["name"],
            "hashedPassword": hashed_password,
            "email": validated_data["email"],
        }
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
    access_token = create_access_token(identity=str(user.id))

    return jsonify({"token": access_token}), 200


# endregion
