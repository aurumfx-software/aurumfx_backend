from fastapi import APIRouter, Depends, File, Form, HTTPException,UploadFile

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import SupportTicket,SupportTicketMessage

from app.utils.spaces import upload_support_ticket_file

from app.schemas import (
    AdminSupportTicketListItem,
    AdminSupportTicketListResponse,
    SupportTicketDetailsResponse,
    SupportTicketMessageResponse,
)


router = APIRouter(
    prefix="/admin/help-center",
    tags=["Admin Help Center"],
)


# ============================================================
# GET ALL SUPPORT TICKETS
# ============================================================

@router.get(
    "/tickets",
    response_model=AdminSupportTicketListResponse,
)
def get_all_support_tickets(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    """
    Get all support tickets for admin panel.
    """

    tickets = (
        db.query(SupportTicket)
        .order_by(
            SupportTicket.created_at.desc()
        )
        .all()
    )

    ticket_list = []

    for ticket in tickets:

        ticket_list.append(
            AdminSupportTicketListItem(
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                user_id=ticket.user_id,
                subject=ticket.subject,
                message=ticket.message,
                attachment=ticket.attachment,
                status=ticket.status,
                created_at=ticket.created_at,
                updated_at=ticket.updated_at,
            )
        )

    return AdminSupportTicketListResponse(
        tickets=ticket_list
    )

# ============================================================
# ADMIN REPLY TO TICKET
# ============================================================

@router.post(
    "/tickets/{ticket_id}/reply",
)
async def admin_reply_to_ticket(
    ticket_id: int,

    message: str = Form(...),

    attachment: UploadFile | None = File(None),

    db: Session = Depends(get_db),

    current_user: str = Depends(get_current_user),
):
    """
    Admin replies to a support ticket.
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
            SupportTicket.id == ticket_id
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
        sender_type="ADMIN",
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
# GET ADMIN TICKET DETAILS
# ============================================================

@router.get(
    "/tickets/{ticket_id}",
    response_model=SupportTicketDetailsResponse,
)
def get_admin_ticket_details(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    ticket = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.id == ticket_id
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