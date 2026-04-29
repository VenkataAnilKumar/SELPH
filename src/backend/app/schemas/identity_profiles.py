"""Schemas for multi-identity profile management."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class IdentityVariantCreateRequest(BaseModel):
    profile_name: str = Field(min_length=1, max_length=100)
    profile_type: str = Field(default="personal_brand", min_length=1, max_length=50)
    vocabulary_description: Optional[str] = None
    communication_style: Optional[str] = None


class IdentityVariantUpdateRequest(BaseModel):
    profile_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    profile_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    vocabulary_description: Optional[str] = None
    communication_style: Optional[str] = None


class IdentityVariantResponse(BaseModel):
    id: str
    profile_name: str
    profile_type: str
    is_primary: bool
    is_active: bool
    vocabulary_description: Optional[str] = None
    communication_style: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class IdentityVariantListResponse(BaseModel):
    total: int
    items: list[IdentityVariantResponse]


class ChannelProfileMappingUpsertRequest(BaseModel):
    profile_id: str
    channel: str
    platform_account: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=10)


class ChannelProfileMappingResponse(BaseModel):
    id: str
    profile_id: str
    channel: str
    platform_account: Optional[str] = None
    priority: int

    model_config = ConfigDict(from_attributes=True)


class ChannelProfileMappingListResponse(BaseModel):
    total: int
    items: list[ChannelProfileMappingResponse]
