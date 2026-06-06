_CUSTOMER_DATABASE: dict[str, dict[str, str]] = {
    "premium@example.com": {"plan": "Premium", "status": "Active"},
    "basic@example.com": {"plan": "Basic", "status": "Active"},
}

_DEFAULT_CUSTOMER: dict[str, str] = {"plan": "Unknown", "status": "Unknown"}


def lookup_customer(email: str) -> dict[str, str]:
    return _CUSTOMER_DATABASE.get(email.lower(), _DEFAULT_CUSTOMER)
