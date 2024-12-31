from datetime import datetime, timezone


from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required


from app.utils.utils_transactions import (
    check_high_deviation,
    check_rapid_transactions,
    check_unusual_category,
)
from app.models import db, User, Alert, Transaction
from app.utils.utils_email import send_alert_email
from app.utils.utils_auth import get_current_user_id

bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


# region task 5


@bp.route("/", methods=["POST"])
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
        timestamp = data.get("timestamp", datetime.now(timezone.utc))
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        # Check for fraud
        is_fraud = any(
            [
                check_high_deviation(current_user_id, amount, timestamp),
                check_unusual_category(current_user_id, category, timestamp),
                check_rapid_transactions(current_user_id, amount, timestamp),
            ]
        )

        # Create new transaction
        transaction = Transaction(
            user_id=current_user_id,
            amount=amount,
            category=category,
            timestamp=timestamp,
            fraud=is_fraud,
        )

        # Update user balance
        user: User = User.query.get(current_user_id)

        # Update user balance
        user.balance += amount
        db.session.add(transaction)
        db.session.commit()

        # Check alerts after transaction
        alerts: list[Alert] = Alert.query.filter_by(user_id=current_user_id).all()

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
                "data": transaction.to_dict(),
            }
        ), 201

    except ValueError:
        return jsonify({"msg": "Invalid amount value."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


# endregion
