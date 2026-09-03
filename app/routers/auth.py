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
from app.services.spaces_service import upload_profile_image, upload_bank_proof, get_presigned_url,delete_spaces_object
from app.core.security import verify_password, get_password_hash

from app.services.email_service import send_registration_email

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

        state=user.state,

        district=user.district,


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

        bank_status="PENDING",

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
    # 10. SEND REGISTRATION EMAIL
    # ==========================================================

    try:

        joining_date = (
            db_user.created_at.strftime("%d-%m-%Y")
            if db_user.created_at
            else ""
        )

        send_registration_email(

            to_email=db_user.email,

            user_id=db_user.user_id,

            first_name=db_user.first_name,

            last_name=db_user.last_name,

            joining_date=joining_date,

            enroller_id=db_user.enroller_id,

            password=user.password,

            plan_type="14%"
        )

    except Exception as e:

        print(
            f"User registered successfully, "
            f"but registration email failed: {str(e)}"
        )


    # ==========================================================
    # 11. RESPONSE
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

        "state": user.state,

        "district": user.district,


        "city": user.city,

        "gender": user.gender,

        "profile_image": user.profile_image,

        "zip_code": user.zip_code,

        "building_no": user.building_no,

        "street": user.street,


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
    # if profile.email != user.email:

    #     existing_email = db.query(User).filter(
    #         User.email == profile.email,
    #         User.id != user.id
    #     ).first()

    #     if existing_email:
    #         raise HTTPException(
    #             status_code=400,
    #             detail="Email already registered"
    #       )

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
    user.state = profile.state
    user.district = profile.district
    user.city = profile.city
    user.zip_code = profile.zip_code
    user.building_no = profile.building_no
    user.street = profile.street

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

    # ======================================================
    # BANK DETAILS
    # ======================================================

    bank_account: str | None = Form(None),
    bank_name: str | None = Form(None),
    ifsc: str | None = Form(None),

    # ======================================================
    # BANK PROOF
    # ======================================================

    proof_document: UploadFile | None = File(None),

    # ======================================================
    # AUTH
    # ======================================================

    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ======================================================
    # 1. FIND USER
    # ======================================================

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # ======================================================
    # 2. GET BANK DETAILS
    # ======================================================

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    # ======================================================
    # 3. CHECK INPUT
    # ======================================================

    has_bank_account = (
        bank_account is not None
        and bank_account.strip() != ""
    )

    has_bank_name = (
        bank_name is not None
        and bank_name.strip() != ""
    )

    has_ifsc = (
        ifsc is not None
        and ifsc.strip() != ""
    )

    has_proof_document = (
        proof_document is not None
    )

    if not any([
        has_bank_account,
        has_bank_name,
        has_ifsc,
        has_proof_document,
    ]):
        raise HTTPException(
            status_code=400,
            detail="Please provide at least one bank field to update.",
        )

    # ======================================================
    # 4. CREATE RECORD IF NOT EXISTS
    # ======================================================

    if not bank_details:

        bank_details = UserBankDetails(
            user_id=user.id,
            bank_status="PENDING",
            bank_rejection_reason=None,
        )

        db.add(bank_details)
        db.flush()

    # ======================================================
    # 5. CHECK FIRST BANK SUBMISSION
    # ======================================================

    is_first_bank_submission = (
        bank_details.bank_account is None
        and bank_details.bank_name is None
        and bank_details.ifsc is None
        and bank_details.bank_proof is None
    )

    if is_first_bank_submission:

        if not has_bank_account:
            raise HTTPException(
                status_code=400,
                detail="Bank account is required.",
            )

        if not has_bank_name:
            raise HTTPException(
                status_code=400,
                detail="Bank name is required.",
            )

        if not has_ifsc:
            raise HTTPException(
                status_code=400,
                detail="IFSC is required.",
            )

        if not has_proof_document:
            raise HTTPException(
                status_code=400,
                detail="Bank proof document is required.",
            )

    # ======================================================
    # 6. FILE SETTINGS
    # ======================================================

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }

    max_size = 5 * 1024 * 1024

    new_proof_key = None
    old_proof_key = None

    # ======================================================
    # 7. UPLOAD BANK PROOF
    # ======================================================

    if has_proof_document:

        if proof_document.content_type not in allowed_types:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only JPG, PNG and PDF bank proof "
                    "documents are allowed."
                ),
            )

        content = await proof_document.read()

        if len(content) > max_size:

            raise HTTPException(
                status_code=400,
                detail="Bank proof document must be less than 5 MB.",
            )

        # --------------------------------------------------
        # OLD FILE
        # --------------------------------------------------

        old_proof_key = bank_details.bank_proof

        # --------------------------------------------------
        # EXTENSION
        # --------------------------------------------------

        extension = allowed_types[
            proof_document.content_type
        ]

        # --------------------------------------------------
        # FILENAME
        # --------------------------------------------------

        filename = (
            f"{user.user_id}_bank_proof"
            f"{extension}"
        )

        # --------------------------------------------------
        # UPLOAD
        # --------------------------------------------------

        try:

            new_proof_key = upload_bank_proof(
                file_content=content,
                filename=filename,
                content_type=proof_document.content_type,
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to upload bank proof: "
                    f"{str(exc)}"
                ),
            )

        bank_details.bank_proof = new_proof_key

    # ======================================================
    # 8. UPDATE BANK ACCOUNT
    # ======================================================

    if has_bank_account:

        bank_details.bank_account = (
            bank_account.strip()
        )

    # ======================================================
    # 9. UPDATE BANK NAME
    # ======================================================

    if has_bank_name:

        bank_details.bank_name = (
            bank_name.strip()
        )

    # ======================================================
    # 10. UPDATE IFSC
    # ======================================================

    if has_ifsc:

        bank_details.ifsc = (
            ifsc.strip().upper()
        )

    # ======================================================
    # 11. RESET APPROVAL STATUS
    # ======================================================

    bank_details.bank_status = "PENDING"
    bank_details.bank_rejection_reason = None

    # ======================================================
    # 12. SAVE
    # ======================================================

    try:

        db.commit()
        db.refresh(bank_details)

    except Exception as exc:

        db.rollback()

        if new_proof_key:
            delete_spaces_object(new_proof_key)

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update bank details: "
                f"{str(exc)}"
            ),
        )

    # ======================================================
    # 13. DELETE OLD FILE
    # ======================================================

    if old_proof_key and old_proof_key != new_proof_key:

        try:
            delete_spaces_object(old_proof_key)
        except Exception:
            pass

    # ======================================================
    # 14. RESPONSE
    # ======================================================

    return {

        "message": "Bank details updated successfully.",

        "bank_details": {

            "id": bank_details.id,

            "bank_account": bank_details.bank_account,

            "bank_name": bank_details.bank_name,

            "ifsc": bank_details.ifsc,

            "bank_proof": bank_details.bank_proof,

            "status": bank_details.bank_status,

            "rejection_reason": bank_details.bank_rejection_reason,
        },
    }


