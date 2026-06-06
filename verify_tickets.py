"""
End-to-end verification of the support ticket pipeline.

Runs 5 realistic tickets through the full workflow:
  POST /tickets  ->  classification  ->  routing  ->  storage
  GET  /tickets/{id}  ->  retrieval verification
  GET  /tickets        ->  list verification

The OpenAI layer is patched with canned responses so no API key is required.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# ---------------------------------------------------------------------------
# In-memory database (isolated from support.db)
# ---------------------------------------------------------------------------

_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(bind=_engine)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db

# ---------------------------------------------------------------------------
# 5 realistic tickets with hand-crafted AI responses
# ---------------------------------------------------------------------------

TICKETS = [
    {
        "input": {
            "customer_name": "Sarah Chen",
            "email": "premium@example.com",
            "message": (
                "I've just noticed my credit card was charged twice for this month's "
                "subscription -- once on the 1st and again on the 3rd. Please issue a "
                "refund for the duplicate charge as soon as possible."
            ),
        },
        "ai_response": {
            "category": "Billing",
            "priority": "High",
            "summary": "Customer was charged twice for their subscription in the same month and is requesting a refund.",
            "suggested_response": (
                "Hi Sarah, thank you for flagging this. I can confirm we've identified the "
                "duplicate charge on your account and have initiated a full refund. You should "
                "see the credit within 3-5 business days. We sincerely apologise for the inconvenience."
            ),
        },
        "expected_team": "Billing Team",
    },
    {
        "input": {
            "customer_name": "Marcus Webb",
            "email": "basic@example.com",
            "message": (
                "The iOS app crashes every single time I try to attach a file to a ticket. "
                "I'm on iPhone 15 Pro running iOS 18.2. This has been happening for the past "
                "two days and is blocking my entire workflow."
            ),
        },
        "ai_response": {
            "category": "Technical",
            "priority": "High",
            "summary": "App crashes on iOS 18.2 when attaching files, blocking the customer's workflow for two days.",
            "suggested_response": (
                "Hi Marcus, I'm sorry for the disruption. Our engineering team has been made "
                "aware of a file-attachment crash on iOS 18.2 and a fix is being deployed today. "
                "In the meantime, please try attaching files via the web app at app.example.com. "
                "We'll notify you as soon as the iOS update is live."
            ),
        },
        "expected_team": "Technical Support",
    },
    {
        "input": {
            "customer_name": "Priya Nair",
            "email": "priya.nair@company.io",
            "message": (
                "I've been completely locked out of my account for the past three days. "
                "Password reset emails are not arriving -- I've checked spam as well. "
                "I have an important client demo tomorrow and urgently need access restored."
            ),
        },
        "ai_response": {
            "category": "Account Access",
            "priority": "High",
            "summary": "Customer locked out for three days with password reset emails not delivering, and a critical demo tomorrow.",
            "suggested_response": (
                "Hi Priya, I understand how urgent this is. I've manually triggered a password "
                "reset link which has been sent to your registered email from a different sender "
                "domain -- please check within the next 10 minutes. If it still doesn't arrive, "
                "reply to this message and we'll restore access directly for you before your demo."
            ),
        },
        "expected_team": "Customer Success",
    },
    {
        "input": {
            "customer_name": "David Okonkwo",
            "email": "david@startup.dev",
            "message": (
                "Our whole team works late evenings and the white dashboard is really straining "
                "our eyes. Would it be possible to add a dark mode option? I think a lot of "
                "your users would appreciate this. Happy to beta test if you need volunteers."
            ),
        },
        "ai_response": {
            "category": "Feature Request",
            "priority": "Low",
            "summary": "Customer requests a dark mode for the dashboard and offers to beta test it.",
            "suggested_response": (
                "Hi David, thanks for the suggestion and for offering to help test it -- we love "
                "that kind of engagement! Dark mode is already on our product roadmap. I've added "
                "your upvote and flagged your interest in beta testing to the product team. We'll "
                "reach out when we're ready to run a preview."
            ),
        },
        "expected_team": "Product Team",
    },
    {
        "input": {
            "customer_name": "Elena Russo",
            "email": "elena.russo@agency.com",
            "message": (
                "Hi, I'm evaluating your service for our agency. Could you explain the main "
                "differences between the Basic and Premium plans, specifically around API rate "
                "limits, number of team seats, and SLA guarantees? We manage about 15 clients."
            ),
        },
        "ai_response": {
            "category": "General Inquiry",
            "priority": "Low",
            "summary": "Prospective agency customer comparing Basic vs Premium plans on rate limits, seats, and SLA.",
            "suggested_response": (
                "Hi Elena, great to hear from you! For an agency managing 15 clients, our Premium "
                "plan is the right fit: it includes 500k API calls/month (vs 50k on Basic), "
                "unlimited team seats, and a 99.9% uptime SLA with priority support. I'd love to "
                "set up a 20-minute call to walk you through it."
            ),
        },
        "expected_team": "General Support",
    },
]

# ---------------------------------------------------------------------------
# Verification helpers
# ---------------------------------------------------------------------------

_results: list[bool] = []


def check(label: str, condition: bool) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"    [{status}]  {label}")
    _results.append(condition)
    return condition


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run() -> bool:
    created_ids: list[int] = []

    with TestClient(app) as client:

        # ------------------------------------------------------------------ #
        #  PHASE 1 -- Create all 5 tickets                                    #
        # ------------------------------------------------------------------ #
        section("PHASE 1 -- Ticket Creation & Pipeline Verification")

        for i, scenario in enumerate(TICKETS, start=1):
            name = scenario["input"]["customer_name"]
            preview = scenario["input"]["message"][:75]
            print(f"Ticket {i}: {name}")
            print(f'  Message: "{preview}..."')

            with patch("app.routes.tickets.analyze_ticket", return_value=scenario["ai_response"]):
                resp = client.post("/tickets", json=scenario["input"])

            ok = check("POST /tickets returns 200", resp.status_code == 200)
            data = resp.json()
            created_ids.append(data.get("ticket_id", -1))

            check(
                f"category = {scenario['ai_response']['category']!r}",
                data.get("category") == scenario["ai_response"]["category"],
            )
            check(
                f"priority = {scenario['ai_response']['priority']!r}",
                data.get("priority") == scenario["ai_response"]["priority"],
            )
            check(
                f"assigned_team = {scenario['expected_team']!r}",
                data.get("assigned_team") == scenario["expected_team"],
            )
            check("summary is non-empty", bool(data.get("summary")))
            check("suggested_response is non-empty", bool(data.get("suggested_response")))
            check("ticket_id is a positive integer",
                  isinstance(data.get("ticket_id"), int) and data["ticket_id"] > 0)

            tag = f"[{data.get('category')} / {data.get('priority')} / {data.get('assigned_team')}]"
            print(f"  -> ticket_id={data.get('ticket_id')}  {tag}\n")

        # ------------------------------------------------------------------ #
        #  PHASE 2 -- Individual retrieval                                    #
        # ------------------------------------------------------------------ #
        section("PHASE 2 -- Individual Retrieval (GET /tickets/{id})")

        for ticket_id, scenario in zip(created_ids, TICKETS):
            name = scenario["input"]["customer_name"]
            print(f"GET /tickets/{ticket_id}  ({name})")
            resp = client.get(f"/tickets/{ticket_id}")

            check("returns 200", resp.status_code == 200)
            data = resp.json()
            check(f"customer_name = {name!r}", data.get("customer_name") == name)
            check(f"email = {scenario['input']['email']!r}",
                  data.get("email") == scenario["input"]["email"])
            check("original message stored correctly",
                  data.get("message") == scenario["input"]["message"])
            check("analysis object present", data.get("analysis") is not None)

            if data.get("analysis"):
                a = data["analysis"]
                check(
                    f"analysis.category = {scenario['ai_response']['category']!r}",
                    a.get("category") == scenario["ai_response"]["category"],
                )
                check(
                    f"analysis.assigned_team = {scenario['expected_team']!r}",
                    a.get("assigned_team") == scenario["expected_team"],
                )
                check("analysis.ticket_id matches parent", a.get("ticket_id") == ticket_id)
                check("analysis.summary stored", bool(a.get("summary")))
            print()

        # ------------------------------------------------------------------ #
        #  PHASE 3 -- List endpoint                                           #
        # ------------------------------------------------------------------ #
        section("PHASE 3 -- List Endpoint (GET /tickets)")

        resp = client.get("/tickets")
        check("returns 200", resp.status_code == 200)
        data = resp.json()
        check(f"returns exactly {len(TICKETS)} tickets", len(data) == len(TICKETS))
        check("all ticket IDs present", set(t["id"] for t in data) == set(created_ids))
        check("every ticket has an analysis", all(t.get("analysis") is not None for t in data))

        categories_found = sorted(t["analysis"]["category"] for t in data)
        categories_expected = sorted(s["ai_response"]["category"] for s in TICKETS)
        check(f"all 5 categories present: {categories_expected}", categories_found == categories_expected)

        teams_found = sorted(t["analysis"]["assigned_team"] for t in data)
        teams_expected = sorted(s["expected_team"] for s in TICKETS)
        check(f"all 5 teams assigned: {teams_expected}", teams_found == teams_expected)
        print()

        # ------------------------------------------------------------------ #
        #  PHASE 4 -- Error handling                                          #
        # ------------------------------------------------------------------ #
        section("PHASE 4 -- Error Handling")

        print("404 for non-existent ticket")
        check("GET /tickets/9999 returns 404", client.get("/tickets/9999").status_code == 404)
        print()

        print("422 for missing required fields")
        check("POST with only customer_name returns 422",
              client.post("/tickets", json={"customer_name": "Ghost"}).status_code == 422)
        print()

        print("422 for invalid email format")
        check("POST with malformed email returns 422",
              client.post("/tickets", json={
                  "customer_name": "Bad",
                  "email": "not-an-email",
                  "message": "Test",
              }).status_code == 422)
        print()

        print("422 for empty message body")
        check("POST with empty message string returns 422",
              client.post("/tickets", json={
                  "customer_name": "Empty",
                  "email": "e@example.com",
                  "message": "",
              }).status_code == 422)
        print()

        # ------------------------------------------------------------------ #
        #  Summary                                                            #
        # ------------------------------------------------------------------ #
        total = len(_results)
        passed = sum(_results)
        failed = total - passed

        print("=" * 60)
        print(f"  RESULT: {passed}/{total} checks passed", end="")
        if failed:
            print(f"  ({failed} FAILED)")
        else:
            print("  -- ALL PASSED")
        print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
