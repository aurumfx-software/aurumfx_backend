from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.models import (
    SupportTicket,
    SupportTicketMessage,
)

from app.utils.spaces import (
    upload_support_ticket_file,
    generate_support_ticket_url,
)

from app.utils.notifications import (
    create_user_notification,
)

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

    tickets = (
        db.query(SupportTicket)
        .order_by(
            SupportTicket.created_at.desc()
        )
        .all()
    )

    ticket_list = []

    for ticket in tickets:

        # Generate temporary URL for attachment
        attachment_url = (
            generate_support_ticket_url(
                ticket.attachment
            )
            if ticket.attachment
            else None
        )

        ticket_list.append(
            AdminSupportTicketListItem(
                ticket_id=ticket.id,
                ticket_number=ticket.ticket_number,
                user_id=ticket.user_id,
                subject=ticket.subject,
                message=ticket.message,

                # IMPORTANT
                # Return presigned URL
                attachment=attachment_url,

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
    # Upload attachment
    # --------------------------------------------------------

    attachment_key = None

    if attachment and attachment.filename:

        attachment_key = upload_support_ticket_file(
            file=attachment,
            user_id=current_user,
        )

    # --------------------------------------------------------
    # Create admin reply
    # --------------------------------------------------------

    reply = SupportTicketMessage(
        ticket_id=ticket.id,
        user_id=current_user,
        message=message,
        attachment=attachment_key,
        sender_type="ADMIN",
    )

    db.add(reply)

    # --------------------------------------------------------
    # Update ticket status
    # --------------------------------------------------------

    ticket.status = "OPEN"

    # --------------------------------------------------------
    # USER NOTIFICATION
    # --------------------------------------------------------

    create_user_notification(
        db=db,
        user_id=ticket.user_id,
        notification_type="SUPPORT_TICKET_REPLY",
        title="New Support Ticket Reply",
        message=(
            f"Admin replied to your ticket "
            f"{ticket.ticket_number}"
        ),
        reference_id=ticket.id,
        reference_type="SUPPORT_TICKET",
    )

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

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

        # IMPORTANT
        attachment=ticket_attachment_url,

        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,

        replies=reply_list,
    )