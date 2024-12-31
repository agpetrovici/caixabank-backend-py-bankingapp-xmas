from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.utils.utils_exchange import get_exchange_data


bp = Blueprint("transfers", __name__, url_prefix="/api/transfers")

# region task 3


@bp.route("/simulate", methods=["POST"])
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
            return jsonify({"msg": "Invalid currencies or no exchange data available."}), 404

        # Calculate final amount using formula: target_amount = source_amount × (1-fee) × rate
        final_amount = amount * (1 - fee) * rate

        return jsonify({"msg": f"Amount in target currency: {final_amount:.2f}"}), 201

    except ValueError:
        return jsonify({"msg": "Invalid amount value."}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@bp.route("/fees", methods=["GET"])
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
            return jsonify({"msg": "No fee information available for these currencies."}), 404

        return jsonify({"fee": fee}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@bp.route("/rates", methods=["GET"])
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
            return jsonify({"msg": "No exchange rate available for these currencies."}), 404

        return jsonify({"rate": rate}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


# endregion
