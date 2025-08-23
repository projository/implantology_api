import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import HTTPException, status
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def get_all_keys_from_s3(
    bucket_name: str,
    prefix: str = "",
    page: int = 1,
    per_page: int = 10
) -> dict:
    all_objects = []
    paginator = s3_client.get_paginator("list_objects_v2")

    # Step 1: Collect all objects
    for page_data in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        contents = page_data.get("Contents", [])
        all_objects.extend(contents)

    # Step 2: Sort by LastModified (newest first)
    all_objects.sort(key=lambda x: x["LastModified"], reverse=True)

    # Step 3: Extract keys
    total = len(all_objects)
    start = (page - 1) * per_page
    end = start + per_page
    page_keys = [obj["Key"] for obj in all_objects[start:end]]

    # Step 4: Calculate last page
    value = total / per_page
    last_page = int(value) if value == int(value) else int(value) + 1

    return {
        "keys": page_keys,
        "pagination": {
            "current_page": page,
            "per_page": per_page,
            "total": total,
            "last_page": last_page
        }
    }


def upload_file_to_s3(file, bucket_name, object_key):
    try:
        s3_client.upload_fileobj(file, bucket_name, object_key)
    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="AWS credentials not found"
        )


def generate_presigned_url(bucket_name, object_key, expiration=3600):
    try:
        # Check if object exists
        s3_client.head_object(Bucket=bucket_name, Key=object_key)

        # Generate presigned URL if object exists
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
    except s3_client.exceptions.ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with object_key '{object_key}' not found in bucket '{bucket_name}'.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AWS ClientError: {str(e)}",
            )
    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AWS credentials not found"
        )

    return response


def get_file_from_s3(bucket_name: str, object_key: str) -> bytes:
    try:
        # Check if the object exists
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        
        # If exists, proceed to get the object
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        return response["Body"].read()

    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AWS credentials not found"
        )
    except s3_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == "404" or error_code == "NoSuchKey":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with object_key '{object_key}' not found in bucket '{bucket_name}'.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch file: {str(e)}"
        )
    

def delete_file_from_s3(bucket_name: str, object_key: str):
    try:
        # Check if the object exists
        s3_client.head_object(Bucket=bucket_name, Key=object_key)
        
        # Proceed to delete
        s3_client.delete_object(Bucket=bucket_name, Key=object_key)

    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AWS credentials not found"
        )
    except s3_client.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code in ("404", "NoSuchKey"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with object_key '{object_key}' not found in bucket '{bucket_name}'.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"S3 error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )

    
# def download_file_to_s3(bucket_name, object_key, download_path):
#     try:
#         # Check if object exists
#         s3_client.head_object(Bucket=bucket_name, Key=object_key)

#         # Proceed to download if object exists
#         s3_client.download_file(bucket_name, object_key, download_path)
#         return download_path

#     except (NoCredentialsError, PartialCredentialsError):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="AWS credentials not found"
#         )

#     except ClientError as e:
#         error_code = e.response['Error']['Code']
#         if error_code == '404' or error_code == 'NoSuchKey':
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"File with key '{object_key}' not found in bucket '{bucket_name}'."
#             )
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail=f"An AWS error occurred: {str(e)}"
#             )

#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"An unexpected error occurred: {str(e)}"
#         )