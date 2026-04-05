# storage.py  — Supabase Storage backend
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
SUPABASE_BUCKET      = os.getenv("SUPABASE_BUCKET", "files").strip()


def _storage_url(key: str) -> str:
    """Public URL of the uploaded object."""
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{key}"


async def upload_bytes_to_s3(data: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """
    Upload *data* to Supabase Storage at path *key* inside SUPABASE_BUCKET.
    Returns the public URL of the uploaded object.
    Compatible drop-in for the old YC S3 function — same signature.
    """
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{key}"

    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",          # overwrite if already exists
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(upload_url, data=data, headers=headers) as resp:
            if resp.status not in (200, 201):
                body = await resp.text()
                raise RuntimeError(
                    f"Supabase Storage upload failed [{resp.status}]: {body}"
                )

    return _storage_url(key)


async def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    """
    Generate a signed (time-limited) URL for *key* via Supabase Storage API.
    Falls back to the public URL if the bucket is public.
    """
    sign_url = (
        f"{SUPABASE_URL}/storage/v1/object/sign/{SUPABASE_BUCKET}/{key}"
    )
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"expiresIn": expires_in}

    async with aiohttp.ClientSession() as session:
        async with session.post(sign_url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                signed_path = data.get("signedURL", "")
                return f"{SUPABASE_URL}{signed_path}"
            # If signing fails (e.g. public bucket), return plain public URL
            return _storage_url(key)
