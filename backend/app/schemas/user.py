import uuid
from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

# Email regex pattern that does not require the third-party email-validator package
EmailPattern = Annotated[
    str,
    Field(
        pattern=r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$",
        max_length=255,
        examples=["user@example.com"],
    ),
]


class UserCreate(BaseModel):
    email: EmailPattern
    display_name: Optional[str] = Field(None, max_length=255)
    consent_accepted: bool = False


class UserUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    consent_accepted: Optional[bool] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str] = None
    consent_accepted_at: Optional[datetime] = None
    created_at: datetime

    @computed_field
    @property
    def full_name(self) -> Optional[str]:
        """Alias for display_name to match Frontend user profile contract."""
        return self.display_name

    model_config = ConfigDict(from_attributes=True)
