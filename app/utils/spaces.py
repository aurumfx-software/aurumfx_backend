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
                "ContentType": file.content_type or "application/octet-stream",
                "ACL": "public-read",
            },
        )

    except (BotoCoreError, ClientError) as e:
        raise Exception(
            f"Failed to upload support ticket file: {str(e)}"
        )

    file_url = (
        f"{SPACES_ENDPOINT}/{object_key}"
    )

    return file_url