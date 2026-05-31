from pydantic import BaseModel, EmailStr
from datetime import datetime
from uuid import UUID
from typing import Optional
from app.models.user import UserRole, SubscriptionTier


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: UserRole
    subscription_tier: SubscriptionTier
    is_active: bool
    is_verified: bool
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
