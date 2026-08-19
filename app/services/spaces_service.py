# import os

# import boto3
# from botocore.client import Config
# from dotenv import load_dotenv

# load_dotenv()


# SPACES_BUCKET = os.getenv("SPACES_BUCKET")
# SPACES_REGION = os.getenv("SPACES_REGION")
# SPACES_ENDPOINT = os.getenv("SPACES_ENDPOINT")
# SPACES_ACCESS_KEY = os.getenv("SPACES_ACCESS_KEY")
# SPACES_SECRET_KEY = os.getenv("SPACES_SECRET_KEY")


# spaces_client = boto3.client(
#     "s3",
#     region_name=SPACES_REGION,
#     endpoint_url=SPACES_ENDPOINT,
#     aws_access_key_id=SPACES_ACCESS_KEY,
#     aws_secret_access_key=SPACES_SECRET_KEY,
#     config=Config(signature_version="s3v4")
# )


# def upload_profile_image(
#     file_content: bytes,
#     filename: str,
#     content_type: str
# ):
#     key = f"user_images/{filename}"

#     spaces_client.put_object(
#         Bucket=SPACES_BUCKET,
#         Key=key,
#         Body=file_content,
#         ContentType=content_type,
#         ACL="public-read"
#     )

#     image_url = f"{SPACES_ENDPOINT}/{SPACES_BUCKET}/{key}"

#     return image_url

# def upload_bank_proof(
#     file_content: bytes,
#     filename: str,
#     content_type: str
# ):
#     key = f"user_bank_proofs/{filename}"

#     spaces_client.put_object(
#         Bucket=SPACES_BUCKET,
#         Key=key,
#         Body=file_content,
#         ContentType=content_type
#     )

#     return key

# def get_spaces_url(object_key: str | None):
#     if not object_key:
#         return None

#     # If already a full URL, don't modify it
#     if object_key.startswith("http://") or object_key.startswith("https://"):
#         return object_key

#     return f"{SPACES_ENDPOINT.rstrip('/')}/{object_key.lstrip('/')}"

import os
import uuid
import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

load_dotenv()


SPACES_BUCKET = os.getenv("SPACES_BUCKET")
SPACES_REGION = os.getenv("SPACES_REGION")
SPACES_ENDPOINT = os.getenv("SPACES_ENDPOINT")
SPACES_ACCESS_KEY = os.getenv("SPACES_ACCESS_KEY")
SPACES_SECRET_KEY = os.getenv("SPACES_SECRET_KEY")


spaces_client = boto3.client(
    "s3",
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=SPACES_ACCESS_KEY,
    aws_secret_access_key=SPACES_SECRET_KEY,
    config=Config(signature_version="s3v4")
)


# ============================================================
# PROFILE IMAGE
# ============================================================

def upload_profile_image(
    file_content: bytes,
    filename: str,
    content_type: str
):
    key = f"user_images/{filename}"

    spaces_client.put_object(
        Bucket=SPACES_BUCKET,
        Key=key,
        Body=file_content,
        ContentType=content_type,
        ACL="public-read"
    )

    image_url = f"{SPACES_ENDPOINT}/{SPACES_BUCKET}/{key}"

    return image_url


# ============================================================
# BANK / NOMINEE DOCUMENT
# ============================================================

def upload_bank_proof(
    file_content: bytes,
    filename: str,
    content_type: str
):
    key = f"user_bank_proofs/{filename}"

    spaces_client.put_object(
        Bucket=SPACES_BUCKET,
        Key=key,
        Body=file_content,
        ContentType=content_type
    )

    return key


# ============================================================
# PUBLIC URL
# ============================================================

def get_spaces_url(object_key: str | None):
    if not object_key:
        return None

    if object_key.startswith("http://") or object_key.startswith("https://"):
        return object_key

    return (
        f"{SPACES_ENDPOINT.rstrip('/')}/"
        f"{object_key.lstrip('/')}"
    )


# ============================================================
# PRESIGNED URL
# ============================================================

def get_presigned_url(
    object_key: str | None,
    expires_in: int = 3600
):
    if not object_key:
        return None

    # If DB contains a full URL, extract the object key.
    if object_key.startswith("http://") or object_key.startswith("https://"):

        # Example:
        # https://bucket.region.digitaloceanspaces.com/user_bank_proofs/file.jpg
        #
        # We only need:
        # user_bank_proofs/file.jpg

        object_key = object_key.split(".com/", 1)[-1]

    try:
        return spaces_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": SPACES_BUCKET,
                "Key": object_key
            },
            ExpiresIn=expires_in
        )

    except (BotoCoreError, ClientError) as e:
        raise Exception(
            f"Failed to generate presigned URL: {str(e)}"
        )

def upload_investment_payment_proof(
    file_content: bytes,
    filename: str,
    content_type: str,
    user_id: str
):
    extension = ""

    if filename:
        _, ext = os.path.splitext(filename)
        extension = ext.lower()

    unique_filename = f"{uuid.uuid4()}{extension}"

    key = (
        f"user_investment_proofs/"
        f"{user_id}/"
        f"{unique_filename}"
    )

    spaces_client.put_object(
        Bucket=SPACES_BUCKET,
        Key=key,
        Body=file_content,
        ContentType=content_type
    )

    return key