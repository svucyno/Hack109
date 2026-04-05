from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

from django.conf import settings

try:
    import boto3
except ImportError:  # pragma: no cover - optional dependency
    boto3 = None


def _safe_filename(filename: str) -> str:
    return Path(filename).name or 'resume.pdf'


def _s3_client() -> Any:
    if boto3 is None:
        return None
    client_kwargs: dict[str, str] = {}
    if settings.RESUME_STORAGE_REGION:
        client_kwargs['region_name'] = settings.RESUME_STORAGE_REGION
    if settings.RESUME_STORAGE_ENDPOINT_URL:
        client_kwargs['endpoint_url'] = settings.RESUME_STORAGE_ENDPOINT_URL
    if settings.RESUME_STORAGE_ACCESS_KEY_ID:
        client_kwargs['aws_access_key_id'] = settings.RESUME_STORAGE_ACCESS_KEY_ID
    if settings.RESUME_STORAGE_SECRET_ACCESS_KEY:
        client_kwargs['aws_secret_access_key'] = settings.RESUME_STORAGE_SECRET_ACCESS_KEY
    return boto3.client('s3', **client_kwargs)


def build_storage_key(reference_no: str, filename: str) -> str:
    safe_name = _safe_filename(filename)
    return f"{settings.RESUME_STORAGE_PREFIX}/{safe_name}" if settings.RESUME_STORAGE_PREFIX else safe_name


def _should_use_s3() -> bool:
    return bool(settings.RESUME_STORAGE_BUCKET) and boto3 is not None


def is_s3_configured() -> bool:
    return _should_use_s3()


def generate_presigned_upload_url(reference_no: str, filename: str, content_type: str | None) -> dict[str, str | int]:
    if not _should_use_s3():
        raise RuntimeError('S3 is not configured for pre-signed uploads.')

    key = build_storage_key(reference_no, filename)
    client = _s3_client()
    expires_in = settings.RESUME_PRESIGNED_URL_EXPIRY_SECONDS

    params: dict[str, str] = {
        'Bucket': settings.RESUME_STORAGE_BUCKET,
        'Key': key,
    }

    upload_url = client.generate_presigned_url(
        ClientMethod='put_object',
        Params=params,
        ExpiresIn=expires_in,
    )

    return {
        'upload_url': upload_url,
        'storage_key': key,
        'storage_uri': f"s3://{settings.RESUME_STORAGE_BUCKET}/{key}",
        'expires_in': expires_in,
    }


def get_s3_object_metadata(storage_key: str) -> dict[str, str | int | None]:
    if not _should_use_s3():
        raise RuntimeError('S3 is not configured for metadata checks.')
    client = _s3_client()
    head = client.head_object(Bucket=settings.RESUME_STORAGE_BUCKET, Key=storage_key)
    return {
        'content_length': head.get('ContentLength'),
        'etag': str(head.get('ETag', '')).strip('"'),
    }


def store_resume_file(reference_no: str, filename: str, content: bytes, content_type: str | None) -> dict[str, str]:
    safe_name = _safe_filename(filename)
    storage_name = f"{reference_no}-{safe_name}"

    if _should_use_s3():
        key = build_storage_key(reference_no, filename)
        client = _s3_client()
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        client.upload_fileobj(BytesIO(content), settings.RESUME_STORAGE_BUCKET, key, ExtraArgs=extra_args or None)
        return {
            'storage_backend': 's3',
            'storage_uri': f"s3://{settings.RESUME_STORAGE_BUCKET}/{key}",
            'storage_key': key,
            'filename': storage_name,
        }

    storage_dir = Path(settings.RESUME_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    local_path = storage_dir / storage_name
    local_path.write_bytes(content)
    return {
        'storage_backend': 'local',
        'storage_uri': str(local_path),
        'storage_key': str(local_path),
        'filename': storage_name,
    }


def read_resume_file(storage_backend: str, storage_key: str) -> bytes:
    if storage_backend == 's3':
        if not _should_use_s3():
            raise RuntimeError('S3 is not configured for reads.')
        client = _s3_client()
        obj = client.get_object(Bucket=settings.RESUME_STORAGE_BUCKET, Key=storage_key)
        return obj['Body'].read()

    return Path(storage_key).read_bytes()