@router.put("/profile/nominee-details")
async def update_nominee_details(

    # ======================================================
    # NOMINEE DETAILS
    # ======================================================

    nominee_name: str | None = Form(None),
    nominee_relation: str | None = Form(None),
    nominee_gender: str | None = Form(None),
    nominee_dob: date | None = Form(None),
    nominee_address: str | None = Form(None),
    nominee_aadhar: str | None = Form(None),
    nominee_mobile: str | None = Form(None),

    # ======================================================
    # NOMINEE AADHAAR DOCUMENTS
    # ======================================================

    nominee_aadhar_front: UploadFile | None = File(None),
    nominee_aadhar_back: UploadFile | None = File(None),

    # ======================================================
    # AUTH
    # ======================================================

    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ======================================================
    # 1. FIND USER
    # ======================================================

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # ======================================================
    # 2. GET BANK DETAILS RECORD
    # ======================================================

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    # ======================================================
    # 3. CHECK INPUT
    # ======================================================

    has_nominee_name = (
        nominee_name is not None
        and nominee_name.strip() != ""
    )

    has_nominee_relation = (
        nominee_relation is not None
        and nominee_relation.strip() != ""
    )

    has_nominee_gender = (
        nominee_gender is not None
        and nominee_gender.strip() != ""
    )

    has_nominee_dob = (
        nominee_dob is not None
    )

    has_nominee_address = (
        nominee_address is not None
        and nominee_address.strip() != ""
    )

    has_nominee_aadhar = (
        nominee_aadhar is not None
        and nominee_aadhar.strip() != ""
    )

    has_nominee_mobile = (
        nominee_mobile is not None
        and nominee_mobile.strip() != ""
    )

    has_nominee_front = (
        nominee_aadhar_front is not None
    )

    has_nominee_back = (
        nominee_aadhar_back is not None
    )

    if not any([
        has_nominee_name,
        has_nominee_relation,
        has_nominee_gender,
        has_nominee_dob,
        has_nominee_address,
        has_nominee_aadhar,
        has_nominee_mobile,
        has_nominee_front,
        has_nominee_back,
    ]):

        raise HTTPException(
            status_code=400,
            detail="Please provide at least one nominee field to update.",
        )

    # ======================================================
    # 4. CREATE RECORD IF NOT EXISTS
    # ======================================================

    if not bank_details:

        bank_details = UserBankDetails(
            user_id=user.id,
            nominee_status="PENDING",
            nominee_rejection_reason=None,
        )

        db.add(bank_details)
        db.flush()

    # ======================================================
    # 5. CHECK FIRST NOMINEE SUBMISSION
    # ======================================================

    is_first_nominee_submission = (
        bank_details.nominee_name is None
        and bank_details.nominee_aadhar is None
        and bank_details.nominee_mobile is None
        and bank_details.nominee_aadhar_front is None
        and bank_details.nominee_aadhar_back is None
    )

    if is_first_nominee_submission:

        if not has_nominee_name:

            raise HTTPException(
                status_code=400,
                detail="Nominee name is required.",
            )

        if not has_nominee_aadhar:

            raise HTTPException(
                status_code=400,
                detail="Nominee Aadhaar is required.",
            )

        if not has_nominee_mobile:

            raise HTTPException(
                status_code=400,
                detail="Nominee mobile is required.",
            )

        if not has_nominee_front:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar front "
                    "document is required."
                ),
            )

        if not has_nominee_back:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar back "
                    "document is required."
                ),
            )

    # ======================================================
    # 6. FILE SETTINGS
    # ======================================================

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }

    max_size = 5 * 1024 * 1024

    new_front_key = None
    new_back_key = None

    old_front_key = None
    old_back_key = None

    # ======================================================
    # 7. NOMINEE AADHAAR FRONT
    # ======================================================

    if has_nominee_front:

        if nominee_aadhar_front.content_type not in allowed_types:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar front must be "
                    "JPG, PNG or PDF."
                ),
            )

        front_content = (
            await nominee_aadhar_front.read()
        )

        if len(front_content) > max_size:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar front must be "
                    "less than 5 MB."
                ),
            )

        old_front_key = (
            bank_details.nominee_aadhar_front
        )

        extension = allowed_types[
            nominee_aadhar_front.content_type
        ]

        filename = (
            f"{user.user_id}_nominee_aadhar_front"
            f"{extension}"
        )

        try:

            new_front_key = upload_bank_proof(
                file_content=front_content,
                filename=filename,
                content_type=(
                    nominee_aadhar_front.content_type
                ),
            )

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to upload nominee "
                    "Aadhaar front: "
                    f"{str(exc)}"
                ),
            )

        bank_details.nominee_aadhar_front = (
            new_front_key
        )

    # ======================================================
    # 8. NOMINEE AADHAAR BACK
    # ======================================================

    if has_nominee_back:

        if nominee_aadhar_back.content_type not in allowed_types:

            if new_front_key:
                delete_spaces_object(new_front_key)

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar back must be "
                    "JPG, PNG or PDF."
                ),
            )

        back_content = (
            await nominee_aadhar_back.read()
        )

        if len(back_content) > max_size:

            if new_front_key:
                delete_spaces_object(new_front_key)

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar back must be "
                    "less than 5 MB."
                ),
            )

        old_back_key = (
            bank_details.nominee_aadhar_back
        )

        extension = allowed_types[
            nominee_aadhar_back.content_type
        ]

        filename = (
            f"{user.user_id}_nominee_aadhar_back"
            f"{extension}"
        )

        try:

            new_back_key = upload_bank_proof(
                file_content=back_content,
                filename=filename,
                content_type=(
                    nominee_aadhar_back.content_type
                ),
            )

        except Exception as exc:

            if new_front_key:
                delete_spaces_object(new_front_key)

            raise HTTPException(
                status_code=500,
                detail=(
                    "Failed to upload nominee "
                    "Aadhaar back: "
                    f"{str(exc)}"
                ),
            )

        bank_details.nominee_aadhar_back = (
            new_back_key
        )

    # ======================================================
    # 9. UPDATE NOMINEE NAME
    # ======================================================

    if has_nominee_name:

        bank_details.nominee_name = (
            nominee_name.strip()
        )

    # ======================================================
    # 10. UPDATE NOMINEE RELATION
    # ======================================================

    if has_nominee_relation:

        bank_details.nominee_relation = (
            nominee_relation.strip()
        )

    # ======================================================
    # 11. UPDATE NOMINEE GENDER
    # ======================================================

    if has_nominee_gender:

        bank_details.nominee_gender = (
            nominee_gender.strip()
        )

    # ======================================================
    # 12. UPDATE NOMINEE DOB
    # ======================================================

    if has_nominee_dob:

        bank_details.nominee_dob = nominee_dob

    # ======================================================
    # 13. UPDATE NOMINEE ADDRESS
    # ======================================================

    if has_nominee_address:

        bank_details.nominee_address = (
            nominee_address.strip()
        )

    # ======================================================
    # 14. UPDATE NOMINEE AADHAAR
    # ======================================================

    if has_nominee_aadhar:

        normalized_nominee_aadhar = (
            nominee_aadhar
            .replace(" ", "")
            .strip()
        )

        if (
            not normalized_nominee_aadhar.isdigit()
            or len(normalized_nominee_aadhar) != 12
        ):

            if new_front_key:
                delete_spaces_object(new_front_key)

            if new_back_key:
                delete_spaces_object(new_back_key)

            raise HTTPException(
                status_code=400,
                detail=(
                    "Nominee Aadhaar number must "
                    "contain exactly 12 digits."
                ),
            )

        bank_details.nominee_aadhar = (
            normalized_nominee_aadhar
        )

    # ======================================================
    # 15. UPDATE NOMINEE MOBILE
    # ======================================================

    if has_nominee_mobile:

        bank_details.nominee_mobile = (
            nominee_mobile.strip()
        )

    # ======================================================
    # 16. RESET STATUS
    # ======================================================

    bank_details.nominee_status = "PENDING"
    bank_details.nominee_rejection_reason = None

    # ======================================================
    # 17. SAVE
    # ======================================================

    try:

        db.commit()
        db.refresh(bank_details)

    except Exception as exc:

        db.rollback()

        if new_front_key:
            delete_spaces_object(new_front_key)

        if new_back_key:
            delete_spaces_object(new_back_key)

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to update nominee details: "
                f"{str(exc)}"
            ),
        )

    # ======================================================
    # 18. DELETE OLD FILES
    # ======================================================

    if old_front_key and old_front_key != new_front_key:

        try:
            delete_spaces_object(old_front_key)
        except Exception:
            pass

    if old_back_key and old_back_key != new_back_key:

        try:
            delete_spaces_object(old_back_key)
        except Exception:
            pass

    # ======================================================
    # 19. RESPONSE
    # ======================================================

    return {

        "message": "Nominee details updated successfully.",

        "nominee_details": {

            "nominee_name": (
                bank_details.nominee_name
            ),

            "nominee_relation": (
                bank_details.nominee_relation
            ),

            "nominee_gender": (
                bank_details.nominee_gender
            ),

            "nominee_dob": (
                bank_details.nominee_dob
            ),

            "nominee_address": (
                bank_details.nominee_address
            ),

            "nominee_aadhar": (
                bank_details.nominee_aadhar
            ),

            "nominee_mobile": (
                bank_details.nominee_mobile
            ),

            "nominee_aadhar_front": (
                bank_details.nominee_aadhar_front
            ),

            "nominee_aadhar_back": (
                bank_details.nominee_aadhar_back
            ),

            "status": (
                bank_details.nominee_status
            ),

            "rejection_reason": (
                bank_details.nominee_rejection_reason
            ),
        },
    }




