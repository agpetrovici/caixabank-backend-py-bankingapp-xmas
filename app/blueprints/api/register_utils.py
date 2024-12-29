from pyisemail import is_email

# from app.blueprints.api.is_valid_email import is_valid_email

from app.models import User


def validate_registration_data(
    data: dict,
) -> tuple[dict | None, tuple[dict, int] | None]:
    # Check if all required fields are present
    if not all(key in data for key in ["email", "password", "name"]):
        return None, ({"error": "All fields are required."}, 400)

    # Check for null/empty fields
    if not all(data.values()):
        return None, ({"error": "No empty fields allowed."}, 400)

    email = data["email"]
    password = data["password"]
    name = data["name"]

    # Validate email format
    if not is_email(email):
        return None, ({"error": f"Invalid email: {email}"}, 400)

    # Clean email by converting to lowercase and stripping whitespace
    email = email.lower().strip()

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return None, ({"error": "Email already exists."}, 400)

    return {"email": email, "password": password, "name": name}, None
