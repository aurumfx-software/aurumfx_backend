from sqlalchemy import Column, Integer, String, Date, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    enroller_id = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=False)
    country = Column(String, nullable=False)
    aadhar_no = Column(String, unique=True, nullable=False)
    city = Column(String, nullable=True)
    zip_code = Column(String, nullable=False)
    mobile = Column(String, nullable=False)
    pan = Column(String, nullable=False)
    gender = Column(String, nullable=True)
    club = Column(String, nullable=True)
     # Bank Details
    bank_account = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    ifsc = Column(String, nullable=True)
    bank_proof = Column(String, nullable=True)


    #image
    profile_image = Column(String, nullable=True)
    
    #KYC
    kyc_documents = relationship("UserKYC",back_populates="user",cascade="all, delete-orphan")

    # Nominee Details
    nominee_name = Column(String, nullable=False)
    nominee_relation = Column(String, nullable=True)
    nominee_gender = Column(String, nullable=True)
    nominee_dob = Column(Date, nullable=True)
    nominee_address = Column(String, nullable=True)
    nominee_aadhar = Column(String, nullable=False)
    nominee_mobile = Column(String, nullable=False)

    placement_parent = Column(String, nullable=True)
    role = Column(String, default="USER")
    current_rank_id = Column(Integer,ForeignKey("rank_settings.id"),nullable=True)
    rank_histories = relationship("UserRankHistory",back_populates="user")
    current_rank = relationship("RankSetting",foreign_keys=[current_rank_id])
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    updated_at = Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())

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
    
    # daily_commission_limit = Column(
    #     Float,
    #     nullable=True
    # )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )



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
        nullable=False,
        unique=True
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

    pending_balance = Column(
        Float,
        default=0
    )
    admin_fee = Column(
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
        nullable=True
    )

    amount = Column(
        Float,
        nullable=False
    )

    transaction_type = Column(
        String(30),
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="PENDING"
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

    # admin_fee_percentage = Column(
    #     Float,
    #     nullable=False,
    #     default=0
    # )

    # admin_fee_amount = Column(
    #     Float,
    #     nullable=False,
    #     default=0
    # )

    payment_date = Column(
        DateTime,
        nullable=True
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
        default="PENDING"
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


class LotSetting(Base):
    __tablename__ = "lot_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Business lot number
    lot_number = Column(
        Integer,
        nullable=False,
        unique=True
    )

    # Amount required for this lot
    amount = Column(
        Float,
        nullable=False
    )

    status = Column(
        Integer,
        default=1
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


class BinaryWallet(Base):
    __tablename__ = "binary_wallet"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    left_business = Column(Float, default=0)

    right_business = Column(Float, default=0)

    left_carry = Column(Float, default=0)

    right_carry = Column(Float, default=0)

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

class BinaryIncome(Base):
    __tablename__ = "binary_income"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False
    )

    matched_amount = Column(Float)

    percentage = Column(Float, default=4)

    income = Column(Float)

    daily_limit = Column(Float)

    paid_income = Column(Float)

    left_before = Column(Float)

    right_before = Column(Float)

    left_after = Column(Float)

    right_after = Column(Float)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    user = relationship("User")

    investment = relationship("Investment")



class LevelCommission(Base):
    __tablename__ = "level_commissions"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Integer, unique=True, nullable=False)
    commission_percentage = Column(Float, nullable=False)
    status = Column(Integer, default=1)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class LevelIncome(Base):
    __tablename__ = "level_income"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Investment that generated this commission
    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False
    )

    # Investor who invested
    from_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # Sponsor who receives the commission
    to_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # Level (1 - 15)
    level = Column(
        Integer,
        nullable=False
    )

    # Investment Amount
    investment_amount = Column(
        Float,
        nullable=False
    )

    # Percentage from LevelCommission table
    commission_percentage = Column(
        Float,
        nullable=False
    )

    # Calculated commission
    commission_amount = Column(
        Float,
        nullable=False
    )

    status = Column(
        String,
        default="PAID"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    investment = relationship(
        "Investment",
        foreign_keys=[investment_id]
    )

    from_user = relationship(
        "User",
        foreign_keys=[from_user_id]
    )

    to_user = relationship(
        "User",
        foreign_keys=[to_user_id]
    )

class LevelCommissionHistory(Base):
    __tablename__ = "level_commission_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    investment_id = Column(
        Integer,
        ForeignKey("investments.id"),
        nullable=False
    )

    # Investor who made the investment
    investor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # Sponsor receiving the commission
    sponsor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    level = Column(
        Integer,
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

    status = Column(
        String(20),
        default="PAID"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    investment = relationship(
        "Investment",
        foreign_keys=[investment_id]
    )

    investor = relationship(
        "User",
        foreign_keys=[investor_id]
    )

    sponsor = relationship(
        "User",
        foreign_keys=[sponsor_id]
    )


class RankSetting(Base):
    __tablename__ = "rank_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    rank_name = Column(
        String(100),
        nullable=False,
        unique=True
    )

    rank_no = Column(
        Integer,
        nullable=False,
        unique=True
    )

    minimum_total_lots = Column(
        Integer,
        nullable=False,
        default=0
    )

    minimum_direct_sponsors = Column(
        Integer,
        nullable=False,
        default=0
    )

    reward_income = Column(
        Float,
        nullable=False,
        default=0
    )

    criteria = Column(
    Text,
    nullable=True
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

    # Relationships

    conditions = relationship(
        "RankCondition",
        back_populates="rank",
        cascade="all, delete-orphan"
    )

    histories = relationship(
        "UserRankHistory",
        back_populates="rank"
    )

class RankCondition(Base):
    __tablename__ = "rank_conditions"

    id = Column(Integer, primary_key=True, index=True)

    rank_id = Column(
        Integer,
        ForeignKey("rank_settings.id", ondelete="CASCADE"),
        nullable=False
    )

    order_no = Column(
        Integer,
        nullable=False,
        default=1
    )

    minimum_group_lots = Column(
        Integer,
        nullable=False
    )

    required_group_count = Column(
        Integer,
        nullable=False
    )

    rank = relationship(
        "RankSetting",
        back_populates="conditions"
    )



class UserRankHistory(Base):
    __tablename__ = "user_rank_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    rank_id = Column(
        Integer,
        ForeignKey("rank_settings.id"),
        nullable=False
    )

    reward_income = Column(
        Float,
        nullable=False,
        default=0
    )

    reward_paid = Column(
        Boolean,
        default=False
    )

    achieved_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    paid_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="rank_histories"
    )

    rank = relationship(
        "RankSetting",
        back_populates="histories"
    )


