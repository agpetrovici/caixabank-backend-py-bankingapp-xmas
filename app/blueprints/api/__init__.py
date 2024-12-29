import hashlib
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt,
)

from app.blueprints.api.register_utils import validate_registration_data
from app.models import User, db, RecurringExpense

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


@bp.route("/auth/register", methods=["POST"])
def register():
    raw_data = request.get_json()

    data, status, code = validate_registration_data(raw_data)
    if not status:
        return jsonify(data), code

    # Create new user
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
        return jsonify({"error": str(e)}), 400

    return jsonify(
        {
            "name": data["name"],
            "hashedPassword": hashed_password,
            "email": data["email"],
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
    claims = {"user_id": user.id}
    access_token = create_access_token(
        identity="user_identity",
        additional_claims=claims,
    )

    return jsonify({"token": access_token}), 200


# endregion


# # region task 2
# def get_current_user_id():
#     return get_jwt()["user_id"]


# @bp.route("/recurring-expenses", methods=["POST"])
# @jwt_required()
# def add_recurring_expense():
#     data = request.get_json()

#     # Check if data was provided
#     if not data:
#         return jsonify({"msg": "No data provided."}), 400

#     # Check required fields
#     required_fields = ["expense_name", "amount", "frequency", "start_date"]
#     if not all(field in data for field in required_fields):
#         return jsonify({"msg": "No empty fields allowed."}), 400

#     # Check for null/empty values
#     if any(not data[field] for field in required_fields):
#         return jsonify({"msg": "No empty fields allowed."}), 400

#     try:
#         # Get current user from JWT token
#         current_user_id = get_current_user_id()

#         # Parse start date
#         start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")

#         # Create new recurring expense
#         new_expense = RecurringExpense(
#             user_id=current_user_id,
#             expense_name=data["expense_name"],
#             amount=float(data["amount"]),
#             frequency=data["frequency"],
#             start_date=start_date,
#             created_at=datetime.now(timezone.utc),
#         )

#         db.session.add(new_expense)
#         db.session.commit()

#         return jsonify(
#             {
#                 "msg": "Recurring expense added successfully.",
#                 "data": {
#                     "id": new_expense.id,
#                     "expense_name": new_expense.expense_name,
#                     "amount": new_expense.amount,
#                     "frequency": new_expense.frequency,
#                     "start_date": new_expense.start_date.strftime("%Y-%m-%d"),
#                 },
#             }
#         ), 201

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"msg": str(e)}), 400


# @bp.route("/recurring-expenses", methods=["GET"])
# @jwt_required()
# def get_recurring_expenses():
#     current_user_id = get_current_user_id()

#     try:
#         expenses = RecurringExpense.query.filter_by(user_id=current_user_id).all()

#         expenses_list = [
#             {
#                 "id": expense.id,
#                 "expense_name": expense.expense_name,
#                 "amount": expense.amount,
#                 "frequency": expense.frequency,
#                 "start_date": expense.start_date.strftime("%Y-%m-%d"),
#                 "created_at": expense.created_at.strftime("%Y-%m-%d %H:%M:%S"),
#             }
#             for expense in expenses
#         ]

#         return jsonify(expenses_list), 200

#     except Exception as e:
#         return jsonify({"msg": str(e)}), 400


# # endregion
