from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    password = Column(String)
    enroller_id = Column(String)
    date_of_birth = Column(Date)
    country = Column(String)
    city = Column(String)
    zip_code = Column(String)
    mobile = Column(String)
    aadhar_no = Column(String)
    gender = Column(String)
    club = Column(String)
    role = Column(String, default="USER")


class InvestmentPlan(Base):
    __tablename__ = "investment_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_name = Column(String(100), nullable=False, unique=True)
    duration_months = Column(Integer, nullable=False)
    return_percentage = Column(Float, nullable=False)
    minimum_amount = Column(Float, nullable=False)
    # maximum_amount = Column(Float, nullable=False)
    status = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )