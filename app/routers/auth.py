from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models import User
from app.schemas import RegisterUser, LoginUser
from app.utils.user_id import generate_user_id
from app.utils.jwt import create_access_token
from app.core.security import get_current_user
from app.services.binary_tree import find_placement_parent


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# ----------------------------
# Register
# ----------------------------
@router.post("/register")
def register(user: RegisterUser, db: Session = Depends(get_db)):

    # Password Match
    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password mismatch"
        )
    
    # Email already exists
    existing_email = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Aadhaar already exists
    if db.query(User).filter(User.aadhar_no == user.aadhar_no).first():
        raise HTTPException(
            status_code=400,
            detail="Aadhar number already registered"
        )

    # # PAN already exists
    # if db.query(User).filter(User.pan == user.pan).first():
    #     raise HTTPException(
    #         status_code=400,
    #         detail="PAN already registered"
    #     )
    # Validate Enroller ID
    placement_parent = None

    # Validate Enroller ID
    if user.enroller_id:

        enroller = db.query(User).filter(
            User.user_id == user.enroller_id
        ).first()

        if not enroller:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Enroller ID"
            )

    # Find placement parent
    # placement_parent = find_placement_parent(
    #     db=db,
    #     sponsor=enroller,
    #     club=user.club
    # )
    # placement_parent = ""

        # if enroller.role != "ADMIN":
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Only ADMIN users can enroll new users"
        #     )

    # Generate User ID
    
    user_id = generate_user_id(db)
    print("Generated User ID:", user_id)

    # Create User
    db_user = User(
        user_id=user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        password=pwd_context.hash(user.password),
        enroller_id=user.enroller_id,
        # placement_parent=placement_parent.user_id if placement_parent else None,
        date_of_birth=user.date_of_birth,
        country=user.country,
        city=user.city,
        zip_code=user.zip_code,
        mobile=user.mobile,
        aadhar_no=user.aadhar_no,
        pan=user.pan,
        gender=user.gender,
        # club=user.club,
        # Bank Details
        bank_account=user.bank_account,
        bank_name=user.bank_name,
        ifsc=user.ifsc,

        # Nominee Details
        nominee_name=user.nominee_name,
        nominee_relation=user.nominee_relation,
        nominee_gender=user.nominee_gender,
        nominee_dob=user.nominee_dob,
        nominee_address=user.nominee_address,
        nominee_aadhar=user.nominee_aadhar,
        nominee_mobile=user.nominee_mobile,
        role="USER"
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "message": "Registration Successful",
        "user_id": db_user.user_id
    }


# ----------------------------
# Login
# ----------------------------
@router.post("/login")
def login(user: LoginUser, db: Session = Depends(get_db)):
    

    db_user = db.query(User).filter(
        User.user_id == user.user_id
    ).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid User ID"
        )

    if not pwd_context.verify(
        user.password,
        db_user.password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Password"
        )

    access_token = create_access_token(
        data={
            "sub": db_user.user_id
        }
    )

    return {
        "message": "Login Successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.user_id,
        "name": db_user.first_name,
        "role": db_user.role
    }


@router.get("/profile")
def profile(

    current_user: str = Depends(get_current_user),

    db: Session = Depends(get_db)

):

    user = db.query(User).filter(
        User.user_id == current_user
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {

        "user_id": user.user_id,

        "email": user.email,

        "first_name": user.first_name,

        "last_name": user.last_name,

        "mobile": user.mobile,

        "country": user.country,

        "city": user.city,

        "club": user.club,

        "role": user.role

        

    }