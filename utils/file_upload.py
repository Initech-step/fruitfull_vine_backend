import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import os
import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_SECRET_KEY"),
)

# Initialize S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION"),
)


def upload_file_to_s3(file_data, file_name, content_type, is_product=True):
    """
    Uploads a file to S3 and returns the CloudFront URL.
    """
    bucket_name = "fruitfulvinestorage"
    blog_folder = "blogimages"
    product_folder = "productimages"
    folder = None

    if is_product:
        folder = product_folder
    folder = blog_folder

    try:
        # Generate a unique filename to prevent overwriting
        filename = f"{folder}/{file_name}"
        # Upload the file
        s3_client.put_object(
            Bucket=bucket_name, Key=filename, Body=file_data, ContentType=content_type
        )

    except NoCredentialsError:
        return None
    except Exception as e:
        print(f"Error uploading: {e}")
        return None


def upload_file_to_cloudinary(file_data) -> dict:
    """
    Uploads a file to cloudinary.
    """
    try:
        upload_result = cloudinary.uploader.upload(
            file_data, resource_type="image", folder="fruitfulvine"
        )
        # Return the secure URL of the uploaded image
        return {
            "url": upload_result.get("url"),
            "secure_url": upload_result.get("secure_url"),
            "public_id": upload_result.get("public_id"),
        }

    except Exception as e:
        print(f"Error uploading: {e}")
        return {}
