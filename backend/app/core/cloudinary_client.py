"""
Thin wrapper around the Cloudinary SDK for certificate/avatar uploads.
Configured lazily from Settings so importing this module never fails
even when Cloudinary credentials aren't set.
"""
from dataclasses import dataclass
from typing import BinaryIO

import cloudinary
import cloudinary.uploader

from app.core.config import get_settings

_configured = False


def _ensure_configured() -> None:
    global _configured
    if _configured:
        return
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
    )
    _configured = True


@dataclass
class UploadResult:
    url: str
    public_id: str


def upload_file(file: BinaryIO, *, folder: str) -> UploadResult:
    """Raises RuntimeError if Cloudinary isn't configured."""
    settings = get_settings()
    if not settings.CLOUDINARY_CLOUD_NAME:
        raise RuntimeError("Cloudinary is not configured (CLOUDINARY_CLOUD_NAME is empty)")

    _ensure_configured()
    result = cloudinary.uploader.upload(file, folder=folder, resource_type="auto")
    return UploadResult(url=result["secure_url"], public_id=result["public_id"])


def delete_file(public_id: str) -> None:
    _ensure_configured()
    cloudinary.uploader.destroy(public_id)
