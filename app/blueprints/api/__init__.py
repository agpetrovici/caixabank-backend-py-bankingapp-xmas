from datetime import datetime, timezone, timedelta
from typing import List


from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt,
)

from app.utils.utils_exchange import get_exchange_data
from app.utils.utils_auth import (
    generate_hashed_password,
    validate_registration_data,
    password_matches,
    sanitize_registration_data,
)
from app.utils.utils_transactions import (
    check_high_deviation,
    check_rapid_transactions,
    check_unusual_category,
)
from app.models import db, User, RecurringExpense, Alert, Transaction
from app.utils.utils_email import send_alert_email

bp = Blueprint(
    "api",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/static/api",
)

# region task 1


@bp.route("/auth/register", methods=["POST"])
def register():
    raw_data = request.get_json()

    # Sanitize input data
    sanitized_data = sanitize_registration_data(raw_data)

    # Validate sanitized data
    data, status, code = validate_registration_data(sanitized_data)
    if not status:
        return jsonify(data), code

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
    if not password_matches(password, user.hashed_password):
        return jsonify({"msg": "Bad credentials."}), 401

    # Create JWT token
    claims = {"user_id": user.id}
    access_token = create_access_token(
        identity="user_identity",
        additional_claims=claims,
    )

    return jsonify({"token": access_token}), 200


# endregion


# region task 2


def get_current_user_id():
    return get_jwt()["user_id"]


