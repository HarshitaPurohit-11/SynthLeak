"""
SynthLeak Work-Order Maintenance Dispatch Endpoints.
Implements POST /tickets conforming strictly to CONTRACT.md schemas.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services import TicketService
from shared.schemas import TicketCreateRequest, TicketResponse, StandardErrorResponse

router = APIRouter(tags=["Tickets"])


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Work-Order Maintenance Ticket",
    description="Dispatches a field repair work order associated with an acoustic anomaly alert.",
    responses={
        400: {"model": StandardErrorResponse, "description": "Validation or Pipeline Not Found Error"},
        422: {"description": "Unprocessable Entity (Payload Schema Validation Error)"},
    },
)
def create_ticket(
    request: TicketCreateRequest,
    db: Session = Depends(get_db),
):
    try:
        ticket = TicketService.create_ticket(db, request)
        return ticket
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

