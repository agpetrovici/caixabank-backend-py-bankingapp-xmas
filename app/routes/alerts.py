from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models import db, User, Alert
from app.utils.utils_auth import get_current_user_id

bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")

# region task 4


@bp.route("/amount_reached", methods=["POST"])
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


@bp.route("/balance_drop", methods=["POST"])
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


@bp.route("/delete", methods=["POST"])
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
        alert = Alert.query.filter_by(id=data["alert_id"], user_id=current_user_id).first()

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


@bp.route("/list", methods=["GET"])
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
                progress = (user.balance / alert.target_amount) * 100 if alert.target_amount > 0 else 0
                alert_data["progress"] = round(progress, 2)
                alert_data["status"] = "TRIGGERED" if user.balance >= alert.alert_threshold else "PENDING"

            # Add status for balance drop alerts
            if alert.balance_drop_threshold is not None:
                alert_data["status"] = "PENDING"  # Status will be updated when transactions occur

            alerts_list.append(alert_data)

        return jsonify({"data": alerts_list}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


# endregion
