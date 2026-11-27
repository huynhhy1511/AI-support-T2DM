import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

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

PreparationStateType = Literal["raw", "cooked", "ready_to_eat"]


class AllergenResponse(BaseModel):
    id: uuid.UUID
    code: str
    name_vi: str
    name_en: str

    model_config = ConfigDict(from_attributes=True)


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
    sodium_mg: Optional[float] = Field(default=None, ge=0)
    saturated_fat_g: Optional[float] = Field(default=None, ge=0)
    preparation_state: PreparationStateType = "cooked"
    data_source: str = Field(default="VN_NIN_USDA", min_length=1, max_length=100)
    data_version: str = Field(default="v1.0", min_length=1, max_length=30)
    is_test_data: bool = False
    source_name: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)
    allergen_codes: Optional[List[str]] = Field(default=None)


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
    sodium_mg: Optional[float] = Field(default=None, ge=0)
    saturated_fat_g: Optional[float] = Field(default=None, ge=0)
    preparation_state: Optional[PreparationStateType] = None
    data_source: Optional[str] = Field(None, min_length=1, max_length=100)
    data_version: Optional[str] = Field(None, min_length=1, max_length=30)
    is_test_data: Optional[bool] = None
    source_name: Optional[str] = Field(None, max_length=255)
    source_url: Optional[str] = Field(None, max_length=500)
    allergen_codes: Optional[List[str]] = None


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
    sodium_mg: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    preparation_state: str
    data_source: str
    data_version: str
    is_test_data: bool
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    allergens: List[AllergenResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FoodAlternativeResponse(FoodResponse):
    kcal_diff: float
    gi_diff: Optional[float] = None
    similarity_reason: str
