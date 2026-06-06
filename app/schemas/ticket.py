from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.analysis import AnalysisResponse


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=1)
    email: EmailStr
    message: str = Field(min_length=1)


class TicketResponse(BaseModel):
    ticket_id: int
    category: str
    priority: str
    assigned_team: str
    summary: str
    suggested_response: str


class TicketDetail(BaseModel):
    id: int
    customer_name: str
    email: str
    message: str
    status: str
    created_at: datetime
    analysis: Optional[AnalysisResponse] = None

    model_config = {"from_attributes": True}
