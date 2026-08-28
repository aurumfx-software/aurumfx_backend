from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, date
from app.database import get_db
from app.models import User, UserActivityHistory, UserKYC, UserBankDetails
from app.schemas import RegisterUser, LoginUser, ActivityHistoryResponse, UpdateProfile, ChangePassword
from app.utils.user_id import generate_user_id
from app.utils.jwt import create_access_token
from app.core.security import get_current_user
from app.services.binary_tree import  find_placement_parent
from app.services.activity_service import get_activity_history
from app.services.spaces_service import upload_profile_image, upload_bank_proof, get_presigned_url
from app.core.security import verify_password, get_password_hash
# from app.services.email_service import send_registration_email

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
def check_enroller(
    enroller_id: str,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(
            User.user_id == enroller_id,
            User.status == "ACTIVE"
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Enroller ID not found or inactive"
        )

    return {
        "exists": True,
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}".strip()
    }
# ----------------------------
# Register
# ----------------------------
@router.post("/register")
def register(
    user: RegisterUser,
    db: Session = Depends(get_db)
):

    # ==========================================================
    # 1. PASSWORD MATCH
    # ==========================================================

    if user.password != user.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password mismatch"
        )

    # ==========================================================
    # 2. CHECK AADHAAR IN KYC TABLE
    # ==========================================================

    existing_aadhar = (
        db.query(UserKYC)
        .filter(UserKYC.aadhar_no == user.aadhar_no)
        .first()
    )

    if existing_aadhar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aadhar number already registered"
        )

    # ==========================================================
    # 3. CHECK PAN IN KYC TABLE
    # ==========================================================

    # if user.pan:

    #     existing_pan = (
    #         db.query(UserKYC)
    #         .filter(UserKYC.pan_no == user.pan)
    #         .first()
    #     )

    #     if existing_pan:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="PAN already registered"
    #         )

    # ==========================================================
    # 4. VALIDATE ENROLLER
    # ==========================================================

    if user.enroller_id:

        enroller = (
            db.query(User)
            .filter(
                User.user_id == user.enroller_id
            )
            .first()
        )

        if not enroller:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Enroller ID"
            )

    # ==========================================================
    # 5. GENERATE USER ID
    # ==========================================================

    user_id = generate_user_id(db)

    print("Generated User ID:", user_id)

    # ==========================================================
    # 6. CREATE USER
    # ==========================================================

    db_user = User(
        user_id=user_id,

        email=user.email,

        first_name=user.first_name,

        last_name=user.last_name,

        password=pwd_context.hash(
            user.password
        ),

        enroller_id=user.enroller_id,

        date_of_birth=user.date_of_birth,

        country=user.country,

        city=user.city,

        zip_code=user.zip_code,

        building_no=user.building_no,

        street=user.street,

        mobile=user.mobile,

        gender=user.gender,

        role="USER"
    )

    db.add(db_user)

    # Flush so db_user.id is generated
    # before creating KYC and bank records.
    db.flush()

    # ==========================================================
    # 7. CREATE KYC
    # ==========================================================

    db_kyc = UserKYC(
        user_id=db_user.id,

        aadhar_no=user.aadhar_no,

        pan_no=user.pan,

        status="PENDING"
    )

    db.add(db_kyc)

    # ==========================================================
    # 8. CREATE BANK + NOMINEE DETAILS
    # ==========================================================

    db_bank_details = UserBankDetails(
        user_id=db_user.id,

        # -------------------------
        # Bank
        # -------------------------

        bank_account=user.bank_account,

        bank_name=user.bank_name,

        ifsc=user.ifsc,

        status="PENDING",

        # -------------------------
        # Nominee
        # -------------------------

        nominee_name=user.nominee_name,

        nominee_relation=user.nominee_relation,

        nominee_gender=user.nominee_gender,

        nominee_dob=user.nominee_dob,

        nominee_address=user.nominee_address,

        nominee_aadhar=user.nominee_aadhar,

        nominee_mobile=user.nominee_mobile,

        nominee_aadhar_front=None,

        nominee_aadhar_back=None
    )

    db.add(db_bank_details)

    # ==========================================================
    # 9. COMMIT EVERYTHING
    # ==========================================================

    try:

        db.commit()

        db.refresh(db_user)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

    # ==========================================================
    # 10. RESPONSE
    # ==========================================================

    return {
        "message": "Registration Successful",
        "user_id": db_user.user_id
    }

