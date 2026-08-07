import os

import boto3
from botocore.client import Config
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