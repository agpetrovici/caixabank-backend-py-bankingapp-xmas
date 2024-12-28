import csv
import sys
from pathlib import Path
import pytest

# Add the parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.blueprints.api.is_valid_email import is_valid_email


def load_test_emails():
    """Load test emails from CSV file."""
    test_data_path = Path(__file__).parent / "data" / "test_emails.csv"
    test_cases = []

    with open(test_data_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row["email"]
            expected = row["is_valid"].lower() == "true"
            test_cases.append((email, expected))

    return test_cases


@pytest.mark.parametrize("email,expected", load_test_emails())
def test_email_validation(email, expected):
    """Test email validation against test cases from CSV file."""
    assert is_valid_email(email) == expected


def test_invalid_input_types():
    """Test invalid input types."""
    assert not is_valid_email(None)
    assert not is_valid_email(123)
    assert not is_valid_email([])
    assert not is_valid_email({})


def test_empty_input():
    """Test empty input."""
    assert not is_valid_email("")
    assert not is_valid_email("   ")


def test_max_length_constraints():
    """Test email length constraints."""
    # Test email exceeding total length limit (254 characters)
    local_part = "a" * 64
    domain = "b" * 190
    long_email = f"{local_part}@{domain}.com"
    assert not is_valid_email(long_email)

    # Test local part exceeding length limit (64 characters)
    local_part = "a" * 65
    long_local_email = f"{local_part}@example.com"
    assert not is_valid_email(long_local_email)


if __name__ == "__main__":
    pytest.main([__file__])
