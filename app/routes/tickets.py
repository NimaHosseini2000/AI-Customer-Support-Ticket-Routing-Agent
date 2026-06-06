from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.analysis import TicketAnalysis
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate, TicketDetail, TicketResponse
from app.services.ai_service import analyze_ticket
from app.services.customer_lookup_service import lookup_customer
from app.services.notification_service import send_notification
from app.services.routing_service import route_ticket

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}")
    return {"status": "ok"}


@router.post("/tickets", response_model=TicketResponse)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(
        customer_name=payload.customer_name,
        email=payload.email,
        message=payload.message,
    )
    db.add(ticket)
    db.flush()  # populates ticket.id within the open transaction; nothing committed yet

    customer_info = lookup_customer(payload.email)

    try:
        analysis_data = analyze_ticket(
            message=payload.message,
            customer_plan=customer_info["plan"],
            customer_status=customer_info["status"],
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc))
    except (RuntimeError, EnvironmentError) as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc))

    assigned_team = route_ticket(analysis_data["category"])

    analysis = TicketAnalysis(
        ticket_id=ticket.id,
        category=analysis_data["category"],
        priority=analysis_data["priority"],
        summary=analysis_data["summary"],
        suggested_response=analysis_data["suggested_response"],
        assigned_team=assigned_team,
    )
    db.add(analysis)
    db.commit()  # single commit: ticket + analysis land together or not at all

    send_notification(
        category=analysis_data["category"],
        priority=analysis_data["priority"],
        assigned_team=assigned_team,
    )

    return TicketResponse(
        ticket_id=ticket.id,
        category=analysis_data["category"],
        priority=analysis_data["priority"],
        assigned_team=assigned_team,
        summary=analysis_data["summary"],
        suggested_response=analysis_data["suggested_response"],
    )


@router.get("/tickets", response_model=List[TicketDetail])
def get_all_tickets(db: Session = Depends(get_db)):
    return (
        db.query(Ticket)
        .options(joinedload(Ticket.analysis))
        .order_by(Ticket.id.desc())
        .all()
    )


@router.get("/tickets/{ticket_id}", response_model=TicketDetail)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = (
        db.query(Ticket)
        .options(joinedload(Ticket.analysis))
        .filter(Ticket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    return ticket
