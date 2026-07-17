from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from app.enums import GenderEnum, ClubEnum


class RegisterUser(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    confirm_password: str
    enroller_id: str | None = None
    date_of_birth: date
    country: str
    city: str
    zip_code: str
    mobile: str
    aadhar_no: str
    gender: GenderEnum
    club: ClubEnum

class LoginUser(BaseModel):
    user_id: str
    password: str

class ReturnTypeCreate(BaseModel):
    return_type: str

class ReturnTypeUpdate(BaseModel):
    return_type: str | None = None
    status: bool | None = None

class ReturnTypeResponse(BaseModel):
    id: int
    return_type: str
    status: bool
    class Config:
        from_attributes = True

class InvestmentPlanCreate(BaseModel):
    plan_name: str = Field(..., example="10 Month Plan")
    duration_months: int = Field(..., example=10)
    return_percentage: float = Field(..., example=14)
    minimum_amount: float = Field(..., example=5000)
    # maximum_amount: float = Field(..., example=500000)

class InvestmentPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    duration_months: Optional[int] = None
    return_percentage: Optional[float] = None
    minimum_amount: Optional[float] = None
    # maximum_amount: Optional[float] = None
    status: Optional[bool] = None

class InvestmentPlanResponse(BaseModel):
    id: int
    plan_name: str
    duration_months: int
    return_percentage: float
    minimum_amount: float
    # maximum_amount: float
    status: bool

    class Config:
        from_attributes = True

class InvestmentCreate(BaseModel):
    investment_plan_id: int
    return_type_id: int
    amount: float = Field(..., ge=5000)
    bank_transaction_id: str
    enroller_id: str
    investment_date: date

class InvestmentResponse(BaseModel):
    id: int
    investment_id: str
    return_type: str
    plan_name: str
    amount: float
    lots: int
    monthly_return_percentage: float
    monthly_return_amount: float
    return_which: int
    return_balance: int
    return_date: date
    investment_status: str
    approval_status: str
    investment_date: date

    class Config:
        from_attributes = True

class InvestmentList(BaseModel):
    investment_id: str
    plan_name: str
    amount: float
    investment_status: str
    approval_status: str
    investment_date: date

    class Config:
        from_attributes = True

class InvestmentApproval(BaseModel):
    approval_status: str

class AdminInvestmentResponse(BaseModel):
    id: int
    investment_id: str
    user_id: str
    user_name: str
    plan_name: str
    return_type: str
    amount: float
    lots: int
    investment_status: str
    approval_status: str
    investment_date: date

    class Config:
        from_attributes = True

class ReturnApprove(BaseModel):
    remarks: str | None = None

class WalletResponse(BaseModel):
    balance: float

    class Config:
        from_attributes = True

from datetime import datetime

class WalletTransactionResponse(BaseModel):
    amount: float
    transaction_type: str
    remarks: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReferralCommissionResponse(BaseModel):

    investment_id: str

    from_user_id: str

    to_user_id: str

    commission_percentage: float

    commission_amount: float

    paid_amount: float

    washout_amount: float

    status: str

    created_at: datetime

    class Config:
        from_attributes = True