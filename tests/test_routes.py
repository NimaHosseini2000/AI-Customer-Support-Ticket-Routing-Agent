from unittest.mock import patch

_MOCK_ANALYSIS = {
    "category": "Billing",
    "priority": "High",
    "summary": "Customer reports a duplicate charge on their account.",
    "suggested_response": "We are reviewing the duplicate billing issue and will resolve it within 24 hours.",
}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_ticket_valid(client):
    with patch("app.routes.tickets.analyze_ticket", return_value=_MOCK_ANALYSIS):
        response = client.post(
            "/tickets",
            json={
                "customer_name": "John Smith",
                "email": "john@example.com",
                "message": "I was charged twice this month.",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == 1
    assert data["category"] == "Billing"
    assert data["priority"] == "High"
    assert data["assigned_team"] == "Billing Team"
    assert "summary" in data
    assert "suggested_response" in data


def test_create_ticket_invalid_payload(client):
    response = client.post(
        "/tickets",
        json={"customer_name": "John Smith"},
    )
    assert response.status_code == 422


def test_get_all_tickets_empty(client):
    response = client.get("/tickets")
    assert response.status_code == 200
    assert response.json() == []


def test_get_ticket_not_found(client):
    response = client.get("/tickets/999")
    assert response.status_code == 404


def test_get_ticket_by_id(client):
    with patch("app.routes.tickets.analyze_ticket", return_value=_MOCK_ANALYSIS):
        client.post(
            "/tickets",
            json={
                "customer_name": "Jane Doe",
                "email": "jane@example.com",
                "message": "My password reset email never arrived.",
            },
        )

    response = client.get("/tickets/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["customer_name"] == "Jane Doe"
    assert data["analysis"]["category"] == "Billing"
