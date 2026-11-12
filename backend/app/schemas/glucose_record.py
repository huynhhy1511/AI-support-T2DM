import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

GlucoseUnitType = Literal["mmol/L", "mg/dL"]
MeasurementContextType = Literal["fasting", "before_meal", "after_meal", "random", "other"]


class GlucoseRecordBase(BaseModel):
    measured_at: Optional[datetime] = None
    glucose_value: Decimal = Field(..., gt=0, le=1000, decimal_places=2)
    unit: GlucoseUnitType = "mmol/L"
    measurement_context: Optional[MeasurementContextType] = None
    note: Optional[str] = None


class GlucoseRecordCreate(GlucoseRecordBase):
    user_id: uuid.UUID


class GlucoseRecordUpdate(BaseModel):
    measured_at: Optional[datetime] = None
    glucose_value: Optional[Decimal] = Field(None, gt=0, le=1000, decimal_places=2)
    unit: Optional[GlucoseUnitType] = None
    measurement_context: Optional[MeasurementContextType] = None
    note: Optional[str] = None


class GlucoseRecordResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    measured_at: datetime
    glucose_value: float
    unit: str
    measurement_context: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlucoseStatsResponse(BaseModel):
    user_id: uuid.UUID
    count: int
    avg_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = "mmol/L"
