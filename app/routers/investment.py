from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile,File,Form
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models import User, Investment, InvestmentPlan, ReturnType, LotSetting
from app.schemas import (
    InvestmentCreate,
    InvestmentResponse
)
from app.core.security import get_current_user
from app.utils.investment_id import generate_investment_id
from app.utils.return_date import calculate_return_date
from app.services.spaces_service import (
    upload_investment_payment_proof, get_presigned_url
)

router = APIRouter(
    prefix="/investments",
    tags=["Investments"]
)

@router.post("/", response_model=InvestmentResponse)
async def create_investment(
    investment_plan_id: int = Form(...),
    amount: float = Form(...),
    return_type_id: int = Form(...),
    bank_transaction_id: str = Form(...),
    investment_date: date = Form(...),

    payment_proof: UploadFile = File(...),

    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------------------------
    # Logged in User
    # --------------------------------------------------

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    # --------------------------------------------------
    # Check Bank Transaction ID
    # --------------------------------------------------

    bank_transaction_id = bank_transaction_id.strip()

    if not bank_transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Bank transaction ID is required."
        )

    existing_transaction = (
        db.query(Investment)
        .filter(
            Investment.bank_transaction_id == bank_transaction_id
        )
        .first()
    )

    if existing_transaction:
        raise HTTPException(
            status_code=400,
            detail="This bank transaction ID has already been used."
        )
    # --------------------------------------------------
    # Investment Plan
    # --------------------------------------------------

    plan = (
        db.query(InvestmentPlan)
        .filter(
            InvestmentPlan.id == investment_plan_id,
            InvestmentPlan.status == True
        )
        .first()
    )

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="Investment Plan not found"
        )

    # --------------------------------------------------
    # Lot Setting
    # --------------------------------------------------

    lot_setting = (
        db.query(LotSetting)
        .filter(LotSetting.status == 1)
        .first()
    )

    if not lot_setting:
        raise HTTPException(
            status_code=500,
            detail="Lot setting is not configured"
        )

    lot_amount = float(lot_setting.amount)

    if lot_amount <= 0:
        raise HTTPException(
            status_code=500,
            detail="Invalid lot amount configuration"
        )

    # --------------------------------------------------
    # Minimum Amount
    # --------------------------------------------------

    if amount < 5000:
        raise HTTPException(
            status_code=400,
            detail="Minimum investment amount is ₹5000."
        )

    # --------------------------------------------------
    # Multiple of 5000
    # --------------------------------------------------

    if amount % 5000 != 0:
        raise HTTPException(
            status_code=400,
            detail="Investment amount must be a multiple of ₹5000."
        )

    # --------------------------------------------------
    # Lots
    # --------------------------------------------------

    lots = int(amount / lot_amount)

    # --------------------------------------------------
    # Monthly Return
    # --------------------------------------------------

    monthly_return_amount = (
        amount * plan.return_percentage
    ) / 100

    # --------------------------------------------------
    # Return Balance
    # --------------------------------------------------

    return_balance = plan.duration_months

    # --------------------------------------------------
    # Return Date
    # --------------------------------------------------

    return_date = calculate_return_date(
        db,
        investment_date
    )

    # --------------------------------------------------
    # Return Type
    # --------------------------------------------------

    return_type = (
        db.query(ReturnType)
        .filter(
            ReturnType.id == return_type_id,
            ReturnType.status == True
        )
        .first()
    )

    if not return_type:
        raise HTTPException(
            status_code=404,
            detail="Return type not found"
        )

    # --------------------------------------------------
    # Validate Payment Proof
    # --------------------------------------------------

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf"
    }

    if payment_proof.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Payment proof must be JPG, PNG or PDF"
        )

    payment_proof_content = await payment_proof.read()

    max_size = 5 * 1024 * 1024

    if len(payment_proof_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Payment proof must be less than 5 MB"
        )

    # --------------------------------------------------
    # Upload Payment Proof
    # --------------------------------------------------

    payment_proof_key = upload_investment_payment_proof(
        file_content=payment_proof_content,
        filename=payment_proof.filename or "payment_proof",
        content_type=payment_proof.content_type,
        user_id=user.user_id
    )

    # --------------------------------------------------
    # Investment ID
    # --------------------------------------------------

    investment_id = generate_investment_id(db)

    # --------------------------------------------------
    # Save Investment
    # --------------------------------------------------

    db_investment = Investment(

        investment_id=investment_id,

        user_id=user.id,

        return_type_id=return_type.id,

        investment_plan_id=plan.id,

        amount=amount,

        lots=lots,

        monthly_return_percentage=plan.return_percentage,

        monthly_return_amount=monthly_return_amount,

        return_which=0,

        return_balance=return_balance,

        return_date=return_date,

        bank_transaction_id=bank_transaction_id,

        payment_proof=payment_proof_key,

        enroller_id=user.enroller_id,

        investment_status="PENDING",

        approval_status="PENDING",

        investment_date=investment_date
    )

    db.add(db_investment)
    db.commit()
    db.refresh(db_investment)

    # --------------------------------------------------
    # Response
    # --------------------------------------------------

    return InvestmentResponse(

        id=db_investment.id,

        investment_id=db_investment.investment_id,

        return_type=return_type.return_type,

        plan_name=plan.plan_name,

        amount=db_investment.amount,

        lots=db_investment.lots,

        monthly_return_percentage=db_investment.monthly_return_percentage,

        monthly_return_amount=db_investment.monthly_return_amount,

        return_which=db_investment.return_which,

        return_balance=db_investment.return_balance,

        return_date=db_investment.return_date,

        investment_status=db_investment.investment_status,

        approval_status=db_investment.approval_status,

        investment_date=db_investment.investment_date
    )


