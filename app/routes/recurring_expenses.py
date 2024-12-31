from datetime import datetime, timezone, timedelta
from typing import List
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import db, RecurringExpense
from app.utils.utils_auth import get_current_user_id

bp = Blueprint("recurring-expenses", __name__, url_prefix="/api/recurring-expenses")


def validate_request_data(data, required_fields=None):
    """Validate request data and required fields"""
    if not request.is_json:
        return "Content type must be application/json", 415

    if not data:
        return "No data provided.", 400

    if required_fields:
        if not all(field in data for field in required_fields):
            return "No empty fields allowed.", 400
        if any(not data[field] for field in required_fields):
            return "No empty fields allowed.", 400

    return None, None


def create_expense_response(expense, msg):
    """Create standardized response for expense operations"""
    return {
        "msg": msg,
        "data": {
            "id": expense.id,
            "expense_name": expense.expense_name,
            "amount": expense.amount,
            "frequency": expense.frequency,
            "start_date": expense.start_date.strftime("%Y-%m-%d"),
        },
    }


def handle_expense_operation(operation_func):
    """Generic error handler for expense operations"""
    try:
        return operation_func()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": str(e)}), 400


def create_expense_object(data, user_id):
    """Create a new RecurringExpense object from data"""
    start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
    return RecurringExpense(
        user_id=user_id,
        expense_name=data["expense_name"],
        amount=float(data["amount"]),
        frequency=data["frequency"],
        start_date=start_date,
        created_at=datetime.now(timezone.utc),
    )


@bp.route("/", methods=["POST"])
@jwt_required()
def add_recurring_expense():
    def create():
        data = request.get_json()
        error, code = validate_request_data(data, ["expense_name", "amount", "frequency", "start_date"])
        if error:
            return jsonify({"msg": error}), code

        new_expense = create_expense_object(data, get_current_user_id())
        db.session.add(new_expense)
        db.session.commit()

        response = create_expense_response(new_expense, "Recurring expense added successfully.")
        return jsonify(response), 201

    return handle_expense_operation(create)


@bp.route("/", methods=["GET"])
@jwt_required()
def get_recurring_expenses():
    def get_all():
        expenses = RecurringExpense.query.filter_by(user_id=get_current_user_id()).all()
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
        return jsonify({"data": expenses_list}), 200

    return handle_expense_operation(get_all)


@bp.route("/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_recurring_expense(expense_id):
    def update():
        data = request.get_json()
        error, code = validate_request_data(data, ["expense_name", "amount", "frequency", "start_date"])
        if error:
            return jsonify({"msg": error}), code

        expense = RecurringExpense.query.filter_by(id=expense_id, user_id=get_current_user_id()).first()
        if not expense:
            return jsonify({"msg": "Expense not found."}), 404

        start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
        expense.expense_name = data["expense_name"]
        expense.amount = float(data["amount"])
        expense.frequency = data["frequency"]
        expense.start_date = start_date

        db.session.commit()
        response = create_expense_response(expense, "Recurring expense updated successfully.")
        return jsonify(response), 200

    return handle_expense_operation(update)


@bp.route("/<int:expense_id>", methods=["DELETE"])
@jwt_required()
def delete_recurring_expense(expense_id):
    def delete():
        expense = RecurringExpense.query.filter_by(id=expense_id, user_id=get_current_user_id()).first()
        if not expense:
            return jsonify({"msg": "Expense not found."}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({"msg": "Recurring expense deleted successfully."}), 200

    return handle_expense_operation(delete)


def calculate_monthly_expenses(expenses: List[RecurringExpense], target_date: datetime) -> float:
    """Calculate total expenses for a given month"""
    partial_amount = 0.0
    for expense in expenses:
        if expense.frequency == "monthly":
            if expense.start_date.replace(tzinfo=timezone.utc) >= target_date:
                partial_amount += expense.amount
        elif expense.frequency == "yearly":
            if target_date.month == expense.start_date.month and target_date.year >= expense.start_date.year:
                partial_amount += expense.amount
    return partial_amount


@bp.route("/projection", methods=["GET"])
@jwt_required()
def get_expenses_projection():
    def project():
        expenses = RecurringExpense.query.filter_by(user_id=get_current_user_id()).all()

        start_date = datetime.now(timezone.utc).replace(day=1) + timedelta(days=32)
        start_date = start_date.replace(day=1)

        projections = []
        total_amount = 0.0

        for month_offset in range(12):
            target_date = start_date + timedelta(days=32 * month_offset)
            target_date = target_date.replace(day=1)
            month_key = target_date.strftime("%Y-%m")

            partial_amount = calculate_monthly_expenses(expenses, target_date)
            total_amount += partial_amount

            projections.append(
                {
                    "month": month_key,
                    "recurring_expenses": total_amount,
                }
            )

        return jsonify({"data": projections}), 200

    return handle_expense_operation(project)
