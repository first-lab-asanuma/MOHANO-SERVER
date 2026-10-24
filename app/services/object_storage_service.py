from __future__ import annotations

from uuid import UUID, uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings
from app.core.errors import ServiceError
from app.schemas.profile import ProfilePhotoUploadRequest, ProfilePhotoUploadUrl


class ObjectStorageService:
    """S3-compatible private profile-photo storage boundary.

    Silo and Cloudflare R2 share this API. Object keys never leave the service
    layer; API clients receive only short-lived signed URLs.
    """

    _allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/heic",
        "image/heif",
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = self._new_client(settings.object_storage_endpoint)
        self._presigning_client = self._new_client(
            settings.object_storage_public_endpoint or settings.object_storage_endpoint,
        )

    def create_upload_url(self, user_id: str, payload: ProfilePhotoUploadRequest) -> ProfilePhotoUploadUrl:
        content_type = self._normalize_content_type(payload.content_type)
        if payload.content_length > self._settings.profile_photo_max_bytes:
            raise ServiceError("photo_too_large", "Photos must be 10 MB or smaller", 400)

        upload_id = str(uuid4())
        key = self.staging_key(user_id, upload_id)
        try:
            upload_url = self._presigning_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": self._settings.object_storage_bucket, "Key": key, "ContentType": content_type},
                ExpiresIn=self._settings.object_storage_upload_url_expire_seconds,
                HttpMethod="PUT",
            )
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error
        return ProfilePhotoUploadUrl(
            upload_id=upload_id,
            upload_url=upload_url,
            content_type=content_type,
            expires_in_seconds=self._settings.object_storage_upload_url_expire_seconds,
        )

    def validate_staged_upload(self, user_id: str, upload_id: str) -> tuple[str, str]:
        key = self.staging_key(user_id, upload_id)
        try:
            metadata = self._client.head_object(Bucket=self._settings.object_storage_bucket, Key=key)
            content_length = int(metadata.get("ContentLength", 0))
            content_type = self._normalize_content_type(str(metadata.get("ContentType", "")))
            if content_length <= 0 or content_length > self._settings.profile_photo_max_bytes:
                raise ServiceError("photo_too_large", "Photos must be 10 MB or smaller", 400)
            response = self._client.get_object(
                Bucket=self._settings.object_storage_bucket,
                Key=key,
                Range="bytes=0-31",
            )
            try:
                header = response["Body"].read()
            finally:
                response["Body"].close()
        except ServiceError:
            self._delete_quietly(key)
            raise
        except (BotoCoreError, ClientError) as error:
            raise ServiceError("photo_upload_missing", "The uploaded photo could not be found. Please try again.", 400) from error

        if not self._matches_image_signature(header, content_type):
            self._delete_quietly(key)
            raise ServiceError("photo_invalid", "Choose a valid JPEG, PNG, WebP, HEIC, or HEIF image", 400)
        return key, content_type

    @staticmethod
    def normalize_upload_id(upload_id: str) -> str:
        try:
            return str(UUID(upload_id))
        except ValueError as error:
            raise ServiceError("photo_upload_invalid", "The photo upload request is invalid. Please try again.", 400) from error

    def promote(self, staging_key: str, final_key: str, content_type: str) -> None:
        try:
            self._client.copy_object(
                Bucket=self._settings.object_storage_bucket,
                Key=final_key,
                CopySource={"Bucket": self._settings.object_storage_bucket, "Key": staging_key},
                ContentType=content_type,
                MetadataDirective="REPLACE",
            )
            self._client.delete_object(Bucket=self._settings.object_storage_bucket, Key=staging_key)
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error

    def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._settings.object_storage_bucket, Key=key)
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error

    def delete_user_objects(self, user_id: str) -> None:
        """Remove both completed and abandoned staged uploads for a withdrawing user."""
        try:
            for prefix in (f"profiles/{user_id}/", f"staging/{user_id}/"):
                continuation_token = None
                while True:
                    request = {"Bucket": self._settings.object_storage_bucket, "Prefix": prefix}
                    if continuation_token is not None:
                        request["ContinuationToken"] = continuation_token
                    response = self._client.list_objects_v2(**request)
                    objects = [{"Key": item["Key"]} for item in response.get("Contents", [])]
                    if objects:
                        self._client.delete_objects(
                            Bucket=self._settings.object_storage_bucket,
                            Delete={"Objects": objects, "Quiet": True},
                        )
                    if not response.get("IsTruncated"):
                        break
                    continuation_token = response.get("NextContinuationToken")
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error

    def download_url(self, key: str) -> str:
        try:
            return self._presigning_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._settings.object_storage_bucket, "Key": key},
                ExpiresIn=self._settings.object_storage_read_url_expire_seconds,
                HttpMethod="GET",
            )
        except (BotoCoreError, ClientError) as error:
            raise self._unavailable(error) from error

    @staticmethod
    def staging_key(user_id: str, upload_id: str) -> str:
        return f"staging/{user_id}/{upload_id}/original"

    @staticmethod
    def profile_key(user_id: str, photo_id: str) -> str:
        return f"profiles/{user_id}/{photo_id}/original"

    def _new_client(self, endpoint_url: str):
        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=self._settings.object_storage_access_key,
            aws_secret_access_key=self._settings.object_storage_secret_key,
            region_name=self._settings.object_storage_region,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        )

    def _delete_quietly(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._settings.object_storage_bucket, Key=key)
        except (BotoCoreError, ClientError):
            pass

    def _normalize_content_type(self, value: str) -> str:
        content_type = value.split(";", 1)[0].strip().lower()
        if content_type not in self._allowed_content_types:
            raise ServiceError("photo_type_not_supported", "Choose a JPEG, PNG, WebP, HEIC, or HEIF image", 400)
        return content_type

    @staticmethod
    def _matches_image_signature(header: bytes, content_type: str) -> bool:
        if content_type == "image/jpeg":
            return header.startswith(b"\xff\xd8\xff")
        if content_type == "image/png":
            return header.startswith(b"\x89PNG\r\n\x1a\n")
        if content_type == "image/webp":
            return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        if content_type in {"image/heic", "image/heif"}:
            return len(header) >= 12 and header[4:8] == b"ftyp" and header[8:12] in {b"heic", b"heix", b"hevc", b"hevx", b"mif1"}
        return False

    @staticmethod
    def _unavailable(_: Exception) -> ServiceError:
        return ServiceError("photo_storage_unavailable", "Photo storage is temporarily unavailable. Please try again.", 503)
