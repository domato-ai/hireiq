from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from fastapi import Depends

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Async abstraction over Azure Blob Storage.

    Supports both connection-string auth (for local dev) and
    DefaultAzureCredential (managed identity in production).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: BlobServiceClient | None = None

    # ------------------------------------------------------------------ #
    # FastAPI dependency factory
    # ------------------------------------------------------------------ #

    @classmethod
    def from_settings(
        cls,
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> "StorageService":
        return cls(settings)

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _get_client(self) -> BlobServiceClient:
        if self._client is not None:
            return self._client

        s = self._settings
        if s.azure_storage_connection_string:
            self._client = BlobServiceClient.from_connection_string(
                s.azure_storage_connection_string
            )
        elif s.azure_storage_account_name:
            account_url = f"https://{s.azure_storage_account_name}.blob.core.windows.net"
            credential = DefaultAzureCredential()
            self._client = BlobServiceClient(account_url=account_url, credential=credential)
        else:
            raise RuntimeError(
                "Azure Storage is not configured. Set AZURE_STORAGE_CONNECTION_STRING "
                "or AZURE_STORAGE_ACCOUNT_NAME."
            )
        return self._client

    def _resolve_container(self, container: str) -> str:
        """Map a logical container name (e.g. 'resumes') to the configured one."""
        mapping = {
            "resumes": self._settings.azure_storage_container_resumes,
            "jd": self._settings.azure_storage_container_jds,
        }
        return mapping.get(container, container)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def upload(
        self,
        container: str,
        blob_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        overwrite: bool = True,
    ) -> str:
        """
        Upload ``data`` to Blob Storage and return the canonical blob URL.

        Args:
            container: Logical container alias ("resumes" or "jd") or a real container name.
            blob_name: Path within the container, e.g. ``{role_id}/{uuid}/{filename}``.
            data: Raw bytes to upload.
            content_type: MIME type set on the blob metadata.
            overwrite: Whether to overwrite an existing blob with the same name.

        Returns:
            Canonical HTTPS URL of the uploaded blob (without SAS token).
        """
        container_name = self._resolve_container(container)
        client = self._get_client()

        async with client:
            blob_client = client.get_blob_client(container=container_name, blob=blob_name)
            await blob_client.upload_blob(
                data,
                overwrite=overwrite,
                content_settings={"content_type": content_type},
            )
            url: str = blob_client.url
            logger.info("Uploaded blob: %s", url)
            return url

    async def download(self, container: str, blob_name: str) -> bytes:
        """
        Download a blob and return its contents as bytes.

        Args:
            container: Logical container alias or real container name.
            blob_name: Path within the container.

        Returns:
            Raw bytes of the blob content.
        """
        container_name = self._resolve_container(container)
        client = self._get_client()

        async with client:
            blob_client = client.get_blob_client(container=container_name, blob=blob_name)
            stream = await blob_client.download_blob()
            data: bytes = await stream.readall()
            return data

    async def get_signed_url(
        self,
        container: str,
        blob_name: str,
        expiry_hours: int | None = None,
        permission: BlobSasPermissions | None = None,
    ) -> str:
        """
        Generate a time-limited SAS URL for a blob.

        Args:
            container: Logical container alias or real container name.
            blob_name: Path within the container.
            expiry_hours: SAS token validity in hours (defaults to settings value).
            permission: Azure SAS permission set (defaults to read-only).

        Returns:
            Full HTTPS SAS URL.
        """
        s = self._settings
        container_name = self._resolve_container(container)
        hours = expiry_hours if expiry_hours is not None else s.azure_storage_sas_expiry_hours
        perm = permission or BlobSasPermissions(read=True)

        expiry = datetime.now(tz=timezone.utc) + timedelta(hours=hours)

        if not s.azure_storage_account_name or not s.azure_storage_account_key:
            raise RuntimeError(
                "SAS URL generation requires AZURE_STORAGE_ACCOUNT_NAME "
                "and AZURE_STORAGE_ACCOUNT_KEY to be set."
            )

        sas_token = generate_blob_sas(
            account_name=s.azure_storage_account_name,
            account_key=s.azure_storage_account_key,
            container_name=container_name,
            blob_name=blob_name,
            permission=perm,
            expiry=expiry,
        )

        url = (
            f"https://{s.azure_storage_account_name}.blob.core.windows.net"
            f"/{container_name}/{blob_name}?{sas_token}"
        )
        return url

    async def delete(self, container: str, blob_name: str) -> None:
        """Delete a blob. Silently succeeds if the blob does not exist."""
        container_name = self._resolve_container(container)
        client = self._get_client()

        async with client:
            blob_client = client.get_blob_client(container=container_name, blob=blob_name)
            await blob_client.delete_blob(delete_snapshots="include")
            logger.info("Deleted blob: %s/%s", container_name, blob_name)