@router.get("/profile/bank-details")
def get_bank_details(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ======================================================
    # 1. FIND LOGGED-IN USER
    # ======================================================

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # ======================================================
    # 2. GET BANK DETAILS
    # ======================================================

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    # ======================================================
    # 3. BANK DETAILS NOT FOUND
    # ======================================================

    if not bank_details:

        return {
            "message": "Bank details not found",
            "bank_details": None,
        }

    # ======================================================
    # 4. RESPONSE
    # ======================================================

    return {

        "message": "Bank details fetched successfully",

        "bank_details": {

            "id": bank_details.id,

            "bank_account": (
                bank_details.bank_account
            ),

            "bank_name": (
                bank_details.bank_name
            ),

            "ifsc": (
                bank_details.ifsc
            ),

            "bank_proof": (
                get_presigned_url(
                    bank_details.bank_proof
                )
                if bank_details.bank_proof
                else None
            ),

            "bank_status": (
                bank_details.bank_status
            ),

            "bank_rejection_reason": (
                bank_details.bank_rejection_reason
            ),
        },
    }


@router.get("/profile/nominee-details")
def get_nominee_details(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # ======================================================
    # 1. FIND LOGGED-IN USER
    # ======================================================

    user = (
        db.query(User)
        .filter(User.user_id == current_user)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # ======================================================
    # 2. GET NOMINEE DETAILS
    # ======================================================

    bank_details = (
        db.query(UserBankDetails)
        .filter(
            UserBankDetails.user_id == user.id
        )
        .first()
    )

    # ======================================================
    # 3. NOMINEE DETAILS NOT FOUND
    # ======================================================

    if not bank_details:

        return {
            "message": "Nominee details not found",
            "nominee_details": None,
        }

    # ======================================================
    # 4. CHECK NOMINEE DATA
    # ======================================================

    has_nominee_data = any([
        bank_details.nominee_name,
        bank_details.nominee_relation,
        bank_details.nominee_gender,
        bank_details.nominee_dob,
        bank_details.nominee_address,
        bank_details.nominee_aadhar,
        bank_details.nominee_mobile,
        bank_details.nominee_aadhar_front,
        bank_details.nominee_aadhar_back,
    ])

    if not has_nominee_data:

        return {
            "message": "Nominee details not found",
            "nominee_details": None,
        }

    # ======================================================
    # 5. RESPONSE
    # ======================================================

    return {

        "message": "Nominee details fetched successfully",

        "nominee_details": {

            "id": bank_details.id,

            "nominee_name": (
                bank_details.nominee_name
            ),

            "nominee_relation": (
                bank_details.nominee_relation
            ),

            "nominee_gender": (
                bank_details.nominee_gender
            ),

            "nominee_dob": (
                bank_details.nominee_dob
            ),

            "nominee_address": (
                bank_details.nominee_address
            ),

            "nominee_aadhar": (
                bank_details.nominee_aadhar
            ),

            "nominee_mobile": (
                bank_details.nominee_mobile
            ),

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

            "nominee_status": (
                bank_details.nominee_status
            ),

            "nominee_rejection_reason": (
                bank_details.nominee_rejection_reason
            ),
        },
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