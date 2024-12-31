from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, User, Alert
from app.utils.utils_auth import get_current_user_id

bp = Blueprint("alerts", __name__, url_prefix="/api/alerts")


def validate_request_data(data, required_fields):
    """Validate request data and required fields"""
    if not data:
        return "No empty fields allowed."

    if required_fields:
        if not all(field in data for field in required_fields):
            return "No empty fields allowed."
        if any(not data[field] for field in required_fields):
            return "No empty fields allowed."

    return None


def create_alert_response(alert, msg, extra_data=None):
    """Create standardized response for alert operations"""
    response = {
        "msg": msg,
        "data": {
            "id": alert.id,
            "user_id": alert.user_id,
        },
    }

    if extra_data:
        response["data"].update(extra_data)

    return response


def handle_alert_operation(operation_func):
    """Generic error handler for alert operations"""
    try:
        return operation_func()
    except ValueError:
        return jsonify({"msg": "Invalid numeric value."}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


@bp.route("/amount_reached", methods=["POST"])
@jwt_required()
def create_savings_alert():
    def create():
        data = request.get_json()
        error = validate_request_data(data, ["target_amount", "alert_threshold"])
        if error:
            return jsonify({"msg": error}), 400

        new_alert = Alert(
            user_id=get_current_user_id(),
            target_amount=float(data["target_amount"]),
            alert_threshold=float(data["alert_threshold"]),
            created_at=datetime.now(timezone.utc),
        )

        db.session.add(new_alert)
        db.session.commit()

        extra_data = {
            "target_amount": new_alert.target_amount,
            "alert_threshold": new_alert.alert_threshold,
        }
        response = create_alert_response(new_alert, "Correctly added savings alert!", extra_data)
        return jsonify(response), 201

    return handle_alert_operation(create)


@bp.route("/balance_drop", methods=["POST"])
@jwt_required()
def create_balance_drop_alert():
    def create():
        data = request.get_json()
        error = validate_request_data(data, ["balance_drop_threshold"])
        if error:
            return jsonify({"msg": error}), 400

        new_alert = Alert(
            user_id=get_current_user_id(),
            balance_drop_threshold=float(data["balance_drop_threshold"]),
            created_at=datetime.now(timezone.utc),
        )

        db.session.add(new_alert)
        db.session.commit()

        extra_data = {"balance_drop_threshold": new_alert.balance_drop_threshold}
        response = create_alert_response(new_alert, "Correctly added balance drop alert!", extra_data)
        return jsonify(response), 201

    return handle_alert_operation(create)


@bp.route("/delete", methods=["POST"])
@jwt_required()
def delete_alert():
    def delete():
        data = request.get_json()
        error = validate_request_data(data, ["alert_id"])
        if error:
            return jsonify({"msg": error}), 400

        current_user_id = get_current_user_id()
        alert = Alert.query.filter_by(id=data["alert_id"], user_id=current_user_id).first()

        if not alert:
            return jsonify({"msg": "Alert not found."}), 404

        db.session.delete(alert)
        db.session.commit()
        return jsonify({"msg": "Alert deleted successfully."}), 200

    return handle_alert_operation(delete)


@bp.route("/list", methods=["GET"])
@jwt_required()
def list_alerts():
    def get_alert_data(alert, user):
        alert_data = {
            "id": alert.id,
            "user_id": alert.user_id,
            "target_amount": alert.target_amount,
            "alert_threshold": alert.alert_threshold,
            "balance_drop_threshold": alert.balance_drop_threshold,
        }

        if alert.target_amount is not None:
            progress = (user.balance / alert.target_amount) * 100 if alert.target_amount > 0 else 0
            alert_data["progress"] = round(progress, 2)
            alert_data["status"] = "TRIGGERED" if user.balance >= alert.alert_threshold else "PENDING"

        if alert.balance_drop_threshold is not None:
            alert_data["status"] = "PENDING"

        return alert_data

    def list_all():
        current_user_id = get_current_user_id()
        user = User.query.get(current_user_id)
        alerts = Alert.query.filter_by(user_id=current_user_id).all()

        alerts_list = [get_alert_data(alert, user) for alert in alerts]
        return jsonify({"data": alerts_list}), 200

    return handle_alert_operation(list_all)
