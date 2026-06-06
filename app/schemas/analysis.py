from datetime import datetime

from pydantic import BaseModel


class AnalysisResponse(BaseModel):
    id: int
    ticket_id: int
    category: str
    priority: str
    summary: str
    suggested_response: str
    assigned_team: str
    created_at: datetime

    model_config = {"from_attributes": True}
