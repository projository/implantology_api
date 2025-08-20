from fastapi import Query, APIRouter, UploadFile, File, HTTPException, status
from app.utils.s3 import get_all_keys_from_s3, upload_file_to_s3, generate_presigned_url, get_file_from_s3, delete_file_from_s3
from app.core.config import settings
import random
import string
from PIL import Image, ImageFilter
from io import BytesIO
from fastapi.responses import Response
import os

router = APIRouter()

# Constants
THUMBNAIL_SIZE = (10, 10)


def generate_key() -> str:
    return ''.join(random.choice(string.ascii_letters) for _ in range(40))


def validate_file(file: UploadFile):
    file_extension = file.filename.split(".")[-1].lower()
    file_size_mb = len(file.file.read()) / (1024 * 1024)
    file.file.seek(0)  # Reset file pointer after reading

    if file_extension in settings.ALLOWED_IMAGE_EXTENSIONS:
        if file_size_mb > settings.MAX_IMAGE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image file too large",
            )
    elif file_extension in settings.ALLOWED_VIDEO_EXTENSIONS:
        if file_size_mb > settings.MAX_VIDEO_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Video file too large",
            )
    elif file_extension in settings.ALLOWED_DOC_EXTENSIONS:
        if file_size_mb > settings.MAX_DOC_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Document file too large",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type"
        )


@router.get("", response_model=dict)
async def get_all_attachments(
    keyword: str = Query(None, description="Search query string"),  # Optional
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
):
    response = get_all_keys_from_s3(
        bucket_name=settings.S3_BUCKET_NAME,
        prefix="",
        page=page,
        per_page=per_page
    )

    if not keyword :
        return response
    else:
        all_keys = response["keys"]

        # Filter keys based on search query (case-insensitive)
        filtered_keys = [key for key in all_keys if keyword.lower() in key.lower()]

        # Filter keys based on search query (case-insensitive)
        filtered_keys = [key for key in all_keys if keyword in key]

        total = len(filtered_keys)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_keys = filtered_keys[start:end]

        return {
            "keys": paginated_keys,
            "pagination": {
                "current_page": page,
                "per_page": per_page,
                "total": total,
                "last_page": (total + per_page - 1) // per_page
            }
        }


@router.post("", response_model=dict)
async def upload_attachment(
    file: UploadFile = File(...)
):
    validate_file(file)

    file_extension = file.filename.split(".")[-1].lower()
    
    key = generate_key()
    object_key = f"{key}.{file_extension}"

    upload_file_to_s3(file.file, settings.S3_BUCKET_NAME, object_key)

    return {
        "object_key": object_key 
    }


@router.get("/presigned-url/{object_key}", response_model=dict)
async def get_presigned_url(object_key: str):
    presigned_url = generate_presigned_url(settings.S3_BUCKET_NAME, object_key)
    return {"object_key": object_key, "presigned_url": presigned_url}


# @router.get("/download/{object_key}", response_model=dict)
# def download_attachment(object_key: str):
#     downloaded_path = download_file_to_s3(settings.S3_BUCKET_NAME, object_key, object_key)
#     return {"object_key": object_key, "downloaded_path": downloaded_path}


@router.get("/image/{object_key}")
async def get_image(
    object_key: str,
    thumbnail: bool = Query(False),
    w: int = Query(None),
    q: int = Query(75)
):
    # Step 1: Fetch image bytes from S3
    try:
        image_bytes = get_file_from_s3(settings.S3_BUCKET_NAME, object_key)
    except Exception as e:
        return Response(content=f"Error fetching image: {e}", status_code=500)

    # Step 2: Open the image using Pillow
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")  # WEBP requires RGB mode
    except Exception:
        return Response(content="Invalid image format", status_code=400)

    # Step 3: Resize and blur thumbnail (if `thumbnail` is set) or Resize while preserving aspect ratio (if `w` is set)
    if thumbnail:
        image = image.resize(THUMBNAIL_SIZE)
        image = image.filter(ImageFilter.GaussianBlur(radius=1))
    elif w:
        aspect_ratio = image.height / image.width
        new_height = int(w * aspect_ratio)
        image = image.resize((w, new_height))

    # Step 4: Encode to WEBP
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=q)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="image/webp",
        headers={
            "Cache-Control": "public, max-age=31536000",  # cache for 1 year
            "Expires": "Tue, 22 Jul 2026 20:00:00 GMT"
        }
    )


@router.delete("/{object_key}")
def delete_attachment(object_key: str):
    delete_file_from_s3(settings.S3_BUCKET_NAME, object_key)
    return {"message": f"File '{object_key}' deleted successfully."}