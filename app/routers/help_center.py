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

from app.models import (
    SupportTicket,
    SupportTicketMessage,
)

from app.schemas import (
    SupportTicketResponse,
    SupportTicketListItem,
    SupportTicketListResponse,
    SupportTicketMessageResponse,
    SupportTicketDetailsResponse,
)

from app.utils.spaces import (
    upload_support_ticket_file,
    generate_support_ticket_url,
)


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

    next_id = (
        1
        if not last_ticket
        else last_ticket.id + 1
    )

    ticket_number = f"TKT-{next_id:06d}"

    # --------------------------------------------------------
    # Upload attachment
    # --------------------------------------------------------

    attachment_key = None

    if attachment and attachment.filename:

        attachment_key = upload_support_ticket_file(
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
        attachment=attachment_key,
        status="OPEN",
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # --------------------------------------------------------
    # Generate display URL
    # --------------------------------------------------------

    attachment_url = generate_support_ticket_url(
        ticket.attachment
    )

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

        attachment_url = (
            generate_support_ticket_url(
                ticket.attachment
            )
            if ticket.attachment
            else None
        )

        ticket_list.append(
            SupportTicketListItem(
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                subject=ticket.subject,
                message=ticket.message,
                attachment=attachment_url,
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
    # Check status
    # --------------------------------------------------------

    if ticket.status == "CLOSED":
        raise HTTPException(
            status_code=400,
            detail="This ticket is closed",
        )

    # --------------------------------------------------------
    # Upload attachment
    # --------------------------------------------------------

    attachment_key = None

    if attachment and attachment.filename:

        attachment_key = upload_support_ticket_file(
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
        attachment=attachment_key,
        sender_type="USER",
    )

    db.add(reply)

    # --------------------------------------------------------
    # Update ticket
    # --------------------------------------------------------

    ticket.status = "OPEN"

    db.commit()
    db.refresh(reply)

    # --------------------------------------------------------
    # Generate attachment URL
    # --------------------------------------------------------

    attachment_url = (
        generate_support_ticket_url(
            reply.attachment
        )
        if reply.attachment
        else None
    )

    return {
        "message": "Reply submitted successfully",
        "reply_id": reply.id,
        "ticket_id": ticket.id,
        "status": ticket.status,
        "attachment": attachment_url,
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
    # Get replies
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Ticket attachment URL
    # --------------------------------------------------------

    ticket_attachment_url = (
        generate_support_ticket_url(
            ticket.attachment
        )
        if ticket.attachment
        else None
    )

    # --------------------------------------------------------
    # Reply list
    # --------------------------------------------------------

    reply_list = []

    for reply in replies:

        reply_attachment_url = (
            generate_support_ticket_url(
                reply.attachment
            )
            if reply.attachment
            else None
        )

        reply_list.append(
            SupportTicketMessageResponse(
                id=reply.id,
                user_id=reply.user_id,
                message=reply.message,
                attachment=reply_attachment_url,
                sender_type=reply.sender_type,
                created_at=reply.created_at,
            )
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return SupportTicketDetailsResponse(
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        user_id=ticket.user_id,
        subject=ticket.subject,
        message=ticket.message,
        attachment=ticket_attachment_url,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        replies=reply_list,
    )