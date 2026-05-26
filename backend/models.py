from pydantic import BaseModel
from typing import Optional, List


class TextInput(BaseModel):
    user_text: str


class TicketData(BaseModel):
    project_key:    str
    summary:        str
    description:    str
    issue_type:     str
    priority:       str
    reporter_email: Optional[str] = ""
    assignee_email: Optional[str] = ""
    start_date:     Optional[str] = ""
    due_date:       Optional[str] = ""
    epic_link:      Optional[str] = ""
    parent_task:    Optional[str] = ""
    temp_id:        Optional[str] = ""
    temp_parent_id: Optional[str] = ""


class ChangeRequest(BaseModel):
    current_ticket: TicketData
    feedback:       str


class SelectedTickets(BaseModel):
    tickets: List[TicketData]


class CreateSingleTicket(BaseModel):
    ticket: TicketData