from datetime import datetime, timezone, timedelta
from typing import List

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models import db, RecurringExpense
from app.utils.utils_auth import get_current_user_id

bp = Blueprint("recurring-expenses", __name__, url_prefix="/api/recurring-expenses")

# region task 2


@bp.route("/", methods=["POST"])
@jwt_required()
def add_recurring_expense():
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


@bp.route("/", methods=["GET"])
@jwt_required()
def get_recurring_expenses():
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

        return jsonify({"data": expenses_list}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


@bp.route("/<int:expense_id>", methods=["PUT"])
@jwt_required()
def update_recurring_expense(expense_id):
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


@bp.route("/<int:expense_id>", methods=["DELETE"])
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


@bp.route("/projection", methods=["GET"])
@jwt_required()
def get_expenses_projection():
    try:
        current_user_id = get_current_user_id()

        # Get all recurring expenses for the user
        # Get current user's balance
        # user = User.query.get(current_user_id)
        # current_balance = user.balance
        expenses: List[RecurringExpense] = RecurringExpense.query.filter_by(
            user_id=current_user_id
        ).all()

        # Start from next month
        start_date = datetime.now(timezone.utc).replace(day=1) + timedelta(days=32)
        start_date = start_date.replace(day=1)  # Ensure first day of the month
        projections = []
        total_amount = 0.0

        # Calculate for next 12 months
        for month_offset in range(12):
            # Calculate target month
            target_date = start_date + timedelta(days=32 * month_offset)
            target_date = target_date.replace(day=1)  # First day of month

            # Format as YYYY-MM
            month_key = target_date.strftime("%Y-%m")

            # Calculate total recurring expenses for this month
            partial_amount = 0.0

            for expense in expenses:
                if expense.frequency == "monthly":
                    # Monthly expenses are included if created after start_date
                    if expense.start_date.replace(tzinfo=timezone.utc) >= start_date:
                        partial_amount += expense.amount

                elif expense.frequency == "yearly":
                    # Yearly expenses only included on their anniversary month
                    if (
                        target_date.month == expense.start_date.month
                        and target_date.year >= expense.start_date.year
                    ):
                        partial_amount += expense.amount

            # Calculate projected balance by subtracting recurring expenses (because positive values are expenses and negative are income)
            # current_balance -= total_amount
            # current_balance = round(current_balance, 2)
            total_amount += partial_amount
            projections.append(
                {
                    "month": month_key,
                    "recurring_expenses": total_amount,
                }
            )

        return jsonify({"data": projections}), 200

    except Exception as e:
        return jsonify({"msg": str(e)}), 400


# endregion
