# Verification Report

**Project:** AI Customer Support & Ticket Routing Agent  
**Date:** 2026-06-06  
**Method:** In-process TestClient with mocked OpenAI layer (no API key required)  
**Result:** 90 / 90 checks passed &nbsp;|&nbsp; 18 / 18 unit tests passed

---

## Diagrams

| Diagram | File |
|---|---|
| System Architecture | [diagrams/architecture.png](diagrams/architecture.png) |
| Ticket Processing Workflow | [diagrams/workflow.png](diagrams/workflow.png) |

---

## Test Tickets

Five realistic scenarios covering every category and routing path were submitted through the full pipeline.

| # | Customer | Scenario | Category | Priority | Assigned Team |
|---|---|---|---|---|---|
| 1 | Sarah Chen | Duplicate subscription charge — refund requested | Billing | High | Billing Team |
| 2 | Marcus Webb | iOS 18.2 app crash on file attach, workflow blocked | Technical | High | Technical Support |
| 3 | Priya Nair | Account locked 3 days, password reset not arriving, demo tomorrow | Account Access | High | Customer Success |
| 4 | David Okonkwo | Dark mode request, offers to beta test | Feature Request | Low | Product Team |
| 5 | Elena Russo | Agency evaluating Basic vs Premium plans | General Inquiry | Low | General Support |

---

## Phase Results

### Phase 1 — Ticket Creation (35 checks)

Verified for every ticket submitted via `POST /tickets`:

- HTTP 200 response
- `category` matches expected classification
- `priority` matches expected level
- `assigned_team` matches the routing table
- `summary` is present and non-empty
- `suggested_response` is present and non-empty
- `ticket_id` is a positive integer

All 5 × 7 = **35 checks passed**.

---

### Phase 2 — Individual Retrieval (45 checks)

Verified for every ticket retrieved via `GET /tickets/{id}`:

- HTTP 200 response
- `customer_name` matches submitted value
- `email` matches submitted value
- `message` stored verbatim (no truncation or transformation)
- `analysis` object is present
- `analysis.category` matches Phase 1 result
- `analysis.assigned_team` matches Phase 1 result
- `analysis.ticket_id` FK links to the correct parent ticket
- `analysis.summary` is present and non-empty

All 5 × 9 = **45 checks passed**.

---

### Phase 3 — List Endpoint (6 checks)

Verified via `GET /tickets`:

- HTTP 200 response
- Exactly 5 tickets returned
- All 5 ticket IDs present in the list
- Every ticket carries a nested `analysis` object
- All 5 category values present across the list
- All 5 team assignments present across the list

**6 / 6 checks passed**.

---

### Phase 4 — Error Handling (4 checks)

| Test | Expected | Result |
|---|---|---|
| `GET /tickets/9999` | 404 Not Found | PASS |
| `POST /tickets` with only `customer_name` | 422 Unprocessable Entity | PASS |
| `POST /tickets` with `email: "not-an-email"` | 422 Unprocessable Entity | PASS |
| `POST /tickets` with `message: ""` | 422 Unprocessable Entity | PASS |

**4 / 4 checks passed**.

---

## Bug Found and Fixed

The empty-message check (Phase 4, last row) **initially failed**.

**Root cause:** Pydantic's `str` type accepts empty strings by default. A ticket with `"message": ""` was passing validation and reaching the database.

**Fix applied** in [app/schemas/ticket.py](app/schemas/ticket.py):

```python
# Before
class TicketCreate(BaseModel):
    customer_name: str
    email: EmailStr
    message: str

# After
class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1)
    email: EmailStr
    message: str = Field(min_length=1)
```

After this change all 90 checks passed and the 18 unit tests remained green.

---

## Unit Test Suite

```
tests/test_ai_parser.py     6 passed
tests/test_routes.py        6 passed
tests/test_routing.py       6 passed
─────────────────────────────
Total                      18 passed
```

### Coverage by module

| Module | Tests |
|---|---|
| `app/services/ai_service.py` | Valid JSON parse, markdown fence, prose-embedded JSON, invalid JSON error, malformed object error |
| `app/routes/tickets.py` | Health check, valid creation, invalid payload, empty list, 404, full create+retrieve round-trip |
| `app/services/routing_service.py` | All 5 categories, unknown category fallback |

---

## Routing Coverage

All 5 category → team mappings exercised:

| Category | Team |
|---|---|
| Billing | Billing Team |
| Technical | Technical Support |
| Account Access | Customer Success |
| Feature Request | Product Team |
| General Inquiry | General Support |

---

## How to Reproduce

```bash
# End-to-end scenario runner (no API key needed)
python verify_tickets.py

# Unit test suite
pytest -v
```
