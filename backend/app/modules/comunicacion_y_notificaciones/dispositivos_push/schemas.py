from __future__ import annotations

from pydantic import BaseModel, Field


class FcmTokenRegisterIn(BaseModel):
    token: str = Field(..., min_length=32, max_length=512)
    platform: str | None = Field(None, max_length=20)