# -----------------------------------
# My Investments
# -----------------------------------
@router.get("/", response_model=list[InvestmentResponse])
def my_investments(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    status: str | None = Query(None),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # investments = (
    #     db.query(Investment)
    #     .filter(Investment.user_id == user.id)
    #     .all()
    # )

    query = db.query(Investment).filter(
    Investment.user_id == user.id
)

    # Filter by Start Date
    if start_date:
        query = query.filter(
            Investment.investment_date >= start_date
        )

    # Filter by End Date
    if end_date:
        query = query.filter(
            Investment.investment_date <= end_date
        )

    # Filter by Status
    if status:
        query = query.filter(
            Investment.investment_status == status.upper()
        )

    investments = query.order_by(
        Investment.id.desc()
    ).all()
     
    response = []

    for inv in investments:

        plan = (
            db.query(InvestmentPlan)
            .filter(
                InvestmentPlan.id == inv.investment_plan_id
            )
            .first()
        )

        return_type = (
            db.query(ReturnType)
            .filter(
                ReturnType.id == inv.return_type_id
            )
            .first()
        )

        response.append(
            InvestmentResponse(
                id=inv.id,
                investment_id=inv.investment_id,
                return_type=return_type.return_type if return_type else "",
                plan_name=plan.plan_name if plan else "",
                amount=inv.amount,
                lots=inv.lots,
                monthly_return_percentage=inv.monthly_return_percentage,
                monthly_return_amount=inv.monthly_return_amount,
                return_which=inv.return_which,
                return_balance=inv.return_balance,
                return_date=inv.return_date,
                investment_status=inv.investment_status,
                approval_status=inv.approval_status,
                investment_date=inv.investment_date,
                payment_proof=get_presigned_url(inv.payment_proof),
            )
        )

    return response


# -----------------------------------
# Investment Details
# -----------------------------------
@router.get("/{id}", response_model=InvestmentResponse)
def investment_details(
    id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    investment = (
        db.query(Investment)
        .filter(
            Investment.id == id,
            Investment.user_id == user.id
        )
        .first()
    )

    if not investment:
        raise HTTPException(
            status_code=404,
            detail="Investment not found"
        )

    plan = (
        db.query(InvestmentPlan)
        .filter(
            InvestmentPlan.id == investment.investment_plan_id
        )
        .first()
    )
    return_type = (
        db.query(ReturnType)
        .filter(
            ReturnType.id == investment.return_type_id
        )
        .first()
    )

    return InvestmentResponse(
        id=investment.id,
        investment_id=investment.investment_id,
        return_type=return_type.return_type if return_type else "",
        plan_name=plan.plan_name,
        amount=investment.amount,
        lots=investment.lots,
        monthly_return_percentage=investment.monthly_return_percentage,
        monthly_return_amount=investment.monthly_return_amount,
        return_which=investment.return_which,
        return_balance=investment.return_balance,
        return_date=investment.return_date,
        investment_status=investment.investment_status,
        approval_status=investment.approval_status,
        investment_date=investment.investment_date,
        payment_proof=get_presigned_url(
        investment.payment_proof
    )
    )