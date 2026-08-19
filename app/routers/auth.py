from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, date
from app.database import get_db
from app.models import User, UserActivityHistory
from app.schemas import RegisterUser, LoginUser, ActivityHistoryResponse, UpdateProfile, ChangePassword
from app.utils.user_id import generate_user_id
from app.utils.jwt import create_access_token
from app.core.security import get_current_user
from app.services.binary_tree import  find_placement_parent
from app.services.activity_service import get_activity_history
from app.services.spaces_service import upload_profile_image, upload_bank_proof




router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)
# ----------------------------
# Check entroller
# ----------------------------
@router.get("/check-enroller/{enroller_id}")
def check_enroller(enroller_id: str, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.user_id == enroller_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Enroller ID not found"
        )

    return {
        "exists": True,
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}"
    }
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
    # existing_email = db.query(User).filter(
    #     User.email == user.email
    # ).first()

    # if existing_email:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )

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
def user_login(login: LoginUser, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == login.user_id).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid User ID or Password")

    if user.role != "USER":
        raise HTTPException(
            status_code=403,
            detail="This account is not authorized for user login."
        )

    if not pwd_context.verify(login.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid User ID or Password")

    token = create_access_token(
        data={
            "sub": user.user_id,
            "role": user.role
        }
    )
    activity = UserActivityHistory(
    user_id=user.id,
    activity_type="LOGIN",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    created_at=datetime.utcnow()
)

    db.add(activity)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.role
    }

@router.post("/admin/login")
def admin_login(login: LoginUser, request: Request, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.user_id == login.user_id).first()

    if not admin:
        raise HTTPException(status_code=401, detail="Invalid User ID or Password")

    if admin.role != "ADMIN":
        raise HTTPException(
            status_code=403,
            detail="This account is not authorized for admin login."
        )

    if not pwd_context.verify(login.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid User ID or Password")

    token = create_access_token(
        data={
            "sub": admin.user_id,
            "role": admin.role
        }
    )
    activity = UserActivityHistory(
    user_id=admin.id,
    activity_type="LOGIN",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    created_at=datetime.utcnow()
    )
    
    db.add(activity)
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": admin.user_id,
        "role": admin.role
    }
@router.post("/logout")
def logout(
    request: Request,
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

    activity = UserActivityHistory(
        user_id=user.id,
        activity_type="LOGOUT",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        created_at=datetime.utcnow()
    )

    db.add(activity)
    db.commit()

    return {
        "message": "Logged out successfully"
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

        "gender": user.gender,

        "profile_image": user.profile_image,

        "zip_code": user.zip_code,

        "date_of_birth": user.date_of_birth,

        "aadhar_no": user.aadhar_no,

        "pan": user.pan,

        "role": user.role

    }

@router.get(
    "/profile/activity-history",
    response_model=list[ActivityHistoryResponse]
)
def activity_history(
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

    return get_activity_history(db, user.id)

@router.put("/profile")
def update_profile(
    profile: UpdateProfile,
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

    # --------------------------------
    # Check email already exists
    # --------------------------------
    if profile.email != user.email:

        existing_email = db.query(User).filter(
            User.email == profile.email,
            User.id != user.id
        ).first()

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

    # --------------------------------
    # Check Aadhar already exists
    # --------------------------------
    # if profile.aadhar_no != user.aadhar_no:

    #     existing_aadhar = db.query(User).filter(
    #         User.aadhar_no == profile.aadhar_no,
    #         User.id != user.id
    #     ).first()

    #     if existing_aadhar:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Aadhar number already registered"
    #         )

    # --------------------------------
    # Check PAN already exists
    # --------------------------------
    # if profile.pan != user.pan:

    #     existing_pan = db.query(User).filter(
    #         User.pan == profile.pan,
    #         User.id != user.id
    #     ).first()

    #     if existing_pan:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="PAN already registered"
    #         )

    # --------------------------------
    # Update profile
    # --------------------------------

    user.email = profile.email
    user.first_name = profile.first_name
    user.last_name = profile.last_name
    user.date_of_birth = profile.date_of_birth
    user.country = profile.country
    user.city = profile.city
    user.zip_code = profile.zip_code
    user.mobile = profile.mobile
    # user.aadhar_no = profile.aadhar_no
    # user.pan = profile.pan
    user.gender = profile.gender

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile updated successfully",
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_of_birth": user.date_of_birth,
            "country": user.country,
            "city": user.city,
            "zip_code": user.zip_code,
            "mobile": user.mobile,
            # "aadhar_no": user.aadhar_no,
            # "pan": user.pan,
            "gender": user.gender,
            # "club": user.club,
            "role": user.role
        }
    }

@router.post("/profile/image")
async def upload_profile_image_api(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------
    # Find logged-in user
    # --------------------------------
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

    # --------------------------------
    # Validate file type
    # --------------------------------
    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp"
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and WEBP images are allowed"
        )

    # --------------------------------
    # Read image
    # --------------------------------
    file_content = await file.read()

    # --------------------------------
    # Validate file size
    # Maximum 5 MB
    # --------------------------------
    max_size = 5 * 1024 * 1024

    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Image size must be less than 5 MB"
        )

    # --------------------------------
    # Generate filename
    # Example: FX001.jpg
    # --------------------------------
    extension = allowed_types[file.content_type]

    filename = f"{user.user_id}{extension}"

    # --------------------------------
    # Upload to DigitalOcean Spaces
    # --------------------------------
    image_url = upload_profile_image(
        file_content=file_content,
        filename=filename,
        content_type=file.content_type
    )

    # --------------------------------
    # Save URL in database
    # --------------------------------
    user.profile_image = image_url

    db.commit()
    db.refresh(user)

    return {
        "message": "Profile image uploaded successfully",
        "user_id": user.user_id,
        "profile_image": image_url
    }

