from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TicketAnalysis(Base):
    __tablename__ = "ticket_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False, unique=True)
    category = Column(String(100), nullable=False)
    priority = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    suggested_response = Column(Text, nullable=False)
    assigned_team = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ticket = relationship("Ticket", back_populates="analysis")
