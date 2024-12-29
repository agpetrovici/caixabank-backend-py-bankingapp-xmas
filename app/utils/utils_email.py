from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def send_alert_email(user_email: str, user_name: str, alert_type: str, **kwargs):
    """Send alert email based on type"""

    if alert_type == "savings":
        subject = "Savings Goal Alert"
        template = f"""
        Dear {user_name},

        Great news! Your savings are nearing the target amount of {kwargs.get('alert_target_amount', 0)}.
        Keep up the great work and stay consistent!

        Best Regards,
        The Management Team
        """
    else:  # balance_drop
        subject = "Balance Drop Alert"
        template = f"""
        Dear {user_name},

        We noticed a significant balance drop in your account more than {kwargs.get('alert_balance_drop_threshold', 0)}.
        If this wasn't you, please review your recent transactions to ensure everything is correct.

        Best Regards,
        The Management Team
        """

    msg = Message(
        subject=subject,
        sender=current_app.config["MAIL_DEFAULT_SENDER"],
        recipients=[user_email],
        body=template,
    )

    mail.send(msg)
