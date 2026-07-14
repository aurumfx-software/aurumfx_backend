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