from pydantic import BaseModel, EmailStr
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