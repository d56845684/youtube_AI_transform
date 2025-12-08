"""Helpers for retrieving video provider configuration values."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .logger import get_logger

logger = get_logger(__name__)


class VideoProviderError(Exception):
    """Raised when video provider configuration is missing or invalid."""


async def _get_zoom_provider(db: AsyncSession) -> models.VideoProvider:
    result = await db.execute(
        select(models.VideoProvider).where(models.VideoProvider.provider.ilike("zoom"))
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise VideoProviderError("Zoom provider is not configured in video_providers table")

    return provider


async def get_zoom_credentials(db: AsyncSession) -> dict:
    """Return Zoom credentials from the ``video_providers`` table."""

    provider = await _get_zoom_provider(db)
    missing_fields = [
        field for field in ("client_id", "client_secret", "account_id") if not getattr(provider, field)
    ]
    if missing_fields:
        missing_str = ", ".join(missing_fields)
        raise VideoProviderError(f"Zoom provider missing required fields: {missing_str}")

    return {
        "client_id": provider.client_id,
        "client_secret": provider.client_secret,
        "account_id": provider.account_id,
    }
