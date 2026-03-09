from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, BaseModel, Field


class LinkCreate(BaseModel):
    original_url: AnyHttpUrl
    custom_alias: Optional[str] = Field(default=None, min_length=3, max_length=50)
    expires_at: Optional[datetime] = None
    project_id: Optional[int] = None


class LinkUpdate(BaseModel):
    original_url: Optional[AnyHttpUrl] = None
    new_alias: Optional[str] = Field(default=None, min_length=3, max_length=50)
    expires_at: Optional[datetime] = None


class LinkOut(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime]
    owner_id: Optional[int]
    project_id: Optional[int]


class LinkStats(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    click_count: int
    last_accessed_at: Optional[datetime]
    expires_at: Optional[datetime]


class ExpiredLinkOut(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expired_at: datetime
    last_accessed_at: Optional[datetime]
    click_count: int

    model_config = {'from_attributes': True}
