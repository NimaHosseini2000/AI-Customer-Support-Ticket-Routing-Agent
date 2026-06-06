from app.services.routing_service import route_ticket


def test_billing_routes_correctly():
    assert route_ticket("Billing") == "Billing Team"


def test_technical_routes_correctly():
    assert route_ticket("Technical") == "Technical Support"


def test_account_access_routes_correctly():
    assert route_ticket("Account Access") == "Customer Success"


def test_feature_request_routes_correctly():
    assert route_ticket("Feature Request") == "Product Team"


def test_general_inquiry_routes_correctly():
    assert route_ticket("General Inquiry") == "General Support"


def test_unknown_category_falls_back_to_general_support():
    assert route_ticket("Unknown Category") == "General Support"