# ----------------------------
# Login
# ----------------------------
@router.post("/login")
def user_login(
    login: LoginUser,
    request: Request,
    db: Session = Depends(get_db),
):
    # ======================================================
    # FIND USER
    # ======================================================

    user = (
        db.query(User)
        .filter(User.user_id == login.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid User ID or Password",
        )

    # ======================================================
    # CHECK ROLE
    # ======================================================

    if user.role != "USER":
        raise HTTPException(
            status_code=403,
            detail="This account is not authorized for user login.",
        )

    # ======================================================
    # CHECK ACCOUNT STATUS
    # ======================================================

    if user.status == "BLOCKED":
        raise HTTPException(
            status_code=403,
            detail="Your account has been blocked. Please contact support.",
        )

    # ======================================================
    # VERIFY PASSWORD
    # ======================================================

    if not pwd_context.verify(login.password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid User ID or Password",
        )

    # ======================================================
    # CREATE ACCESS TOKEN
    # ======================================================

    token = create_access_token(
        data={
            "sub": user.user_id,
            "role": user.role,
        }
    )

    # ======================================================
    # LOGIN ACTIVITY
    # ======================================================

    activity = UserActivityHistory(
        user_id=user.id,
        activity_type="LOGIN",
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        created_at=datetime.utcnow(),
    )

    db.add(activity)
    db.commit()

    # ======================================================
    # RESPONSE
    # ======================================================

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.user_id,
        "role": user.role,
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

        # "aadhar_no": user.aadhar_no,

        # "pan": user.pan,

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
    db: Session = Depends(get_db),
):
    # =================================
    # 1. Find logged-in user
    # =================================

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

    # =================================
    # 2. Get existing bank details
    # =================================

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    # =================================
    # 3. Validate IFSC
    # =================================

    # ifsc = ifsc.strip().upper()

    # if len(ifsc) != 11:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="Invalid IFSC code"
    #     )

    # =================================
    # 4. Allowed File Types
    # =================================

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }

    max_size = 5 * 1024 * 1024

    # =================================
    # 5. Validate Bank Proof
    # =================================

    if proof_document.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only JPG, PNG and PDF bank proof "
                "documents are allowed"
            )
        )

    bank_proof_content = await proof_document.read()

    if len(bank_proof_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Bank proof document must be less than 5 MB"
        )

    # =================================
    # 6. Validate Nominee Aadhaar Front
    # =================================

    if nominee_aadhar_front.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Nominee Aadhaar front must be JPG, PNG or PDF"
        )

    nominee_front_content = (
        await nominee_aadhar_front.read()
    )

    if len(nominee_front_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nominee Aadhaar front must be "
                "less than 5 MB"
            )
        )

    # =================================
    # 7. Validate Nominee Aadhaar Back
    # =================================

    if nominee_aadhar_back.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Nominee Aadhaar back must be JPG, PNG or PDF"
        )

    nominee_back_content = (
        await nominee_aadhar_back.read()
    )

    if len(nominee_back_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=(
                "Nominee Aadhaar back must be "
                "less than 5 MB"
            )
        )

    # =================================
    # 8. Generate Extensions
    # =================================

    bank_extension = allowed_types[
        proof_document.content_type
    ]

    nominee_front_extension = allowed_types[
        nominee_aadhar_front.content_type
    ]

    nominee_back_extension = allowed_types[
        nominee_aadhar_back.content_type
    ]

    # =================================
    # 9. Generate Filenames
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
    # 10. Upload Bank Proof
    # =================================

    proof_key = upload_bank_proof(
        file_content=bank_proof_content,
        filename=bank_filename,
        content_type=proof_document.content_type,
    )

    # =================================
    # 11. Upload Nominee Aadhaar Front
    # =================================

    nominee_front_key = upload_bank_proof(
        file_content=nominee_front_content,
        filename=nominee_front_filename,
        content_type=nominee_aadhar_front.content_type,
    )

    # =================================
    # 12. Upload Nominee Aadhaar Back
    # =================================

    nominee_back_key = upload_bank_proof(
        file_content=nominee_back_content,
        filename=nominee_back_filename,
        content_type=nominee_aadhar_back.content_type,
    )

    # =================================
    # 13. Create or Update Bank Details
    # =================================

    if not bank_details:

        bank_details = UserBankDetails(
            user_id=user.id,
            status="PENDING",
        )

        db.add(bank_details)

    # =================================
    # 14. Update Bank Details
    # =================================

    bank_details.bank_account = (
        bank_account.strip()
    )

    bank_details.bank_name = (
        bank_name.strip()
    )

    bank_details.ifsc = ifsc

    bank_details.bank_proof = proof_key

    # =================================
    # 15. Update Nominee Details
    # =================================

    bank_details.nominee_name = (
        nominee_name.strip()
    )

    bank_details.nominee_relation = (
        nominee_relation.strip()
        if nominee_relation
        else None
    )

    bank_details.nominee_gender = (
        nominee_gender.strip()
        if nominee_gender
        else None
    )

    bank_details.nominee_dob = nominee_dob

    bank_details.nominee_address = (
        nominee_address.strip()
        if nominee_address
        else None
    )

    bank_details.nominee_aadhar = (
        nominee_aadhar.strip()
    )

    bank_details.nominee_mobile = (
        nominee_mobile.strip()
    )

    # =================================
    # 16. Save Nominee Aadhaar Documents
    # =================================

    bank_details.nominee_aadhar_front = (
        nominee_front_key
    )

    bank_details.nominee_aadhar_back = (
        nominee_back_key
    )

    # =================================
    # 17. Reset Status
    # =================================

    bank_details.status = "PENDING"

    bank_details.rejection_reason = None

    # =================================
    # 18. Save
    # =================================

    try:

        db.commit()

        db.refresh(bank_details)

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to update bank details: {str(e)}"
        )

    # =================================
    # 19. Response
    # =================================

    return {
        "message": "Bank and nominee details updated successfully",

        "bank_details": {
            "id": bank_details.id,
            "bank_account": bank_details.bank_account,
            "bank_name": bank_details.bank_name,
            "ifsc": bank_details.ifsc,
            "bank_proof": bank_details.bank_proof,
            "status": bank_details.status,
            "rejection_reason": bank_details.rejection_reason,
        },

        "nominee_details": {
            "nominee_name": bank_details.nominee_name,
            "nominee_relation": bank_details.nominee_relation,
            "nominee_gender": bank_details.nominee_gender,
            "nominee_dob": bank_details.nominee_dob,
            "nominee_address": bank_details.nominee_address,
            "nominee_aadhar": bank_details.nominee_aadhar,
            "nominee_mobile": bank_details.nominee_mobile,
            "nominee_aadhar_front": (
                bank_details.nominee_aadhar_front
            ),
            "nominee_aadhar_back": (
                bank_details.nominee_aadhar_back
            ),
        },
    }
