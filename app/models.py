from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
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

class ReturnType(Base):
    __tablename__ = "return_types"

    id = Column(Integer, primary_key=True, index=True)

    return_type = Column(
        String(30),
        unique=True,
        nullable=False
    )

    status = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

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

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    DateTime
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)

    investment_id = Column(
        String(20),
        unique=True,
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    return_type_id = Column(
        Integer,
        ForeignKey("return_types.id"),
        nullable=False
    )

    investment_plan_id = Column(
        Integer,
        ForeignKey("investment_plans.id"),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    lots = Column(
        Integer,
        nullable=False
    )

    monthly_return_percentage = Column(
        Float,
        nullable=False
    )

    monthly_return_amount = Column(
        Float,
        nullable=False
    )

    bank_transaction_id = Column(
        String(100),
        nullable=False
    )

    payment_proof = Column(
        String(255),
        nullable=True
    )

    enroller_id = Column(
        String(20),
        nullable=True
    )

    investment_status = Column(
        String(20),
        default="PENDING"
    )

    approval_status = Column(
        String(20),
        default="PENDING"
    )

    investment_date = Column(
        Date,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        backref="investments"
    )

    investment_plan = relationship(
        "InvestmentPlan",
        backref="investments"
    )

    return_which = Column(
    Integer,
    default=0
    )

    return_balance = Column(
        Integer,
        nullable=False
    )

    return_date = Column(
        Date,
        nullable=False
    )

class ReturnHistory(Base):
    __tablename__ = "return_history"

    id = Column(Integer, primary_key=True, index=True)

    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    return_number = Column(Integer, nullable=False)

    return_percentage = Column(Float, nullable=False)

    return_amount = Column(Float, nullable=False)

    approved_date = Column(Date, nullable=False)

    status = Column(String, default="PAID")

    remarks = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    balance = Column(
        Float,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship("User")

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)

    wallet_id = Column(
        Integer,
        ForeignKey("wallets.id"),
        nullable=False
    )

    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False
    )

    amount = Column(
        Float,
        nullable=False
    )

    transaction_type = Column(
        String(30),
        nullable=False
    )

    remarks = Column(
        String(255)
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    wallet = relationship("Wallet")

    investment = relationship("Investment")


class ReferralCommission(Base):
    __tablename__ = "referral_commissions"

    id = Column(Integer, primary_key=True, index=True)

    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False
    )

    investor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    enroller_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    investment_amount = Column(
        Float,
        nullable=False
    )

    commission_percentage = Column(
        Float,
        nullable=False
    )

    commission_amount = Column(
        Float,
        nullable=False
    )

    paid_amount = Column(
        Float,
        nullable=False
    )

    washout_amount = Column(
        Float,
        default=0
    )

    status = Column(
        String(20),
        default="PAID"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    # Relationships
    investment = relationship(
        "Investment",
        foreign_keys=[investment_id]
    )

    investor = relationship(
        "User",
        foreign_keys=[investor_id]
    )

    enroller = relationship(
        "User",
        foreign_keys=[enroller_id]
    )