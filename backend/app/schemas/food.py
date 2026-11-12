import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

FoodCategoryType = Literal[
    "staple",
    "vegetables",
    "protein",
    "fruits",
    "dairy",
    "fat_oil",
    "snack",
    "beverage",
]


class FoodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: FoodCategoryType
    serving_size_g: Decimal = Field(..., gt=0, decimal_places=2)
    energy_kcal: Decimal = Field(..., ge=0, decimal_places=2)
    carbohydrate_g: Decimal = Field(..., ge=0, decimal_places=2)
    protein_g: Decimal = Field(..., ge=0, decimal_places=2)
    fat_g: Decimal = Field(..., ge=0, decimal_places=2)
    fiber_g: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    sugar_g: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    glycemic_index: Optional[Decimal] = Field(None, ge=0, le=150, decimal_places=2)
    glycemic_load: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_test_data: bool = False
    source_name: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)


class FoodCreate(FoodBase):
    pass


class FoodUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[FoodCategoryType] = None
    serving_size_g: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    energy_kcal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    carbohydrate_g: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    protein_g: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fat_g: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    fiber_g: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    sugar_g: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    glycemic_index: Optional[Decimal] = Field(None, ge=0, le=150, decimal_places=2)
    glycemic_load: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    is_test_data: Optional[bool] = None
    source_name: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)


class FoodResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    serving_size_g: float
    energy_kcal: float
    carbohydrate_g: float
    protein_g: float
    fat_g: float
    fiber_g: Optional[float] = 0.0
    sugar_g: Optional[float] = 0.0
    glycemic_index: Optional[float] = None
    glycemic_load: Optional[float] = None
    is_test_data: bool
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

