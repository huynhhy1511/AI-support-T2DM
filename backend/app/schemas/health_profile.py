import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field

SexType = Literal["male", "female", "other"]
ActivityLevelType = Literal["sedentary", "light", "moderate", "active", "very_active"]


class HealthProfileBase(BaseModel):
    date_of_birth: Optional[date] = None
    sex: Optional[SexType] = None
    height_cm: Optional[Decimal] = Field(None, gt=0, le=300, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, gt=0, le=500, decimal_places=2)
    diabetes_type: str = Field(default="type2", max_length=50)
    diagnosis_year: Optional[int] = Field(None, ge=1900, le=2100)
    activity_level: Optional[ActivityLevelType] = None
    dietary_preference: Optional[str] = Field(None, max_length=100)


class HealthProfileCreate(HealthProfileBase):
    user_id: uuid.UUID


class HealthProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    sex: Optional[SexType] = None
    height_cm: Optional[Decimal] = Field(None, gt=0, le=300, decimal_places=2)
    weight_kg: Optional[Decimal] = Field(None, gt=0, le=500, decimal_places=2)
    diabetes_type: Optional[str] = Field(None, max_length=50)
    diagnosis_year: Optional[int] = Field(None, ge=1900, le=2100)
    activity_level: Optional[ActivityLevelType] = None
    dietary_preference: Optional[str] = Field(None, max_length=100)


class HealthProfileResponse(HealthProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    updated_at: datetime

    @computed_field
    @property
    def bmi(self) -> Optional[float]:
        """Calculate Body Mass Index (BMI) = weight (kg) / (height (m) ^ 2)."""
        if self.height_cm and self.weight_kg and self.height_cm > 0:
            height_m = float(self.height_cm) / 100.0
            bmi_val = float(self.weight_kg) / (height_m * height_m)
            return round(bmi_val, 2)
        return None

    model_config = ConfigDict(from_attributes=True)