@bp.route("/recurring-expenses", methods=["POST"])
@jwt_required()
def add_recurring_expense():
    # 100 pts
    if not request.is_json:
        return jsonify({"msg": "Content type must be application/json"}), 415

    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No data provided."}), 400

    # Check required fields
    required_fields = ["expense_name", "amount", "frequency", "start_date"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check for null/empty values
    if any(not data[field] for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        # Get current user from JWT token
        current_user_id = get_current_user_id()

        # Parse start date
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")

        # Create new recurring expense
        new_expense = RecurringExpense(
            user_id=current_user_id,
            expense_name=data["expense_name"],
            amount=float(data["amount"]),
            frequency=data["frequency"],
            start_date=start_date,
            created_at=datetime.now(timezone.utc),
        )

        db.session.add(new_expense)
        db.session.commit()

        return jsonify(
            {
                "msg": "Recurring expense added successfully.",
                "data": {
                    "id": new_expense.id,
                    "expense_name": new_expense.expense_name,
                    "amount": new_expense.amount,
                    "frequency": new_expense.frequency,
                    "start_date": new_expense.start_date.strftime("%Y-%m-%d"),
                },
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/recurring-expenses", methods=["GET"])
@jwt_required()
def get_recurring_expenses():
    # 20 pts
    current_user_id = get_current_user_id()

    try:
        expenses = RecurringExpense.query.filter_by(user_id=current_user_id).all()

        expenses_list = [
            {
                "id": expense.id,
                "expense_name": expense.expense_name,
                "amount": expense.amount,
                "frequency": expense.frequency,
                "start_date": expense.start_date.strftime("%Y-%m-%d"),
                "created_at": expense.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for expense in expenses
        ]

        return jsonify(expenses_list), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@bp.route("/recurring-expenses/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_recurring_expense(expense_id):
    # 100 pts
    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No data provided."}), 400

    # Check required fields
    required_fields = ["expense_name", "amount", "frequency", "start_date"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check for null/empty values
    if any(not data[field] for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        current_user_id = get_current_user_id()

        # Find the expense
        expense = RecurringExpense.query.filter_by(
            id=expense_id, user_id=current_user_id
        ).first()

        if not expense:
            return jsonify({"msg": "Expense not found."}), 404

        # Parse start date
        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")

        # Update expense fields
        expense.expense_name = data["expense_name"]
        expense.amount = float(data["amount"])
        expense.frequency = data["frequency"]
        expense.start_date = start_date

        db.session.commit()

        return jsonify(
            {
                "msg": "Recurring expense updated successfully.",
                "data": {
                    "id": expense.id,
                    "expense_name": expense.expense_name,
                    "amount": expense.amount,
                    "frequency": expense.frequency,
                    "start_date": expense.start_date.strftime("%Y-%m-%d"),
                },
            }
        ), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/recurring-expenses/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_recurring_expense(expense_id):
    try:
        current_user_id = get_current_user_id()

        # Find the expense
        expense = RecurringExpense.query.filter_by(
            id=expense_id, user_id=current_user_id
        ).first()

        if not expense:
            return jsonify({"msg": "Expense not found."}), 404

        # Delete the expense
        db.session.delete(expense)
        db.session.commit()

        return jsonify({"msg": "Recurring expense deleted successfully."}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


# @bp.route("/recurring-expenses/projection", methods=["GET"])
# @jwt_required()
# def get_expenses_projection():
#     try:
#         current_user_id = get_current_user_id()

#         # Get all recurring expenses for the user
#         expenses: List[RecurringExpense] = RecurringExpense.query.filter_by(
#             user_id=current_user_id
#         ).all()

#         # Start from next month
#         start_date = datetime.now(timezone.utc).replace(day=1) + timedelta(days=32)
#         start_date = start_date.replace(day=1)  # Ensure first day of next month
#         projections = []

#         # Calculate for next 12 months
#         for month_offset in range(12):
#             # Calculate target month
#             target_date = start_date + timedelta(days=32 * month_offset)
#             target_date = target_date.replace(day=1)  # First day of month

#             # Format as YYYY-MM
#             month_key = target_date.strftime("%Y-%m")

#             # Calculate total recurring expenses for this month
#             total_amount = 0.0

#             for expense in expenses:
#                 if expense.frequency == "monthly":
#                     # Monthly expenses are included if created on or before target date
#                     if expense.start_date.replace(tzinfo=timezone.utc) <= target_date:
#                         total_amount += expense.amount

#                 elif expense.frequency == "yearly":
#                     # Yearly expenses only included on their anniversary month
#                     if (
#                         target_date.month == expense.start_date.month
#                         and target_date.year >= expense.start_date.year
#                     ):
#                         total_amount += expense.amount

#             projections.append({"month": month_key, "recurring_expenses": total_amount})

#         return jsonify(projections), 200

#     except Exception as e:
#         return jsonify({"msg": str(e)}), 400


# endregion


# region task 3


@bp.route("/transfers/simulate", methods=["POST"])
@jwt_required()
def simulate_transfer():
    if not request.is_json:
        return jsonify({"msg": "Content type must be application/json"}), 415
    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check required fields
    required_fields = ["amount", "source_currency", "target_currency"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check for null/empty values
    if any(not data[field] for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        amount = float(data["amount"])
        source_currency = data["source_currency"]
        target_currency = data["target_currency"]

        # Get exchange rate and fee
        rate, fee = get_exchange_data(source_currency, target_currency)

        if rate is None or fee is None:
            return jsonify(
                {"msg": "Invalid currencies or no exchange data available."}
            ), 404

        # Calculate final amount using formula: target_amount = source_amount × (1-fee) × rate
        final_amount = amount * (1 - fee) * rate

        return jsonify({"msg": f"Amount in target currency: {final_amount:.2f}"}), 201

    except ValueError:
        return jsonify({"msg": "Invalid amount value."}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@bp.route("/transfers/fees", methods=["GET"])
@jwt_required()
def get_transfer_fees():
    # Get query parameters
    source_currency = request.args.get("source_currency")
    target_currency = request.args.get("target_currency")

    # Check if parameters are provided
    if not source_currency or not target_currency:
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        # Get exchange rate and fee
        rate, fee = get_exchange_data(source_currency, target_currency)

        if fee is None:
            return jsonify(
                {"msg": "No fee information available for these currencies."}
            ), 404

        return jsonify({"fee": fee}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@bp.route("/transfers/rates", methods=["GET"])
@jwt_required()
def get_exchange_rates():
    # Get query parameters
    source_currency = request.args.get("source_currency")
    target_currency = request.args.get("target_currency")

    # Check if parameters are provided
    if not source_currency or not target_currency:
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        # Get exchange rate and fee
        rate, fee = get_exchange_data(source_currency, target_currency)

        if rate is None:
            return jsonify(
                {"msg": "No exchange rate available for these currencies."}
            ), 404

        return jsonify({"rate": rate}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


# endregion


# region task 4


@bp.route("/alerts/amount_reached", methods=["POST"])
@jwt_required()
def create_savings_alert():
    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check required fields
    required_fields = ["target_amount", "alert_threshold"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check for null/empty values
    if any(not data[field] for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        current_user_id = get_current_user_id()

        # Create new alert
        new_alert = Alert(
            user_id=current_user_id,
            target_amount=float(data["target_amount"]),
            alert_threshold=float(data["alert_threshold"]),
            created_at=datetime.now(timezone.utc),
        )

        db.session.add(new_alert)
        db.session.commit()

        return jsonify(
            {
                "msg": "Correctly added savings alert!",
                "data": {
                    "id": new_alert.id,
                    "user_id": new_alert.user_id,
                    "target_amount": new_alert.target_amount,
                    "alert_threshold": new_alert.alert_threshold,
                },
            }
        ), 201

    except ValueError:
        return jsonify({"msg": "Invalid numeric value."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/alerts/balance_drop", methods=["POST"])
@jwt_required()
def create_balance_drop_alert():
    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check required fields
    if "balance_drop_threshold" not in data:
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check for null/empty value
    if not data["balance_drop_threshold"]:
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        current_user_id = get_current_user_id()

        # Create new alert
        new_alert = Alert(
            user_id=current_user_id,
            balance_drop_threshold=float(data["balance_drop_threshold"]),
            created_at=datetime.now(timezone.utc),
        )

        db.session.add(new_alert)
        db.session.commit()

        return jsonify(
            {
                "msg": "Correctly added balance drop alert!",
                "data": {
                    "id": new_alert.id,
                    "user_id": new_alert.user_id,
                    "balance_drop_threshold": new_alert.balance_drop_threshold,
                },
            }
        ), 201

    except ValueError:
        return jsonify({"msg": "Invalid numeric value."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/alerts/delete", methods=["POST"])
@jwt_required()
def delete_alert():
    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check required fields
    if "alert_id" not in data:
        return jsonify({"msg": "Missing alert ID."}), 400

    # Check for null/empty value
    if not data["alert_id"]:
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        current_user_id = get_current_user_id()

        # Find the alert
        alert = Alert.query.filter_by(
            id=data["alert_id"], user_id=current_user_id
        ).first()

        if not alert:
            return jsonify({"msg": "Alert not found."}), 404

        # Delete the alert
        db.session.delete(alert)
        db.session.commit()

        return jsonify({"msg": "Alert deleted successfully."}), 200

    except ValueError:
        return jsonify({"msg": "Invalid alert ID."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/alerts/list", methods=["GET"])
@jwt_required()
def list_alerts():
    try:
        current_user_id = get_current_user_id()

        # Get current user and their alerts
        user = User.query.get(current_user_id)
        alerts = Alert.query.filter_by(user_id=current_user_id).all()

        # Convert alerts to dictionary format
        alerts_list = []
        for alert in alerts:
            alert_data = {
                "id": alert.id,
                "user_id": alert.user_id,
                "target_amount": alert.target_amount,
                "alert_threshold": alert.alert_threshold,
                "balance_drop_threshold": alert.balance_drop_threshold,
            }

            # Add progress info for savings goal alerts
            if alert.target_amount is not None:
                progress = (
                    (user.balance / alert.target_amount) * 100
                    if alert.target_amount > 0
                    else 0
                )
                alert_data["progress"] = round(progress, 2)
                alert_data["status"] = (
                    "TRIGGERED" if user.balance >= alert.alert_threshold else "PENDING"
                )

            # Add status for balance drop alerts
            if alert.balance_drop_threshold is not None:
                alert_data["status"] = (
                    "PENDING"  # Status will be updated when transactions occur
                )

            alerts_list.append(alert_data)

        return jsonify({"data": alerts_list}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


# endregion


# region task 5


@bp.route("/transactions", methods=["POST"])
@jwt_required()
def add_transaction():
    data = request.get_json()

    # Check if data was provided
    if not data:
        return jsonify({"msg": "No data provided."}), 400

    # Check required fields
    required_fields = ["amount", "category"]
    if not all(field in data for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    # Check for null/empty values
    if any(not data[field] for field in required_fields):
        return jsonify({"msg": "No empty fields allowed."}), 400

    try:
        current_user_id = get_current_user_id()
        amount = float(data["amount"])
        category = data["category"]
        timestamp = datetime.now(timezone.utc)

        # Check for fraud
        is_fraud = any(
            [
                # check_high_deviation(current_user_id, amount, timestamp),  # 219 pts
                check_unusual_category(current_user_id, category, timestamp),
                # check_rapid_transactions(current_user_id, amount, timestamp),
            ]
        )

        # Create new transaction
        new_transaction = Transaction(
            user_id=current_user_id,
            amount=amount,
            category=category,
            timestamp=timestamp,
            fraud=is_fraud,
        )

        # Update user balance
        user = User.query.get(current_user_id)
        user.balance += amount

        db.session.add(new_transaction)
        db.session.commit()

        # Check alerts after transaction
        alerts = Alert.query.filter_by(user_id=current_user_id).all()

        for alert in alerts:
            # Check savings goal alerts
            if alert.target_amount and user.balance >= alert.alert_threshold:
                send_alert_email(
                    user.email,
                    user.name,
                    "savings",
                    alert_target_amount=alert.target_amount,
                )

            # Check balance drop alerts
            if alert.balance_drop_threshold and amount < -alert.balance_drop_threshold:
                send_alert_email(
                    user.email,
                    user.name,
                    "balance_drop",
                    alert_balance_drop_threshold=alert.balance_drop_threshold,
                )

        return jsonify(
            {
                "msg": "Transaction added and evaluated for fraud.",
                "data": new_transaction.to_dict(),
            }
        ), 201

    except ValueError:
        return jsonify({"msg": "Invalid amount value."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


# endregion
