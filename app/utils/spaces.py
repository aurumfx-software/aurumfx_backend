import os
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError


SPACES_BUCKET = os.getenv("SPACES_BUCKET")
SPACES_REGION = os.getenv("SPACES_REGION")
SPACES_ENDPOINT = os.getenv("SPACES_ENDPOINT")
SPACES_ACCESS_KEY = os.getenv("SPACES_ACCESS_KEY")
SPACES_SECRET_KEY = os.getenv("SPACES_SECRET_KEY")


s3_client = boto3.client(
    "s3",
    region_name=SPACES_REGION,
    endpoint_url=SPACES_ENDPOINT,
    aws_access_key_id=SPACES_ACCESS_KEY,
    aws_secret_access_key=SPACES_SECRET_KEY,
)


# ============================================================
# UPLOAD SUPPORT TICKET FILE
# ============================================================

def upload_support_ticket_file(
    file,
    user_id: str,
) -> str:

    extension = ""

    if file.filename:
        _, ext = os.path.splitext(file.filename)
        extension = ext.lower()

    filename = f"{uuid.uuid4()}{extension}"

    object_key = (
        f"user_support_tickets/{user_id}/{filename}"
    )

    try:
        s3_client.upload_fileobj(
            file.file,
            SPACES_BUCKET,
            object_key,
            ExtraArgs={
                "ContentType": (
                    file.content_type
                    or "application/octet-stream"
                )
            },
        )

    except (BotoCoreError, ClientError) as e:
        raise Exception(
            f"Failed to upload support ticket file: {str(e)}"
        )

    # Store this in DB
    return object_key


# ============================================================
# GENERATE PRESIGNED URL
# ============================================================

def generate_support_ticket_url(
    object_key: str | None,
    expires_in: int = 3600,
) -> str | None:

    if not object_key:
        return None

    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": SPACES_BUCKET,
                "Key": object_key,
            },
            ExpiresIn=expires_in,
        )

    except (BotoCoreError, ClientError) as e:
        raise Exception(
            f"Failed to generate support ticket URL: {str(e)}"
        )