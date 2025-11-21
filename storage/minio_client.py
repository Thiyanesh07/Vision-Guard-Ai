from minio import Minio
from minio.error import S3Error
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# Initialize MinIO client
minio_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure
)

def create_bucket_if_not_exists(bucket_name):
    """
    Create a bucket in MinIO if it does not already exist.

    Args:
        bucket_name (str): The name of the bucket to create.
    """
    try:
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' created.")
        else:
            print(f"Bucket '{bucket_name}' already exists.")
    except S3Error as e:
        print(f"Error checking/creating bucket: {e}")

def upload_frame(bucket_name, file_name, file_data):
    """
    Upload a frame to MinIO and return its public URL.

    Args:
        bucket_name (str): The name of the bucket to upload to.
        file_name (str): The name of the file to save as.
        file_data (BytesIO): The file data to upload.

    Returns:
        str: The public URL of the uploaded file.
    """
    try:
        # Get length of BytesIO object
        file_data.seek(0, 2)  # Seek to end
        length = file_data.tell()
        file_data.seek(0)  # Seek back to beginning
        
        minio_client.put_object(
            bucket_name,
            file_name,
            file_data,
            length=length,
            content_type="image/jpeg"
        )
        print(f"File '{file_name}' uploaded to bucket '{bucket_name}'.")
        
        # Construct URL
        protocol = "https" if settings.minio_secure else "http"
        return f"{protocol}://{settings.minio_endpoint}/{bucket_name}/{file_name}"
    except S3Error as e:
        print(f"Error uploading file: {e}")
        return None

def get_presigned_url(bucket_name, file_name, expires_in_seconds=3600):
    """
    Generate a presigned URL for accessing a file.

    Args:
        bucket_name (str): The name of the bucket.
        file_name (str): The name of the file.
        expires_in_seconds (int): URL expiration time in seconds.

    Returns:
        str: Presigned URL or None if error.
    """
    try:
        from datetime import timedelta
        url = minio_client.presigned_get_object(
            bucket_name,
            file_name,
            expires=timedelta(seconds=expires_in_seconds)
        )
        return url
    except S3Error as e:
        print(f"Error generating presigned URL: {e}")
        return None

if __name__ == "__main__":
    bucket = settings.minio_bucket
    create_bucket_if_not_exists(bucket)
    print(f"MinIO client initialized. Endpoint: {settings.minio_endpoint}")