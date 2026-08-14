from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional, List
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
    pan: str
    gender: GenderEnum
    # club: ClubEnum
    # Bank
    bank_account: str
    bank_name: str
    ifsc: str

    # Nominee
    nominee_name: str
    nominee_relation: str
    nominee_gender: str
    nominee_dob: date
    nominee_address: str
    nominee_aadhar: str 
    nominee_mobile: str


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
    # commission_percentage: float
    # daily_commission_limit: float | None = None
    # admin_fee_percentage: float

class InvestmentPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    duration_months: Optional[int] = None
    return_percentage: Optional[float] = None
    minimum_amount: Optional[float] = None
    # commission_percentage: float
    # daily_commission_limit: float | None = None
    # maximum_amount: Optional[float] = None
    status: Optional[bool] = None

class InvestmentPlanResponse(BaseModel):
    id: int
    plan_name: str
    duration_months: int
    return_percentage: float
    minimum_amount: float
    # maximum_amount: float
    # commission_percentage: float
    # daily_commission_limit: float | None

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

class CommissionIds(BaseModel):
    ids: List[int]

class LotSettingCreate(BaseModel):
    lot_number: int
    amount: float
    status: int = 1


class LotSettingUpdate(BaseModel):
    lot_number: int | None = None
    amount: float | None = None
    status: int | None = None


class LotSettingResponse(BaseModel):
    id: int
    lot_number: int
    amount: float
    status: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True




class LevelCommissionCreate(BaseModel):
    level: int
    commission_percentage: float


class LevelCommissionUpdate(BaseModel):
    commission_percentage: float
    status: int


class LevelCommissionResponse(BaseModel):
    id: int
    level: int
    commission_percentage: float
    status: int

    class Config:
        from_attributes = True



class LevelCommissionHistoryBase(BaseModel):
    investment_id: int
    investor_id: int
    sponsor_id: int
    level: int
    investment_amount: float
    commission_percentage: float
    commission_amount: float
    status: str


class LevelCommissionHistoryCreate(LevelCommissionHistoryBase):
    pass


class LevelCommissionHistoryResponse(LevelCommissionHistoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class RankConditionBase(BaseModel):
    minimum_group_lots: int
    required_group_count: int
    order_no: int


class RankConditionCreate(RankConditionBase):
    pass


class RankConditionResponse(RankConditionBase):
    id: int

    class Config:
        from_attributes = True

class RankSettingCreate(BaseModel):
    rank_name: str
    rank_no: int
    minimum_total_lots: int
    minimum_direct_sponsors: int
    reward_income: float
    status: bool = True

    conditions: List[RankConditionCreate]

class RankSettingUpdate(BaseModel):
    rank_name: str
    rank_no: int
    minimum_total_lots: int
    minimum_direct_sponsors: int
    reward_income: float
    status: bool

    conditions: List[RankConditionCreate]

class RankSettingResponse(BaseModel):
    id: int
    rank_name: str
    rank_no: int
    minimum_total_lots: int
    minimum_direct_sponsors: int
    reward_income: float
    status: bool

    conditions: List[RankConditionResponse]

    class Config:
        from_attributes = True

class ActivityHistoryResponse(BaseModel):
    id: int
    activity_type: str
    ip_address: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class UpdateProfile(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    date_of_birth: date
    country: str
    city: str
    zip_code: str
    mobile: str
    aadhar_no: str
    pan: str
    gender: GenderEnum


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6)
    confirm_password: str

class AdminFeeCreate(BaseModel):
    # investment_plan_id: int
    fee_percentage: float = Field(
        ...,
        gt=0,
        le=100
    )
    status: bool = True


class AdminFeeUpdate(BaseModel):
    # investment_plan_id: int
    fee_percentage: float = Field(
        ...,
        gt=0,
        le=100
    )
    status: bool


class AdminFeeResponse(BaseModel):
    id: int
    # investment_plan_id: int
    fee_percentage: float
    status: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class ReferralCommissionSettingCreate(BaseModel):
    investment_plan_id: int

    minimum_amount: float = Field(
        ...,
        ge=0
    )

    maximum_amount: float | None = Field(
        default=None,
        gt=0
    )

    commission_percentage: float = Field(
        ...,
        gt=0,
        le=100
    )

    status: bool = True

class ReferralCommissionSettingUpdate(BaseModel):
    investment_plan_id: int

    minimum_amount: float = Field(
        ...,
        ge=0
    )

    maximum_amount: float | None = Field(
        default=None,
        gt=0
    )

    commission_percentage: float = Field(
        ...,
        gt=0,
        le=100
    )

    status: bool

class ReferralCommissionSettingResponse(BaseModel):
    id: int
    investment_plan_id: int
    plan_name: str
    minimum_amount: float
    maximum_amount: float | None
    commission_percentage: float
    status: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class EnrollerResponse(BaseModel):
    user_id: str
    fullname: str
    date_of_joining: date | None
    rank: str | None
    total_investment_amount: float
    total_lots: int


class EnrollerListResponse(BaseModel):
    total: int
    enrollers: List[EnrollerResponse]