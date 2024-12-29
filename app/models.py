from os import getenv
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(engine_options={"url": getenv("SQLALCHEMY_DATABASE_URI")})


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=0.0)


class RecurringExpense(db.Model):
    __tablename__ = "recurring_expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    expense_name = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(timezone.utc),
    )


class Alert(db.Model):
    """Model for user alerts including savings goals and balance drop thresholds"""

    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_amount = db.Column(db.Float, nullable=True)  # For savings goal alerts
    alert_threshold = db.Column(db.Float, nullable=True)  # For savings goal alerts
    balance_drop_threshold = db.Column(
        db.Float, nullable=True
    )  # For balance drop alerts
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationship with User model
    user = db.relationship("User", backref=db.backref("alerts", lazy=True))

    def __repr__(self):
        return f"<Alert {self.id} for user {self.user_id}>"

    def to_dict(self):
        """Convert alert object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_amount": self.target_amount,
            "alert_threshold": self.alert_threshold,
            "balance_drop_threshold": self.balance_drop_threshold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    """Model for user transactions with fraud detection"""

    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(
        db.DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    fraud = db.Column(db.Boolean, default=False)

    # Relationship with User model
    user = db.relationship("User", backref=db.backref("transactions", lazy=True))

    def __repr__(self):
        return f"<Transaction {self.id} for user {self.user_id}>"

    def to_dict(self):
        """Convert transaction object to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "category": self.category,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "fraud": self.fraud,
        }