class UserActivityHistory(Base):
    __tablename__ = "user_activity_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    activity_type = Column(String, nullable=False)   # LOGIN / LOGOUT
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class AdminFeeSetting(Base):
    __tablename__ = "admin_fee_settings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # investment_plan_id = Column(
    #     Integer,
    #     ForeignKey("investment_plans.id"),
    #     nullable=False
    # )

    fee_percentage = Column(
        Float,
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

class ReferralCommissionSetting(Base):
    __tablename__ = "referral_commission_settings"

    id = Column(Integer, primary_key=True, index=True)

    investment_plan_id = Column(
        Integer,
        ForeignKey("investment_plans.id"),
        nullable=False
    )

    minimum_amount = Column(
        Float,
        nullable=False
    )

    maximum_amount = Column(
        Float,
        nullable=True
    )

    commission_percentage = Column(
        Float,
        nullable=False
    )

    daily_commission_limit = Column(
                Float,
                nullable=True
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

    investment_plan = relationship(
        "InvestmentPlan",
        backref="referral_commission_settings"
    )

class PayoutHistory(Base):
    __tablename__ = "payout_history"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # ========================================================
    # Income
    # ========================================================

    referral_income = Column(
        Float,
        nullable=False,
        default=0
    )

    level_income = Column(
        Float,
        nullable=False,
        default=0
    )

    rank_income = Column(
        Float,
        nullable=False,
        default=0
    )

    total_income = Column(
        Float,
        nullable=False,
        default=0
    )

    # ========================================================
    # Admin Fee
    # ========================================================

    admin_fee_percentage = Column(
        Float,
        nullable=False,
        default=0
    )

    admin_fee = Column(
        Float,
        nullable=False,
        default=0
    )

    net_payable = Column(
        Float,
        nullable=False,
        default=0
    )

    # ========================================================
    # Payout Details
    # ========================================================

    payout_method = Column(
        String(50),
        nullable=False,
        default="BANK_TRANSFER"
    )

    payout_information = Column(
        String(1000),
        nullable=True
    )

    # ========================================================
    # Status
    # ========================================================

    status = Column(
        String(20),
        nullable=False,
        default="PAID"
    )

    paid_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user = relationship(
        "User",
        foreign_keys=[user_id]
    )

# ==========================================================
# USER KYC
# ==========================================================

class UserKYC(Base):
    __tablename__ = "user_kyc"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_type = Column(
        String,
        nullable=False
    )

    file_name = Column(
        String,
        nullable=False
    )

    file_url = Column(
        Text,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="PENDING"
    )

    rejection_reason = Column(
        Text,
        nullable=True
    )

    uploaded_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="kyc_documents"
    )