@router.get("/profile/bank-details")
def get_bank_details(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # =================================
    # Find logged-in user
    # =================================

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

    # =================================
    # Get bank details
    # =================================

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    # =================================
    # No bank details
    # =================================

    if not bank_details:
        return {
            "message": "Bank details not found",

            "bank_details": None,

            "nominee_details": None
        }

    # =================================
    # Response
    # =================================

    return {
        "message": "Bank details fetched successfully",

        "bank_details": {
            "id": bank_details.id,
            "bank_account": bank_details.bank_account,
            "bank_name": bank_details.bank_name,
            "ifsc": bank_details.ifsc,

            "bank_proof": (
                get_presigned_url(
                    bank_details.bank_proof
                )
                if bank_details.bank_proof
                else None
            ),

            "status": bank_details.status,

            "rejection_reason": (
                bank_details.rejection_reason
            ),
        },

        "nominee_details": {
            "nominee_name": bank_details.nominee_name,
            "nominee_relation": bank_details.nominee_relation,
            "nominee_gender": bank_details.nominee_gender,
            "nominee_dob": bank_details.nominee_dob,
            "nominee_address": bank_details.nominee_address,
            "nominee_aadhar": bank_details.nominee_aadhar,
            "nominee_mobile": bank_details.nominee_mobile,

            "nominee_aadhar_front": (
                get_presigned_url(
                    bank_details.nominee_aadhar_front
                )
                if bank_details.nominee_aadhar_front
                else None
            ),

            "nominee_aadhar_back": (
                get_presigned_url(
                    bank_details.nominee_aadhar_back
                )
                if bank_details.nominee_aadhar_back
                else None
            ),
        }
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

@router.post("/change-password")
def change_password(
    data: ChangePassword,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user),
):
    # Get logged-in user
    user = (
        db.query(User)
        .filter(User.user_id == current_user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(
        data.current_password,
        user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Check new password confirmation
    if data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match",
        )

    # Prevent same password
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Hash and update
    user.password = get_password_hash(data.new_password)

    db.commit()

    return {
        "success": True,
        "message": "Password changed successfully",
    }