@router.put("/profile/bank-details")
async def update_bank_details(
    # -----------------------------
    # Bank Details
    # -----------------------------
    bank_account: str = Form(...),
    bank_name: str = Form(...),
    ifsc: str = Form(...),

    # -----------------------------
    # Nominee Details
    # -----------------------------
    nominee_name: str = Form(...),
    nominee_relation: str | None = Form(None),
    nominee_gender: str | None = Form(None),
    nominee_dob: date | None = Form(None),
    nominee_address: str | None = Form(None),
    nominee_aadhar: str = Form(...),
    nominee_mobile: str = Form(...),

    # -----------------------------
    # Bank Proof
    # -----------------------------
    proof_document: UploadFile = File(...),

    # -----------------------------
    # Nominee Aadhaar
    # -----------------------------
    nominee_aadhar_front: UploadFile = File(...),
    nominee_aadhar_back: UploadFile = File(...),

    # -----------------------------
    # Authentication
    # -----------------------------
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------
    # Find logged-in user
    # --------------------------------
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

    # --------------------------------
    # Validate IFSC
    # --------------------------------
    ifsc = ifsc.strip().upper()

    if len(ifsc) != 11:
        raise HTTPException(
            status_code=400,
            detail="Invalid IFSC code"
        )

    # =================================
    # Allowed File Types
    # =================================

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf"
    }

    # =================================
    # Validate Bank Proof
    # =================================

    if proof_document.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG and PDF bank proof documents are allowed"
        )

    bank_proof_content = await proof_document.read()

    max_size = 5 * 1024 * 1024

    if len(bank_proof_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Bank proof document must be less than 5 MB"
        )

    # =================================
    # Validate Nominee Aadhaar Front
    # =================================

    if nominee_aadhar_front.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Nominee Aadhaar front must be JPG, PNG or PDF"
        )

    nominee_front_content = await nominee_aadhar_front.read()

    if len(nominee_front_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Nominee Aadhaar front must be less than 5 MB"
        )

    # =================================
    # Validate Nominee Aadhaar Back
    # =================================

    if nominee_aadhar_back.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Nominee Aadhaar back must be JPG, PNG or PDF"
        )

    nominee_back_content = await nominee_aadhar_back.read()

    if len(nominee_back_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Nominee Aadhaar back must be less than 5 MB"
        )

    # =================================
    # Generate Extensions
    # =================================

    bank_extension = allowed_types[proof_document.content_type]

    nominee_front_extension = allowed_types[
        nominee_aadhar_front.content_type
    ]

    nominee_back_extension = allowed_types[
        nominee_aadhar_back.content_type
    ]

    # =================================
    # Generate Filenames
    # =================================

    bank_filename = (
        f"{user.user_id}_bank_proof{bank_extension}"
    )

    nominee_front_filename = (
        f"{user.user_id}_nominee_aadhar_front"
        f"{nominee_front_extension}"
    )

    nominee_back_filename = (
        f"{user.user_id}_nominee_aadhar_back"
        f"{nominee_back_extension}"
    )

    # =================================
    # Upload Bank Proof
    # =================================

    proof_key = upload_bank_proof(
        file_content=bank_proof_content,
        filename=bank_filename,
        content_type=proof_document.content_type
    )

    # =================================
    # Upload Nominee Aadhaar Front
    # =================================

    nominee_front_key = upload_bank_proof(
        file_content=nominee_front_content,
        filename=nominee_front_filename,
        content_type=nominee_aadhar_front.content_type
    )

    # =================================
    # Upload Nominee Aadhaar Back
    # =================================

    nominee_back_key = upload_bank_proof(
        file_content=nominee_back_content,
        filename=nominee_back_filename,
        content_type=nominee_aadhar_back.content_type
    )

    # =================================
    # Update Bank Details
    # =================================

    user.bank_account = bank_account.strip()
    user.bank_name = bank_name.strip()
    user.ifsc = ifsc
    user.bank_proof = proof_key

    # =================================
    # Update Nominee Details
    # =================================

    user.nominee_name = nominee_name.strip()

    user.nominee_relation = (
        nominee_relation.strip()
        if nominee_relation
        else None
    )

    user.nominee_gender = (
        nominee_gender.strip()
        if nominee_gender
        else None
    )

    user.nominee_dob = nominee_dob

    user.nominee_address = (
        nominee_address.strip()
        if nominee_address
        else None
    )

    user.nominee_aadhar = nominee_aadhar.strip()
    user.nominee_mobile = nominee_mobile.strip()

    # =================================
    # Save Nominee Aadhaar Documents
    # =================================

    user.nominee_aadhar_front = nominee_front_key
    user.nominee_aadhar_back = nominee_back_key

    # =================================
    # Save
    # =================================

    db.commit()
    db.refresh(user)

    return {
        "message": "Bank and nominee details updated successfully",

        "bank_details": {
            "bank_account": user.bank_account,
            "bank_name": user.bank_name,
            "ifsc": user.ifsc,
            "bank_proof": user.bank_proof
        },

        "nominee_details": {
            "nominee_name": user.nominee_name,
            "nominee_relation": user.nominee_relation,
            "nominee_gender": user.nominee_gender,
            "nominee_dob": user.nominee_dob,
            "nominee_address": user.nominee_address,
            "nominee_aadhar": user.nominee_aadhar,
            "nominee_mobile": user.nominee_mobile,
            "nominee_aadhar_front": user.nominee_aadhar_front,
            "nominee_aadhar_back": user.nominee_aadhar_back
        }
    }

