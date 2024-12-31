from datetime import datetime, timedelta
from app.models import Transaction


def check_high_deviation(user_id: int, amount: float, timestamp: datetime) -> bool:
    """Check if transaction amount exceeds 3 standard deviations from 90-day average"""

    # Get transactions from last 90 days
    ninety_days_ago = timestamp - timedelta(days=90)
    past_transactions: list[Transaction] = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.timestamp >= ninety_days_ago,
        Transaction.timestamp < timestamp,
    ).all()

    if not past_transactions:
        return False

    # Calculate daily spending statistics
    daily_amounts = {}
    for trans in past_transactions:
        date_key = trans.timestamp.date()
        daily_amounts[date_key] = daily_amounts.get(date_key, 0) + trans.amount

    daily_spends = list(daily_amounts.values())
    avg_daily = sum(daily_spends) / len(daily_spends)
    std_dev = (sum((x - avg_daily) ** 2 for x in daily_spends) / len(daily_spends)) ** 0.5

    # Check if amount exceeds 3 standard deviations
    return amount > (avg_daily + (3 * std_dev))


def check_unusual_category(user_id: int, category: str, timestamp: datetime) -> bool:
    """Check if category hasn't been used in last 6 months"""

    six_months_ago = timestamp - timedelta(days=180)
    past_categories = (
        Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.timestamp >= six_months_ago,
            Transaction.timestamp < timestamp,
        )
        .with_entities(Transaction.category)
        .distinct()
        .all()
    )

    past_categories = {cat[0] for cat in past_categories}
    return category not in past_categories


def check_rapid_transactions(user_id: int, amount: float, timestamp: datetime) -> bool:
    """Check for suspicious rapid transactions"""

    # Get transactions in last 5 minutes
    five_mins_ago = timestamp - timedelta(minutes=5)
    recent_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.timestamp >= five_mins_ago,
        Transaction.timestamp < timestamp,
    ).all()

    if len(recent_transactions) < 3:
        return False

    # Calculate daily average spend
    day_ago = timestamp - timedelta(days=1)
    past_day_transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.timestamp >= day_ago,
        Transaction.timestamp < timestamp,
    ).all()

    if not past_day_transactions:
        return False

    daily_avg = sum(t.amount for t in past_day_transactions) / len(past_day_transactions)

    # Check if combined recent amounts exceed daily average
    recent_total = sum(t.amount for t in recent_transactions) + amount
    return recent_total > daily_avg
