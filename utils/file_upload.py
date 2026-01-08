import boto3
from botocore.exceptions import NoCredentialsError
import uuid
import os

# Initialize S3 Client
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def upload_file_to_s3(file_data, is_product=True):
    """
    Uploads a file to S3 and returns the CloudFront URL.
    """
    bucket_name="fruitfulvinestorage"
    blog_folder="blogimages"
    product_folder="productimages"
    folder=None
    
    if is_product:
        folder=product_folder
    folder=blog_folder

    try:
        # Generate a unique filename to prevent overwriting
        filename = f"{folder}/{uuid.uuid4()}"
        
        # Upload the file
        s3_client.put_object(
            Bucket=bucket_name,
            Key=filename,
            Body=file_data,
        )
        
        # Construct the CLOUDFRONT URL (not the S3 URL)
        # cloudfront_domain = os.getenv("CLOUDFRONT_DOMAIN") # e.g., d111.cloudfront.net
        # return f"https://{cloudfront_domain}/{filename}"

    except NoCredentialsError:
        return None
    except Exception as e:
        print(f"Error uploading: {e}")
        return None