@router.get("/profile/bank-details")
def get_bank_details(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # --------------------------------
    # Find logged-in user
    # --------------------------------
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

    return {
        "message": "Bank details fetched successfully",

        "bank_details": {
            "bank_account": user.bank_account,
            "bank_name": user.bank_name,
            "ifsc": user.ifsc,
            "bank_proof": user.bank_proof
        },

        "nominee_details": {
            "nominee_name": user.nominee_name,
            "nominee_relation": user.nominee_relation,
            "nominee_gender": user.nominee_gender,
            "nominee_dob": user.nominee_dob,
            "nominee_address": user.nominee_address,
            "nominee_aadhar": user.nominee_aadhar,
            "nominee_mobile": user.nominee_mobile,
            "nominee_aadhar_front": user.nominee_aadhar_front,
            "nominee_aadhar_back": user.nominee_aadhar_back
        }
    }

@router.put("/change-password")
def change_password(
    password_data: ChangePassword,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find logged-in user
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

    # Verify current password
    if not pwd_context.verify(
        password_data.current_password,
        user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    # Check new password confirmation
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="New password and confirm password do not match"
        )

    # Prevent same password
    if pwd_context.verify(
        password_data.new_password,
        user.password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password"
        )

    # Hash new password
    user.password = pwd_context.hash(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully"
    }

@router.get("/image")
def get_profile_image(
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
        "profile_image": user.profile_image
    }