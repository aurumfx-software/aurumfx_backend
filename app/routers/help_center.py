from app.utils.spaces import upload_support_ticket_file

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.models import User, SupportTicket, SupportTicketMessage
from app.schemas import SupportTicketResponse, SupportTicketListItem, SupportTicketListResponse, SupportTicketMessageResponse, SupportTicketDetailsResponse


router = APIRouter(
    prefix="/user/help-center",
    tags=["User Help Center"],
)


# ============================================================
# CREATE SUPPORT TICKET
# ============================================================

@router.post(
    "/tickets",
    response_model=SupportTicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_support_ticket(
    subject: str = Form(...),
    message: str = Form(...),
    attachment: UploadFile | None = File(None),

    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):

    # --------------------------------------------------------
    # Validate subject
    # --------------------------------------------------------

    subject = subject.strip()

    if not subject:
        raise HTTPException(
            status_code=400,
            detail="Subject is required",
        )

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    message = message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message is required",
        )

    # --------------------------------------------------------
    # Generate ticket number
    # --------------------------------------------------------

    last_ticket = (
        db.query(SupportTicket)
        .order_by(SupportTicket.id.desc())
        .first()
    )

    next_id = 1 if not last_ticket else last_ticket.id + 1

    ticket_number = f"TKT-{next_id:06d}"

    # --------------------------------------------------------
    # Upload optional attachment to DigitalOcean Spaces
    # --------------------------------------------------------

    attachment_url = None

    if attachment and attachment.filename:

        attachment_url = upload_support_ticket_file(
            file=attachment,
            user_id=current_user,
        )

    # --------------------------------------------------------
    # Create ticket
    # --------------------------------------------------------

    ticket = SupportTicket(
        ticket_number=ticket_number,
        user_id=current_user,
        subject=subject,
        message=message,
        attachment=attachment_url,
        status="OPEN",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return SupportTicketResponse(
        message="Ticket created successfully",
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        status=ticket.status,
    )

# ============================================================
# GET MY SUPPORT TICKETS
# ============================================================

@router.get(
    "/tickets",
    response_model=SupportTicketListResponse,
)
def get_my_support_tickets(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get all support tickets created by the logged-in user.
    """

    tickets = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.user_id == current_user
        )
        .order_by(
            SupportTicket.created_at.desc()
        )
        .all()
    )

    ticket_list = []

    for ticket in tickets:
        ticket_list.append(
            SupportTicketListItem(
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                subject=ticket.subject,
                message=ticket.message,
                attachment=ticket.attachment,
                status=ticket.status,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
            )
        )

    return SupportTicketListResponse(
        tickets=ticket_list
    )

# ============================================================
# USER REPLY TO TICKET
# ============================================================

@router.post(
    "/tickets/{ticket_id}/reply",
)
async def user_reply_to_ticket(
    ticket_id: int,

    message: str = Form(...),

    attachment: UploadFile | None = File(None),

    db: Session = Depends(get_db),

    current_user: str = Depends(get_current_user),
):
    """
    User replies to their own support ticket.
    """

    # --------------------------------------------------------
    # Validate message
    # --------------------------------------------------------

    message = message.strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Message is required",
        )

    # --------------------------------------------------------
    # Get ticket
    # --------------------------------------------------------

    ticket = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == current_user,
        )
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    # --------------------------------------------------------
    # Check ticket status
    # --------------------------------------------------------

    if ticket.status == "CLOSED":
        raise HTTPException(
            status_code=400,
            detail="This ticket is closed",
        )

    # --------------------------------------------------------
    # Upload optional attachment
    # --------------------------------------------------------

    attachment_url = None

    if attachment and attachment.filename:

        attachment_url = upload_support_ticket_file(
            file=attachment,
            user_id=current_user,
        )

    # --------------------------------------------------------
    # Create reply
    # --------------------------------------------------------

    reply = SupportTicketMessage(
        ticket_id=ticket.id,
        user_id=current_user,
        message=message,
        attachment=attachment_url,
        sender_type="USER",
    )

    db.add(reply)

    # --------------------------------------------------------
    # Update ticket status
    # --------------------------------------------------------

    ticket.status = "OPEN"

    db.commit()

    db.refresh(reply)

    return {
        "message": "Reply submitted successfully",
        "reply_id": reply.id,
        "ticket_id": ticket.id,
        "status": ticket.status,
    }

# ============================================================
# GET USER TICKET DETAILS
# ============================================================

@router.get(
    "/tickets/{ticket_id}",
    response_model=SupportTicketDetailsResponse,
)
def get_user_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    ticket = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.id == ticket_id,
            SupportTicket.user_id == current_user,
        )
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    replies = (
        db.query(SupportTicketMessage)
        .filter(
            SupportTicketMessage.ticket_id == ticket.id
        )
        .order_by(
            SupportTicketMessage.created_at.asc()
        )
        .all()
    )

    reply_list = [
        SupportTicketMessageResponse(
            id=reply.id,
            user_id=reply.user_id,
            message=reply.message,
            attachment=reply.attachment,
            sender_type=reply.sender_type,
            created_at=reply.created_at,
        )
        for reply in replies
    ]

    return SupportTicketDetailsResponse(
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        user_id=ticket.user_id,
        subject=ticket.subject,
        message=ticket.message,
        attachment=ticket.attachment,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        replies=reply_list,
    )