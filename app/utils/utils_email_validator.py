import re


def is_valid_email(email: str) -> bool:
    # Check for basic email format using regex
    if not email or not isinstance(email, str):
        return False

    # Remove any leading/trailing whitespace
    email = email.strip()

    # Check length constraints
    if len(email) > 254:  # Maximum length per RFC 5321
        return False

    # Check for exactly one @ symbol
    if email.count("@") != 1:
        return False

    # Split into local and domain parts
    try:
        local, domain = email.rsplit("@", 1)
    except ValueError:
        return False

    # Check local part has at least one character
    if len(local) < 1:
        return False

    if len(domain) < 1:
        return False

    # Check local part ends with alphanumeric character
    if not local[-1].isalnum():
        return False

    # Check local paSrt only contains alphanumeric chars and underscore
    if not all(c.isalnum() or c == "." or c == "_" or c == "-" for c in local):
        return False

    # Check first character before @ and first character after @ is alphanumeric
    if not local[0].isalnum() or not domain[0].isalnum():
        return False

    # Validate lengths of local and domain parts
    if len(local) > 64 or len(domain) > 255:  # RFC 5321
        return False

    # Check for consecutive dots
    if ".." in email:
        return False

    # Validate local part characters
    local_pattern = r"^[a-zA-Z0-9!#$%&\'*+\-/=?^_`{|}~.]+$"
    if not re.match(local_pattern, local):
        return False

    # Validate domain - must have at least one dot and valid characters
    if "." not in domain:
        return False

    domain_pattern = r"^[a-zA-Z0-9.-]+$"
    if not re.match(domain_pattern, domain):
        return False

    # Domain cannot start/end with hyphen or dot
    if domain[0] in ".-" or domain[-1] in ".-":
        return False

    # Check for invalid hyphen-dot or dot-hyphen sequences in domain
    if "-." in domain or ".-" in domain:
        return False
    return True
