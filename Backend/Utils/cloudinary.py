import logging
from typing import Optional
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException, status
from Config.config import settings

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CYPHER_CRESCENT_CLOUDINARY_CLOUD_NAME,
    api_key=settings.CYPHER_CRESCENT_CLOUDINARY_API_KEY,
    api_secret=settings.CYPHER_CRESCENT_CLOUDINARY_API_SECRET,
    secure=True,
)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SUPPORTED_FORMATS = {"jpeg", "png", "webp", "gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

# Profile photos are capped to 512x512, auto-optimized and never store or serve a full-resolution upload.
PROFILE_PHOTO_TRANSFORM = [{
    "width": 512,
    "height": 512,
    "crop": "fill",
    "gravity": "auto",
    "quality": "auto",
    "fetch_format": "auto",
}]

# Getting the image format.
def detect_image_format(data: bytes) -> Optional[str]:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    # HEIC/HEIF (iPhone default): an ISO-BMFF "ftyp" box with a HEIF brand.
    if data[4:8] == b"ftyp" and data[8:12] in (b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1"):
        return "heic"
    return None

def upload_image_to_cloudinary(file: UploadFile, folder: str, transformation=PROFILE_PHOTO_TRANSFORM) -> str:
    contents = file.file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image exceeds the 5 MB limit")

    fmt = detect_image_format(contents)
    if fmt == "heic":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="HEIC images aren't supported. On iPhone: Settings → Camera → Formats → 'Most Compatible', or upload a JPG, PNG, or WebP.",
        )
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image format. Please upload a JPG, PNG, or WebP.",
        )

    file.file.seek(0)
    try:
        result = cloudinary.uploader.upload(
            file.file,
            folder=folder,
            resource_type="image",
            transformation=transformation,
        )
        return result["secure_url"]
    except Exception:
        logger.exception("Cloudinary upload failed for folder=%s", folder)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not process this image. Please try a different file.",
        )

def delete_image_from_cloudinary(image_url: str):
    try:
        parts = image_url.split("/upload/")
        if len(parts) != 2:
            return

        public_id_with_ext = parts[1].split("/", 1)[-1] if "/" in parts[1] else parts[1]
        # Remove version prefix
        if public_id_with_ext.startswith("v") and "/" in public_id_with_ext:
            public_id_with_ext = public_id_with_ext.split("/", 1)[1]

        public_id = public_id_with_ext.rsplit(".", 1)[0]  # remove extension

        cloudinary.uploader.destroy(public_id, resource_type="image")

    except Exception:
        pass
