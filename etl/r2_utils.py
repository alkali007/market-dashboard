import os
import boto3
from botocore.config import Config
from datetime import datetime

def get_r2_client():
    """
    Initializes and returns a boto3 client for Cloudflare R2.
    """
    access_key = os.getenv("R2_ACCESS_KEY")
    secret_key = os.getenv("R2_SECRET_KEY")
    endpoint_url = os.getenv("R2_ENDPOINT_URL")
    
    if not all([access_key, secret_key, endpoint_url]):
        print("Warning: R2 credentials missing. Skipping cloud upload.")
        return None

    return boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='auto' # R2 doesn't use regions like AWS but boto3 requires it
    )

def upload_raw_to_r2(category_name, file_path):
    """
    Uploads a raw JSON file to the specified R2 bucket.
    Organizes files by date: backups/YYYY-MM-DD/category_raw.json
    """
    bucket_name = os.getenv("R2_BUCKET_NAME")
    if not bucket_name:
        print("Warning: R2_BUCKET_NAME missing. Skipping cloud upload.")
        return False

    client = get_r2_client()
    if not client:
        return False

    # Create a timestamped key for the object
    date_str = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H-%M-%S")
    object_key = f"backups/{date_str}/{category_name}_{timestamp}_raw.json"

    try:
        print(f"[{category_name}] R2: Uploading to {object_key}...")
        client.upload_file(file_path, bucket_name, object_key)
        print(f"[{category_name}] R2: Upload successful.")
        return True
    except Exception as e:
        print(f"[{category_name}] R2: Upload failed: {e}")
        return False

if __name__ == "__main__":
    # Test connection if run directly
    client = get_r2_client()
    if client:
        print("R2 Client initialized successfully.")
    else:
        print("R2 Client failed to initialize.")
